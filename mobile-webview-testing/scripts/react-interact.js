/**
 * react-interact.js — React state manipulation snippets for CDP.
 *
 * These snippets are designed to be evaluated via CDP Runtime.evaluate.
 * Each is wrapped in an IIFE to avoid global scope conflicts.
 *
 * Usage with cdp-eval.py:
 *   python3 cdp-eval.py <ws_url> -f react-interact.js
 *
 * Or copy individual snippets into your own CDP evaluation calls.
 */

// ============================================================
// 1. Set input/textarea value (triggers React onChange)
// ============================================================

// Replace '.my-input' with your CSS selector
// Replace 'Hello World' with your desired value

/*
(function() {
    const el = document.querySelector('.my-input');
    if (!el) return 'Element not found';
    const propsKey = Object.keys(el).find(k => k.startsWith('__reactProps'));
    if (!propsKey) return 'Not a React element';
    el.value = 'Hello World';
    el[propsKey].onChange({ target: el });
    return el.value;
})()
*/

// ============================================================
// 2. Change select/dropdown value
// ============================================================

/*
(function() {
    const select = document.querySelector('select.my-select');
    if (!select) return 'Select not found';
    const propsKey = Object.keys(select).find(k => k.startsWith('__reactProps'));
    if (!propsKey) return 'Not a React element';
    select[propsKey].onChange({ target: { value: 'option-value' } });
    return 'Changed to: option-value';
})()
*/

// ============================================================
// 3. Toggle checkbox
// ============================================================

/*
(function() {
    const cb = document.querySelector('input[type="checkbox"].my-checkbox');
    if (!cb) return 'Checkbox not found';
    const propsKey = Object.keys(cb).find(k => k.startsWith('__reactProps'));
    if (!propsKey) return 'Not a React element';
    const newChecked = !cb.checked;
    cb[propsKey].onChange({ target: { checked: newChecked, type: 'checkbox' } });
    return 'Checked: ' + newChecked;
})()
*/

// ============================================================
// 4. Click a React button (simulates full event)
// ============================================================

/*
(function() {
    const btn = document.querySelector('.my-button');
    if (!btn) return 'Button not found';
    const propsKey = Object.keys(btn).find(k => k.startsWith('__reactProps'));
    if (propsKey && btn[propsKey].onClick) {
        btn[propsKey].onClick({ preventDefault: () => {}, stopPropagation: () => {} });
        return 'onClick triggered';
    }
    btn.click();
    return 'DOM click triggered';
})()
*/

// ============================================================
// 5. Read React component state (debug inspection)
// ============================================================

/*
(function() {
    const el = document.querySelector('.my-component');
    if (!el) return 'Element not found';
    const fiberKey = Object.keys(el).find(k => k.startsWith('__reactFiber'));
    if (!fiberKey) return 'No React fiber found';
    const fiber = el[fiberKey];
    const state = fiber.memoizedState;
    return JSON.stringify(state, null, 2);
})()
*/

// ============================================================
// 6. List all interactive elements with React props
// ============================================================

/*
(function() {
    const elements = document.querySelectorAll('input, textarea, select, button');
    return JSON.stringify(Array.from(elements).map((el, i) => {
        const propsKey = Object.keys(el).find(k => k.startsWith('__reactProps'));
        return {
            i,
            tag: el.tagName,
            type: el.type || '',
            className: el.className?.substring(0, 40),
            hasReactProps: !!propsKey,
            hasOnChange: !!(propsKey && el[propsKey]?.onChange),
            hasOnClick: !!(propsKey && el[propsKey]?.onClick),
            value: el.value?.substring(0, 30) || ''
        };
    }), null, 2);
})()
*/
