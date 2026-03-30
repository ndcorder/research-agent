import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: [vitePreprocess()],
  compilerOptions: {
    // Disable HMR wrapping to avoid WebKit TDZ bug in Tauri's WKWebView.
    // The Svelte HMR wrapper causes "Cannot access 'component' before initialization"
    // errors in JavaScriptCore due to strict temporal dead zone enforcement.
    hmr: false,
  },
  kit: {
    adapter: adapter({
      fallback: "index.html",
    }),
  },
};

export default config;
