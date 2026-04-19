#!/usr/bin/env python3
"""
cdp-eval.py — Execute JavaScript in an Android WebView via CDP.

Usage:
    python3 cdp-eval.py <websocket_url> <js_expression>
    python3 cdp-eval.py <websocket_url> -f <js_file>

Examples:
    python3 cdp-eval.py ws://localhost:9222/devtools/page/ABC "document.title"
    python3 cdp-eval.py ws://localhost:9222/devtools/page/ABC -f test-script.js

The script automatically wraps bare expressions in an IIFE to avoid
variable declaration conflicts across multiple evaluations.
"""

import argparse
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("Error: 'websockets' package required. Install with: pip3 install websockets", file=sys.stderr)
    sys.exit(1)


def wrap_iife(js: str) -> str:
    stripped = js.strip()
    if stripped.startswith("(function") or stripped.startswith("(async function"):
        return stripped
    return f"(function() {{\n{stripped}\n}})()"


async def evaluate(ws_url: str, expression: str, timeout: float = 10.0):
    async with websockets.connect(ws_url) as ws:
        cmd = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        }
        await ws.send(json.dumps(cmd))
        resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))

        if "error" in resp:
            print(f"CDP error: {resp['error']}", file=sys.stderr)
            sys.exit(1)

        result = resp.get("result", {}).get("result", {})

        if result.get("type") == "undefined":
            return None

        exception = resp.get("result", {}).get("exceptionDetails")
        if exception:
            text = exception.get("text", "")
            desc = result.get("description", "")
            print(f"JS exception: {text} {desc}", file=sys.stderr)
            sys.exit(1)

        return result.get("value", result.get("description", ""))


def main():
    parser = argparse.ArgumentParser(description="Execute JS in an Android WebView via CDP")
    parser.add_argument("ws_url", help="WebSocket URL (from cdp-connect.sh or /json endpoint)")
    parser.add_argument("expression", nargs="?", help="JavaScript expression to evaluate")
    parser.add_argument("-f", "--file", help="Read JavaScript from a file instead")
    parser.add_argument("--raw", action="store_true", help="Don't wrap in IIFE")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout in seconds (default: 10)")
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            js = f.read()
    elif args.expression:
        js = args.expression
    else:
        parser.error("Provide a JS expression or use -f <file>")
        return

    if not args.raw:
        js = wrap_iife(js)

    result = asyncio.run(evaluate(args.ws_url, js, timeout=args.timeout))
    if result is not None:
        if isinstance(result, (dict, list)):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result)


if __name__ == "__main__":
    main()
