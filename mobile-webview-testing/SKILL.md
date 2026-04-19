---
name: mobile-webview-testing
description: >
  Test Capacitor, Ionic, and WebView hybrid apps on real Android devices using
  Chrome DevTools Protocol (CDP) via ADB. Use when the user wants to test a
  mobile app on a physical device, debug WebView content, interact with React
  or Vue state on a real phone, take device screenshots, or test offline and
  network scenarios. Handles the core challenge that uiautomator cannot see
  WebView content by using CDP for web elements and uiautomator for native
  system dialogs.
license: MIT
compatibility: Requires adb in PATH, Android device connected via USB with USB debugging enabled, Python 3 with websockets package
metadata:
  author: wimi321
  version: "1.0"
---

# Mobile WebView Testing

Test any Capacitor, Ionic, or WebView hybrid app on a real Android device.

**The core insight:** `uiautomator` cannot see WebView content. Your entire app UI is invisible to native Android automation tools. This skill uses **Chrome DevTools Protocol (CDP)** for web elements and **uiautomator** only for native system dialogs — a hybrid approach that covers 100% of the UI.

## Prerequisites

- Android device connected via USB with USB debugging enabled
- `adb` available in PATH
- Python 3 with `websockets` package (`pip3 install websockets`)

## Phase 1: Connect to WebView via CDP

Every WebView-based app exposes a DevTools socket. Connect to it in 4 steps:

### Step 1: Get the app's PID

```bash
PID=$(adb shell pidof com.example.myapp)
echo "PID: $PID"
```

### Step 2: Forward the DevTools port

```bash
adb forward tcp:9222 localabstract:webview_devtools_remote_${PID}
```

### Step 3: Get the WebSocket debug URL

```bash
curl -s http://localhost:9222/json | python3 -c \
  "import sys,json; pages=json.load(sys.stdin); print(pages[0]['webSocketDebuggerUrl'])"
```

### Step 4: Connect via Python

```python
import json, asyncio, websockets

async def cdp_eval(ws_url, js_expression):
    async with websockets.connect(ws_url) as ws:
        cmd = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": js_expression, "returnByValue": True}
        }
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        return resp.get("result", {}).get("result", {}).get("value", "")
```

Or use the bundled helper: `scripts/cdp-connect.sh <package.name>` prints the WebSocket URL.

## Phase 2: Execute JavaScript in WebView

### IIFE Isolation (Critical)

CDP's `Runtime.evaluate` shares a **single global scope** across all calls in the same session. Declaring a variable twice causes `SyntaxError: Identifier has already been declared`.

**Always wrap code in an IIFE:**

```javascript
(function() {
    const result = document.querySelector('.my-element');
    return result ? result.textContent : 'not found';
})()
```

### Query DOM Elements

```javascript
// List all buttons
(function() {
    return JSON.stringify(
        Array.from(document.querySelectorAll('button')).map((b, i) => ({
            i,
            text: b.textContent?.trim().substring(0, 60),
            cls: b.className
        }))
    );
})()
```

### Click Elements

```javascript
// Click by CSS selector
document.querySelector('.submit-btn').click()

// Click by index (useful when selectors are unreliable)
document.querySelectorAll('button')[2].click()
```

### Navigate

```javascript
// SPA hash navigation
window.location.hash = '#settings';

// Full navigation
window.location.href = '/dashboard';
```

## Phase 3: Interact with Framework State

### React (Most Common for Capacitor/Ionic)

Standard DOM `.value = x` does **NOT** trigger React state updates. React uses synthetic events and ignores direct property changes on controlled inputs.

**Solution: Use React's internal `__reactProps` key:**

```javascript
(function() {
    const input = document.querySelector('input.my-input');
    const propsKey = Object.keys(input).find(k => k.startsWith('__reactProps'));
    const props = input[propsKey];
    input.value = 'Hello from CDP';
    props.onChange({ target: input });
    return input.value;
})()
```

This works for `<input>`, `<textarea>`, and `<select>` elements.

**For `<select>` elements:**

```javascript
(function() {
    const select = document.querySelector('select.language-picker');
    const propsKey = Object.keys(select).find(k => k.startsWith('__reactProps'));
    const props = select[propsKey];
    props.onChange({ target: { value: 'fr' } });
    return 'switched';
})()
```

See [REACT-STATE.md](references/REACT-STATE.md) for advanced patterns (checkboxes, radio buttons, custom components).

### Vue / Angular

See [FRAMEWORK-SUPPORT.md](references/FRAMEWORK-SUPPORT.md) for Vue's `__vue__` and Angular's `ng.getComponent` approaches.

## Phase 4: Handle Native UI Elements

System dialogs (permission prompts, file pickers, share sheets) are **native Android UI**, not WebView content. Use `uiautomator` for these:

### Dump the UI hierarchy

```bash
adb shell uiautomator dump /data/local/tmp/ui.xml
adb pull /data/local/tmp/ui.xml /tmp/ui.xml
```

