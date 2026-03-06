# 在线考试系统 - 前端（Vite + Vue 3）

本目录为在线考试系统的前端工程，技术栈：**Vite + Vue 3 + Pinia + Vue Router**（具体依赖以 `package.json` 为准）。

## 开发启动

```bat
npm install
npm run dev
```

## 目录要点

- `src/api/`：接口封装（与 Django 后端 `/api/*` 对接）
- `src/router/`：路由
- `src/stores/`：Pinia 状态管理
- `src/view/`：页面

## 联调提示

- 后端默认：`http://localhost:8000/`
- 若本地开发遇到跨域：
  - 优先使用 `vite.config.js` 的 devServer proxy（如已配置）；
  - 或在后端配置 CORS（若你后续引入 `django-cors-headers`）。

> 更完整的后端启动与功能说明请查看仓库根目录 `README.md`。
