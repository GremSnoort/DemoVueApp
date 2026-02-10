# Vue 3 + Vite

This template should help get you started developing with Vue 3 in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about IDE Support for Vue in the [Vue Docs Scaling up Guide](https://vuejs.org/guide/scaling-up/tooling.html#ide-support).

# Quick Start

Create template:
```bash
npm create vite@latest frontend -- --template vue
```

Install deps:
```bash
npm i axios vue-router
```

Run:
```bash
npm run dev
```

```bash
mkdir src/api/
mkdir src/auth/
mkdir src/router/
mkdir src/pages/
mkdir src/styles/
```

```bash
tree --gitignore | grep -a -v -E "public|.svg|assets"
.
├── index.html
├── package.json
├── package-lock.json
├── README.md
├── src
│   ├── api
│   │   └── http.js
│   ├── App.vue
│   ├── auth
│   │   └── auth.store.js
│   ├── components
│   │   └── AppHeader.vue
│   ├── main.js
│   ├── pages
│   │   ├── AdminPage.vue
│   │   ├── LoginPage.vue
│   │   ├── RegisterPage.vue
│   │   ├── RequestCreatePage.vue
│   │   └── RequestsListPage.vue
│   ├── router
│   │   └── index.js
│   ├── style.css
│   └── styles
│       └── base.css
└── vite.config.js
```
