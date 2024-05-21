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
  npmClient: "yarn",
});
