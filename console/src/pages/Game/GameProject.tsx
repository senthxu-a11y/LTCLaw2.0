import { useCallback, useEffect, useState } from "react";
import { Form, Input, Switch, Button, Card } from "@agentscope-ai/design";
import { CopyOutlined } from "@ant-design/icons";
import { Alert, Descriptions, Empty, InputNumber, Modal, Progress, Select, Space, Tag, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import { gameApi } from "../../api/modules/game";
import { agentsApi } from "../../api/modules/agents";
import type {
  ColdStartJobState,
  FrontendRuntimeInfo,
  GameStorageSummary,
  ProjectCapabilityStatus,
  ProjectSetupStatusResponse,
  ProjectTableSourceDiscoveryResponse,
  ProjectConfig,
  UserGameConfig,
  LocalAgentProfile,
  ValidationIssue,
  WorkspaceRootStatus,
} from "../../api/types/game";
import { useAgentStore } from "../../stores/agentStore";
import { copyText } from "../Chat/utils";
import FormalMapWorkspace from "./components/FormalMapWorkspace";
import {
  buildProjectSetupDiagnosticsText,
  canStartRuleOnlyColdStartBuild,
  clearProjectSetupCachedDiscovery,
  clearColdStartActiveJobId,
  getEffectiveProjectSetupBuildReadiness,
  loadColdStartActiveJobId,
  loadProjectSetupCachedDiscovery,
  saveColdStartActiveJobId,
  saveProjectSetupCachedDiscovery,
  getAvailableColdStartTables,
  getProjectSetupDiscoverySummary,
  isProjectSetupProjectRootDirty,
  isProjectSetupBuildBlocked,
  joinProjectSetupLines,
  splitProjectSetupLines,
  toColdStartProgressView,
} from "./components/projectSetupHelpers";
import styles from "./GameProject.module.less";

const { TextArea } = Input;
const { Text } = Typography;

interface GameProjectFormData {
  name: string;
  description?: string;
  is_maintainer: boolean;
  svn_url?: string;
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
const WORKSPACE_AGENT_ROLE_OPTIONS: LocalAgentProfile["role"][] = ["viewer", "planner", "source_writer", "admin"];
const WORKSPACE_AGENT_CAPABILITY_OPTIONS = [
  "knowledge.read",
  "knowledge.build",
  "knowledge.publish",
  "knowledge.map.read",
  "knowledge.map.edit",
  "knowledge.candidate.read",
  "knowledge.candidate.write",
  "workbench.read",
  "workbench.test.write",
  "workbench.test.export",
  "workbench.source.write",
] as const;

export default function GameProject() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const navigate = useNavigate();
  const { selectedAgent, addAgent, setSelectedAgent, updateAgent } = useAgentStore();
  const [form] = Form.useForm<GameProjectFormData>();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [storageSummary, setStorageSummary] = useState<GameStorageSummary | null>(null);
  const [frontendRuntimeInfo, setFrontendRuntimeInfo] = useState<FrontendRuntimeInfo | null>(null);
  const [projectCapabilityStatus, setProjectCapabilityStatus] = useState<ProjectCapabilityStatus | null>(null);
  const [workspaceRootStatus, setWorkspaceRootStatus] = useState<WorkspaceRootStatus | null>(null);
  const [workspaceAgentProfile, setWorkspaceAgentProfile] = useState<LocalAgentProfile | null>(null);
  const [savingWorkspaceAgentProfile, setSavingWorkspaceAgentProfile] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardSaving, setWizardSaving] = useState(false);
  const [wizardForm] = Form.useForm<{ id?: string; name: string }>();
  const [setupStatus, setSetupStatus] = useState<ProjectSetupStatusResponse | null>(null);
  const [discoveryResult, setDiscoveryResult] = useState<ProjectTableSourceDiscoveryResponse | null>(null);
  const [workspaceRootInput, setWorkspaceRootInput] = useState("");
  const [projectRootInput, setProjectRootInput] = useState("");
  const [tablesRootsInput, setTablesRootsInput] = useState("");
  const [tablesIncludeInput, setTablesIncludeInput] = useState("");
  const [tablesExcludeInput, setTablesExcludeInput] = useState("");
  const [tablesHeaderRow, setTablesHeaderRow] = useState(1);
  const [tablesPrimaryKeysInput, setTablesPrimaryKeysInput] = useState("");
  const [savingProjectSetupRoot, setSavingProjectSetupRoot] = useState(false);
  const [savingWorkspaceRoot, setSavingWorkspaceRoot] = useState(false);
  const [savingProjectSetupTables, setSavingProjectSetupTables] = useState(false);
  const [discoveringSources, setDiscoveringSources] = useState(false);
  const [activeColdStartJobId, setActiveColdStartJobId] = useState("");
  const [coldStartJob, setColdStartJob] = useState<ColdStartJobState | null>(null);
  const [creatingColdStartJob, setCreatingColdStartJob] = useState(false);
  const [cancellingColdStartJob, setCancellingColdStartJob] = useState(false);
  const [restoringColdStartJob, setRestoringColdStartJob] = useState(false);

  const applySetupStatus = useCallback((status: ProjectSetupStatusResponse | null) => {
    setSetupStatus(status);
    if (!status) {
      setWorkspaceRootInput("");
      setProjectRootInput("");
      setTablesRootsInput("");
      setTablesIncludeInput("");
      setTablesExcludeInput("");
      setTablesHeaderRow(1);
      setTablesPrimaryKeysInput("");
      return;
    }
    setWorkspaceRootInput(status.active_workspace_root ?? "");
    setProjectRootInput(status.project_root ?? "");
    setTablesRootsInput(joinProjectSetupLines(status.tables_config.roots));
    setTablesIncludeInput(joinProjectSetupLines(status.tables_config.include));
    setTablesExcludeInput(joinProjectSetupLines(status.tables_config.exclude));
    setTablesHeaderRow(status.tables_config.header_row || 1);
    setTablesPrimaryKeysInput(joinProjectSetupLines(status.tables_config.primary_key_candidates));
  }, []);

  const loadProjectData = useCallback(async () => {
    if (!selectedAgent) {
      applySetupStatus(null);
      setWorkspaceRootStatus(null);
      setDiscoveryResult(null);
      setStorageSummary(null);
      setFrontendRuntimeInfo(null);
      setProjectCapabilityStatus(null);
      setWorkspaceAgentProfile(null);
      setColdStartJob(null);
      setActiveColdStartJobId("");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [projectConfig, userConfig, storage, projectSetupStatus, capabilityStatus, workspaceProfile, workspaceStatus] = await Promise.all([
        gameApi.getProjectConfig(selectedAgent),
        gameApi.getUserConfig(selectedAgent).catch(() => null),
        gameApi.getStorageSummary(selectedAgent).catch(() => null),
        gameApi.getProjectSetupStatus(selectedAgent).catch(() => null),
        gameApi.getProjectCapabilityStatus(selectedAgent).catch(() => null),
        gameApi.getWorkspaceAgentProfile(selectedAgent).catch(() => null),
        gameApi.getWorkspaceRootStatus(selectedAgent).catch(() => null),
      ]);
      const runtimeInfo = await gameApi.getFrontendRuntimeInfo().catch(() => null);
      setStorageSummary(storage);
      setFrontendRuntimeInfo(runtimeInfo);
      setProjectCapabilityStatus(capabilityStatus);
      setWorkspaceAgentProfile(workspaceProfile);
      setWorkspaceRootStatus(workspaceStatus);
      if (capabilityStatus) {
        updateAgent(selectedAgent, {
          role: capabilityStatus.role as LocalAgentProfile["role"],
          capabilities: capabilityStatus.capabilities,
          agent_profile:
            workspaceProfile ?? {
              agent_id: capabilityStatus.agent_id,
              display_name: capabilityStatus.agent_id,
              role: capabilityStatus.role as LocalAgentProfile["role"],
              capabilities: capabilityStatus.capabilities,
            },
        });
      }
      applySetupStatus(projectSetupStatus);
      setDiscoveryResult(loadProjectSetupCachedDiscovery(projectSetupStatus));
      const savedJobId = loadColdStartActiveJobId(selectedAgent);
      if (!savedJobId) {
        setColdStartJob(null);
        setActiveColdStartJobId("");
      } else {
        try {
          const job = await gameApi.getColdStartJob(selectedAgent, savedJobId);
          setColdStartJob(job);
          setActiveColdStartJobId(job.job_id);
          saveColdStartActiveJobId(selectedAgent, job.job_id);
        } catch {
          clearColdStartActiveJobId(selectedAgent);
          setColdStartJob(null);
          setActiveColdStartJobId("");
        }
      }
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
  }, [applySetupStatus, form, selectedAgent, t, updateAgent]);

  const canWriteColdStart = projectCapabilityStatus?.required_for_cold_start["knowledge.candidate.write"] ?? true;
  const hasActiveProjectRoot = Boolean(setupStatus?.active_workspace_project_root || setupStatus?.project_root);

  const handleSaveWorkspaceAgentProfile = async () => {
    if (!selectedAgent || !workspaceAgentProfile) {
      return;
    }
    try {
      setSavingWorkspaceAgentProfile(true);
      const response = await gameApi.saveWorkspaceAgentProfile(selectedAgent, {
        display_name: workspaceAgentProfile.display_name,
        role: workspaceAgentProfile.role,
        capabilities: workspaceAgentProfile.capabilities,
      });
      setWorkspaceAgentProfile(response.profile);
      setProjectCapabilityStatus(response.capability_status);
      updateAgent(selectedAgent, {
        role: response.capability_status.role as LocalAgentProfile["role"],
        capabilities: response.capability_status.capabilities,
        agent_profile: response.profile,
      });
      message.success(t("gameProject.workspaceAgentProfileSaved", { defaultValue: "Agent Role / Capabilities 已保存。" }));
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.saveFailed");
      message.error(errMsg);
    } finally {
      setSavingWorkspaceAgentProfile(false);
    }
  };

  const handleSaveProjectRoot = async () => {
    if (!selectedAgent) {
      return;
    }
    try {
      setSavingProjectSetupRoot(true);
      const response = await gameApi.saveProjectRoot(selectedAgent, projectRootInput.trim());
      applySetupStatus(response.setup_status);
      setDiscoveryResult(null);
      setColdStartJob(null);
      setActiveColdStartJobId("");
      clearColdStartActiveJobId(selectedAgent);
      message.success(t("gameProject.projectRootSaved", { defaultValue: "Local Project Root 已保存。" }));
      await loadProjectData();
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.saveFailed");
      message.error(errMsg);
    } finally {
      setSavingProjectSetupRoot(false);
    }
  };

  const handleSaveWorkspaceRoot = async (createIfMissing = false) => {
    if (!selectedAgent) {
      return;
    }
    const targetPath = workspaceRootInput.trim();
    if (!targetPath) {
      message.error(t("gameProject.workspaceRootRequired", { defaultValue: "Workspace Root 不能为空。" }));
      return;
    }
    try {
      setSavingWorkspaceRoot(true);
      await gameApi.saveWorkspaceRoot(selectedAgent, {
        workspace_root: targetPath,
        workspace_name: setupStatus?.workspace_name || "LTClaw Workspace",
        create_if_missing: createIfMissing,
      });
      await loadProjectData();
      message.success(
        t("gameProject.workspaceRootSaved", {
          defaultValue: `已切换工作区：${targetPath}`,
        }),
      );
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.saveFailed");
      message.error(errMsg);
    } finally {
      setSavingWorkspaceRoot(false);
    }
  };

  const handleSaveTablesSource = async () => {
    if (!selectedAgent) {
      return;
    }
    try {
      setSavingProjectSetupTables(true);
      clearProjectSetupCachedDiscovery(setupStatus);
      const response = await gameApi.saveProjectTablesSource(selectedAgent, {
        roots: splitProjectSetupLines(tablesRootsInput),
        include: splitProjectSetupLines(tablesIncludeInput),
        exclude: splitProjectSetupLines(tablesExcludeInput),
        header_row: tablesHeaderRow,
        primary_key_candidates: splitProjectSetupLines(tablesPrimaryKeysInput),
      });
      applySetupStatus(response.setup_status);
      setDiscoveryResult(null);
      setColdStartJob(null);
      setActiveColdStartJobId("");
      clearColdStartActiveJobId(selectedAgent);
      message.success(t("gameProject.tablesSourceSaved", { defaultValue: "Tables Source 已保存。" }));
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.saveFailed");
      message.error(errMsg);
    } finally {
      setSavingProjectSetupTables(false);
    }
  };

  const handleDiscoverSources = async () => {
    if (!selectedAgent) {
      return;
    }
    try {
      setDiscoveringSources(true);
      const response = await gameApi.discoverProjectTableSources(selectedAgent);
      setDiscoveryResult(response);
      saveProjectSetupCachedDiscovery(setupStatus, response);
      message.success(t("gameProject.discoveryCompleted", { defaultValue: "Source Discovery 已完成。" }));
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.loadFailed");
      message.error(errMsg);
    } finally {
      setDiscoveringSources(false);
    }
  };

  const handleCopyDiagnostics = async () => {
    try {
      await copyText(buildProjectSetupDiagnosticsText({ setupStatus, discovery: discoveryResult, coldStartJob }));
      message.success(t("gameProject.copyDiagnosticsSuccess", { defaultValue: "诊断信息已复制。" }));
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.copyDiagnosticsFailed", { defaultValue: "复制诊断信息失败。" });
      message.error(errMsg);
    }
  };

  const fetchColdStartJob = useCallback(async (jobId: string) => {
    if (!selectedAgent || !jobId) {
      return null;
    }
    const job = await gameApi.getColdStartJob(selectedAgent, jobId);
    setColdStartJob(job);
    setActiveColdStartJobId(job.job_id);
    saveColdStartActiveJobId(selectedAgent, job.job_id);
    return job;
  }, [selectedAgent]);

  const handleStartColdStartJob = async () => {
    if (!selectedAgent) {
      return;
    }
    try {
      setCreatingColdStartJob(true);
      const response = await gameApi.createColdStartJob(selectedAgent, { timeout_seconds: 300 });
      setColdStartJob(response.job);
      setActiveColdStartJobId(response.job.job_id);
      saveColdStartActiveJobId(selectedAgent, response.job.job_id);
      message.success(
        response.reused_existing
          ? t("gameProject.projectSetupColdStartReused", { defaultValue: "检测到同项目已有运行中的冷启动任务，已恢复该任务状态。" })
          : t("gameProject.projectSetupColdStartStarted", { defaultValue: "Rule-only 冷启动构建已开始。" }),
      );
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.loadFailed");
      message.error(errMsg);
    } finally {
      setCreatingColdStartJob(false);
    }
  };

  const handleCancelColdStartJob = async () => {
    if (!selectedAgent || !activeColdStartJobId) {
      return;
    }
    try {
      setCancellingColdStartJob(true);
      const job = await gameApi.cancelColdStartJob(selectedAgent, activeColdStartJobId);
      setColdStartJob(job);
      message.success(t("gameProject.projectSetupColdStartCancelled", { defaultValue: "冷启动任务已取消。" }));
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.loadFailed");
      message.error(errMsg);
    } finally {
      setCancellingColdStartJob(false);
    }
  };

  const handleRetryColdStartJob = async () => {
    await handleStartColdStartJob();
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
              t("gameProject.storageProjectRoot", { defaultValue: "local project root" }),
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
            [t("gameProject.storageSvnCacheLegacy", { defaultValue: "legacy project cache" }), storageSummary.svn_cache_dir],
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
        defaultValue: "Formal map review, save-as-formal-map, and status-only edits now live on the dedicated Map Editor page.",
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

  const discoverySummary = getProjectSetupDiscoverySummary(setupStatus, discoveryResult);
  const discoveryNotScanned = discoverySummary.status === "not_scanned";
  const effectiveReadiness = getEffectiveProjectSetupBuildReadiness(setupStatus, discoveryResult);
  const buildBlocked = isProjectSetupBuildBlocked(setupStatus, discoveryResult);
  const canStartColdStartBuild = canStartRuleOnlyColdStartBuild(setupStatus, discoveryResult);
  const projectRootDirty = isProjectSetupProjectRootDirty(projectRootInput, setupStatus);
  const coldStartProgress = toColdStartProgressView(coldStartJob);
  const availableTableFiles = getAvailableColdStartTables(discoveryResult);
  const recognizedButNotSupportedFiles = discoveryResult?.table_files.filter((item) => !item.cold_start_supported && item.status !== "unsupported") ?? [];
  const unsupportedFiles = discoveryResult?.unsupported_files ?? [];
  const excludedFiles = discoveryResult?.excluded_files ?? [];
  const discoveryErrors = discoveryResult?.errors ?? [];
  const discoveryRoots = discoveryResult?.roots ?? [];

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
    loadProjectData();
  };

  useEffect(() => {
    loadProjectData();
  }, [loadProjectData]);

  useEffect(() => {
    if (!selectedAgent) {
      setActiveColdStartJobId("");
      setColdStartJob(null);
      return;
    }
    const savedJobId = loadColdStartActiveJobId(selectedAgent);
    if (!savedJobId) {
      setActiveColdStartJobId("");
      setColdStartJob(null);
      return;
    }
    setActiveColdStartJobId(savedJobId);
    setRestoringColdStartJob(true);
    fetchColdStartJob(savedJobId)
      .catch(() => {
        clearColdStartActiveJobId(selectedAgent);
        setActiveColdStartJobId("");
        setColdStartJob(null);
      })
      .finally(() => setRestoringColdStartJob(false));
  }, [fetchColdStartJob, selectedAgent]);

  useEffect(() => {
    if (!selectedAgent || !activeColdStartJobId) {
      return;
    }
    if (!coldStartJob || !["pending", "running"].includes(coldStartJob.status)) {
      return;
    }

    const timer = window.setInterval(() => {
      void fetchColdStartJob(activeColdStartJobId).catch(() => undefined);
    }, 1500);

    return () => window.clearInterval(timer);
  }, [activeColdStartJobId, coldStartJob, fetchColdStartJob, selectedAgent]);

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
          <Button size="small" onClick={loadProjectData} style={{ marginTop: 12 }}>
            {t("common.retry")}
          </Button>
        </div>
      </div>
    );
  }

  const currentWorkspaceRoot = workspaceRootStatus?.active_workspace_root || setupStatus?.active_workspace_root || "-";
  const currentWorkspaceConfigPath = workspaceRootStatus?.workspace_config_path || setupStatus?.workspace_config_path || "-";
  const currentActiveProjectKey = workspaceRootStatus?.active_project_key || setupStatus?.active_workspace_project_key || setupStatus?.project_key || "-";
  const currentActiveProjectRoot = workspaceRootStatus?.active_workspace_project_root || setupStatus?.active_workspace_project_root || setupStatus?.project_root || "-";
  const currentProjectBundleRoot = setupStatus?.project_bundle_root || "-";
  const coldStartWarnings = coldStartJob?.warnings || [];
  const coldStartErrors = coldStartJob?.errors || [];
  const coldStartCandidateRefs = coldStartJob?.candidate_refs || [];

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
                    "Project keeps onboarding and configuration ownership. Daily knowledge runtime and formal map editing now live on their dedicated workspace pages.",
                })}
              </div>
            </div>

            <div className={styles.workspaceSwitcherCard}>
              <div className={styles.workspaceSwitcherHeader}>
                <div>
                  <Text strong className={styles.workspaceSwitcherTitle}>
                    {t("gameProject.workspaceCardTitle", { defaultValue: "工作区 / Workspace" })}
                  </Text>
                  <div className={styles.workspaceSwitcherSubtitle}>
                    {t("gameProject.workspaceCardSubtitle", {
                      defaultValue: "当前工作区决定 Project Data、Agent Profiles、Sessions、Audit、Cache 的存储位置。",
                    })}
                  </div>
                </div>
              </div>
              <Alert
                type="info"
                showIcon
                message={t("gameProject.workspaceSwitchGuardrailTitle", { defaultValue: "Workspace Switch" })}
                description={t("gameProject.workspaceSwitchGuardrailBody", {
                  defaultValue: "切换工作区会切换 Project Data / Agent Profiles / Sessions / Cache，但不会删除旧工作区数据。切换 agent 只切换权限和 session，不切换 Project Data。",
                })}
                className={styles.mapReviewAlert}
              />
              <div className={styles.workspaceSwitcherGrid}>
                <div className={styles.workspaceSwitcherPanel}>
                  <Text strong>{t("gameProject.workspaceCurrentPanelTitle", { defaultValue: "当前工作区" })}</Text>
                  <Descriptions column={1} size="small" className={styles.projectSetupMeta}>
                    <Descriptions.Item label={t("gameProject.projectSetupWorkspaceRoot", { defaultValue: "Current Workspace Root" })}>
                      {currentWorkspaceRoot}
                    </Descriptions.Item>
                    <Descriptions.Item label={t("gameProject.projectSetupWorkspaceConfigPath", { defaultValue: "workspace.yaml 路径" })}>
                      {currentWorkspaceConfigPath}
                    </Descriptions.Item>
                    <Descriptions.Item label={t("gameProject.workspaceActiveProjectKey", { defaultValue: "active_project_key" })}>
                      {currentActiveProjectKey}
                    </Descriptions.Item>
                    <Descriptions.Item label={t("gameProject.workspaceActiveProjectRoot", { defaultValue: "active_project_root" })}>
                      {currentActiveProjectRoot}
                    </Descriptions.Item>
                    <Descriptions.Item label={t("gameProject.projectBundleRoot", { defaultValue: "Project Bundle Root" })}>
                      {currentProjectBundleRoot}
                    </Descriptions.Item>
                    <Descriptions.Item label={t("gameProject.projectSetupCurrentAgent", { defaultValue: "当前 agent" })}>
                      {selectedAgent || storageSummary?.current_agent_id || "-"}
                    </Descriptions.Item>
                    <Descriptions.Item label={t("gameProject.projectSetupCapabilityRole", { defaultValue: "当前 role" })}>
                      {projectCapabilityStatus?.role || "-"}
                    </Descriptions.Item>
                    <Descriptions.Item label={t("gameProject.projectSetupCapabilitySource", { defaultValue: "capability_source" })}>
                      {projectCapabilityStatus?.capability_source || "-"}
                    </Descriptions.Item>
                  </Descriptions>
                  {!hasActiveProjectRoot ? (
                    <Alert
                      type="warning"
                      showIcon
                      message={t("gameProject.workspaceMissingProjectRoot", { defaultValue: "请设置 Project Root" })}
                    />
                  ) : null}
                </div>
                <div className={styles.workspaceSwitcherPanel}>
                  <Text strong>{t("gameProject.workspaceSwitchPanelTitle", { defaultValue: "切换工作区" })}</Text>
                  <div className={styles.projectSetupHint}>
                    {t("gameProject.workspaceSwitchPrimaryHint", {
                      defaultValue: "打开/切换工作区是主流程；目录不存在时请使用新建工作区。",
                    })}
                  </div>
                  <Input
                    value={workspaceRootInput}
                    onChange={(event) => setWorkspaceRootInput(event.target.value)}
                    placeholder={t("gameProject.projectSetupWorkspaceRootPlaceholder", { defaultValue: "/Users/Admin/LTClawWorkspace" })}
                  />
                  <Space wrap>
                    <Button size="small" type="primary" onClick={() => void handleSaveWorkspaceRoot(false)} loading={savingWorkspaceRoot}>
                      {t("gameProject.projectSetupOpenWorkspaceRoot", { defaultValue: "打开/切换工作区" })}
                    </Button>
                    <Button size="small" onClick={() => void handleSaveWorkspaceRoot(true)} loading={savingWorkspaceRoot}>
                      {t("gameProject.projectSetupCreateWorkspaceRoot", { defaultValue: "新建工作区" })}
                    </Button>
                    <Button size="small" icon={<CopyOutlined />} onClick={() => copyText(workspaceRootStatus?.active_workspace_root || setupStatus?.active_workspace_root || workspaceRootInput || "") }>
                      {t("gameProject.projectSetupCopyWorkspaceRoot", { defaultValue: "复制当前工作区路径" })}
                    </Button>
                    <Button size="small" disabled title={t("gameProject.projectSetupOpenWorkspaceFolderUnsupported", { defaultValue: "当前客户端暂不支持打开文件夹" })}>
                      {t("gameProject.projectSetupOpenWorkspaceFolder", { defaultValue: "打开工作区文件夹" })}
                    </Button>
                  </Space>
                  <div className={styles.workspaceSwitcherUnsupportedHint}>
                    {t("gameProject.projectSetupOpenWorkspaceFolderUnsupported", { defaultValue: "当前客户端暂不支持打开文件夹" })}
                  </div>
                </div>
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

            <div className={styles.projectSetupBlocks}>
              <div className={styles.projectSetupBlock}>
                <div className={styles.projectSetupBlockHeader}>
                  <Text strong>{t("gameProject.projectSetupEnvironmentTitle", { defaultValue: "Current Environment" })}</Text>
                </div>
                <Descriptions column={1} size="small" className={styles.projectSetupMeta}>
                  <Descriptions.Item label={t("gameProject.projectSetupWorkspaceRoot", { defaultValue: "Workspace Root" })}>
                    {setupStatus?.active_workspace_root || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupProjectRootShort", { defaultValue: "Project Root" })}>
                    {setupStatus?.project_root || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectBundleRoot", { defaultValue: "Project Bundle Root" })}>
                    {setupStatus?.project_bundle_root || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectKey", { defaultValue: "Current Project" })}>
                    {setupStatus?.project_key || setupStatus?.active_workspace_project_key || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupCurrentAgent", { defaultValue: "Current Agent" })}>
                    {selectedAgent || storageSummary?.current_agent_id || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupCapabilityRole", { defaultValue: "Role" })}>
                    {projectCapabilityStatus?.role || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupCapabilitySource", { defaultValue: "Capability Source" })}>
                    {projectCapabilityStatus?.capability_source || "-"}
                  </Descriptions.Item>
                </Descriptions>
              </div>

              <div className={styles.projectSetupBlock}>
                <div className={styles.projectSetupBlockHeader}>
                  <Text strong>{t("gameProject.projectSetupLocalRootTitle", { defaultValue: "Local Project Root" })}</Text>
                  <Button size="small" type="primary" onClick={handleSaveProjectRoot} loading={savingProjectSetupRoot}>
                    {t("common.save")}
                  </Button>
                </div>
                <div className={styles.projectSetupHint}>
                  {t("gameProject.projectSetupLocalRootHint", {
                    defaultValue: "Project Setup 以本地项目目录为主入口，不把 SVN Root 作为主要配置入口。",
                  })}
                </div>
                <Input
                  value={projectRootInput}
                  onChange={(event) => setProjectRootInput(event.target.value)}
                  placeholder={t("gameProject.svnWorkingCopyPathPlaceholder", {
                    defaultValue: LOCAL_PROJECT_DIRECTORY_LABEL,
                  })}
                />
                {projectRootDirty ? (
                  <Alert
                    type="warning"
                    showIcon
                    message={t("gameProject.projectSetupProjectRootDirty", {
                      defaultValue: "当前输入值与后端实际生效的 Project Root 不一致，保存后才会生效。",
                    })}
                    className={styles.mapReviewAlert}
                  />
                ) : null}
                <Descriptions column={1} size="small" className={styles.projectSetupMeta}>
                  <Descriptions.Item label={t("gameProject.projectSetupEffectiveProjectRoot", { defaultValue: "Effective Project Root" })}>
                    {setupStatus?.project_root || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupProjectRootSource", { defaultValue: "Project Root Source" })}>
                    {setupStatus?.project_root_source || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectKey", { defaultValue: "Project Key" })}>
                    {setupStatus?.project_key || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectBundleRoot", { defaultValue: "Project Bundle Root" })}>
                    {setupStatus?.project_bundle_root || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupUserConfigRoot", { defaultValue: "user_config.svn_local_root" })}>
                    {setupStatus?.user_config_svn_local_root || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupProjectConfigRoot", { defaultValue: "project_config.svn.root" })}>
                    {setupStatus?.project_config_svn_root || "-"}
                  </Descriptions.Item>
                </Descriptions>
              </div>

              <div className={styles.projectSetupBlock}>
                <div className={styles.projectSetupBlockHeader}>
                  <Text strong>{t("gameProject.projectSetupFrontendRuntimeTitle", { defaultValue: "Frontend Runtime Info" })}</Text>
                </div>
                <Descriptions column={1} size="small" className={styles.projectSetupMeta}>
                  <Descriptions.Item label={t("gameProject.projectSetupFrontendBuildId", { defaultValue: "Frontend Build" })}>
                    {import.meta.env.VITE_FRONTEND_BUILD_ID || "dev"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupFrontendBuildTime", { defaultValue: "Frontend Build Time" })}>
                    {import.meta.env.VITE_FRONTEND_BUILD_TIME || "dev"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupFrontendApiBase", { defaultValue: "API Base" })}>
                    {frontendRuntimeInfo?.api_base || "/api"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupFrontendStaticSource", { defaultValue: "Backend Static Source" })}>
                    {frontendRuntimeInfo?.console_static_source || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupFrontendStaticDir", { defaultValue: "Backend Static Dir" })}>
                    {frontendRuntimeInfo?.console_static_dir || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupFrontendIndexMtime", { defaultValue: "Index MTime" })}>
                    {frontendRuntimeInfo?.console_index_mtime || "-"}
                  </Descriptions.Item>
                </Descriptions>
              </div>

              <div className={styles.projectSetupBlock}>
                <div className={styles.projectSetupBlockHeader}>
                  <Text strong>{t("gameProject.projectSetupCapabilityStatusTitle", { defaultValue: "Capability Status" })}</Text>
                  <Space wrap>
                    <Button size="small" onClick={() => navigate("/agent/config")}>
                      {t("gameProject.projectSetupOpenAgentConfig", { defaultValue: "打开 Agent 设置" })}
                    </Button>
                    <Button
                      size="small"
                      type="primary"
                      onClick={() => void handleSaveWorkspaceAgentProfile()}
                      loading={savingWorkspaceAgentProfile}
                      disabled={!selectedAgent || !workspaceAgentProfile}
                    >
                      {t("gameProject.projectSetupSaveAgentProfile", { defaultValue: "保存 Role / Capabilities" })}
                    </Button>
                  </Space>
                </div>
                <Descriptions column={1} size="small" className={styles.projectSetupMeta}>
                  <Descriptions.Item label={t("gameProject.projectSetupCapabilityRole", { defaultValue: "Role" })}>
                    {projectCapabilityStatus?.role || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupCapabilityAgentId", { defaultValue: "Agent ID" })}>
                    {projectCapabilityStatus?.agent_id || selectedAgent || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupCapabilitySource", { defaultValue: "Capability Source" })}>
                    {projectCapabilityStatus?.capability_source || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupCapabilityLegacyFallback", { defaultValue: "Legacy Role Fallback" })}>
                    {projectCapabilityStatus ? String(projectCapabilityStatus.is_legacy_role_fallback) : "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupCapabilityColdStart", { defaultValue: "Cold-start" })}>
                    {projectCapabilityStatus
                      ? `${String(projectCapabilityStatus.required_for_cold_start["knowledge.candidate.read"])} / ${String(projectCapabilityStatus.required_for_cold_start["knowledge.candidate.write"])}`
                      : "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupCapabilityFormalMap", { defaultValue: "Formal Map" })}>
                    {projectCapabilityStatus
                      ? `${String(projectCapabilityStatus.required_for_formal_map["knowledge.map.read"])} / ${String(projectCapabilityStatus.required_for_formal_map["knowledge.map.edit"])}`
                      : "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupCapabilityRelease", { defaultValue: "Release" })}>
                    {projectCapabilityStatus
                      ? `${String(projectCapabilityStatus.required_for_release["knowledge.read"])} / ${String(projectCapabilityStatus.required_for_release["knowledge.build"])} / ${String(projectCapabilityStatus.required_for_release["knowledge.publish"])}`
                      : "-"}
                  </Descriptions.Item>
                </Descriptions>
                {projectCapabilityStatus && !projectCapabilityStatus.required_for_cold_start["knowledge.candidate.write"] ? (
                  <Alert
                    type="warning"
                    showIcon
                    message={t("gameProject.projectSetupCapabilityColdStartMissing", {
                      defaultValue: "当前缺少 knowledge.candidate.write，Rule-only 冷启动写入请求会被拦截。",
                    })}
                    className={styles.mapReviewAlert}
                  />
                ) : null}
                {projectCapabilityStatus && projectCapabilityStatus.missing_required_capabilities.length > 0 ? (
                  <Alert
                    type="info"
                    showIcon
                    message={t("gameProject.projectSetupCapabilityMissingList", {
                      defaultValue: `Missing required capabilities: ${projectCapabilityStatus.missing_required_capabilities.join(", ")}`,
                    })}
                    className={styles.mapReviewAlert}
                  />
                ) : null}
                {workspaceAgentProfile ? (
                  <div className={styles.projectSetupListSection}>
                    <Text strong>{t("gameProject.projectSetupAgentProfileEditor", { defaultValue: "Role / Capability Editor" })}</Text>
                    <Form.Item label={t("gameProject.projectSetupAgentDisplayName", { defaultValue: "Display Name" })}>
                      <Input
                        value={workspaceAgentProfile.display_name}
                        onChange={(event) =>
                          setWorkspaceAgentProfile((current) =>
                            current
                              ? { ...current, display_name: event.target.value }
                              : current,
                          )
                        }
                      />
                    </Form.Item>
                    <Form.Item label={t("gameProject.projectSetupAgentRole", { defaultValue: "Role" })}>
                      <Select
                        value={workspaceAgentProfile.role}
                        onChange={(value) =>
                          setWorkspaceAgentProfile((current) =>
                            current
                              ? { ...current, role: value as LocalAgentProfile["role"] }
                              : current,
                          )
                        }
                        options={WORKSPACE_AGENT_ROLE_OPTIONS.map((role) => ({ label: role, value: role }))}
                      />
                    </Form.Item>
                    <Form.Item label={t("gameProject.projectSetupAgentCapabilities", { defaultValue: "Explicit Capabilities" })}>
                      <Select
                        mode="multiple"
                        value={workspaceAgentProfile.capabilities}
                        onChange={(values) =>
                          setWorkspaceAgentProfile((current) =>
                            current
                              ? { ...current, capabilities: values as string[] }
                              : current,
                          )
                        }
                        options={WORKSPACE_AGENT_CAPABILITY_OPTIONS.map((capability) => ({ label: capability, value: capability }))}
                        placeholder={t("gameProject.projectSetupAgentCapabilitiesPlaceholder", {
                          defaultValue: "留空表示使用 Role 模板能力集",
                        })}
                      />
                    </Form.Item>
                  </div>
                ) : null}
              </div>

              <div className={styles.projectSetupBlock}>
                <div className={styles.projectSetupBlockHeader}>
                  <Text strong>{t("gameProject.projectSetupTablesTitle", { defaultValue: "Tables Source" })}</Text>
                  <Button size="small" type="primary" onClick={handleSaveTablesSource} loading={savingProjectSetupTables}>
                    {t("common.save")}
                  </Button>
                </div>
                <Form.Item label={t("gameProject.projectSetupTablesRoots", { defaultValue: "Roots" })}>
                  <TextArea rows={2} value={tablesRootsInput} onChange={(event) => setTablesRootsInput(event.target.value)} />
                </Form.Item>
                <Form.Item label={t("gameProject.projectSetupTablesInclude", { defaultValue: "Include" })}>
                  <TextArea rows={3} value={tablesIncludeInput} onChange={(event) => setTablesIncludeInput(event.target.value)} />
                </Form.Item>
                <Form.Item label={t("gameProject.projectSetupTablesExclude", { defaultValue: "Exclude" })}>
                  <TextArea rows={3} value={tablesExcludeInput} onChange={(event) => setTablesExcludeInput(event.target.value)} />
                </Form.Item>
                <Form.Item label={t("gameProject.projectSetupHeaderRow", { defaultValue: "Header Row" })}>
                  <InputNumber min={1} value={tablesHeaderRow} onChange={(value) => setTablesHeaderRow(Number(value || 1))} />
                </Form.Item>
                <Form.Item label={t("gameProject.projectSetupPrimaryKeys", { defaultValue: "Primary Key Candidates" })}>
                  <TextArea rows={2} value={tablesPrimaryKeysInput} onChange={(event) => setTablesPrimaryKeysInput(event.target.value)} />
                </Form.Item>
              </div>

              <div className={styles.projectSetupBlock}>
                <div className={styles.projectSetupBlockHeader}>
                  <Text strong>{t("gameProject.projectSetupDiscoveryTitle", { defaultValue: "Source Discovery" })}</Text>
                  <Button size="small" onClick={handleDiscoverSources} loading={discoveringSources}>
                    {t("gameProject.projectSetupDiscoverButton", { defaultValue: "检查数据源" })}
                  </Button>
                </div>
                <div className={styles.projectSetupSummaryGrid}>
                  <div className={styles.projectSetupSummaryItem}><span>discovered</span><strong>{discoverySummary.discovered_table_count}</strong></div>
                  <div className={styles.projectSetupSummaryItem}><span>available</span><strong>{discoverySummary.available_table_count ?? 0}</strong></div>
                  <div className={styles.projectSetupSummaryItem}><span>excluded</span><strong>{discoverySummary.excluded_table_count}</strong></div>
                  <div className={styles.projectSetupSummaryItem}><span>unsupported</span><strong>{discoverySummary.unsupported_table_count}</strong></div>
                  <div className={styles.projectSetupSummaryItem}><span>errors</span><strong>{discoverySummary.error_count}</strong></div>
                </div>
                {discoveryRoots.length > 0 ? (
                  <div className={styles.projectSetupListSection}>
                    <Text strong>{t("gameProject.projectSetupRootsResolved", { defaultValue: "Resolved Source Roots" })}</Text>
                    {discoveryRoots.map((item) => (
                      <div key={`${item.configured_root}-${item.resolved_root}`} className={styles.projectSetupListItem}>
                        <span>{`${item.configured_root} -> ${item.resolved_root}`}</span>
                        <Tag color={item.exists && item.is_directory ? "green" : "red"}>
                          {item.exists && item.is_directory ? "exists" : "missing"}
                        </Tag>
                      </div>
                    ))}
                    {discoveryErrors.some((item) => item.reason === "source_root_missing") ? (
                      <Alert
                        type="warning"
                        showIcon
                        message={t("gameProject.projectSetupSourceRootMissingHint", {
                          defaultValue: "如果 Project Root 已经是 multi_source_project，则 Table Root 应填写 Tables，而不是再次填写 multi_source_project。",
                        })}
                      />
                    ) : null}
                  </div>
                ) : null}
                {discoveryNotScanned ? (
                  <Alert
                    type="info"
                    showIcon
                    message={t("gameProject.projectSetupDiscoveryNotScanned", {
                      defaultValue: "尚未检查数据源",
                    })}
                  />
                ) : null}
                {!discoveryNotScanned && (discoverySummary.available_table_count ?? 0) <= 0 ? (
                  <Alert
                    type="info"
                    showIcon
                    message={t("gameProject.projectSetupNoTablesMessage", {
                      defaultValue: "当前没有可用于 Rule-only 冷启动的 CSV 表文件，后续构建阶段不可继续。",
                    })}
                  />
                ) : null}
                <div className={styles.projectSetupListGroup}>
                  <div className={styles.projectSetupListSection}>
                    <Text strong>{t("gameProject.projectSetupAvailableList", { defaultValue: "Rule-only Available (CSV)" })}</Text>
                    {availableTableFiles.length > 0 ? (
                      availableTableFiles.map((item) => (
                        <div key={`available-${item.source_path}`} className={styles.projectSetupListItem}>
                          <span>{item.source_path}</span>
                          <Tag color="green">{item.cold_start_reason}</Tag>
                        </div>
                      ))
                    ) : discoveryNotScanned ? (
                      <div className={styles.projectSetupListEmpty}>-</div>
                    ) : (
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={t("gameProject.projectSetupNoAvailableTables", { defaultValue: "没有发现可用于 Rule-only 冷启动的 CSV 表文件" })} />
                    )}
                  </div>
                  <div className={styles.projectSetupListSection}>
                    <Text strong>{t("gameProject.projectSetupRecognizedList", { defaultValue: "Recognized But Not Rule-only" })}</Text>
                    {recognizedButNotSupportedFiles.length > 0 ? (
                      recognizedButNotSupportedFiles.map((item) => (
                        <div key={`recognized-${item.source_path}`} className={styles.projectSetupListItem}>
                          <span>{item.source_path}</span>
                          <Tag color="gold">{item.cold_start_reason}</Tag>
                        </div>
                      ))
                    ) : (
                      <div className={styles.projectSetupListEmpty}>-</div>
                    )}
                  </div>
                  <div className={styles.projectSetupListSection}>
                    <Text strong>{t("gameProject.projectSetupExcludedList", { defaultValue: "Excluded" })}</Text>
                    {excludedFiles.length > 0 ? (
                      excludedFiles.map((item) => (
                        <div key={`excluded-${item.source_path}`} className={styles.projectSetupListItem}>
                          <span>{item.source_path}</span>
                          <Tag>{item.reason}</Tag>
                        </div>
                      ))
                    ) : (
                      <div className={styles.projectSetupListEmpty}>-</div>
                    )}
                  </div>
                  <div className={styles.projectSetupListSection}>
                    <Text strong>{t("gameProject.projectSetupUnsupportedList", { defaultValue: "Unsupported" })}</Text>
                    {unsupportedFiles.length > 0 ? (
                      unsupportedFiles.map((item) => (
                        <div key={`unsupported-${item.source_path}`} className={styles.projectSetupListItem}>
                          <span>{item.source_path}</span>
                          <Tag color="orange">{item.reason}</Tag>
                        </div>
                      ))
                    ) : (
                      <div className={styles.projectSetupListEmpty}>-</div>
                    )}
                  </div>
                  <div className={styles.projectSetupListSection}>
                    <Text strong>{t("gameProject.projectSetupErrorsList", { defaultValue: "Errors" })}</Text>
                    {discoveryErrors.length > 0 ? (
                      discoveryErrors.map((item, index) => (
                        <div key={`error-${item.source_path || index}`} className={styles.projectSetupListItem}>
                          <span>{item.source_path || "-"}</span>
                          <Tag color="red">{item.reason}</Tag>
                        </div>
                      ))
                    ) : (
                      <div className={styles.projectSetupListEmpty}>-</div>
                    )}
                  </div>
                </div>
              </div>

              <div className={styles.projectSetupBlock}>
                <div className={styles.projectSetupBlockHeader}>
                  <Text strong>{t("gameProject.projectSetupBuildPipelineTitle", { defaultValue: "Build Pipeline Status" })}</Text>
                  <Space wrap>
                    <Button
                      size="small"
                      type="primary"
                      onClick={handleStartColdStartJob}
                      disabled={!canStartColdStartBuild || coldStartProgress.isRunning || !canWriteColdStart}
                      loading={creatingColdStartJob}
                    >
                      {t("gameProject.projectSetupRuleOnlyBuildButton", { defaultValue: "Rule-only 冷启动构建" })}
                    </Button>
                    <Button size="small" icon={<CopyOutlined />} onClick={handleCopyDiagnostics}>
                      {t("gameProject.projectSetupCopyDiagnostics", { defaultValue: "复制诊断信息" })}
                    </Button>
                  </Space>
                </div>
                <Descriptions column={1} size="small" className={styles.projectSetupMeta}>
                  <Descriptions.Item label={t("gameProject.projectSetupBlockingReason", { defaultValue: "Blocking Reason" })}>
                    {effectiveReadiness.blocking_reason || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupNextAction", { defaultValue: "Next Action" })}>
                    {effectiveReadiness.next_action || "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupReadinessSource", { defaultValue: "Readiness Source" })}>
                    {effectiveReadiness.source}
                  </Descriptions.Item>
                </Descriptions>
                {buildBlocked ? (
                  <Alert
                    type="warning"
                    showIcon
                    message={t("gameProject.projectSetupBlockedMessage", {
                      defaultValue: "尚未发现可用于 Rule-only 冷启动的 CSV 表文件，后续构建入口保持不可继续状态。",
                    })}
                  />
                ) : (
                  <Alert
                    type="success"
                    showIcon
                    message={t("gameProject.projectSetupReadyMessage", {
                      defaultValue: "Source Discovery 已发现可用于 Rule-only 冷启动的 CSV 表文件，可以继续后续构建链路。",
                    })}
                  />
                )}
                {!canStartColdStartBuild ? (
                  <div className={styles.projectSetupHint}>
                    {t("gameProject.projectSetupRuleOnlyBuildBlocked", {
                      defaultValue: "未配置有效 Project Root / Tables Source，或当前 Source Discovery 没有可用于 Rule-only 冷启动的 CSV 表，因此构建按钮不可用。",
                    })}
                  </div>
                ) : null}
                {canStartColdStartBuild && !canWriteColdStart ? (
                  <div className={styles.projectSetupHint}>
                    {t("gameProject.projectSetupRuleOnlyBuildPermissionBlocked", {
                      defaultValue: "当前 agent 缺少 knowledge.candidate.write，构建入口已在前端预先禁用。",
                    })}
                  </div>
                ) : null}
                {restoringColdStartJob ? (
                  <Alert
                    type="info"
                    showIcon
                    message={t("gameProject.projectSetupRestoringJob", { defaultValue: "正在恢复上次冷启动任务状态。" })}
                  />
                ) : null}
                {coldStartJob ? (
                  <div className={styles.projectSetupJobPanel}>
                    <Progress percent={coldStartProgress.percent} status={coldStartProgress.statusTone} />
                    <Descriptions column={1} size="small" className={styles.projectSetupMeta}>
                      <Descriptions.Item label={t("gameProject.projectSetupJobId", { defaultValue: "Job ID" })}>
                        {coldStartJob.job_id}
                      </Descriptions.Item>
                      <Descriptions.Item label={t("gameProject.projectSetupJobStatus", { defaultValue: "Status" })}>
                        {coldStartJob.status}
                      </Descriptions.Item>
                      <Descriptions.Item label={t("gameProject.projectSetupJobStage", { defaultValue: "Stage" })}>
                        {coldStartJob.stage}
                      </Descriptions.Item>
                      <Descriptions.Item label={t("gameProject.projectSetupJobMessage", { defaultValue: "Message" })}>
                        {coldStartJob.message}
                      </Descriptions.Item>
                      <Descriptions.Item label={t("gameProject.projectSetupJobCurrentFile", { defaultValue: "Current File" })}>
                        {coldStartJob.current_file || "-"}
                      </Descriptions.Item>
                      <Descriptions.Item label={t("gameProject.projectSetupJobNextAction", { defaultValue: "Next Action" })}>
                        {coldStartJob.next_action || "-"}
                      </Descriptions.Item>
                    </Descriptions>
                    <div className={styles.projectSetupSummaryGrid}>
                      <div className={styles.projectSetupSummaryItem}><span>discovered</span><strong>{coldStartJob.counts.discovered_table_count}</strong></div>
                      <div className={styles.projectSetupSummaryItem}><span>docs</span><strong>{coldStartJob.counts.discovered_doc_count ?? 0}</strong></div>
                      <div className={styles.projectSetupSummaryItem}><span>scripts</span><strong>{coldStartJob.counts.discovered_script_count ?? 0}</strong></div>
                      <div className={styles.projectSetupSummaryItem}><span>raw</span><strong>{coldStartJob.counts.raw_table_index_count}</strong></div>
                      <div className={styles.projectSetupSummaryItem}><span>canonical</span><strong>{coldStartJob.counts.canonical_table_count}</strong></div>
                      <div className={styles.projectSetupSummaryItem}><span>candidate</span><strong>{coldStartJob.counts.candidate_table_count}</strong></div>
                      <div className={styles.projectSetupSummaryItem}><span>warnings</span><strong>{coldStartWarnings.length}</strong></div>
                      <div className={styles.projectSetupSummaryItem}><span>errors</span><strong>{coldStartErrors.length}</strong></div>
                      <div className={styles.projectSetupSummaryItem}><span>timeout</span><strong>{coldStartJob.timeout_seconds}s</strong></div>
                    </div>
                    <div className={styles.projectSetupJobActions}>
                      <Button
                        size="small"
                        onClick={handleCancelColdStartJob}
                        disabled={!coldStartProgress.canCancel}
                        loading={cancellingColdStartJob}
                      >
                        {t("common.cancel")}
                      </Button>
                      <Button size="small" onClick={handleRetryColdStartJob} disabled={!coldStartProgress.canRetry}>
                        {t("common.retry")}
                      </Button>
                      <Button size="small" onClick={() => navigate("/game/map")} disabled={coldStartJob.status !== "succeeded"}>
                        {t("gameProject.projectSetupOpenCandidateMap", { defaultValue: "查看 Candidate Map" })}
                      </Button>
                      <Button size="small" onClick={() => navigate("/game/map")} disabled={coldStartJob.status !== "succeeded"}>
                        {t("gameProject.projectSetupOpenDiffReview", { defaultValue: "查看 Diff Review" })}
                      </Button>
                      <Button size="small" onClick={() => navigate("/game/map")} disabled={coldStartJob.status !== "succeeded"}>
                        {t("gameProject.projectSetupSaveFormalMapEntry", { defaultValue: "保存 Formal Map" })}
                      </Button>
                    </div>
                    {coldStartWarnings.length > 0 ? (
                      <div className={styles.projectSetupListSection}>
                        <Text strong>{t("gameProject.projectSetupWarningsList", { defaultValue: "Warnings" })}</Text>
                        {coldStartWarnings.map((item) => (
                          <div key={item} className={styles.projectSetupListItem}>
                            <span>{item}</span>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {coldStartErrors.length > 0 ? (
                      <div className={styles.projectSetupListSection}>
                        <Text strong>{t("gameProject.projectSetupJobErrors", { defaultValue: "Job Errors" })}</Text>
                        {coldStartErrors.map((item, index) => (
                          <div key={`${item.error}-${index}`} className={styles.projectSetupListItem}>
                            <span>{[item.stage, item.error, item.source_path].filter(Boolean).join(" / ")}</span>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {coldStartJob.status === "succeeded" ? (
                      <Alert
                        type="success"
                        showIcon
                        message={t("gameProject.projectSetupColdStartSuccess", {
                          defaultValue: "Rule-only 冷启动构建完成。可以查看 Candidate Map / Diff Review，并在 Map Editor 中显式执行 Save Formal Map。",
                        })}
                        description={
                          <div className={styles.projectSetupSuccessMeta}>
                            <div>{`candidate_table_count: ${coldStartProgress.candidateTableCount}`}</div>
                            <div>{`candidate_refs: ${coldStartCandidateRefs.join(", ") || "-"}`}</div>
                          </div>
                        }
                      />
                    ) : null}
                  </div>
                ) : (
                  <Button disabled={buildBlocked} className={styles.projectSetupDisabledBuildButton}>
                    {t("gameProject.projectSetupSubsequentBuildEntry", { defaultValue: "后续构建入口状态" })}
                  </Button>
                )}
              </div>
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

          <Card
            title={t("gameProject.projectAccessConfig", { defaultValue: "Project access" })}
            className={styles.section}
          >
            <Form.Item
              label={t("gameProject.maintainerModeLabel", { defaultValue: "Maintainer mode" })}
              name="is_maintainer"
              valuePropName="checked"
              tooltip={t(
                "gameProject.maintainerModeTooltip",
                "This legacy role toggle is still kept for compatibility. It no longer enables built-in SVN runtime operations.",
              )}
            >
              <Switch />
            </Form.Item>
            <Form.Item
              label={t("gameProject.svnWorkingCopyPath", { defaultValue: "Local project root" })}
              name="svn_working_copy_path"
              rules={[{ required: true, message: t("gameProject.svnWorkingCopyPathRequired") }]}
            >
              <Input
                placeholder={t("gameProject.svnWorkingCopyPathPlaceholder", {
                  defaultValue: LOCAL_PROJECT_DIRECTORY_LABEL,
                })}
              />
            </Form.Item>

            <div className={styles.projectIntroHint}>
              {t(
                "gameProject.projectRootHint",
                "LTClaw currently uses this path only as the local project root. SVN URL, credentials, trust cert, update, commit, watcher, and polling are frozen and must stay in your external SVN workflow.",
              )}
            </div>

            <div className={styles.storageHint}>
              {t(
                "gameProject.legacySvnConfigHint",
                "Legacy config fields such as svn_local_root and svn.root are still read for compatibility, but they now only mean the local project path.",
              )}
            </div>
          </Card>

          <Card title={t("gameProject.sourceScopeConfig", { defaultValue: "Source scope and filters" })} className={styles.section}>
            <div className={styles.storageHint}>
              {t(
                "gameProject.sourceScopeHint",
                "These fields now describe which local project paths and file patterns LTClaw reads for indexing and analysis. They are not an active SVN watcher or polling runtime.",
              )}
            </div>
            <Form.Item label={t("gameProject.sourcePaths", { defaultValue: "Project source paths" })} name="watch_paths">
              <TextArea
                rows={4}
                placeholder={t("gameProject.sourcePathsPlaceholder", { defaultValue: "One relative path per line, for example:\nTables\nConfigs" })}
              />
            </Form.Item>

            <Form.Item label={t("gameProject.sourceIncludePatterns", { defaultValue: "Included file patterns" })} name="watch_patterns">
              <TextArea
                rows={4}
                placeholder={t("gameProject.sourceIncludePatternsPlaceholder", { defaultValue: "One pattern per line, for example:\n.xlsx\n.csv\n.md" })}
              />
            </Form.Item>

            <Form.Item label={t("gameProject.sourceExcludePatterns", { defaultValue: "Excluded file patterns" })} name="watch_exclude_patterns">
              <TextArea
                rows={4}
                placeholder={t("gameProject.sourceExcludePatternsPlaceholder", { defaultValue: "One exclude pattern per line, for example:\n**/temp/**\n**/.svn/**\n**/~$*" })}
              />
            </Form.Item>
          </Card>

          <Card title={t("gameProject.legacyFrozenRuntimeConfig", { defaultValue: "Legacy frozen runtime settings" })} className={styles.section}>
            <div className={styles.storageHint}>
              {t(
                "gameProject.legacyFrozenRuntimeHint",
                "These legacy fields are shown only to explain current compatibility boundaries. LTClaw no longer starts an SVN watcher, polling loop, or config commit flow from this page.",
              )}
            </div>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Form.Item name="auto_sync" valuePropName="checked">
                <Switch disabled /> {t("gameProject.autoSyncFrozen", { defaultValue: "SVN auto sync (frozen)" })}
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
                <Input
                  disabled
                  placeholder={t("gameProject.indexCommitMessageTemplateFrozen", {
                    defaultValue: "Frozen with SVN runtime. Index commits are not part of the current LTClaw main flow.",
                  })}
                />
              </Form.Item>
            </Space>
          </Card>

          <Card title={t("gameProject.formalMapWorkspaceTitle", { defaultValue: "Formal map workspace" })} className={styles.section}>
            <FormalMapWorkspace mode="summary" />
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
