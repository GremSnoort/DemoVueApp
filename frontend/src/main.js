import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./styles/base.css";
import { initTheme } from "@/theme/theme";

initTheme("theme-light");

createApp(App).use(router).mount("#app");
