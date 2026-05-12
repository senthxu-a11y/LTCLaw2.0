import { useCallback, useEffect, useMemo, useState } from "react";
import { Form, Input, Switch, Button, Card } from "@agentscope-ai/design";
import { Alert, Modal, Select, Space, Tag, Tooltip, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import type { FrontendCapabilityToken } from "@/api/types/permissions";
import { canUseGovernanceAction, hasCapabilityContext, isPermissionDeniedError } from "@/utils/permissions";
import { gameApi } from "../../api/modules/game";
import { gameKnowledgeReleaseApi } from "../../api/modules/gameKnowledgeRelease";
import { agentsApi } from "../../api/modules/agents";
import type {
  FormalKnowledgeMapResponse,
  GameStorageSummary,
  KnowledgeDocRef,
  KnowledgeMap,
  KnowledgeRelationship,
  KnowledgeScriptRef,
  KnowledgeStatus,
  KnowledgeSystem,
  KnowledgeTableRef,
  ProjectConfig,
  UserGameConfig,
  ValidationIssue,
} from "../../api/types/game";
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

const LOCAL_PROJECT_DIRECTORY_LABEL = "local project directory";
const NO_CURRENT_RELEASE_DETAIL = "No current knowledge release is set";
const LOCAL_PROJECT_DIRECTORY_ERROR = "Local project directory not configured";
const NO_FORMAL_MAP_MODE = "no_formal_map";
const FORMAL_MAP_STATUS_OPTIONS: Array<{ label: KnowledgeStatus; value: KnowledgeStatus }> = [
  { label: "active", value: "active" },
  { label: "deprecated", value: "deprecated" },
  { label: "ignored", value: "ignored" },
];

function cloneKnowledgeMap(map: KnowledgeMap): KnowledgeMap {
  return JSON.parse(JSON.stringify(map)) as KnowledgeMap;
}

function buildRelationshipWarningMessages(map: KnowledgeMap | null): string[] {
  if (!map) {
    return [];
  }

  const referencedRefs = new Set<string>();
  for (const relationship of map.relationships) {
    referencedRefs.add(relationship.from_ref);
    referencedRefs.add(relationship.to_ref);
  }

  const warnings: string[] = [];
  const appendWarning = (ref: string, title: string, status: KnowledgeStatus) => {
    if ((status === "deprecated" || status === "ignored") && referencedRefs.has(ref)) {
      warnings.push(`${title} (${ref}) is ${status} but is still referenced by relationships.`);
    }
  };

  for (const item of map.systems) {
    appendWarning(`system:${item.system_id}`, item.title, item.status);
  }
  for (const item of map.tables) {
    appendWarning(`table:${item.table_id}`, item.title, item.status);
  }
  for (const item of map.docs) {
    appendWarning(`doc:${item.doc_id}`, item.title, item.status);
  }
  for (const item of map.scripts) {
    appendWarning(`script:${item.script_id}`, item.title, item.status);
  }

  return warnings;
}

export default function GameProject() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const navigate = useNavigate();
  const { selectedAgent, agents, addAgent, setSelectedAgent } = useAgentStore();
  const [form] = Form.useForm<GameProjectFormData>();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [storageSummary, setStorageSummary] = useState<GameStorageSummary | null>(null);
  const [candidateMapLoading, setCandidateMapLoading] = useState(false);
  const [candidateMapError, setCandidateMapError] = useState<string | null>(null);
  const [candidateMap, setCandidateMap] = useState<KnowledgeMap | null>(null);
  const [candidateMapReleaseId, setCandidateMapReleaseId] = useState<string | null>(null);
  const [formalMapLoading, setFormalMapLoading] = useState(false);
  const [formalMapError, setFormalMapError] = useState<string | null>(null);
  const [formalMap, setFormalMap] = useState<FormalKnowledgeMapResponse | null>(null);
  const [formalMapDraft, setFormalMapDraft] = useState<KnowledgeMap | null>(null);
  const [savingFormalMap, setSavingFormalMap] = useState(false);
  const [savingFormalMapDraft, setSavingFormalMapDraft] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardSaving, setWizardSaving] = useState(false);
  const [wizardForm] = Form.useForm<{ id?: string; name: string }>();

  const selectedAgentSummary = agents.find((agent) => agent.id === selectedAgent);
  const capabilities: FrontendCapabilityToken[] | undefined = selectedAgentSummary?.capabilities;
  const hasExplicitCapabilityContext = hasCapabilityContext(capabilities);
  const canReadMap = canUseGovernanceAction(capabilities, "knowledge.map.read");
  const canEditMap = canUseGovernanceAction(capabilities, "knowledge.map.edit");

  const permissionDeniedMessage = t("gameProject.permissionDenied", {
    defaultValue: "You do not have permission to perform this action.",
  });

  const mapReadReason =
    hasExplicitCapabilityContext && !canReadMap
      ? t("gameProject.mapReadPermissionRequired", {
          defaultValue: "Requires knowledge.map.read permission.",
        })
      : null;
  const mapEditReason =
    hasExplicitCapabilityContext && !canEditMap
      ? t("gameProject.mapEditPermissionRequired", {
          defaultValue: "Requires knowledge.map.edit permission.",
        })
      : null;

  const getErrorText = useCallback(
    (error: unknown, fallbackMessage: string) =>
      error instanceof Error ? error.message : fallbackMessage,
    [],
  );

  const resolveMapLoadError = useCallback((error: unknown, fallbackMessage: string) => {
    if (isPermissionDeniedError(error)) {
      return permissionDeniedMessage;
    }
    const messageText = getErrorText(error, fallbackMessage);
    if (messageText.includes(NO_CURRENT_RELEASE_DETAIL)) {
      return NO_CURRENT_RELEASE_DETAIL;
    }
    if (messageText.includes(LOCAL_PROJECT_DIRECTORY_ERROR)) {
      return LOCAL_PROJECT_DIRECTORY_ERROR;
    }
    return messageText;
  }, [getErrorText, permissionDeniedMessage]);

  const summarizeMap = (map: KnowledgeMap | null) => ({
    systems: map?.systems ?? [],
    tables: map?.tables ?? [],
    docs: map?.docs ?? [],
    scripts: map?.scripts ?? [],
    relationships: map?.relationships ?? [],
  });

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

  const fetchCandidateMap = useCallback(async (agentId: string) => {
    setCandidateMapLoading(true);
    setCandidateMapError(null);
    try {
      const response = await gameKnowledgeReleaseApi.getMapCandidate(agentId);
      setCandidateMap(response.map);
      setCandidateMapReleaseId(response.release_id);
    } catch (err) {
      setCandidateMap(null);
      setCandidateMapReleaseId(null);
      setCandidateMapError(
        resolveMapLoadError(
          err,
          t("gameProject.mapCandidateLoadFailed", { defaultValue: "Failed to load candidate map" }),
        ),
      );
    } finally {
      setCandidateMapLoading(false);
    }
  }, [resolveMapLoadError, t]);

  const fetchFormalMap = useCallback(async (agentId: string) => {
    setFormalMapLoading(true);
    setFormalMapError(null);
    try {
      const response = await gameKnowledgeReleaseApi.getFormalMap(agentId);
      setFormalMap(response);
    } catch (err) {
      setFormalMap(null);
      setFormalMapError(
        resolveMapLoadError(
          err,
          t("gameProject.formalMapLoadFailed", { defaultValue: "Failed to load formal map" }),
        ),
      );
    } finally {
      setFormalMapLoading(false);
    }
  }, [resolveMapLoadError, t]);

  const fetchMapReviewData = useCallback(async (agentId: string) => {
    await Promise.all([fetchCandidateMap(agentId), fetchFormalMap(agentId)]);
  }, [fetchCandidateMap, fetchFormalMap]);

  const fetchConfig = useCallback(async () => {
    if (!selectedAgent) {
      setLoading(false);
      setCandidateMap(null);
      setCandidateMapReleaseId(null);
      setCandidateMapError(null);
      setFormalMap(null);
      setFormalMapDraft(null);
      setFormalMapError(null);
      return;
    }
    setLoading(true);
    setError(null);
    if (hasExplicitCapabilityContext && !canReadMap) {
      setCandidateMap(null);
      setCandidateMapReleaseId(null);
      setCandidateMapError(null);
      setFormalMap(null);
      setFormalMapDraft(null);
      setFormalMapError(null);
      setCandidateMapLoading(false);
      setFormalMapLoading(false);
    } else {
      void fetchMapReviewData(selectedAgent);
    }
    try {
      const [projectConfig, userConfig, storage] = await Promise.all([
        gameApi.getProjectConfig(selectedAgent),
        gameApi.getUserConfig(selectedAgent).catch(() => null),
        gameApi.getStorageSummary(selectedAgent).catch(() => null),
      ]);
      setStorageSummary(storage);
      if (projectConfig) {
        const uc: UserGameConfig = userConfig ?? { my_role: "consumer" };
        form.setFieldsValue({
          name: projectConfig.project.name || "",
          description: projectConfig.project.engine || "",
          is_maintainer: uc.my_role === "maintainer",
          svn_url: uc.svn_url || "",
          svn_username: uc.svn_username || "",
          svn_password: uc.svn_password || "",
          svn_trust_cert: !!uc.svn_trust_cert,
          svn_working_copy_path: uc.svn_local_root || projectConfig.svn.root || "",
          watch_paths: projectConfig.paths.map((item) => item.path).join("\n"),
          watch_patterns: projectConfig.filters.include_ext.join("\n"),
          watch_exclude_patterns: projectConfig.filters.exclude_glob.join("\n"),
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
  }, [canReadMap, fetchMapReviewData, form, hasExplicitCapabilityContext, selectedAgent, t]);

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

  const workspaceEntries = [
    {
      key: "knowledge",
      title: t("nav.gameKnowledge", { defaultValue: "Knowledge" }),
      description: t("gameProject.workspaceEntryKnowledgeDescription", {
        defaultValue: "Release status, RAG, citations, and readonly knowledge summaries live on the dedicated Knowledge page.",
      }),
      actionLabel: t("gameProject.openKnowledgeWorkspaceButton", { defaultValue: "Open Knowledge page" }),
      path: "/game/knowledge",
      tone: t("gameProject.workspaceEntryKnowledgeTone", { defaultValue: "Daily knowledge runtime" }),
    },
    {
      key: "map",
      title: t("nav.gameMapEditor", { defaultValue: "Map Editor" }),
      description: t("gameProject.workspaceEntryMapDescription", {
        defaultValue: "Formal map review is still temporarily shown below, but the dedicated Map Editor route is the future ownership target.",
      }),
      actionLabel: t("gameProject.openMapEditorWorkspaceButton", { defaultValue: "Open Map Editor" }),
      path: "/game/map",
      tone: t("gameProject.workspaceEntryMapTone", { defaultValue: "Formal map workspace" }),
    },
    {
      key: "numeric-workbench",
      title: t("gameProject.workspaceEntryNumericWorkbenchTitle", { defaultValue: "Numeric Workbench" }),
      description: t("gameProject.workspaceEntryWorkbenchDescription", {
        defaultValue: "Use NumericWorkbench for draft-only table edits and citation-targeted numeric changes.",
      }),
      actionLabel: t("gameProject.openNumericWorkbenchButton", { defaultValue: "Open NumericWorkbench" }),
      path: "/numeric-workbench",
      tone: t("gameProject.workspaceEntryWorkbenchTone", { defaultValue: "Draft editing workspace" }),
    },
  ];

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
    await gameApi.saveUserConfig(targetAgent, userPayload);

    const paths = splitLines(values.watch_paths).map((p) => ({
      path: p,
      semantic: "table" as const,
    }));
    const projectPayload: ProjectConfig = {
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
    const result = await gameApi.saveProjectConfig(targetAgent, projectPayload);
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

  const handleSaveFormalMap = async () => {
    if (!selectedAgent || !candidateMap) {
      return;
    }
    try {
      setSavingFormalMap(true);
      await gameKnowledgeReleaseApi.saveFormalMap(
        selectedAgent,
        candidateMap,
        selectedAgentSummary?.name || selectedAgent,
      );
      await fetchFormalMap(selectedAgent);
      message.success(
        t("gameProject.formalMapSaveSuccess", {
          defaultValue: "Saved formal map. It will be used by the next safe build.",
        }),
      );
    } catch (err) {
      message.warning(
        isPermissionDeniedError(err)
          ? permissionDeniedMessage
          : getErrorText(
              err,
              t("gameProject.formalMapSaveFailed", { defaultValue: "Failed to save formal map" }),
            ),
      );
    } finally {
      setSavingFormalMap(false);
    }
  };

  const handleSaveFormalMapDraft = async () => {
    if (!selectedAgent || !formalMapDraft) {
      return;
    }
    try {
      setSavingFormalMapDraft(true);
      await gameKnowledgeReleaseApi.saveFormalMap(
        selectedAgent,
        formalMapDraft,
        selectedAgentSummary?.name || selectedAgent,
      );
      await fetchFormalMap(selectedAgent);
      message.success(
        t("gameProject.formalMapSaveSuccess", {
          defaultValue: "Saved formal map. It will be used by the next safe build.",
        }),
      );
    } catch (err) {
      message.warning(
        isPermissionDeniedError(err)
          ? permissionDeniedMessage
          : getErrorText(
              err,
              t("gameProject.formalMapSaveFailed", { defaultValue: "Failed to save formal map" }),
            ),
      );
    } finally {
      setSavingFormalMapDraft(false);
    }
  };

  const updateFormalMapDraftStatus = (
    section: "systems" | "tables" | "docs" | "scripts",
    itemId: string,
    nextStatus: KnowledgeStatus,
  ) => {
    setFormalMapDraft((currentDraft) => {
      if (!currentDraft) {
        return currentDraft;
      }

      if (section === "systems") {
        return {
          ...currentDraft,
          systems: currentDraft.systems.map((item) =>
            item.system_id === itemId ? { ...item, status: nextStatus } : item,
          ),
        };
      }

      if (section === "tables") {
        return {
          ...currentDraft,
          tables: currentDraft.tables.map((item) =>
            item.table_id === itemId ? { ...item, status: nextStatus } : item,
          ),
        };
      }

      if (section === "docs") {
        return {
          ...currentDraft,
          docs: currentDraft.docs.map((item) =>
            item.doc_id === itemId ? { ...item, status: nextStatus } : item,
          ),
        };
      }

      return {
        ...currentDraft,
        scripts: currentDraft.scripts.map((item) =>
          item.script_id === itemId ? { ...item, status: nextStatus } : item,
        ),
      };
    });
  };

  const renderStatusControl = (
    value: KnowledgeStatus,
    onChange: (nextStatus: KnowledgeStatus) => void,
    disabled: boolean,
    disabledReason: string | null,
  ) => (
    <div className={styles.mapReviewItemActions}>
      <Text type="secondary">{t("gameProject.formalMapStatusLabel", { defaultValue: "status" })}</Text>
      <Tooltip title={disabledReason || undefined}>
        <span className={styles.mapReviewStatusControlWrap}>
          <Select
            size="small"
            value={value}
            options={FORMAL_MAP_STATUS_OPTIONS}
            onChange={(nextValue) => onChange(nextValue as KnowledgeStatus)}
            disabled={disabled}
            className={styles.mapReviewStatusSelect}
          />
        </span>
      </Tooltip>
    </div>
  );

  const renderSystemList = (
    items: KnowledgeSystem[],
    options?: {
      editable?: boolean;
      statusControlDisabled?: boolean;
      statusControlDisabledReason?: string | null;
      onStatusChange?: (systemId: string, nextStatus: KnowledgeStatus) => void;
    },
  ) => {
    if (items.length === 0) {
      return <div className={styles.mapReviewEmpty}>{t("gameProject.mapReviewEmptySystems", { defaultValue: "No systems" })}</div>;
    }
    return items.map((item) => (
      <div key={item.system_id} className={styles.mapReviewItemRow}>
        <div className={styles.mapReviewItemMain}>
          <Text strong>{item.title}</Text>
          <div className={styles.mapReviewItemMeta}>
            <span>system_id: {item.system_id}</span>
            {!options?.editable ? <span>status: {item.status}</span> : null}
          </div>
          {options?.editable && options.onStatusChange
            ? renderStatusControl(
                item.status,
                (nextStatus) => options.onStatusChange?.(item.system_id, nextStatus),
                !!options.statusControlDisabled,
                options.statusControlDisabledReason || null,
              )
            : null}
        </div>
      </div>
    ));
  };

  const renderTableList = (
    items: KnowledgeTableRef[],
    options?: {
      editable?: boolean;
      statusControlDisabled?: boolean;
      statusControlDisabledReason?: string | null;
      onStatusChange?: (tableId: string, nextStatus: KnowledgeStatus) => void;
    },
  ) => {
    if (items.length === 0) {
      return <div className={styles.mapReviewEmpty}>{t("gameProject.mapReviewEmptyTables", { defaultValue: "No tables" })}</div>;
    }
    return items.map((item) => (
      <div key={item.table_id} className={styles.mapReviewItemRow}>
        <div className={styles.mapReviewItemMain}>
          <Text strong>{item.title}</Text>
          <div className={styles.mapReviewItemMeta}>
            <span>table_id: {item.table_id}</span>
            <span>source_path: {item.source_path}</span>
            {!options?.editable ? <span>status: {item.status}</span> : null}
          </div>
          {options?.editable && options.onStatusChange
            ? renderStatusControl(
                item.status,
                (nextStatus) => options.onStatusChange?.(item.table_id, nextStatus),
                !!options.statusControlDisabled,
                options.statusControlDisabledReason || null,
              )
            : null}
        </div>
      </div>
    ));
  };

  const renderDocList = (
    items: KnowledgeDocRef[],
    options?: {
      editable?: boolean;
      statusControlDisabled?: boolean;
      statusControlDisabledReason?: string | null;
      onStatusChange?: (docId: string, nextStatus: KnowledgeStatus) => void;
    },
  ) => {
    if (items.length === 0) {
      return <div className={styles.mapReviewEmpty}>{t("gameProject.mapReviewEmptyDocs", { defaultValue: "No docs" })}</div>;
    }
    return items.map((item) => (
      <div key={item.doc_id} className={styles.mapReviewItemRow}>
        <div className={styles.mapReviewItemMain}>
          <Text strong>{item.title}</Text>
          <div className={styles.mapReviewItemMeta}>
            <span>doc_id: {item.doc_id}</span>
            <span>source_path: {item.source_path}</span>
            {!options?.editable ? <span>status: {item.status}</span> : null}
          </div>
          {options?.editable && options.onStatusChange
            ? renderStatusControl(
                item.status,
                (nextStatus) => options.onStatusChange?.(item.doc_id, nextStatus),
                !!options.statusControlDisabled,
                options.statusControlDisabledReason || null,
              )
            : null}
        </div>
      </div>
    ));
  };

  const renderScriptList = (
    items: KnowledgeScriptRef[],
    options?: {
      editable?: boolean;
      statusControlDisabled?: boolean;
      statusControlDisabledReason?: string | null;
      onStatusChange?: (scriptId: string, nextStatus: KnowledgeStatus) => void;
    },
  ) => {
    if (items.length === 0) {
      return <div className={styles.mapReviewEmpty}>{t("gameProject.mapReviewEmptyScripts", { defaultValue: "No scripts" })}</div>;
    }
    return items.map((item) => (
      <div key={item.script_id} className={styles.mapReviewItemRow}>
        <div className={styles.mapReviewItemMain}>
          <Text strong>{item.title}</Text>
          <div className={styles.mapReviewItemMeta}>
            <span>script_id: {item.script_id}</span>
            <span>source_path: {item.source_path}</span>
            {!options?.editable ? <span>status: {item.status}</span> : null}
          </div>
          {options?.editable && options.onStatusChange
            ? renderStatusControl(
                item.status,
                (nextStatus) => options.onStatusChange?.(item.script_id, nextStatus),
                !!options.statusControlDisabled,
                options.statusControlDisabledReason || null,
              )
            : null}
        </div>
      </div>
    ));
  };

  const renderRelationshipList = (items: KnowledgeRelationship[]) => {
    if (items.length === 0) {
      return <div className={styles.mapReviewEmpty}>{t("gameProject.mapReviewEmptyRelationships", { defaultValue: "No relationships" })}</div>;
    }
    return items.map((item) => (
      <div key={item.relationship_id} className={styles.mapReviewItemRow}>
        <div className={styles.mapReviewItemMain}>
          <Text strong>{item.relationship_id}</Text>
          <div className={styles.mapReviewItemMeta}>
            <span>type: {item.relation_type}</span>
            <span>from: {item.from_ref}</span>
            <span>to: {item.to_ref}</span>
          </div>
        </div>
      </div>
    ));
  };

  const candidateSummary = summarizeMap(candidateMap);
  const savedFormalMap = useMemo(
    () => (formalMap?.mode === NO_FORMAL_MAP_MODE ? null : formalMap?.map ?? null),
    [formalMap],
  );
  const formalSummary = summarizeMap(formalMapDraft);
  const hasCandidateMapSummary = !!candidateMap && !candidateMapError;
  const hasFormalMapSummary = !!savedFormalMap && !formalMapError;
  const formalMapDraftDirty = !!savedFormalMap && !!formalMapDraft && JSON.stringify(formalMapDraft) !== JSON.stringify(savedFormalMap);
  const formalMapRelationshipWarnings = buildRelationshipWarningMessages(formalMapDraft);
  const saveFormalMapFirstReason = !savedFormalMap
    ? t("gameProject.formalMapSaveFirstBeforeEdit", {
        defaultValue: "Save a formal map first before editing statuses.",
      })
    : null;
  const saveFormalMapDisabledReason = mapReadReason || mapEditReason || null;
  const canSaveFormalMap = !!selectedAgent && !!candidateMap && (!hasExplicitCapabilityContext || (canReadMap && canEditMap));
  const statusEditDisabledReason = mapEditReason || saveFormalMapFirstReason;
  const canEditFormalMapStatuses = !!savedFormalMap && (!hasExplicitCapabilityContext || (canReadMap && canEditMap));
  const canSaveFormalMapDraft = !!selectedAgent && !!formalMapDraft && formalMapDraftDirty && canEditFormalMapStatuses;

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  useEffect(() => {
    setFormalMapDraft(savedFormalMap ? cloneKnowledgeMap(savedFormalMap) : null);
  }, [savedFormalMap]);

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
            title={t("gameProject.projectSetupTitle", { defaultValue: "Project setup" })}
            className={styles.section}
          >
            <div className={styles.projectIntro}>
              <Text strong>{t("gameProject.projectSetupLead", { defaultValue: "Use this page for project access, local configuration, storage inspection, validation, and save flows." })}</Text>
              <div className={styles.projectIntroHint}>
                {t("gameProject.projectSetupHint", {
                  defaultValue:
                    "Project keeps onboarding and configuration ownership. Daily knowledge runtime has moved out, and formal map editing remains here only as a transitional section until Map Editor takes over.",
                })}
              </div>
            </div>

            <div className={styles.workspaceEntryHeader}>
              <div>
                <Text strong>{t("gameProject.workspaceEntriesTitle", { defaultValue: "Workspace entries" })}</Text>
                <div className={styles.workspaceEntryHint}>
                  {t("gameProject.knowledgeWorkspaceProjectHint", {
                    defaultValue:
                      "Knowledge runtime now lives on its own page. Use the entry cards below to jump into the right workspace without changing Project-owned config and save semantics.",
                  })}
                </div>
              </div>
            </div>

            <div className={styles.workspaceEntryGrid}>
              {workspaceEntries.map((entry) => (
                <div key={entry.key} className={styles.workspaceEntryCard}>
                  <div className={styles.workspaceEntryCardHeader}>
                    <Text strong className={styles.workspaceEntryCardTitle}>{entry.title}</Text>
                    <Tag className={styles.workspaceEntryCardTone}>{entry.tone}</Tag>
                  </div>
                  <div className={styles.workspaceEntryCardBody}>{entry.description}</div>
                  <Button size="small" type="primary" onClick={() => navigate(entry.path)}>
                    {entry.actionLabel}
                  </Button>
                </div>
              ))}
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

          <Card title={t("gameProject.formalMapTransitionTitle", { defaultValue: "Formal map transition" })} className={styles.section}>
            <div className={styles.mapReviewTransitionLead}>
              <Text strong>{t("gameProject.formalMapTransitionLead", { defaultValue: "Formal map editing still runs here in G.3, but this is now a transitional area instead of the Project page's main task." })}</Text>
              <div className={styles.mapReviewHint}>
                {t("gameProject.formalMapTransitionHint", {
                  defaultValue:
                    "Map Editor migration is pending. Keep using the current save and status-edit flows here until G.4 moves the full editor to the dedicated page.",
                })}
              </div>
            </div>

            <Alert
              type="info"
              showIcon
              message={t("gameProject.formalMapTransitionAlertTitle", { defaultValue: "Map Editor migration pending" })}
              description={t("gameProject.formalMapTransitionAlertDescription", {
                defaultValue:
                  "The formal map implementation remains on Project for now. Use Map Editor as the future entry route; current save-as-formal-map and status edit semantics are unchanged in this lane.",
              })}
              className={styles.mapReviewAlert}
            />

            <div className={styles.mapReviewCompactSummary}>
              <div className={styles.mapReviewCompactItem}>
                <Text type="secondary">{t("gameProject.mapCandidateTitle", { defaultValue: "Candidate map" })}</Text>
                <div className={styles.mapReviewCompactValue}>
                  {hasCandidateMapSummary
                    ? t("gameProject.formalMapCompactCounts", {
                        defaultValue: "{{systems}} systems / {{tables}} tables / {{docs}} docs / {{scripts}} scripts / {{relationships}} relationships",
                        systems: candidateSummary.systems.length,
                        tables: candidateSummary.tables.length,
                        docs: candidateSummary.docs.length,
                        scripts: candidateSummary.scripts.length,
                        relationships: candidateSummary.relationships.length,
                      })
                    : candidateMapLoading
                      ? t("common.loading")
                      : candidateMapError || t("gameProject.mapCandidateEmpty", { defaultValue: "No candidate map available" })}
                </div>
              </div>
              <div className={styles.mapReviewCompactItem}>
                <Text type="secondary">{t("gameProject.formalMapTitle", { defaultValue: "Saved formal map" })}</Text>
                <div className={styles.mapReviewCompactValue}>
                  {hasFormalMapSummary
                    ? t("gameProject.formalMapCompactCounts", {
                        defaultValue: "{{systems}} systems / {{tables}} tables / {{docs}} docs / {{scripts}} scripts / {{relationships}} relationships",
                        systems: formalSummary.systems.length,
                        tables: formalSummary.tables.length,
                        docs: formalSummary.docs.length,
                        scripts: formalSummary.scripts.length,
                        relationships: formalSummary.relationships.length,
                      })
                    : formalMapLoading
                      ? t("common.loading")
                      : formalMapError || t("gameProject.noSavedFormalMapTitle", { defaultValue: "no saved formal map" })}
                </div>
              </div>
            </div>

            <div className={styles.mapReviewTransitionActions}>
              <Button size="small" onClick={() => navigate("/game/map")}>
                {t("gameProject.openMapEditorWorkspaceButton", { defaultValue: "Open Map Editor" })}
              </Button>
              <Button
                size="small"
                onClick={() => selectedAgent && fetchMapReviewData(selectedAgent)}
                loading={candidateMapLoading || formalMapLoading}
                disabled={!selectedAgent || !!mapReadReason}
              >
                {t("common.refresh")}
              </Button>
              <Tooltip title={saveFormalMapDisabledReason || undefined}>
                <span>
                  <Button
                    size="small"
                    type="primary"
                    onClick={handleSaveFormalMap}
                    loading={savingFormalMap}
                    disabled={!canSaveFormalMap}
                  >
                    {t("gameProject.saveFormalMapButton", { defaultValue: "Save as formal map" })}
                  </Button>
                </span>
              </Tooltip>
            </div>

            <div className={styles.mapReviewSection}>
              <div className={styles.mapReviewHeader}>
                <div>
                  <Text strong>{t("gameProject.formalMapReviewTitle", { defaultValue: "Formal map review" })}</Text>
                  <div className={styles.mapReviewHint}>
                    {t("gameProject.formalMapReviewHint", {
                      defaultValue:
                        "Review the current candidate map and the saved formal map. Saving formal map does not build or publish a release.",
                    })}
                  </div>
                </div>
              </div>

              {mapReadReason ? (
                <Alert
                  type="info"
                  showIcon
                  message={mapReadReason}
                  className={styles.mapReviewAlert}
                />
              ) : null}

              {saveFormalMapDisabledReason && !mapReadReason ? (
                <Text type="secondary">{saveFormalMapDisabledReason}</Text>
              ) : null}

              <div className={styles.mapReviewGrid}>
                <div className={styles.mapReviewPanel}>
                  <div className={styles.mapReviewPanelHeader}>
                    <Text strong>{t("gameProject.mapCandidateTitle", { defaultValue: "Candidate map" })}</Text>
                    {candidateMapReleaseId ? <Tag color="blue">release_id {candidateMapReleaseId}</Tag> : null}
                  </div>

                  {candidateMapLoading ? (
                    <div className={styles.mapReviewEmpty}>{t("common.loading")}</div>
                  ) : candidateMapError ? (
                    <Alert
                      type={candidateMapError === NO_CURRENT_RELEASE_DETAIL ? "info" : "warning"}
                      showIcon
                      message={
                        candidateMapError === NO_CURRENT_RELEASE_DETAIL
                          ? t("gameProject.mapCandidateNoCurrentTitle", { defaultValue: "No current knowledge release" })
                          : t("gameProject.mapCandidateLoadWarning", { defaultValue: "Candidate map is temporarily unavailable" })
                      }
                      description={
                        candidateMapError === NO_CURRENT_RELEASE_DETAIL
                          ? t("gameProject.mapCandidateNoCurrentDescription", {
                              defaultValue: "Build a knowledge release first to generate a candidate map.",
                            })
                          : candidateMapError
                      }
                      className={styles.mapReviewAlert}
                    />
                  ) : !candidateMap ? (
                    <div className={styles.mapReviewEmpty}>{t("gameProject.mapCandidateEmpty", { defaultValue: "No candidate map available" })}</div>
                  ) : (
                    <>
                      <div className={styles.mapReviewCounts}>
                        <Tag color="blue">systems {candidateSummary.systems.length}</Tag>
                        <Tag color="gold">tables {candidateSummary.tables.length}</Tag>
                        <Tag color="green">docs {candidateSummary.docs.length}</Tag>
                        <Tag color="purple">scripts {candidateSummary.scripts.length}</Tag>
                        <Tag color="cyan">relationships {candidateSummary.relationships.length}</Tag>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapSystemsTitle", { defaultValue: "Systems" })}</Text>
                        <div className={styles.mapReviewList}>{renderSystemList(candidateSummary.systems)}</div>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapTablesTitle", { defaultValue: "Tables" })}</Text>
                        <div className={styles.mapReviewList}>{renderTableList(candidateSummary.tables)}</div>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapDocsTitle", { defaultValue: "Docs" })}</Text>
                        <div className={styles.mapReviewList}>{renderDocList(candidateSummary.docs)}</div>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapScriptsTitle", { defaultValue: "Scripts" })}</Text>
                        <div className={styles.mapReviewList}>{renderScriptList(candidateSummary.scripts)}</div>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapRelationshipsTitle", { defaultValue: "Relationships" })}</Text>
                        <div className={styles.mapReviewList}>{renderRelationshipList(candidateSummary.relationships)}</div>
                      </div>
                    </>
                  )}
                </div>

                <div className={styles.mapReviewPanel}>
                  <div className={styles.mapReviewPanelHeader}>
                    <Text strong>{t("gameProject.formalMapTitle", { defaultValue: "Saved formal map" })}</Text>
                    <Space size={8} wrap>
                      {formalMapDraftDirty ? <Tag color="warning">{t("gameProject.formalMapDraftDirtyTag", { defaultValue: "unsaved status changes" })}</Tag> : null}
                      {formalMap?.map_hash ? <Tag color="success">{formalMap.map_hash}</Tag> : null}
                      <Tooltip title={statusEditDisabledReason || undefined}>
                        <span>
                          <Button
                            size="small"
                            type="primary"
                            onClick={handleSaveFormalMapDraft}
                            loading={savingFormalMapDraft}
                            disabled={!canSaveFormalMapDraft}
                          >
                            {t("gameProject.saveFormalMapStatusButton", { defaultValue: "Save status changes" })}
                          </Button>
                        </span>
                      </Tooltip>
                    </Space>
                  </div>

                  {formalMapLoading ? (
                    <div className={styles.mapReviewEmpty}>{t("common.loading")}</div>
                  ) : formalMapError ? (
                    <Alert
                      type="warning"
                      showIcon
                      message={t("gameProject.formalMapLoadWarning", { defaultValue: "Formal map is temporarily unavailable" })}
                      description={formalMapError}
                      className={styles.mapReviewAlert}
                    />
                  ) : formalMap?.mode === NO_FORMAL_MAP_MODE ? (
                    <Alert
                      type="info"
                      showIcon
                      message={t("gameProject.noSavedFormalMapTitle", { defaultValue: "no saved formal map" })}
                      description={t("gameProject.noSavedFormalMapDescription", {
                        defaultValue: "Use Save as formal map first. Status editing is available only on saved formal map.",
                      })}
                      className={styles.mapReviewAlert}
                    />
                  ) : !savedFormalMap ? (
                    <div className={styles.mapReviewEmpty}>{t("gameProject.formalMapEmpty", { defaultValue: "No saved formal map" })}</div>
                  ) : (
                    <>
                      {statusEditDisabledReason ? <Text type="secondary">{statusEditDisabledReason}</Text> : null}
                      {formalMapRelationshipWarnings.length > 0 ? (
                        <Alert
                          type="warning"
                          showIcon
                          message={t("gameProject.formalMapRelationshipWarningTitle", {
                            defaultValue: "Deprecated or ignored items may still be referenced by relationships.",
                          })}
                          description={
                            <div className={styles.mapReviewWarningList}>
                              {formalMapRelationshipWarnings.map((warning) => (
                                <div key={warning}>{warning}</div>
                              ))}
                            </div>
                          }
                          className={styles.mapReviewAlert}
                        />
                      ) : null}
                      <div className={styles.mapReviewMetaSummary}>
                        <div>{t("gameProject.formalMapUpdatedAt", { defaultValue: "updated_at" })}: {formatDateTime(formalMap?.updated_at)}</div>
                        <div>{t("gameProject.formalMapUpdatedBy", { defaultValue: "updated_by" })}: {formalMap?.updated_by || "-"}</div>
                        <div>
                          {formalMapDraftDirty
                            ? t("gameProject.formalMapDraftDirtyHint", {
                                defaultValue: "Status changes are local until you save them.",
                              })
                            : t("gameProject.formalMapDraftCleanHint", {
                                defaultValue: "No unsaved status changes.",
                              })}
                        </div>
                      </div>
                      <div className={styles.mapReviewCounts}>
                        <Tag color="blue">systems {formalSummary.systems.length}</Tag>
                        <Tag color="gold">tables {formalSummary.tables.length}</Tag>
                        <Tag color="green">docs {formalSummary.docs.length}</Tag>
                        <Tag color="purple">scripts {formalSummary.scripts.length}</Tag>
                        <Tag color="cyan">relationships {formalSummary.relationships.length}</Tag>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapSystemsTitle", { defaultValue: "Systems" })}</Text>
                        <div className={styles.mapReviewList}>{renderSystemList(formalSummary.systems, {
                          editable: true,
                          statusControlDisabled: !canEditFormalMapStatuses,
                          statusControlDisabledReason: statusEditDisabledReason,
                          onStatusChange: (systemId, nextStatus) => updateFormalMapDraftStatus("systems", systemId, nextStatus),
                        })}</div>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapTablesTitle", { defaultValue: "Tables" })}</Text>
                        <div className={styles.mapReviewList}>{renderTableList(formalSummary.tables, {
                          editable: true,
                          statusControlDisabled: !canEditFormalMapStatuses,
                          statusControlDisabledReason: statusEditDisabledReason,
                          onStatusChange: (tableId, nextStatus) => updateFormalMapDraftStatus("tables", tableId, nextStatus),
                        })}</div>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapDocsTitle", { defaultValue: "Docs" })}</Text>
                        <div className={styles.mapReviewList}>{renderDocList(formalSummary.docs, {
                          editable: true,
                          statusControlDisabled: !canEditFormalMapStatuses,
                          statusControlDisabledReason: statusEditDisabledReason,
                          onStatusChange: (docId, nextStatus) => updateFormalMapDraftStatus("docs", docId, nextStatus),
                        })}</div>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapScriptsTitle", { defaultValue: "Scripts" })}</Text>
                        <div className={styles.mapReviewList}>{renderScriptList(formalSummary.scripts, {
                          editable: true,
                          statusControlDisabled: !canEditFormalMapStatuses,
                          statusControlDisabledReason: statusEditDisabledReason,
                          onStatusChange: (scriptId, nextStatus) => updateFormalMapDraftStatus("scripts", scriptId, nextStatus),
                        })}</div>
                      </div>
                      <div className={styles.mapReviewBlock}>
                        <Text strong>{t("gameProject.mapRelationshipsTitle", { defaultValue: "Relationships" })}</Text>
                        <div className={styles.mapReviewList}>{renderRelationshipList(formalSummary.relationships)}</div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
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
    </div>
  );
}
