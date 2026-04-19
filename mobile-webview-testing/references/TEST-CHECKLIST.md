# Test Checklist Template

A reusable checklist for testing WebView hybrid apps on real Android devices. Customize by adding app-specific tests below the template rows.

## How to Use

1. Copy this checklist for each test run
2. Replace `YOUR_APP` with your app's specific elements
3. Add app-specific tests to the bottom
4. Each test should be verified with a screenshot

---

## Core Test Checklist

| # | Test | Steps | Expected Result |
|---|------|-------|-----------------|
| 1 | **App launch** | Install and launch via ADB | App opens, main screen renders correctly |
| 2 | **WebView loads** | Connect CDP, query DOM | CDP returns valid DOM elements |
| 3 | **Text input** | Set input value via CDP React helper | Value appears in input, state updates |
| 4 | **Button interaction** | Click primary action button via CDP | Expected action occurs (API call, navigation, etc.) |
| 5 | **Navigation** | Navigate between screens via hash/route | Each screen renders correctly |
| 6 | **Form submission** | Fill form + submit via CDP | Form processes correctly |
| 7 | **Permission dialog** | Trigger camera/location, handle native dialog | Permission granted, feature works |
| 8 | **Offline mode** | Disable wifi+data → perform core action | App works without network |
| 9 | **Network recovery** | Re-enable network → verify sync | Data syncs, no errors |
| 10 | **Back navigation** | Android back key/gesture | Returns to previous screen or exits cleanly |
| 11 | **Language/locale** | Switch language if supported | UI updates, layout correct (including RTL) |
| 12 | **Error state** | Trigger an error condition | User-friendly error message, no crash |

## Screenshot Verification

After each test, capture a screenshot:

```bash
adb exec-out screencap -p > /tmp/test_N.png
```

If your AI assistant supports vision, read the screenshot to verify the UI visually.

## Extending the Checklist

Add rows for your app's specific features:

```markdown
| 13 | **YOUR_FEATURE** | Steps specific to your app | Expected outcome |
| 14 | **YOUR_FEATURE** | Steps specific to your app | Expected outcome |
```

### Common App-Specific Tests

**E-commerce apps:**
- Add to cart → checkout flow
- Payment form interaction
- Product search and filter

**Chat/messaging apps:**
- Send message → verify delivery
- Receive message → verify notification
- File/image attachment

**Media apps:**
- Play/pause audio or video
- Seek to position
- Fullscreen toggle

**Maps/location apps:**
- Map renders correctly
- Pin/marker interaction
- Route calculation

## Test Run Log Template

```
Test Run: [DATE]
Device: [MODEL] (Android [VERSION])
App: [PACKAGE] v[VERSION]
Network: [wifi/data/offline]

Results:
  #1  App launch      : [ ] Pass  [ ] Fail  Notes: ___
  #2  WebView loads   : [ ] Pass  [ ] Fail  Notes: ___
  #3  Text input      : [ ] Pass  [ ] Fail  Notes: ___
  #4  Button click    : [ ] Pass  [ ] Fail  Notes: ___
  #5  Navigation      : [ ] Pass  [ ] Fail  Notes: ___
  #6  Form submit     : [ ] Pass  [ ] Fail  Notes: ___
  #7  Permission      : [ ] Pass  [ ] Fail  Notes: ___
  #8  Offline mode    : [ ] Pass  [ ] Fail  Notes: ___
  #9  Network recover : [ ] Pass  [ ] Fail  Notes: ___
  #10 Back nav        : [ ] Pass  [ ] Fail  Notes: ___
  #11 Language/locale : [ ] Pass  [ ] Fail  Notes: ___
  #12 Error state     : [ ] Pass  [ ] Fail  Notes: ___

Summary: ___ / 12 passed
Issues found: ___
```
