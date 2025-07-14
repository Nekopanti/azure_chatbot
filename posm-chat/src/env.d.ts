/// <reference types="vite/client" />
declare global {
  interface Window {
    VITE_API_BASE_URL: string;
    VITE_AZURE_TENANT_ID: string;
    VITE_AZURE_CLIENT_ID: string;
    VITE_REDIRECT_URI: string;
    VITE_HOME_URI: string;
  }
}  

interface ImportMetaEnv {
  // Azure 
  readonly VITE_AZURE_TENANT_ID: string;
  readonly VITE_AZURE_CLIENT_ID: string;
  readonly VITE_REDIRECT_URI: string;
  readonly VITE_HOME_URI: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}