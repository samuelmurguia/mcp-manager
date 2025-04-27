#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path

# Default config file location
DEFAULT_CONFIG_PATH = Path(os.path.expanduser("~/.mcpm/config.json"))

def ensure_config_dir():
    """Ensure the config directory exists."""
    config_dir = DEFAULT_CONFIG_PATH.parent
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def load_config():
    """Load the MCP configuration."""
    if not DEFAULT_CONFIG_PATH.exists():
        return {"mcpServers": {}}
    
    try:
        with open(DEFAULT_CONFIG_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {DEFAULT_CONFIG_PATH}")
        return {"mcpServers": {}}

def save_config(config):
    """Save the MCP configuration."""
    ensure_config_dir()
    with open(DEFAULT_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {DEFAULT_CONFIG_PATH}")

def cmd_ls(args):
    """List all configured MCP servers."""
    config = load_config()
    
    if not config.get("mcpServers"):
        print("No MCP servers configured.")
        return
    
    print("Configured MCP servers:")
    for server_name, server_config in config["mcpServers"].items():
        command = server_config.get("command", "")
        server_args = server_config.get("args", [])
        args_str = " ".join(server_args)
        print(f"  {server_name}: {command} {args_str}")

def cmd_rm(args):
    """Remove an MCP server configuration."""
    config = load_config()
    
    if args.server_name not in config.get("mcpServers", {}):
        print(f"Error: Server '{args.server_name}' not found.")
        return
    
    del config["mcpServers"][args.server_name]
    save_config(config)
    print(f"Server '{args.server_name}' removed.")

def parse_server_config(args):
    """Parse server configuration from arguments."""
    if hasattr(args, 'config_string'):
        # Parse the configuration string
        parts = args.config_string.split()
        if len(parts) < 2:
            print("Error: Configuration string must contain at least server name and command")
            return None, None, None
            
        server_name = parts[0]
        command = parts[1]
        command_args = parts[2:] if len(parts) > 2 else []
    else:
        # Using the traditional argument format
        server_name = args.server_name
        command = args.command
        command_args = args.args if hasattr(args, 'args') and args.args else []
        
    return server_name, command, command_args

def cmd_add_server(args):
    """Add a new MCP server configuration."""
    config = load_config()
    
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    server_name, command, command_args = parse_server_config(args)
    if not server_name:
        return
    
    # Check if server already exists
    if server_name in config["mcpServers"]:
        print(f"Error: Server '{server_name}' already exists. Use 'set-server' to update it.")
        return
    
    server_config = {
        "command": command,
        "args": command_args
    }
    
    config["mcpServers"][server_name] = server_config
    save_config(config)
    print(f"Server '{server_name}' added.")
    
    # Print the configuration for verification
    print("\nConfiguration:")
    print(f"  Command: {command}")
    print(f"  Args: {' '.join(command_args)}")
    print(f"  Saved to: {DEFAULT_CONFIG_PATH}")

def cmd_set_server(args):
    """Update an existing MCP server configuration."""
    config = load_config()
    
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    server_name, command, command_args = parse_server_config(args)
    if not server_name:
        return
    
    # Check if server exists
    if server_name not in config["mcpServers"]:
        print(f"Error: Server '{server_name}' does not exist. Use 'add-server' to create it.")
        return
    
    server_config = {
        "command": command,
        "args": command_args
    }
    
    config["mcpServers"][server_name] = server_config
    save_config(config)
    print(f"Server '{server_name}' updated.")
    
    # Print the configuration for verification
    print("\nConfiguration:")
    print(f"  Command: {command}")
    print(f"  Args: {' '.join(command_args)}")
    print(f"  Saved to: {DEFAULT_CONFIG_PATH}")
    

def main():
    parser = argparse.ArgumentParser(description="Model Context Protocol Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # ls command
    subparsers.add_parser("ls", help="List all configured MCP servers")
    
    # rm command
    rm_parser = subparsers.add_parser("rm", help="Remove an MCP server configuration")
    rm_parser.add_argument("server_name", help="Name of the server to remove")
    
    # add-server command (for new servers)
    add_server_parser = subparsers.add_parser("add-server", help="Add a new MCP server configuration")
    add_server_parser.add_argument("server_name", help="Name of the server")
    add_server_parser.add_argument("command", help="Command to run the server")
    add_server_parser.add_argument("args", nargs="*", help="Arguments for the command")
    
    # add command (for new servers with a single string)
    add_parser = subparsers.add_parser("add", help="Add a new MCP server configuration using a single string")
    add_parser.add_argument("config_string", help="Full configuration string in format 'server_name command arg1 arg2 ...'")
    
    # set-server command (for updating existing servers)
    set_server_parser = subparsers.add_parser("set-server", help="Update an existing MCP server configuration")
    set_server_parser.add_argument("server_name", help="Name of the server")
    set_server_parser.add_argument("command", help="Command to run the server")
    set_server_parser.add_argument("args", nargs="*", help="Arguments for the command")
    
    # set command (for updating existing servers with a single string)
    set_parser = subparsers.add_parser("set", help="Update an existing MCP server configuration using a single string")
    set_parser.add_argument("config_string", help="Full configuration string in format 'server_name command arg1 arg2 ...'")

    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "ls":
        cmd_ls(args)
    elif args.command == "rm":
        cmd_rm(args)
    elif args.command == "add-server":
        cmd_add_server(args)
    elif args.command == "add":
        cmd_add_server(args)
    elif args.command == "set-server":
        cmd_set_server(args)
    elif args.command == "set":
        cmd_set_server(args)

if __name__ == "__main__":
    main()
