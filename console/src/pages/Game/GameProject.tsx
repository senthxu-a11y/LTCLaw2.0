import { useEffect, useState } from "react";
import { Form, Input, Switch, Button, Card } from "@agentscope-ai/design";
import { Alert, Checkbox, Modal, Space, Tag, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import { gameApi } from "../../api/modules/game";
import { gameKnowledgeReleaseApi } from "../../api/modules/gameKnowledgeRelease";
import { agentsApi } from "../../api/modules/agents";
import type { GameStorageSummary, KnowledgeManifest, ProjectConfig, ReleaseCandidateListItem, ValidationIssue } from "../../api/types/game";
import { useAgentStore } from "../../stores/agentStore";
import styles from "./GameProject.module.less";

const { TextArea } = Input;
const { Text } = Typography;

interface GameProjectFormData {
  name: string;
  description?: string;
  is_maintainer: boolean;
  svn_url: string;
  svn_username?: string;
  svn_password?: string;
  svn_trust_cert?: boolean;
  svn_working_copy_path?: string;
  watch_paths: string;
  watch_patterns: string;
  watch_exclude_patterns: string;
  auto_sync: boolean;
  auto_index: boolean;
  auto_resolve_dependencies: boolean;
  index_commit_message_template: string;
}

interface BuildReleaseFormData {
  release_id: string;
  release_notes?: string;
}

const LOCAL_PROJECT_DIRECTORY_LABEL = "local project directory";

function createDefaultReleaseId(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `v${now.getFullYear()}.${pad(now.getMonth() + 1)}.${pad(now.getDate())}.${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

export default function GameProject() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent, addAgent, setSelectedAgent } = useAgentStore();
  const [form] = Form.useForm<GameProjectFormData>();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [storageSummary, setStorageSummary] = useState<GameStorageSummary | null>(null);
  const [releaseLoading, setReleaseLoading] = useState(true);
  const [releaseError, setReleaseError] = useState<string | null>(null);
  const [releases, setReleases] = useState<KnowledgeManifest[]>([]);
  const [currentRelease, setCurrentRelease] = useState<KnowledgeManifest | null>(null);
  const [settingCurrentId, setSettingCurrentId] = useState<string | null>(null);
  const [buildModalOpen, setBuildModalOpen] = useState(false);
  const [buildingRelease, setBuildingRelease] = useState(false);
  const [buildCandidatesLoading, setBuildCandidatesLoading] = useState(false);
  const [buildCandidatesError, setBuildCandidatesError] = useState<string | null>(null);
  const [buildCandidates, setBuildCandidates] = useState<ReleaseCandidateListItem[]>([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardSaving, setWizardSaving] = useState(false);
  const [buildForm] = Form.useForm<BuildReleaseFormData>();
  const [wizardForm] = Form.useForm<{ id?: string; name: string }>();

  const getIndexCount = (manifest: KnowledgeManifest | null, indexName: string) => manifest?.indexes?.[indexName]?.count ?? 0;

  const formatDateTime = (value?: string | null) => {
    if (!value) {
      return "-";
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    return parsed.toLocaleString();
  };

  const fetchKnowledgeReleases = async (agentId: string) => {
    setReleaseLoading(true);
    setReleaseError(null);
    try {
      const [releaseList, current] = await Promise.all([
        gameKnowledgeReleaseApi.listReleases(agentId),
        gameKnowledgeReleaseApi.getCurrentRelease(agentId),
      ]);
      setReleases(releaseList);
      setCurrentRelease(current);
    } catch (err) {
      setReleaseError(err instanceof Error ? err.message : t("gameProject.releaseLoadFailed", { defaultValue: "Failed to load knowledge release status" }));
      setReleases([]);
      setCurrentRelease(null);
    } finally {
      setReleaseLoading(false);
    }
  };

  const fetchBuildCandidates = async (agentId: string) => {
    setBuildCandidatesLoading(true);
    setBuildCandidatesError(null);
    try {
      const items = await gameKnowledgeReleaseApi.listBuildCandidates(agentId);
      setBuildCandidates(items);
    } catch (err) {
      setBuildCandidates([]);
      setBuildCandidatesError(
        err instanceof Error
          ? err.message
          : t("gameProject.releaseCandidatesLoadFailed", { defaultValue: "Failed to load release candidates" }),
      );
    } finally {
      setBuildCandidatesLoading(false);
    }
  };

  const fetchConfig = async () => {
    if (!selectedAgent) {
      setLoading(false);
      setReleaseLoading(false);
      setReleaseError(null);
      setReleases([]);
      setCurrentRelease(null);
      return;
    }
    setLoading(true);
    setError(null);
    void fetchKnowledgeReleases(selectedAgent);
    try {
      const [projectConfig, userConfig, storage] = await Promise.all([
        gameApi.getProjectConfig(selectedAgent),
        gameApi.getUserConfig(selectedAgent).catch(() => null),
        gameApi.getStorageSummary(selectedAgent).catch(() => null),
      ]);
      setStorageSummary(storage);
      if (projectConfig) {
        const pc = projectConfig as any;
        const uc = (userConfig || {}) as any;
        form.setFieldsValue({
          name: pc.project?.name || "",
          description: pc.project?.engine || "",
          is_maintainer: uc.my_role === "maintainer",
          svn_url: uc.svn_url || "",
          svn_username: uc.svn_username || "",
          svn_password: uc.svn_password || "",
          svn_trust_cert: !!uc.svn_trust_cert,
          svn_working_copy_path: uc.svn_local_root || pc.svn?.root || "",
          watch_paths: (pc.paths || []).map((item: any) => item.path).join("\n"),
          watch_patterns: (pc.filters?.include_ext || []).join("\n"),
          watch_exclude_patterns: (pc.filters?.exclude_glob || []).join("\n"),
          auto_sync: false,
          auto_index: true,
          auto_resolve_dependencies: true,
          index_commit_message_template: "Auto-index update: {files_changed} files",
        });
      } else {
        // Set default values for new configuration
        form.setFieldsValue({
          name: "",
          description: "Unity",
          is_maintainer: false,
          svn_url: "",
          svn_username: "",
          svn_password: "",
          svn_trust_cert: false,
          svn_working_copy_path: "",
          watch_paths: "Tables\nConfigs",
          watch_patterns: ".xlsx\n.xls\n.csv\n.md\n.txt\n.docx",
          watch_exclude_patterns: "**/temp/**\n**/.svn/**\n**/~$*",
          auto_sync: true,
          auto_index: true,
          auto_resolve_dependencies: true,
          index_commit_message_template: "Auto-index update: {files_changed} files",
        });
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.loadFailed");
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const storageGroups = storageSummary
    ? [
        {
          title: t("gameProject.storageRootTitle", { defaultValue: "统一数据根" }),
          items: [
            [t("gameProject.storageWorkingRoot", { defaultValue: "工作根目录" }), storageSummary.working_root],
            [t("gameProject.storageGameDataRoot", { defaultValue: "游戏数据根" }), storageSummary.game_data_root],
            [t("gameProject.storageWorkspaceDir", { defaultValue: "Agent Workspace" }), storageSummary.workspace_dir],
          ],
        },
        {
          title: t("gameProject.storageProjectTitle", { defaultValue: "项目级" }),
          items: [
            [
              t("gameProject.storageSvnRoot", { defaultValue: "local project directory" }),
              storageSummary.svn_root || "-",
            ],
            [t("gameProject.storageProjectStore", { defaultValue: "项目存储目录" }), storageSummary.project_store_dir || "-"],
            [t("gameProject.storageProjectConfig", { defaultValue: "项目配置文件" }), storageSummary.project_config_path || "-"],
            [t("gameProject.storageProjectIndexes", { defaultValue: "项目索引目录" }), storageSummary.project_index_dir || "-"],
          ],
        },
        {
          title: t("gameProject.storageSessionTitle", { defaultValue: "Agent / 对话级" }),
          items: [
            [t("gameProject.storageAgentRoot", { defaultValue: "Agent 目录" }), storageSummary.agent_store_dir],
            [t("gameProject.storageSessionRoot", { defaultValue: "对话目录" }), storageSummary.session_store_dir],
            [t("gameProject.storageSessionName", { defaultValue: "当前会话名" }), storageSummary.session_name],
            [t("gameProject.storageWorkbench", { defaultValue: "数值工作台目录" }), storageSummary.workbench_dir],
            [t("gameProject.storageProposals", { defaultValue: "提案目录" }), storageSummary.proposals_dir],
          ],
        },
        {
          title: t("gameProject.storageDatabaseTitle", { defaultValue: "缓存 / 数据库" }),
          items: [
            [t("gameProject.storageChroma", { defaultValue: "Chroma 缓存" }), storageSummary.chroma_dir],
            [t("gameProject.storageLlmCache", { defaultValue: "LLM 缓存" }), storageSummary.llm_cache_dir],
            [t("gameProject.storageSvnCache", { defaultValue: "SVN 缓存" }), storageSummary.svn_cache_dir],
            [t("gameProject.storageCodeIndex", { defaultValue: "代码索引库" }), storageSummary.code_index_dir],
            [t("gameProject.storageRetrieval", { defaultValue: "文档检索库" }), storageSummary.retrieval_dir],
            [t("gameProject.storageKnowledgeBase", { defaultValue: "知识库目录" }), storageSummary.knowledge_base_dir],
          ],
        },
        {
          title: t("gameProject.storageUserTitle", { defaultValue: "用户配置" }),
          items: [
            [t("gameProject.storageUserConfig", { defaultValue: "当前用户配置" }), storageSummary.user_config_path],
            [t("gameProject.storageLegacyUserConfig", { defaultValue: "旧用户配置回读" }), storageSummary.legacy_user_config_path],
          ],
        },
      ]
    : [];

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await persistFormToAgent(values, selectedAgent!);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.saveFailed");
      message.error(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const persistFormToAgent = async (values: GameProjectFormData, targetAgent: string) => {
    const splitLines = (s: string | undefined) =>
      (s || "")
        .split(/\r?\n/)
        .map((p) => p.trim())
        .filter((p) => p.length > 0);

    const workingCopyPath = (values.svn_working_copy_path || "").trim();
    if (!workingCopyPath) {
      throw new Error(
        t("gameProject.svnWorkingCopyPathRequired", {
          defaultValue: "请填写 local project directory",
        }),
      );
    }

    const userPayload = {
      my_role: (values.is_maintainer ? "maintainer" : "consumer") as "maintainer" | "consumer",
      svn_local_root: workingCopyPath,
      svn_url: values.svn_url || null,
      svn_username: values.svn_username || null,
      svn_password: values.svn_password || null,
      svn_trust_cert: !!values.svn_trust_cert,
    };
    await gameApi.saveUserConfig(targetAgent, userPayload as any);

    const paths = splitLines(values.watch_paths).map((p) => ({
      path: p,
      semantic: "table" as const,
    }));
    const projectPayload: any = {
      schema_version: "project-config.v1",
      project: {
        name: values.name,
        engine: values.description || "Unity",
        language: "zh",
      },
      svn: {
        root: workingCopyPath,
        poll_interval_seconds: 300,
        jitter_seconds: 30,
      },
      paths,
      filters: {
        include_ext: splitLines(values.watch_patterns),
        exclude_glob: splitLines(values.watch_exclude_patterns),
      },
      table_convention: {
        header_row: 1,
        comment_row: null,
        primary_key_field: "ID",
        id_ranges: [],
      },
      doc_templates: {},
      models: {},
    };
    const result = await gameApi.saveProjectConfig(targetAgent, projectPayload as ProjectConfig);
    message.success(result.message || t("gameProject.saveSuccess"));
  };

  const handleCreateProjectAgent = async () => {
    try {
      const values = await form.validateFields();
      const wizValues = await wizardForm.validateFields();
      setWizardSaving(true);

      const created = await agentsApi.createAgent({
        id: wizValues.id?.trim() || undefined,
        name: wizValues.name.trim(),
        description: (values.description || "").slice(0, 200),
      });

      addAgent({
        id: created.id,
        name: wizValues.name.trim(),
        description: (values.description || "").slice(0, 200),
        workspace_dir: created.workspace_dir,
        enabled: true,
      });
      setSelectedAgent(created.id);

      try {
        await persistFormToAgent(values, created.id);
      } catch (err) {
        const m = err instanceof Error ? err.message : String(err);
        message.warning(
          t("gameProject.wizardCreatedButSaveFailed", {
            defaultValue: `Agent 已创建 (${created.id})，但配置保存失败：${m}`,
          }),
        );
      }

      message.success(
        t("gameProject.wizardSuccess", {
          defaultValue: `已创建项目 Agent: ${created.id}，已切换至该 Agent`,
        }),
      );
      setWizardOpen(false);
      wizardForm.resetFields();
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("agent.createFailed");
      message.error(errMsg);
    } finally {
      setWizardSaving(false);
    }
  };

  const handleValidate = async () => {
    if (!selectedAgent) {
      return;
    }
    try {
      await form.validateFields();
      setSaving(true);
      const issues = await gameApi.validateProjectConfig(selectedAgent);
      const errors = issues.filter((issue: ValidationIssue) => issue.severity === "error");
      if (errors.length === 0) {
        message.success(t("gameProject.validationSuccess"));
      } else {
        message.error(
          `${t("gameProject.validationFailed")}: ${errors
            .map((issue) => `${issue.path}: ${issue.message}`)
            .join(", ")}`
        );
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.validationFailed");
      message.error(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    fetchConfig();
  };

  const handleSetCurrentRelease = async (releaseId: string) => {
    if (!selectedAgent) {
      return;
    }
    try {
      setSettingCurrentId(releaseId);
      await gameKnowledgeReleaseApi.setCurrentRelease(selectedAgent, releaseId);
      await fetchKnowledgeReleases(selectedAgent);
      message.success(
        t("gameProject.releaseSetCurrentSuccess", {
          defaultValue: `Current knowledge release updated: ${releaseId}`,
        }),
      );
    } catch (err) {
      message.warning(
        err instanceof Error
          ? err.message
          : t("gameProject.releaseSetCurrentFailed", { defaultValue: "Failed to set current knowledge release" }),
      );
    } finally {
      setSettingCurrentId(null);
    }
  };

  const openBuildReleaseModal = () => {
    buildForm.setFieldsValue({
      release_id: createDefaultReleaseId(),
      release_notes: currentRelease ? `Build from current indexes based on ${currentRelease.release_id}` : "",
    });
    setSelectedCandidateIds([]);
    setBuildCandidates([]);
    setBuildCandidatesError(null);
    setBuildModalOpen(true);
    if (selectedAgent) {
      void fetchBuildCandidates(selectedAgent);
    }
  };

  const closeBuildReleaseModal = () => {
    if (buildingRelease) {
      return;
    }
    setBuildModalOpen(false);
    setBuildCandidatesError(null);
    setBuildCandidates([]);
    setSelectedCandidateIds([]);
  };

  const refreshBuildCandidates = async () => {
    if (!selectedAgent) {
      return;
    }
    await fetchBuildCandidates(selectedAgent);
  };

  const handleBuildRelease = async () => {
    if (!selectedAgent) {
      return;
    }
    try {
      const values = await buildForm.validateFields();
      setBuildingRelease(true);
      const result = await gameKnowledgeReleaseApi.buildReleaseFromCurrentIndexes(selectedAgent, {
        release_id: values.release_id.trim(),
        release_notes: values.release_notes?.trim() || "",
        candidate_ids: selectedCandidateIds,
      });
      await fetchKnowledgeReleases(selectedAgent);
      setBuildModalOpen(false);
      buildForm.resetFields();
      setBuildCandidatesError(null);
      setBuildCandidates([]);
      setSelectedCandidateIds([]);
      message.success(
        t("gameProject.releaseBuildSuccess", {
          defaultValue: `Knowledge release built: ${result.manifest.release_id}`,
        }),
      );
    } catch (err) {
      setBuildCandidatesError(
        err instanceof Error
          ? err.message
          : t("gameProject.releaseBuildFailed", { defaultValue: "Failed to build knowledge release" }),
      );
      message.warning(
        err instanceof Error
          ? err.message
          : t("gameProject.releaseBuildFailed", { defaultValue: "Failed to build knowledge release" }),
      );
    } finally {
      setBuildingRelease(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, [selectedAgent]);

  if (loading) {
    return (
      <div className={styles.gamePage}>
        <div className={styles.centerState}>
          <span className={styles.stateText}>{t("common.loading")}</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.gamePage}>
        <div className={styles.centerState}>
          <span className={styles.stateTextError}>{error}</span>
          <Button size="small" onClick={fetchConfig} style={{ marginTop: 12 }}>
            {t("common.retry")}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.gamePage}>
      <PageHeader parent={t("nav.game")} current={t("gameProject.title")} />

      <div className={styles.content}>
        <Form form={form} layout="vertical" className={styles.form}>
          <Card
            title={t("gameProject.knowledgeReleaseTitle", { defaultValue: "Knowledge Release Status" })}
            className={styles.section}
          >
            <div className={styles.releaseHint}>
              {t("gameProject.knowledgeReleaseHint", {
                defaultValue:
                  "This panel shows knowledge release assets for the current local project directory. You can build a release from current server-side indexes, view the current release, and switch the current release from the existing release list.",
              })}
            </div>

            <div className={styles.releaseActions}>
              <Button size="small" type="primary" onClick={openBuildReleaseModal} disabled={!selectedAgent}>
                {t("gameProject.releaseBuildButton", { defaultValue: "Build release" })}
              </Button>
              <Text type="secondary">
                {t("gameProject.releaseBuildHint", {
                  defaultValue: "Build uses the safe server-side endpoint and does not auto-set current.",
                })}
              </Text>
            </div>

            {releaseError ? (
              <Alert
                type="warning"
                showIcon
                message={t("gameProject.releaseLoadWarning", { defaultValue: "Knowledge release status is temporarily unavailable" })}
                description={releaseError}
                className={styles.releaseAlert}
              />
            ) : null}

            <div className={styles.releaseSummary}>
              <div className={styles.releaseSummaryRow}>
                <div className={styles.releaseSummaryLabel}>
                  {t("gameProject.releaseCurrentLabel", { defaultValue: "current release id" })}
                </div>
                <div className={styles.releaseSummaryValue}>
                  {releaseLoading ? t("common.loading") : currentRelease?.release_id || "No current knowledge release"}
                </div>
              </div>
              <div className={styles.releaseSummaryRow}>
                <div className={styles.releaseSummaryLabel}>
                  {t("gameProject.releaseBuiltAtLabel", { defaultValue: "built_at / created_at" })}
                </div>
                <div className={styles.releaseSummaryValue}>{releaseLoading ? t("common.loading") : formatDateTime(currentRelease?.created_at)}</div>
              </div>
              <div className={styles.releaseCounters}>
                <Tag color="blue">table_schema {getIndexCount(currentRelease, "table_schema")}</Tag>
                <Tag color="gold">doc_knowledge {getIndexCount(currentRelease, "doc_knowledge")}</Tag>
                <Tag color="green">script_evidence {getIndexCount(currentRelease, "script_evidence")}</Tag>
              </div>
            </div>

            <div className={styles.releaseListBlock}>
              <div className={styles.releaseListHeader}>
                <Text strong>{t("gameProject.releaseListTitle", { defaultValue: "release list" })}</Text>
                <Space size={8}>
                  <Button size="small" onClick={() => selectedAgent && fetchKnowledgeReleases(selectedAgent)} loading={releaseLoading}>
                    {t("common.refresh")}
                  </Button>
                </Space>
              </div>

              {releaseLoading ? (
                <div className={styles.releaseEmpty}>{t("common.loading")}</div>
              ) : releases.length === 0 ? (
                <div className={styles.releaseEmpty}>{t("gameProject.releaseEmpty", { defaultValue: "No knowledge release found for this local project directory" })}</div>
              ) : (
                <div className={styles.releaseList}>
                  {releases.map((release) => {
                    const isCurrent = release.release_id === currentRelease?.release_id;
                    return (
                      <div key={release.release_id} className={styles.releaseRow}>
                        <div className={styles.releaseRowMain}>
                          <div className={styles.releaseRowTop}>
                            <Text strong>{release.release_id}</Text>
                            {isCurrent ? <Tag color="success">current</Tag> : null}
                          </div>
                          <div className={styles.releaseRowMeta}>
                            <span>built_at / created_at: {formatDateTime(release.created_at)}</span>
                            <span>table_schema: {getIndexCount(release, "table_schema")}</span>
                            <span>doc_knowledge: {getIndexCount(release, "doc_knowledge")}</span>
                            <span>script_evidence: {getIndexCount(release, "script_evidence")}</span>
                          </div>
                        </div>
                        <Button
                          size="small"
                          onClick={() => handleSetCurrentRelease(release.release_id)}
                          loading={settingCurrentId === release.release_id}
                          disabled={isCurrent}
                        >
                          {isCurrent
                            ? t("gameProject.releaseCurrentButton", { defaultValue: "Current" })
                            : t("gameProject.releaseSetCurrentButton", { defaultValue: "Set current" })}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </Card>

          <Card
            title={t("gameProject.storageTitle", { defaultValue: "当前实际数据落盘目录" })}
            className={styles.section}
          >
            <div className={styles.storageHint}>
              {t("gameProject.storageHint", {
                defaultValue:
                  "这里显示后端当前实际使用的目录，不是推测值。项目级、Agent 级、对话级以及缓存/数据库都会按这个结果落盘。",
              })}
            </div>
            {storageGroups.map((group) => (
              <div key={group.title} className={styles.storageGroup}>
                <div className={styles.storageGroupTitle}>{group.title}</div>
                {group.items.map(([label, value]) => (
                  <div key={`${group.title}-${label}`} className={styles.storageRow}>
                    <div className={styles.storageLabel}>{label}</div>
                    <div className={styles.storageValue}>{value}</div>
                  </div>
                ))}
              </div>
            ))}
          </Card>
          
          {/* Basic Info Section */}
          <Card title={t("gameProject.basicInfo")} className={styles.section}>
            <Form.Item
              label={t("gameProject.projectName")}
              name="name"
              rules={[{ required: true, message: t("gameProject.projectNameRequired") }]}
            >
              <Input placeholder={t("gameProject.projectNamePlaceholder")} />
            </Form.Item>
            
            <Form.Item
              label={t("gameProject.projectDescription")}
              name="description"
            >
              <TextArea 
                rows={3} 
                placeholder={t("gameProject.projectDescriptionPlaceholder")} 
              />
            </Form.Item>
          </Card>

          {/* SVN Configuration Section */}
          <Card title={t("gameProject.svnConfig")} className={styles.section}>
            <Form.Item
              label="我是维护者（允许维护项目索引）"
              name="is_maintainer"
              valuePropName="checked"
              tooltip="开启=维护者 maintainer；关闭=使用者 consumer。此开关不改变现有接口行为。"
            >
              <Switch />
            </Form.Item>
            <Form.Item
              label={t("gameProject.svnUrl")}
              name="svn_url"
              rules={[{ required: true, message: t("gameProject.svnUrlRequired") }]}
            >
              <Input placeholder="svn://server/path/to/project" />
            </Form.Item>
            
            <Form.Item label={t("gameProject.svnUsername")} name="svn_username">
              <Input placeholder={t("gameProject.svnUsernamePlaceholder")} />
            </Form.Item>
            
            <Form.Item label={t("gameProject.svnPassword")} name="svn_password">
              <Input.Password placeholder={t("gameProject.svnPasswordPlaceholder")} />
            </Form.Item>
            
            <Form.Item label={t("gameProject.svnWorkingCopyPath")} name="svn_working_copy_path">
              <Input placeholder={t("gameProject.svnWorkingCopyPathPlaceholder", { defaultValue: LOCAL_PROJECT_DIRECTORY_LABEL })} />
            </Form.Item>
            
            <Form.Item name="svn_trust_cert" valuePropName="checked">
              <Switch /> {t("gameProject.svnTrustCert")}
            </Form.Item>
          </Card>

          {/* Watch Configuration Section */}
          <Card title={t("gameProject.watchConfig")} className={styles.section}>
            <Form.Item label={t("gameProject.watchPaths")} name="watch_paths">
              <TextArea 
                rows={4} 
                placeholder={t("gameProject.watchPathsPlaceholder")} 
              />
            </Form.Item>
            
            <Form.Item label={t("gameProject.watchPatterns")} name="watch_patterns">
              <TextArea 
                rows={4} 
                placeholder={t("gameProject.watchPatternsPlaceholder")} 
              />
            </Form.Item>
            
            <Form.Item label={t("gameProject.watchExcludePatterns")} name="watch_exclude_patterns">
              <TextArea 
                rows={4} 
                placeholder={t("gameProject.watchExcludePatternsPlaceholder")} 
              />
            </Form.Item>
          </Card>

          {/* Workflow Configuration Section */}
          <Card title={t("gameProject.workflowConfig")} className={styles.section}>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Form.Item name="auto_sync" valuePropName="checked">
                <Switch /> {t("gameProject.autoSync")}
              </Form.Item>
              
              <Form.Item name="auto_index" valuePropName="checked">
                <Switch /> {t("gameProject.autoIndex")}
              </Form.Item>
              
              <Form.Item name="auto_resolve_dependencies" valuePropName="checked">
                <Switch /> {t("gameProject.autoResolveDependencies")}
              </Form.Item>
              
              <Form.Item 
                label={t("gameProject.indexCommitMessageTemplate")} 
                name="index_commit_message_template"
              >
                <Input placeholder={t("gameProject.indexCommitMessageTemplatePlaceholder")} />
              </Form.Item>
            </Space>
          </Card>

        </Form>
      </div>

      <div className={styles.footerActions}>
        <Button onClick={handleReset} disabled={saving} style={{ marginRight: 8 }}>
          {t("common.reset")}
        </Button>
        <Button onClick={handleValidate} disabled={saving} style={{ marginRight: 8 }}>
          {t("gameProject.validate")}
        </Button>
        <Button
          onClick={() => {
            const cur = form.getFieldValue("name") || "";
            wizardForm.setFieldsValue({ name: cur || "新项目", id: "" });
            setWizardOpen(true);
          }}
          disabled={saving}
          style={{ marginRight: 8 }}
        >
          {t("gameProject.createAsAgent", { defaultValue: "另存为新项目 Agent" })}
        </Button>
        <Button type="primary" onClick={handleSave} loading={saving}>
          {t("common.save")}
        </Button>
      </div>

      <Modal
        title={t("gameProject.createAgentTitle", { defaultValue: "为该项目创建独立 Agent" })}
        open={wizardOpen}
        onOk={handleCreateProjectAgent}
        onCancel={() => setWizardOpen(false)}
        okText={t("common.create", { defaultValue: "创建并切换" })}
        cancelText={t("common.cancel")}
        confirmLoading={wizardSaving}
        destroyOnHidden
      >
        <p style={{ marginTop: 0, color: "#666", fontSize: 12 }}>
          {t("gameProject.createAgentHint", {
            defaultValue:
              "将基于当前表单内容创建一个新的 Agent（拥有独立 workspace），并把当前项目配置保存到该 Agent，然后自动切换至新 Agent。",
          })}
        </p>
        <Form form={wizardForm} layout="vertical" autoComplete="off">
          <Form.Item
            name="name"
            label={t("agent.name", { defaultValue: "Agent 名称" })}
            rules={[{ required: true, message: t("agent.nameRequired", { defaultValue: "请输入名称" }) }]}
          >
            <Input placeholder={t("agent.namePlaceholder", { defaultValue: "如：公会战项目" })} />
          </Form.Item>
          <Form.Item
            name="id"
            label={t("agent.idLabel", { defaultValue: "Agent ID（可选）" })}
            help={t("agent.idHelp", { defaultValue: "留空将自动生成。允许字母数字-_，2-64 字符" })}
            rules={[
              {
                pattern: /^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$/,
                message: t("agent.idPattern", { defaultValue: "ID 格式不合法" }),
              },
            ]}
          >
            <Input placeholder="guildwar_proj" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={t("gameProject.releaseBuildModalTitle", { defaultValue: "Build knowledge release" })}
        open={buildModalOpen}
        onCancel={closeBuildReleaseModal}
        onOk={handleBuildRelease}
        okText={t("gameProject.releaseBuildConfirm", { defaultValue: "Build" })}
        cancelText={t("common.cancel")}
        confirmLoading={buildingRelease}
        destroyOnHidden
      >
        <Form form={buildForm} layout="vertical" autoComplete="off">
          <Form.Item
            name="release_id"
            label={t("gameProject.releaseIdLabel", { defaultValue: "release id" })}
            rules={[
              {
                required: true,
                message: t("gameProject.releaseIdRequired", { defaultValue: "Please enter a release id" }),
              },
            ]}
          >
            <Input placeholder="v2026.05.07.001" />
          </Form.Item>
          <Form.Item
            name="release_notes"
            label={t("gameProject.releaseNotesLabel", { defaultValue: "release notes" })}
          >
            <TextArea
              rows={4}
              placeholder={t("gameProject.releaseNotesPlaceholder", {
                defaultValue: "Build from current local indexes",
              })}
            />
          </Form.Item>

          <div className={styles.releaseCandidateSection}>
            <div className={styles.releaseCandidateHeader}>
              <Text strong>{t("gameProject.releaseCandidateSectionTitle", { defaultValue: "Release candidates" })}</Text>
              <Button size="small" onClick={() => void refreshBuildCandidates()} loading={buildCandidatesLoading}>
                {t("common.refresh")}
              </Button>
            </div>

            <div className={styles.releaseCandidateHint}>
              {t("gameProject.releaseCandidateHint", {
                defaultValue:
                  "Only accepted and selected candidates are shown here. Leaving all items unchecked keeps the existing build behavior.",
              })}
            </div>

            {buildCandidatesError ? (
              <Alert
                type="warning"
                showIcon
                message={t("gameProject.releaseCandidateWarning", { defaultValue: "Release candidate list is temporarily unavailable" })}
                description={buildCandidatesError}
                className={styles.releaseCandidateAlert}
              />
            ) : null}

            {buildCandidatesLoading ? (
              <div className={styles.releaseCandidateEmpty}>{t("common.loading")}</div>
            ) : buildCandidates.length === 0 ? (
              <div className={styles.releaseCandidateEmpty}>
                {t("gameProject.releaseCandidateEmpty", {
                  defaultValue: "No accepted and selected release candidates are currently available.",
                })}
              </div>
            ) : (
              <Checkbox.Group value={selectedCandidateIds} onChange={(values) => setSelectedCandidateIds(values as string[])}>
                <div className={styles.releaseCandidateList}>
                  {buildCandidates.map((candidate) => (
                    <label key={candidate.candidate_id} className={styles.releaseCandidateRow}>
                      <Checkbox value={candidate.candidate_id} />
                      <div className={styles.releaseCandidateMain}>
                        <div className={styles.releaseCandidateTitleRow}>
                          <Text strong>{candidate.title}</Text>
                        </div>
                        <div className={styles.releaseCandidateMeta}>
                          <span>candidate_id: {candidate.candidate_id}</span>
                          <span>test_plan_id: {candidate.test_plan_id}</span>
                          <span>created_at: {formatDateTime(candidate.created_at)}</span>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </Checkbox.Group>
            )}
          </div>
        </Form>
      </Modal>
    </div>
  );
}
