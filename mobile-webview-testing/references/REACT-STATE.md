# React State Manipulation via CDP

Advanced patterns for interacting with React components through Chrome DevTools Protocol on real Android devices.

## How React State Works in WebView

React maintains an internal "fiber" tree that tracks component state. DOM elements rendered by React have two hidden properties:

- `__reactProps$xxx` — the props passed to the element (including event handlers)
- `__reactFiber$xxx` — the fiber node with component state and tree position

The `xxx` suffix is a unique hash per React root, consistent within a page session.

## Finding the React Props Key

```javascript
(function() {
    const el = document.querySelector('input.my-input');
    const key = Object.keys(el).find(k => k.startsWith('__reactProps'));
    return key || 'No React props found — element may not be React-rendered';
})()
```

## Input Types

### Text Input / Textarea

```javascript
(function() {
    const el = document.querySelector('input[type="text"]');
    const propsKey = Object.keys(el).find(k => k.startsWith('__reactProps'));
    el.value = 'New value';
    el[propsKey].onChange({ target: el });
    return el.value;
})()
```

### Password Input

Same as text input — React treats them identically:

```javascript
(function() {
    const el = document.querySelector('input[type="password"]');
    const propsKey = Object.keys(el).find(k => k.startsWith('__reactProps'));
    el.value = 'secret123';
    el[propsKey].onChange({ target: el });
    return 'password set';
})()
```

### Select / Dropdown

For `<select>` elements, trigger `onChange` with a synthetic target:

```javascript
(function() {
    const sel = document.querySelector('select.my-select');
    const propsKey = Object.keys(sel).find(k => k.startsWith('__reactProps'));
    sel[propsKey].onChange({ target: { value: 'option-2' } });
    return 'selected: option-2';
})()
```

**List available options first:**

```javascript
(function() {
    const sel = document.querySelector('select.my-select');
    return JSON.stringify(
        Array.from(sel.options).map(o => ({ value: o.value, text: o.text }))
    );
})()
```

### Checkbox

```javascript
(function() {
    const cb = document.querySelector('input[type="checkbox"]');
    const propsKey = Object.keys(cb).find(k => k.startsWith('__reactProps'));
    const newState = !cb.checked;
    cb[propsKey].onChange({
        target: { checked: newState, type: 'checkbox' }
    });
    return 'checked: ' + newState;
})()
```

### Radio Button

```javascript
(function() {
    const radio = document.querySelector('input[type="radio"][value="option-b"]');
    const propsKey = Object.keys(radio).find(k => k.startsWith('__reactProps'));
    radio[propsKey].onChange({
        target: { value: 'option-b', type: 'radio', checked: true }
    });
    return 'selected: option-b';
})()
```

### Range / Slider

```javascript
(function() {
    const slider = document.querySelector('input[type="range"]');
    const propsKey = Object.keys(slider).find(k => k.startsWith('__reactProps'));
    slider.value = 75;
    slider[propsKey].onChange({ target: slider });
    return 'slider value: ' + slider.value;
})()
```

## Custom Components (MUI, Chakra, Ant Design)

Many UI libraries wrap native elements. Find the actual `<input>` inside the wrapper:

```javascript
(function() {
    // MUI TextField: the actual input is nested inside the component wrapper
    const wrapper = document.querySelector('.MuiTextField-root');
    const input = wrapper.querySelector('input');
    const propsKey = Object.keys(input).find(k => k.startsWith('__reactProps'));
    input.value = 'New value';
    input[propsKey].onChange({ target: input });
    return input.value;
})()
```

## Triggering Form Submission

```javascript
(function() {
    const form = document.querySelector('form');
    if (!form) return 'No form found';
    const propsKey = Object.keys(form).find(k => k.startsWith('__reactProps'));
    if (propsKey && form[propsKey].onSubmit) {
        form[propsKey].onSubmit({ preventDefault: () => {} });
        return 'onSubmit triggered';
    }
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitBtn) { submitBtn.click(); return 'submit button clicked'; }
    return 'no submit handler found';
})()
```

## Reading Component State (Debugging)

Access the fiber tree to inspect internal state:

```javascript
(function() {
    const el = document.querySelector('.my-component');
    const fiberKey = Object.keys(el).find(k => k.startsWith('__reactFiber'));
    if (!fiberKey) return 'No fiber found';

    const fiber = el[fiberKey];
    const hooks = [];
    let state = fiber.memoizedState;
    while (state) {
        hooks.push(state.memoizedState);
        state = state.next;
    }
    return JSON.stringify(hooks, null, 2);
})()
```

## Waiting for React Re-render

After triggering a state change, React re-renders asynchronously. Wait briefly before reading the new state:

```javascript
(function() {
    return new Promise(resolve => {
        const el = document.querySelector('input.my-input');
        const propsKey = Object.keys(el).find(k => k.startsWith('__reactProps'));
        el.value = 'Updated';
        el[propsKey].onChange({ target: el });

        // Wait for React to flush updates
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                resolve(el.value);
            });
        });
    });
})()
```

> **Note:** Use `awaitPromise: true` in the CDP `Runtime.evaluate` params when returning Promises.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `__reactProps` not found | Element not rendered by React | Check if it's a native element or web component |
| `onChange is not a function` | Component uses `onInput` instead | Try `el[propsKey].onInput({ target: el })` |
| Value resets after set | Component re-renders from parent state | Set the value at the parent component level |
| "Illegal invocation" | Used `Object.getOwnPropertyDescriptor` approach | Use `__reactProps` method instead |
