/// <reference types="vite/client" />

declare module "dayjs" {
  interface Dayjs {
    fromNow(withoutSuffix?: boolean): string;
  }
}

declare module "*.less" {
  const classes: { [key: string]: string };
  export default classes;
}

interface PyWebViewAPI {
  open_external_link: (url: string) => void;
  save_file: (url: string, filename: string) => Promise<boolean>;
}

interface ImportMetaEnv {
  readonly VITE_FRONTEND_BUILD_ID?: string;
  readonly VITE_FRONTEND_BUILD_TIME?: string;
}

declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewAPI;
    };
  }
}

export {};
