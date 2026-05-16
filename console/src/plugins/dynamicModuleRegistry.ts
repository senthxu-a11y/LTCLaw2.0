/**
 * dynamicModuleRegistry.ts
 *
 * Runtime dynamic module discovery using Vite's import.meta.glob
 * Replaces the need for auto-generated registerHostModules.ts
 *
 * Benefits:
 * - No generated files to commit
 * - No merge conflicts on module registry
 * - Automatically discovers new modules
 * - Clean git history
 */

import { moduleRegistry } from "./moduleRegistry";

/**
 * Dynamically discover and register page entry modules in src/pages.
 * Uses Vite's import.meta.glob for efficient lazy loading.
 *
 * Note: This uses separate glob calls to properly exclude test files at build time
 */
export async function registerHostModulesDynamic(): Promise<void> {
  // Use positive and negative patterns to exclude test files at build time
  const modules = import.meta.glob<Record<string, unknown>>(
    [
      "../pages/*/index.ts",
      "../pages/*/index.tsx",
      "../pages/*/*/index.ts",
      "../pages/*/*/index.tsx",
      "!../pages/Chat/**",
      "../pages/Game/SvnSync.tsx",
      "../pages/Game/IndexMap.tsx",
      "../pages/Game/DocLibrary.tsx",
      "../pages/Game/KnowledgeBase.tsx",
      "../pages/Game/NumericWorkbench.tsx",
      "!../pages/Game/index.ts",
      "!../pages/**/__tests__/**",
      "!../pages/**/*.module.*",
      "!../pages/**/*.test.*",
      "!../pages/**/*.spec.*",
      "!../pages/**/*.d.ts",
    ],
    {
      eager: false,
      import: "*",
    },
  );

  console.log(
    `[patchable] Discovered ${
      Object.keys(modules).length
    } module(s) for registration`,
  );

  // Register modules
  let registeredCount = 0;
  for (const [path, importFn] of Object.entries(modules)) {
    try {
      // Convert absolute path to module key.
      // Directory entries keep their explicit ".../index" key.
      // Flat page files are additionally exposed as ".../index"
      // so lazyImportWithRetry("../../pages/Game/NumericWorkbench")
      // can resolve the plugin-patch lookup key consistently.
      const moduleKey = path
        .replace(/^\.\.\/pages\//, "")
        .replace(/\.(ts|tsx)$/, "");
      const aliasKey = /\/index$/.test(moduleKey)
        ? null
        : `${moduleKey}/index`;

      // Lazy load the module
      const module = await importFn();

      // Check if module has exports
      if (module && Object.keys(module).length > 0) {
        moduleRegistry.register(moduleKey, module);
        if (aliasKey) {
          moduleRegistry.register(aliasKey, module);
        }
        registeredCount++;
      }
    } catch (error) {
      console.warn(`[patchable] Failed to register module: ${path}`, error);
    }
  }

  console.log(`[patchable] Registered ${registeredCount} module(s)`);
}
