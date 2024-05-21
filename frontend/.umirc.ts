import { defineConfig } from "umi";

export default defineConfig({
  routes: [
    { path: "/", component: "index" },
    {
      name: "登录",
      path: "/login",
      component: "./login",
      hideInMenu: true,
      layout: false,
    },
  ],
  history: {
    type: "hash",
  },
  proxy: {
    "/api": {
      target: "http://127.0.0.1:5000/",
      changeOrigin: true,
      pathRewrite: { "^/api": "" },
    },
  },
  npmClient: "yarn",
});
