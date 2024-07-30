import { defineConfig } from "umi";

export default defineConfig({
  routes: [
    {
      path: "/",
      redirect: "/dashboard",
    },
    {
      name: "登录",
      path: "/login",
      component: "./login",
      hideInMenu: true,
      layout: false,
    },
    {
      path: "/",
      component: "@/layouts/management",
      layout: false,
      routes: [
        {
          name: "情报检索",
          path: "/dashboard",
          component: "./dashboard",
        },
        {
          name: "文档管理",
          path: "/doc-management",
          component: "./doc-management",
        },
        {
          name: "标签管理",
          path: "/tag-management",
          component: "./tag-management",
        },
      ],
    },
  ],
  history: {
    type: "hash",
  },
  publicPath: process.env.NODE_ENV === "production" ? "./" : "/",
  proxy: {
    "/api/my-intelligence": {
      target: "http://127.0.0.1:5000/",
      changeOrigin: true,
      pathRewrite: { "^/api/my-intelligence": "" },
    },
  },
  npmClient: "yarn",
});
