// Vite env vars used by src/api. Merges with vite/client's ImportMetaEnv.
interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  readonly VITE_MOCK?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
