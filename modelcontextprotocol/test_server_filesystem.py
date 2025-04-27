import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def start_server(server_config):
    command = [server_config["command"]] + server_config["args"]
    print(f"Starting MCP server with command: {' '.join(command)}")
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return proc


def main():
    config = load_config()
    fs_server = config["mcpServers"]["filesystem"]
    proc = start_server(fs_server)

    try:
        print("Server started. Waiting for it to be ready...")
        time.sleep(2)  # Wait for server to start

        # Get directories from config
        directories = [arg for arg in fs_server["args"] if arg.startswith("/Users/")]
        if not directories:
            print("Error: No directories found in config.")
            return
            
        print(f"Configured directories: {directories}")
        
        # Set up stderr reader thread
        def print_stderr(proc):
            for line in iter(proc.stderr.readline, b''):
                print(f"[SERVER STDERR] {line.decode().rstrip()}")
        threading.Thread(target=print_stderr, args=(proc,), daemon=True).start()
        
        # Function to send a JSON-RPC request and get the response
        def send_json_rpc(method, params, req_id):
            req = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params
            }
            print(f"[DEBUG] Sending: {json.dumps(req)}")
            proc.stdin.write((json.dumps(req) + "\n").encode())
            proc.stdin.flush()
            
            # Read response
            while True:
                line = proc.stdout.readline()
                if not line:
                    print("[DEBUG] No more output from server.")
                    break
                    
                line_str = line.decode().rstrip()
                print(f"[SERVER STDOUT] {line_str}")
                
                try:
                    resp = json.loads(line_str)
                    if resp.get("id") == req_id:
                        return resp
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] Not JSON: {e}")
                    continue
            return None
        
        # Initialize the server with protocol version
        print("[DEBUG] Initializing server...")
        init_resp = send_json_rpc("initialize", {
            "protocolVersion": "2024-11-05",  # Use the version from previous response
            "clientInfo": {"name": "mcp-python-client", "version": "1.0.0"},
            "capabilities": {}
        }, 0)
        
        if init_resp and "result" in init_resp:
            print(f"[DEBUG] Server initialized successfully: {init_resp['result']}")
        else:
            print("[DEBUG] Failed to initialize server properly.")
        
        # Function to count files in a directory using the MCP server
        def count_files_in_directory(path, req_id):
            print(f"\nCounting files in {path}...")
            
            # Use the exact format from the curl example
            resp = send_json_rpc("tools/call", {
                "name": "list_directory",
                "arguments": {"path": path},
                "_meta": {"progressToken": req_id}
            }, req_id)
            
            print(f"[DEBUG] Response: {resp}")
            
            if resp and "result" in resp:
                print(f"[DEBUG] Got result from tools/call")
                result = resp["result"]
                
                # Handle different possible response formats
                entries = []
                if isinstance(result, list):
                    entries = result
                elif isinstance(result, dict) and "entries" in result:
                    entries = result["entries"]
                elif isinstance(result, dict) and "content" in result:
                    content = result["content"]
                    if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                        entries = content[0]["text"].split('\n')
                
                # Count files in the entries
                file_count = sum(1 for entry in entries if isinstance(entry, str) and entry.startswith("[FILE]"))
                return file_count
            
            return None
        
        # Count files in each directory
        for i, directory in enumerate(directories, 1):
            file_count = count_files_in_directory(directory, i)
            if file_count is not None:
                print(f"{directory}: {file_count} files")
            else:
                print(f"{directory}: Could not count files.")
        
        print("\nDone. Press Ctrl+C to stop the server.")
        
        # Keep server running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    except KeyboardInterrupt:
        print("Stopping server...")
        proc.terminate()
        proc.wait()
        print("Server stopped.")


if __name__ == "__main__":
    main()
