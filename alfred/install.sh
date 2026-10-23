#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_FILE="$(cd "$DIR/.." && pwd)/OCR-Clipboard-to-Markdown.alfredworkflow"

echo "Building Alfred Workflow package..."
python3 "$DIR/build_workflow.py"

if [ -f "$WORKFLOW_FILE" ]; then
    echo "Opening $WORKFLOW_FILE with Alfred..."
    open "$WORKFLOW_FILE"
    echo "Workflow opened in Alfred! Click 'Import' in Alfred to finish setup."
else
    echo "Error: Workflow file not found at $WORKFLOW_FILE"
    exit 1
fi
