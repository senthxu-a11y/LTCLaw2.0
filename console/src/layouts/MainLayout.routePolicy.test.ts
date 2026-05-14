import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const currentDir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(resolve(currentDir, "MainLayout", "index.tsx"), "utf-8");

describe("MainLayout route policy", () => {
  it("redirects /game/advanced/svn away from the legacy SVN runtime page", () => {
    assert.equal(
      source.includes('<Route path="/game/advanced/svn" element={<Navigate to="/game/advanced" replace />} />'),
      true,
    );
  });

  it("redirects /svn-sync away from the legacy sync flow", () => {
    assert.equal(
      source.includes('<Route path="/svn-sync" element={<Navigate to="/game/project" replace />} />'),
      true,
    );
  });
});