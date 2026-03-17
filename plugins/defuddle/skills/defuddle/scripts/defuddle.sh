#!/bin/bash

# Defuddle wrapper script
# Automatically installs dependencies on first run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Check if dependencies need to be installed
if [ ! -d "node_modules" ]; then
    echo "Installing defuddle dependencies..." >&2
    npm install || {
        echo "Failed to install dependencies" >&2
        exit 1
    }
fi

# Execute the CLI with all arguments
exec node dist/cli.js "$@"
