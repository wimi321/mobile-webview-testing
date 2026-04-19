# Framework Support

How to interact with component state for different JavaScript frameworks via Chrome DevTools Protocol.

## React

React is the most common framework for Capacitor and Ionic apps.

**Key mechanism:** `__reactProps$xxx` on DOM elements.

See [REACT-STATE.md](REACT-STATE.md) for comprehensive React patterns.

```javascript
(function() {
    const el = document.querySelector('input');
    const key = Object.keys(el).find(k => k.startsWith('__reactProps'));
    el.value = 'text';
    el[key].onChange({ target: el });
    return el.value;
})()
```

## Vue 2

Vue 2 attaches a `__vue__` property to the root element of each component instance.

### Detect Vue 2

```javascript
(function() {
    const el = document.querySelector('#app');
    return el.__vue__ ? 'Vue 2 detected' : 'Not Vue 2';
})()
```

### Set input value

```javascript
(function() {
    const input = document.querySelector('input.my-input');
    const vueComponent = input.closest('[data-v-]')?.__vue__;
    if (!vueComponent) return 'No Vue component found';

    // Set data property directly
    vueComponent.formData.myField = 'new value';
    // Force re-render
    vueComponent.$forceUpdate();
    return 'value set';
})()
```

### Trigger events

```javascript
(function() {
    const input = document.querySelector('input.my-input');
    input.value = 'new value';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    return input.value;
})()
```

> **Note:** Vue 2's `v-model` listens to the `input` event by default, so `dispatchEvent(new Event('input'))` works reliably — unlike React which ignores native events.

## Vue 3

Vue 3 uses `__vue_app__` on the app root and `__vueParentComponent` on elements.

### Detect Vue 3

```javascript
(function() {
    const el = document.querySelector('#app');
    return el.__vue_app__ ? 'Vue 3 detected' : 'Not Vue 3';
})()
```

### Set input value

```javascript
(function() {
    const input = document.querySelector('input.my-input');
    input.value = 'new value';
    // Vue 3 v-model listens to 'update:modelValue' internally,
    // but the DOM event approach works:
    input.dispatchEvent(new Event('input', { bubbles: true }));
    return input.value;
})()
```

### Access component instance

```javascript
(function() {
    const el = document.querySelector('.my-component');
    const component = el.__vueParentComponent;
    if (!component) return 'No Vue 3 component';
    const instance = component.proxy;
    return JSON.stringify(Object.keys(instance.$data));
})()
```

## Angular

Angular uses `ng.getComponent()` and zones for change detection.

### Detect Angular

```javascript
(function() {
    return typeof ng !== 'undefined' && typeof ng.getComponent === 'function'
        ? 'Angular detected'
        : 'Not Angular';
})()
```

### Set input value

```javascript
(function() {
    const input = document.querySelector('input.my-input');
    input.value = 'new value';
    // Angular's zone.js patches native events, so dispatching works:
    input.dispatchEvent(new Event('input', { bubbles: true }));
    // Also dispatch change for ngModel
    input.dispatchEvent(new Event('change', { bubbles: true }));
    return input.value;
})()
```

### Access component instance

```javascript
(function() {
    const el = document.querySelector('app-my-component');
    const component = ng.getComponent(el);
    if (!component) return 'No Angular component';
    return JSON.stringify(Object.keys(component));
})()
```

### Trigger change detection

```javascript
(function() {
    const el = document.querySelector('app-root');
    const appRef = ng.getComponent(el);
    // Force Angular change detection
    const injector = ng.getInjector(el);
    const appRef2 = injector.get(ng.coreTokens?.ApplicationRef);
    if (appRef2) appRef2.tick();
    return 'change detection triggered';
})()
```

## Svelte

Svelte compiles away at build time, so there's no runtime framework object on DOM elements. However, Svelte's event binding uses standard DOM events.

### Set input value

```javascript
(function() {
    const input = document.querySelector('input.my-input');
    input.value = 'new value';
    // Svelte's bind:value listens to 'input' events
    input.dispatchEvent(new Event('input', { bubbles: true }));
    return input.value;
})()
```

> **Note:** Svelte is the easiest framework to automate because it compiles to vanilla DOM operations. Standard `dispatchEvent` works for all bindings.

## Framework Detection (Auto)

Use this snippet to detect which framework an app uses:

```javascript
(function() {
    const root = document.querySelector('#app, #root, [id*="app"], body > *');
    const frameworks = [];

    if (root && Object.keys(root).some(k => k.startsWith('__reactFiber')))
        frameworks.push('React');
    if (root && root.__vue__)
        frameworks.push('Vue 2');
    if (root && root.__vue_app__)
        frameworks.push('Vue 3');
    if (typeof ng !== 'undefined' && typeof ng.getComponent === 'function')
        frameworks.push('Angular');
    // Svelte has no runtime markers

    return frameworks.length ? frameworks.join(', ') : 'Unknown (possibly Svelte or vanilla)';
})()
```

## Quick Reference

| Framework | State Access | Event Trigger | Change Detection |
|-----------|-------------|---------------|-----------------|
| React | `__reactProps` → `onChange` | Must use `onChange` | Automatic |
| Vue 2 | `__vue__` → data | `dispatchEvent('input')` | `$forceUpdate()` |
| Vue 3 | `__vueParentComponent` | `dispatchEvent('input')` | Automatic |
| Angular | `ng.getComponent()` | `dispatchEvent('input'+'change')` | `appRef.tick()` |
| Svelte | N/A (compiled) | `dispatchEvent('input')` | Automatic |