### Parse clickable elements

```python
import xml.etree.ElementTree as ET

tree = ET.parse('/tmp/ui.xml')
for node in tree.iter('node'):
    text = node.get('text', '')
    bounds = node.get('bounds', '')
    clickable = node.get('clickable', '')
    if text and clickable == 'true':
        print(f'{bounds} | text={text}')
```

### Tap by coordinates

Parse `[x1,y1][x2,y2]` bounds and tap the center:

```bash
# Example: bounds [540,1200][900,1300] → center (720, 1250)
adb shell input tap 720 1250
```

### The Hybrid Strategy

| Element Type | Tool | Example |
|-------------|------|---------|
| Web buttons, inputs, text | CDP `Runtime.evaluate` | App UI, forms, navigation |
| Permission dialogs | `uiautomator` + `input tap` | "Allow camera access" |
| File/photo picker | `uiautomator` + `input tap` | Gallery selection |
| System notifications | `uiautomator` dump | Toast messages |

Or use the bundled helper: `scripts/native-ui-parser.py` automates XML parsing.

## Phase 5: Screenshots & Visual Verification

### Capture a screenshot

```bash
adb exec-out screencap -p > /tmp/screenshot.png
```

### Verify with AI vision

If your AI assistant supports image input, read the screenshot file to visually verify the UI state. This is especially useful for:

- Layout verification after language switching (e.g., RTL Arabic)
- Visual regression detection
- Confirming modal dialogs appeared correctly
- Verifying responsive design on different screen sizes

## Phase 6: Network Testing

### Disable network (test offline mode)

```bash
adb shell svc wifi disable
adb shell svc data disable
```

### Re-enable network

```bash
adb shell svc wifi enable
adb shell svc data enable
```

> **Note:** `Settings.Global.AIRPLANE_MODE` broadcast requires system privileges and will fail on most non-rooted devices. Use `svc wifi/data` instead.

### Test flow

1. Ensure app works normally with network
2. Disable wifi + data
3. Perform core actions (verify offline functionality)
4. Re-enable network
5. Verify data syncs correctly

## Phase 7: Debugging

### Filter logcat

```bash
# Clear previous logs
adb logcat -c

# Perform the action you want to debug...

# Capture filtered logs
adb logcat -d | grep -iE "error|exception|crash|your-app-tag" | tail -30
```

### Capture WebView console logs via CDP

```python
# Enable Console domain
await ws.send(json.dumps({"id": 2, "method": "Console.enable"}))

# Listen for console messages
while True:
    msg = json.loads(await ws.recv())
    if msg.get("method") == "Console.messageAdded":
        entry = msg["params"]["message"]
        print(f"[{entry['level']}] {entry['text']}")
```

### Monitor network requests via CDP

```python
# Enable Network domain
await ws.send(json.dumps({"id": 3, "method": "Network.enable"}))

# Listen for responses
while True:
    msg = json.loads(await ws.recv())
    if msg.get("method") == "Network.responseReceived":
        resp = msg["params"]["response"]
        print(f"{resp['status']} {resp['url']}")
```

## Phase 8: Advanced Techniques

### Push large files to app internal storage

Apps cannot read from `/sdcard/` in scoped storage. Use `run-as` to write to the app's private directory:

```bash
# Push to temp location
adb push ./large-file.bin /data/local/tmp/

# Move into app's internal storage
adb shell run-as com.example.myapp mkdir -p files/data
adb shell "cat /data/local/tmp/large-file.bin | \
  run-as com.example.myapp sh -c 'cat > files/data/large-file.bin'"
```

### Handle CDP reconnection after app restart

After `am force-stop`, the WebSocket URL changes. Full reconnection flow:

```bash
# Restart the app
adb shell am force-stop com.example.myapp
adb shell am start -n com.example.myapp/.MainActivity

# Wait for WebView to initialize
sleep 3

# Re-discover PID and reconnect
PID=$(adb shell pidof com.example.myapp)
adb forward tcp:9222 localabstract:webview_devtools_remote_${PID}
# Fetch new WebSocket URL from /json endpoint
```

### Handle multiple WebView pages

Some apps have multiple WebView pages (e.g., main app + in-app browser):

```bash
# List all debuggable pages
curl -s http://localhost:9222/json
# Returns an array — pick the page by title or URL
```

```python
import json, urllib.request

pages = json.loads(urllib.request.urlopen("http://localhost:9222/json").read())
for p in pages:
    print(f"  {p['title']} → {p['webSocketDebuggerUrl']}")
```

## Common Pitfalls

See [COMMON-PITFALLS.md](references/COMMON-PITFALLS.md) for 8 battle-tested pitfalls and their solutions, learned from real production testing.

## Test Checklist

See [TEST-CHECKLIST.md](references/TEST-CHECKLIST.md) for a reusable 12-point test template covering app launch, input interaction, navigation, offline mode, and more.
