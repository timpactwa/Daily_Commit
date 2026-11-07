import { defineConfig, loadEnv } from "vite";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const mock = env.VITE_MOCK === "1" || env.VITE_MOCK === "true";
  return {
  plugins: [react(), tailwindcss(), ...(!mock ? [{
    name: "exclude-mock-answers",
    enforce: "pre" as const,
    resolveId(source: string, importer: string | undefined) {
      if (source === "./mock" && importer?.replaceAll("\\", "/").endsWith("/src/api/client.ts")) {
        return fileURLToPath(new URL("./src/disabled-mock.ts", import.meta.url));
      }
    },
  }] : [])],
  server: {
    host: true,
    proxy: {
      "/v1": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
}; });
