import { defineConfig } from "umi";

export default defineConfig({
  routes: [{ path: "/", component: "index" }],
  history: {
    type: "hash",
  },
  npmClient: "yarn",
});
