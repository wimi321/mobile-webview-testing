# Common Pitfalls

Eight battle-tested pitfalls discovered during real-world production testing of WebView hybrid apps on Android devices. Each includes the problem, root cause, and verified solution.

---

## 1. "uiautomator sees nothing"

**Problem:** You run `uiautomator dump` and the XML contains only 2-3 nodes — none of your app's buttons, inputs, or text are visible.

**Root cause:** Capacitor, Ionic, and other WebView frameworks render the entire UI inside a single Android `WebView` widget. `uiautomator` sees the `WebView` container but cannot inspect its internal DOM.

**Solution:** Use Chrome DevTools Protocol (CDP) to access WebView content:

```bash
PID=$(adb shell pidof com.example.myapp)
adb forward tcp:9222 localabstract:webview_devtools_remote_${PID}
curl -s http://localhost:9222/json  # Lists debuggable pages
```

Use `uiautomator` only for native system dialogs (permissions, file pickers).

---

## 2. "React input value won't update"

**Problem:** You set `input.value = 'text'` via CDP and the DOM shows the new value, but React's state doesn't update — the component behaves as if the value never changed.

**Root cause:** React uses synthetic events and controlled components. Setting `.value` directly bypasses React's event system. React never sees the change and overwrites it on the next render.

**Solution:** Access React's internal `__reactProps` key and trigger `onChange`:

```javascript
(function() {
    const input = document.querySelector('input.my-input');
    const propsKey = Object.keys(input).find(k => k.startsWith('__reactProps'));
    input.value = 'new value';
    input[propsKey].onChange({ target: input });
    return input.value;
})()
```

> **Note:** `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, v)` — a commonly suggested approach — may throw "Illegal invocation" in some WebView environments. The `__reactProps` method is more reliable.

---

## 3. "SyntaxError: Identifier has already been declared"

**Problem:** Your second or third CDP `Runtime.evaluate` call fails with `SyntaxError: Identifier 'myVar' has already been declared`.

**Root cause:** CDP's `Runtime.evaluate` shares a single global JavaScript scope across all evaluations in the same page session. `const` and `let` declarations from previous calls persist.

**Solution:** Always wrap code in an IIFE (Immediately Invoked Function Expression):

```javascript
// WRONG — will conflict on second call
const result = document.querySelector('.my-el');

// CORRECT — each evaluation gets its own scope
(function() {
    const result = document.querySelector('.my-el');
    return result?.textContent;
})()
```

---

## 4. "WebSocket URL changed after restart"

**Problem:** After `adb shell am force-stop`, your CDP WebSocket connection dies and the previous URL no longer works.

**Root cause:** The DevTools socket name includes the process ID (`webview_devtools_remote_{PID}`). After a force-stop and relaunch, the app gets a new PID. The old forwarded port now points to a dead socket.

**Solution:** Re-run the full connection sequence:

```bash
# 1. Restart the app
adb shell am force-stop com.example.myapp
adb shell am start -n com.example.myapp/.MainActivity
sleep 3  # Wait for WebView to initialize

# 2. Get new PID
PID=$(adb shell pidof com.example.myapp)

# 3. Re-forward port
adb forward tcp:9222 localabstract:webview_devtools_remote_${PID}

# 4. Get new WebSocket URL
curl -s http://localhost:9222/json | python3 -c \
  "import sys,json; print(json.load(sys.stdin)[0]['webSocketDebuggerUrl'])"
```

---

## 5. "Permission dialog blocks everything"

**Problem:** You trigger a camera or location action, a system permission dialog appears, and your CDP commands no longer reach the WebView.

**Root cause:** The permission dialog is a native Android overlay. While it's visible, the WebView is technically still accessible via CDP, but user interaction is blocked by the overlay.

**Solution:** Use `uiautomator` to handle the permission dialog, then continue with CDP:

```bash
# Dump native UI to find the permission dialog
adb shell uiautomator dump /data/local/tmp/ui.xml
adb pull /data/local/tmp/ui.xml /tmp/ui.xml

# Find and tap "Allow" or "While using the app"
python3 native-ui-parser.py --tap "Allow"

# Continue testing via CDP
```

---

## 6. "Tap hits wrong element"

**Problem:** You calculate tap coordinates manually (e.g., "the button should be around x=540, y=1200") and it taps the wrong element.

**Root cause:** Screen densities, status bar heights, navigation bar presence, and device-specific layouts make coordinate guessing unreliable.

**Solution:**

For **WebView elements** — use CDP to click by selector (no coordinates needed):

```javascript
document.querySelector('.my-button').click()
```

For **native elements** — use `uiautomator dump` to get exact bounds:

```bash
python3 native-ui-parser.py --clickable-only
# Shows precise coordinates for every clickable element
```

Get device resolution for reference: `adb shell wm size`

---

## 7. "airplane_mode broadcast denied"

**Problem:** You try to toggle airplane mode via ADB:

```bash
adb shell am broadcast -a android.intent.action.AIRPLANE_MODE
```

And get: `SecurityException: Permission Denial: not allowed to send broadcast android.intent.action.AIRPLANE_MODE`

**Root cause:** Since Android 7+, toggling airplane mode via broadcast requires system-level privileges that are not available to shell or non-system apps.

**Solution:** Control wifi and mobile data separately:

```bash
# Disable all network (effectively offline)
adb shell svc wifi disable
adb shell svc data disable

# Re-enable
adb shell svc wifi enable
adb shell svc data enable
```

---

## 8. "Large file push to app storage fails"

**Problem:** You push a large file (e.g., an ML model) to the device, but the app can't find it because it's on shared storage and the app uses scoped storage.

**Root cause:** Android's scoped storage (Android 10+) restricts apps from accessing files outside their private directories. Files pushed to `/sdcard/` are not accessible to the app.

**Solution:** Use `run-as` to pipe the file into the app's internal storage:

```bash
# Step 1: Push to temp location (accessible to shell)
adb push ./my-large-file.bin /data/local/tmp/

# Step 2: Create target directory inside app storage
adb shell run-as com.example.myapp mkdir -p files/models

# Step 3: Pipe file into app storage via run-as
adb shell "cat /data/local/tmp/my-large-file.bin | \
  run-as com.example.myapp sh -c 'cat > files/models/my-large-file.bin'"

# Step 4: Clean up temp file
adb shell rm /data/local/tmp/my-large-file.bin
```

> **Tip:** For files > 1 GB, this transfer takes 30-60 seconds over USB 3.0. Run it in the background if needed.
