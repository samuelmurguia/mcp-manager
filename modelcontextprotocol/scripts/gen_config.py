#!/usr/bin/env python3

import argparse
import json
import os
import sys

def generate_config(command, *args):
    """Generate MCP server configuration JSON."""
    # Extract the base command and arguments
    if command == "npx" and len(args) > 0 and args[0] == "-y":
        # Handle npx -y pattern
        server_command = command
        server_args = list(args)
    else:
        # Handle other patterns
        server_command = command
        server_args = list(args)
    
    # Create the configuration structure
    config = {
        "mcpServers": {
            "filesystem": {
                "command": server_command,
                "args": server_args
            }
        }
    }
    
    return config

def main():
    # Skip the script name
    args = sys.argv[1:]
    
    if not args:
        print("Usage: gen_config <command> [args...]")
        print("Example: gen_config npx -y @modelcontextprotocol/server-filesystem /path/to/dir1 /path/to/dir2")
        sys.exit(1)
    
    # Generate the configuration
    config = generate_config(*args)
    
    # Output the configuration as JSON
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    main()
