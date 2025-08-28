#!/bin/bash
set -eo pipefail

# Claude Code Submodule Index Helper Script
# Provides interactive submodule indexing capabilities

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/submodule_index.py"

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "❌ Error: Submodule index script not found"
    echo "   Missing: $PYTHON_SCRIPT"
    echo ""
    echo "To reinstall, run:"
    echo "   curl -fsSL https://raw.githubusercontent.com/ericbuess/claude-code-project-index/main/install.sh | bash"
    exit 1
fi

# Determine Python command to use
INSTALL_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_CMD_FILE="$INSTALL_DIR/.python_cmd"
if [[ -f "$PYTHON_CMD_FILE" ]]; then
    PYTHON_CMD=$(cat "$PYTHON_CMD_FILE")
elif [[ -f "$SCRIPT_DIR/find_python.sh" ]]; then
    PYTHON_CMD=$(bash "$SCRIPT_DIR/find_python.sh" 2>/dev/null)
    if [[ -z "$PYTHON_CMD" ]]; then
        exit 1
    fi
else
    # Fallback to basic check
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ Error: Python 3.8+ is required but not installed"
        echo "Please install Python 3.8+ and try again"
        exit 1
    fi
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⚠️  Warning: Not in a Git repository"
    echo "   Submodule detection may not work properly"
    echo ""
fi

# Run the submodule indexer
echo "🚀 Starting Submodule Index Manager..."
echo ""

# Execute the Python script
if $PYTHON_CMD "$PYTHON_SCRIPT" "$@"; then
    echo ""
    echo "✨ Submodule indexing completed!"
    echo ""
    echo "📌 Usage tips:"
    echo "   • Reference parent index: @PROJECT_INDEX.json"
    echo "   • Reference submodule: @submodule_path/PROJECT_INDEX.json"
    echo "   • Run /index-submodules anytime to manage indexes"
else
    exit_code=$?
    echo ""
    echo "❌ Error in submodule indexing (exit code: $exit_code)"
    echo ""
    echo "For help, see: $INSTALL_DIR/README.md"
    exit $exit_code
fi