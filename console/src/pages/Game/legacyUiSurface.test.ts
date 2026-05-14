import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = dirname(fileURLToPath(import.meta.url));
const consoleRoot = resolve(currentDir, "..", "..");

const sidebarSource = readFileSync(resolve(consoleRoot, "layouts", "Sidebar.tsx"), "utf-8");
const zhLocale = JSON.parse(readFileSync(resolve(consoleRoot, "locales", "zh.json"), "utf-8"));
const enLocale = JSON.parse(readFileSync(resolve(consoleRoot, "locales", "en.json"), "utf-8"));
const jaLocale = JSON.parse(readFileSync(resolve(consoleRoot, "locales", "ja.json"), "utf-8"));
const ruLocale = JSON.parse(readFileSync(resolve(consoleRoot, "locales", "ru.json"), "utf-8"));
const knowledgeBaseSource = readFileSync(resolve(currentDir, "KnowledgeBase.tsx"), "utf-8");
const docLibrarySource = readFileSync(resolve(currentDir, "DocLibrary.tsx"), "utf-8");

describe("legacy UI surface", () => {
  it("shows legacy labels for Doc Library and Knowledge Base in navigation locales", () => {
    assert.equal(zhLocale.nav.docLibrary, "Legacy 文档库");
    assert.equal(zhLocale.nav.knowledgeBase, "Legacy 知识库");
    assert.equal(enLocale.nav.docLibrary, "Legacy Doc Library");
    assert.equal(enLocale.nav.knowledgeBase, "Legacy Knowledge Base");
    assert.equal(jaLocale.nav.docLibrary, "Legacy Doc Library");
    assert.equal(jaLocale.nav.knowledgeBase, "Legacy Knowledge Base");
    assert.equal(ruLocale.nav.docLibrary, "Legacy Doc Library");
    assert.equal(ruLocale.nav.knowledgeBase, "Legacy Knowledge Base");
  });

  it("renders legacy KB and Doc Library as reachable sidebar items", () => {
    assert.equal(sidebarSource.includes('key: "doc-library"'), true);
    assert.equal(sidebarSource.includes('label: t("nav.docLibrary")'), true);
    assert.equal(sidebarSource.includes('key: "knowledge-base"'), true);
    assert.equal(sidebarSource.includes('label: t("nav.knowledgeBase")'), true);
  });

  it("keeps page descriptions explicit about not being formal knowledge entry points", () => {
    assert.match(String(zhLocale.knowledgeBase.description), /不参与正式 Release、RAG、Chat 或 Workbench Suggest/);
    assert.match(String(enLocale.knowledgeBase.description), /does not participate in formal Release, RAG, Chat, or Workbench Suggest/i);
    assert.match(String(zhLocale.docLibrary.description), /不属于正式 Current Release 知识链路/);
    assert.match(String(enLocale.docLibrary.description), /not part of the formal Current Release knowledge chain/i);
  });

  it("does not expose Build Release or Publish actions on legacy pages", () => {
    for (const source of [knowledgeBaseSource, docLibrarySource]) {
      assert.equal(source.includes("knowledge.build"), false);
      assert.equal(source.includes("knowledge.publish"), false);
      assert.equal(source.includes("build_release"), false);
      assert.equal(source.includes("publish_set_current"), false);
    }
  });

  it("does not route legacy KB into the formal RAG flow", () => {
    assert.equal(knowledgeBaseSource.includes("gameKnowledgeBaseApi.search"), true);
    assert.equal(knowledgeBaseSource.includes("gameKnowledgeApi"), false);
    assert.equal(knowledgeBaseSource.includes("/game/knowledge/rag"), false);
    assert.equal(knowledgeBaseSource.includes("build_rag"), false);
  });
});