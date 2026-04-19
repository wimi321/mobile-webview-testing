#!/bin/bash
#
# cdp-connect.sh — Connect to a WebView app's Chrome DevTools Protocol
#
# Usage: ./cdp-connect.sh <package.name> [port]
# Example: ./cdp-connect.sh com.example.myapp 9222
#
# Outputs the WebSocket debug URL ready for use with CDP clients.

set -euo pipefail

PACKAGE=${1:?"Usage: cdp-connect.sh <package.name> [port]"}
PORT=${2:-9222}

PID=$(adb shell pidof "$PACKAGE" 2>/dev/null || true)

if [ -z "$PID" ]; then
    echo "Error: '$PACKAGE' is not running. Launch the app first:" >&2
    echo "  adb shell am start -n $PACKAGE/.MainActivity" >&2
    exit 1
fi

echo "Found $PACKAGE with PID $PID" >&2

adb forward tcp:"$PORT" localabstract:webview_devtools_remote_"$PID"
echo "Port forwarded: localhost:$PORT → webview_devtools_remote_$PID" >&2

WS_URL=$(curl -s "http://localhost:$PORT/json" | python3 -c \
    "import sys,json
pages = json.load(sys.stdin)
if not pages:
    print('Error: no debuggable WebView pages found', file=sys.stderr)
    sys.exit(1)
print(pages[0]['webSocketDebuggerUrl'])")

echo "$WS_URL"
