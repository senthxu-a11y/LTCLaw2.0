import { useCallback, useEffect, useState } from "react";
import { Form, Input, Switch, Button } from "@agentscope-ai/design";
import {
  CheckCircleOutlined,
  CopyOutlined,
  DatabaseOutlined,
  DownOutlined,
  ExclamationCircleOutlined,
  FolderOpenOutlined,
  LoadingOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Alert, Descriptions, Drawer, Empty, InputNumber, Modal, Progress, Space, Tabs, Tooltip, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
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
  ValidationIssue,
} from "../../api/types/game";
import { useAgentStore } from "../../stores/agentStore";
import { copyText } from "../Chat/utils";
import {
  buildProjectSetupDiagnosticsText,
  canStartRuleOnlyColdStartBuild,
  clearColdStartActiveJobId,
  getEffectiveProjectSetupBuildReadiness,
  loadColdStartActiveJobId,
  saveColdStartActiveJobId,
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

type ProjectSetupViewState = {
  level: "empty" | "dirty" | "notScanned" | "warning" | "blocked" | "ready" | "running" | "error" | "unknown";
  titleKey: string;
  suggestionKey: string;
  reasonKey?: string;
  reasonText?: string;
  primaryAction: "save" | "discover" | "viewIssues" | "coldStart" | "viewJob" | null;
};

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
  const [frontendRuntimeInfo, setFrontendRuntimeInfo] = useState<FrontendRuntimeInfo | null>(null);
  const [projectCapabilityStatus, setProjectCapabilityStatus] = useState<ProjectCapabilityStatus | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardSaving, setWizardSaving] = useState(false);
  const [wizardForm] = Form.useForm<{ id?: string; name: string }>();
  const [setupStatus, setSetupStatus] = useState<ProjectSetupStatusResponse | null>(null);
  const [discoveryResult, setDiscoveryResult] = useState<ProjectTableSourceDiscoveryResponse | null>(null);
  const [projectRootInput, setProjectRootInput] = useState("");
  const [tablesRootsInput, setTablesRootsInput] = useState("");
  const [tablesIncludeInput, setTablesIncludeInput] = useState("");
  const [tablesExcludeInput, setTablesExcludeInput] = useState("");
  const [tablesHeaderRow, setTablesHeaderRow] = useState(1);
  const [tablesPrimaryKeysInput, setTablesPrimaryKeysInput] = useState("");
  const [savingProjectSetupRoot, setSavingProjectSetupRoot] = useState(false);
  const [savingProjectSetupTables, setSavingProjectSetupTables] = useState(false);
  const [discoveringSources, setDiscoveringSources] = useState(false);
  const [activeColdStartJobId, setActiveColdStartJobId] = useState("");
  const [coldStartJob, setColdStartJob] = useState<ColdStartJobState | null>(null);
  const [creatingColdStartJob, setCreatingColdStartJob] = useState(false);
  const [cancellingColdStartJob, setCancellingColdStartJob] = useState(false);
  const [advancedDrawerOpen, setAdvancedDrawerOpen] = useState(false);
  const [sourceDrawerOpen, setSourceDrawerOpen] = useState(false);

  const applySetupStatus = useCallback((status: ProjectSetupStatusResponse | null) => {
    setSetupStatus(status);
    if (!status) {
      setProjectRootInput("");
      setTablesRootsInput("");
      setTablesIncludeInput("");
      setTablesExcludeInput("");
      setTablesHeaderRow(1);
      setTablesPrimaryKeysInput("");
      return;
    }
    setProjectRootInput(status.project_root ?? "");
    setTablesRootsInput(joinProjectSetupLines(status.tables_config.roots));
    setTablesIncludeInput(joinProjectSetupLines(status.tables_config.include));
    setTablesExcludeInput(joinProjectSetupLines(status.tables_config.exclude));
    setTablesHeaderRow(status.tables_config.header_row || 1);
    setTablesPrimaryKeysInput(joinProjectSetupLines(status.tables_config.primary_key_candidates));
  }, []);

  const fetchConfig = useCallback(async () => {
    if (!selectedAgent) {
      applySetupStatus(null);
      setDiscoveryResult(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [projectConfig, userConfig, storage, projectSetupStatus, capabilityStatus] = await Promise.all([
        gameApi.getProjectConfig(selectedAgent),
        gameApi.getUserConfig(selectedAgent).catch(() => null),
        gameApi.getStorageSummary(selectedAgent).catch(() => null),
        gameApi.getProjectSetupStatus(selectedAgent).catch(() => null),
        gameApi.getProjectCapabilityStatus(selectedAgent).catch(() => null),
      ]);
      const runtimeInfo = await gameApi.getFrontendRuntimeInfo().catch(() => null);
      setStorageSummary(storage);
      setFrontendRuntimeInfo(runtimeInfo);
      setProjectCapabilityStatus(capabilityStatus);
      applySetupStatus(projectSetupStatus);
      setDiscoveryResult(null);
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
  }, [applySetupStatus, form, selectedAgent, t]);

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
      await fetchConfig();
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.saveFailed");
      message.error(errMsg);
    } finally {
      setSavingProjectSetupRoot(false);
    }
  };

  const handleSaveTablesSource = async () => {
    if (!selectedAgent) {
      return;
    }
    try {
      setSavingProjectSetupTables(true);
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
  const selectedAgentSummary = agents.find((agent) => agent.id === selectedAgent);
  const currentProjectName = selectedAgentSummary?.name || setupStatus?.project_key || selectedAgent || "-";
  const tablesConfigDirty =
    joinProjectSetupLines(splitProjectSetupLines(tablesRootsInput)) !== joinProjectSetupLines(setupStatus?.tables_config.roots) ||
    joinProjectSetupLines(splitProjectSetupLines(tablesIncludeInput)) !== joinProjectSetupLines(setupStatus?.tables_config.include) ||
    joinProjectSetupLines(splitProjectSetupLines(tablesExcludeInput)) !== joinProjectSetupLines(setupStatus?.tables_config.exclude) ||
    tablesHeaderRow !== (setupStatus?.tables_config.header_row || 1) ||
    joinProjectSetupLines(splitProjectSetupLines(tablesPrimaryKeysInput)) !== joinProjectSetupLines(setupStatus?.tables_config.primary_key_candidates);
  const sourceIssueCount = recognizedButNotSupportedFiles.length + unsupportedFiles.length + excludedFiles.length + discoveryErrors.length;
  const latestDiscoveryLabel = "-";
  const advancedStorageItems = [
    [t("gameWorkspaceUi.project.labels.effectiveProjectRoot", { defaultValue: "Effective Project Root" }), setupStatus?.project_root || "-"],
    [t("gameWorkspaceUi.project.labels.projectRootSource", { defaultValue: "Project Root Source" }), setupStatus?.project_root_source || "-"],
    [t("gameWorkspaceUi.project.labels.projectKey", { defaultValue: "Project Key" }), setupStatus?.project_key || "-"],
    [t("gameWorkspaceUi.project.labels.projectBundleRoot", { defaultValue: "Project Bundle Root" }), setupStatus?.project_bundle_root || "-"],
    [t("gameWorkspaceUi.project.labels.userConfigRoot", { defaultValue: "user_config.svn_local_root" }), setupStatus?.user_config_svn_local_root || "-"],
    [t("gameWorkspaceUi.project.labels.projectConfigRoot", { defaultValue: "project_config.svn.root" }), setupStatus?.project_config_svn_root || "-"],
    [t("gameWorkspaceUi.project.labels.blockingReason", { defaultValue: "Blocking Reason" }), effectiveReadiness.blocking_reason || "-"],
    [t("gameWorkspaceUi.project.labels.nextAction", { defaultValue: "Next Action" }), effectiveReadiness.next_action || "-"],
  ] as const;
  const projectSetupViewState: ProjectSetupViewState = (() => {
    if (coldStartJob && coldStartProgress.isRunning) {
      return {
        level: "running",
        titleKey: "gameWorkspaceUi.project.status.runningTitle",
        reasonKey: "gameWorkspaceUi.project.status.runningReason",
        reasonText: coldStartJob.message || coldStartJob.stage,
        suggestionKey: "gameWorkspaceUi.project.status.runningSuggestion",
        primaryAction: "viewJob",
      };
    }
    if (coldStartJob && (coldStartJob.status === "failed" || coldStartJob.status === "cancelled")) {
      return {
        level: "error",
        titleKey: "gameWorkspaceUi.project.status.errorTitle",
        reasonKey: "gameWorkspaceUi.project.status.errorReason",
        reasonText: coldStartJob.message || coldStartJob.status,
        suggestionKey: "gameWorkspaceUi.project.status.errorSuggestion",
        primaryAction: "viewJob",
      };
    }
    if (projectRootDirty || tablesConfigDirty) {
      return {
        level: "dirty",
        titleKey: "gameWorkspaceUi.project.status.dirtyTitle",
        reasonKey: "gameWorkspaceUi.project.status.dirtyReason",
        reasonText: t("gameWorkspaceUi.project.status.dirtyReasonText", { defaultValue: "当前输入与已保存配置不一致。" }),
        suggestionKey: "gameWorkspaceUi.project.status.dirtySuggestion",
        primaryAction: "save",
      };
    }
    if (!setupStatus?.project_root) {
      return {
        level: "empty",
        titleKey: "gameWorkspaceUi.project.status.emptyTitle",
        reasonKey: "gameWorkspaceUi.project.status.emptyReason",
        reasonText: t("gameWorkspaceUi.project.status.emptyReasonText", { defaultValue: "尚未填写本地项目目录。" }),
        suggestionKey: "gameWorkspaceUi.project.status.emptySuggestion",
        primaryAction: "save",
      };
    }
    if (discoveryNotScanned) {
      return {
        level: "notScanned",
        titleKey: "gameWorkspaceUi.project.status.notScannedTitle",
        reasonKey: "gameWorkspaceUi.project.status.notScannedReason",
        reasonText: t("gameWorkspaceUi.project.status.notScannedReasonText", { defaultValue: "尚未执行数据源检查。" }),
        suggestionKey: "gameWorkspaceUi.project.status.notScannedSuggestion",
        primaryAction: "discover",
      };
    }
    if (sourceIssueCount > 0) {
      return {
        level: "warning",
        titleKey: "gameWorkspaceUi.project.status.warningTitle",
        reasonKey: "gameWorkspaceUi.project.status.warningReason",
        reasonText: t("gameWorkspaceUi.project.status.warningReasonText", { count: sourceIssueCount }),
        suggestionKey: "gameWorkspaceUi.project.status.warningSuggestion",
        primaryAction: "viewIssues",
      };
    }
    if (buildBlocked) {
      return {
        level: "blocked",
        titleKey: "gameWorkspaceUi.project.status.blockedTitle",
        reasonKey: "gameWorkspaceUi.project.status.blockedReason",
        reasonText: effectiveReadiness.blocking_reason || undefined,
        suggestionKey: "gameWorkspaceUi.project.status.blockedSuggestion",
        primaryAction: "discover",
      };
    }
    if (canStartColdStartBuild) {
      return {
        level: "ready",
        titleKey: "gameWorkspaceUi.project.status.readyTitle",
        reasonKey: "gameWorkspaceUi.project.status.readyReason",
        reasonText: t("gameWorkspaceUi.project.status.readyReasonText", { defaultValue: "数据源已满足冷启动构建条件。" }),
        suggestionKey: "gameWorkspaceUi.project.status.readySuggestion",
        primaryAction: "coldStart",
      };
    }
    return {
      level: "unknown",
      titleKey: "gameWorkspaceUi.project.status.unknownTitle",
      reasonText: t("gameWorkspaceUi.project.status.unknownReasonText", { defaultValue: "当前状态还不能明确判断。" }),
      suggestionKey: "gameWorkspaceUi.project.status.unknownSuggestion",
      primaryAction: null,
    };
  })();

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

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

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
    fetchColdStartJob(savedJobId)
      .catch(() => {
        clearColdStartActiveJobId(selectedAgent);
        setActiveColdStartJobId("");
        setColdStartJob(null);
      });
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

  const handleSaveAndContinue = async () => {
    if (projectRootDirty) {
      await handleSaveProjectRoot();
    }
    if (tablesConfigDirty) {
      await handleSaveTablesSource();
    }
  };

  const sourceDrawerTabs = [
    {
      key: "issues",
      label: t("gameWorkspaceUi.project.sourceDrawer.tabs.issues", { defaultValue: "异常" }),
      items: [
        ...recognizedButNotSupportedFiles.map((item) => ({ key: `recognized-${item.source_path}`, title: item.source_path, detail: item.cold_start_reason })),
        ...unsupportedFiles.map((item) => ({ key: `unsupported-${item.source_path}`, title: item.source_path, detail: item.reason })),
        ...excludedFiles.map((item) => ({ key: `excluded-${item.source_path}`, title: item.source_path, detail: item.reason })),
        ...discoveryErrors.map((item, index) => ({ key: `error-${index}`, title: item.source_path || "-", detail: item.reason })),
      ],
    },
    {
      key: "all",
      label: t("gameWorkspaceUi.project.sourceDrawer.tabs.all", { defaultValue: "全部" }),
      items: discoveryResult?.table_files.map((item) => ({ key: `all-${item.source_path}`, title: item.source_path, detail: `${item.status} / ${item.cold_start_reason}` })) ?? [],
    },
    {
      key: "available",
      label: t("gameWorkspaceUi.project.sourceDrawer.tabs.available", { defaultValue: "可用" }),
      items: availableTableFiles.map((item) => ({ key: `available-${item.source_path}`, title: item.source_path, detail: item.cold_start_reason })),
    },
    {
      key: "excluded",
      label: t("gameWorkspaceUi.project.sourceDrawer.tabs.excluded", { defaultValue: "已排除" }),
      items: excludedFiles.map((item) => ({ key: `excluded-drawer-${item.source_path}`, title: item.source_path, detail: item.reason })),
    },
    {
      key: "unsupported",
      label: t("gameWorkspaceUi.project.sourceDrawer.tabs.unsupported", { defaultValue: "不支持" }),
      items: unsupportedFiles.map((item) => ({ key: `unsupported-drawer-${item.source_path}`, title: item.source_path, detail: item.reason })),
    },
    {
      key: "errors",
      label: t("gameWorkspaceUi.project.sourceDrawer.tabs.errors", { defaultValue: "错误" }),
      items: discoveryErrors.map((item, index) => ({ key: `errors-drawer-${index}`, title: item.source_path || "-", detail: item.reason })),
    },
  ];

  const renderProjectStatusIcon = () => {
    if (projectSetupViewState.level === "ready") {
      return <CheckCircleOutlined />;
    }
    if (projectSetupViewState.level === "running") {
      return <LoadingOutlined />;
    }
    return <ExclamationCircleOutlined />;
  };

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
      <PageHeader
        items={[{ title: t("gameWorkspaceUi.project.title", { defaultValue: "项目配置" }) }]}
        className={styles.projectPageHeader}
        extra={
          <div className={styles.projectHeaderSelector}>
            <FolderOpenOutlined />
            <Text strong>{currentProjectName}</Text>
            <DownOutlined />
          </div>
        }
      />

      <div className={styles.content}>
        <Form form={form} layout="vertical" className={styles.form}>
          <div className={styles.workspaceShell}>
            <div className={styles.statusBanner} data-tone={projectSetupViewState.level}>
              <div className={styles.statusBannerIcon}>{renderProjectStatusIcon()}</div>
              <div className={styles.statusBannerBody}>
                <Text strong className={styles.statusBannerTitle}>{t(projectSetupViewState.titleKey)}</Text>
                <div className={styles.statusBannerMeta}>
                  <span>{t(projectSetupViewState.reasonKey || "gameWorkspaceUi.project.status.defaultReason", { defaultValue: "当前状态" })}</span>
                  <strong>{projectSetupViewState.reasonText || effectiveReadiness.blocking_reason || effectiveReadiness.next_action || "-"}</strong>
                </div>
                <div className={styles.statusBannerMeta}>
                  <span>{t("gameWorkspaceUi.project.labels.suggestion", { defaultValue: "建议操作" })}</span>
                  <strong>{t(projectSetupViewState.suggestionKey)}</strong>
                </div>
              </div>
              <div className={styles.statusBannerActions}>
                <Button onClick={handleDiscoverSources} loading={discoveringSources}>
                  {t("gameWorkspaceUi.project.actions.discover", { defaultValue: "检查数据源" })}
                </Button>
                <Button
                  type="primary"
                  onClick={handleStartColdStartJob}
                  disabled={!canStartColdStartBuild || coldStartProgress.isRunning}
                  loading={creatingColdStartJob}
                >
                  {t("gameWorkspaceUi.project.actions.startColdStart", { defaultValue: "进入冷启动构建" })}
                </Button>
                {coldStartProgress.canCancel ? (
                  <Button onClick={handleCancelColdStartJob} loading={cancellingColdStartJob}>
                    {t("common.cancel")}
                  </Button>
                ) : null}
                {coldStartProgress.canRetry ? (
                  <Button onClick={handleRetryColdStartJob}>{t("common.retry", { defaultValue: "重试" })}</Button>
                ) : null}
              </div>
            </div>

            <div className={styles.workspaceGrid}>
              <div className={styles.workspaceCard}>
                <div className={styles.workspaceCardHeader}>
                  <div className={styles.workspaceCardTitleRow}>
                    <span className={styles.workspaceCardTitleIcon}><FolderOpenOutlined /></span>
                    <Text strong>{t("gameWorkspaceUi.project.access.title", { defaultValue: "项目接入" })}</Text>
                  </div>
                </div>
                <Form.Item label={t("gameWorkspaceUi.project.labels.localProjectRoot", { defaultValue: "本地项目目录" })}>
                  <div className={styles.inlineActionField}>
                    <Input
                      value={projectRootInput}
                      onChange={(event) => setProjectRootInput(event.target.value)}
                      placeholder={t("gameProject.svnWorkingCopyPathPlaceholder", { defaultValue: LOCAL_PROJECT_DIRECTORY_LABEL })}
                    />
                    <Tooltip title={t("gameWorkspaceUi.project.actions.manualInputOnly", { defaultValue: "请手动输入目录路径" })}>
                      <span>
                        <Button disabled>{t("gameWorkspaceUi.project.actions.browse", { defaultValue: "浏览" })}</Button>
                      </span>
                    </Tooltip>
                  </div>
                </Form.Item>
                <Form.Item label={t("gameWorkspaceUi.project.labels.tablesRoot", { defaultValue: "数据表目录" })}>
                  <div className={styles.inlineActionField}>
                    <TextArea rows={2} value={tablesRootsInput} onChange={(event) => setTablesRootsInput(event.target.value)} />
                    <Tooltip title={t("gameWorkspaceUi.project.actions.manualInputOnly", { defaultValue: "请手动输入目录路径" })}>
                      <span>
                        <Button disabled>{t("gameWorkspaceUi.project.actions.browse", { defaultValue: "浏览" })}</Button>
                      </span>
                    </Tooltip>
                  </div>
                </Form.Item>
                {projectRootDirty || tablesConfigDirty ? (
                  <Alert type="warning" showIcon message={t("gameWorkspaceUi.project.access.unsaved", { defaultValue: "当前输入与已保存配置不一致，保存后才会生效。" })} className={styles.workspaceAlert} />
                ) : null}
                <div className={styles.workspaceCardActions}>
                  <Button type="primary" onClick={() => void handleSaveAndContinue()} loading={savingProjectSetupRoot || savingProjectSetupTables} disabled={!projectRootDirty && !tablesConfigDirty}>
                    {t("gameWorkspaceUi.project.actions.saveConfig", { defaultValue: "保存配置" })}
                  </Button>
                  <Button onClick={() => setAdvancedDrawerOpen(true)}>{t("gameWorkspaceUi.project.actions.openAdvanced", { defaultValue: "高级配置" })}</Button>
                </div>
              </div>

              <div className={styles.workspaceCard}>
                <div className={styles.workspaceCardHeader}>
                  <div className={styles.workspaceCardTitleRow}>
                    <span className={styles.workspaceCardTitleIcon}><DatabaseOutlined /></span>
                    <Text strong>{t("gameWorkspaceUi.project.sourceStatus.title", { defaultValue: "数据源状态" })}</Text>
                  </div>
                </div>
                <div className={styles.metricGrid}>
                  <div className={styles.metricItem}><span>{t("gameWorkspaceUi.project.labels.discovered", { defaultValue: "已发现" })}</span><strong>{discoverySummary.discovered_table_count}</strong></div>
                  <div className={styles.metricItem}><span>{t("gameWorkspaceUi.project.labels.available", { defaultValue: "可用" })}</span><strong>{discoverySummary.available_table_count ?? 0}</strong></div>
                  <div className={styles.metricItem}><span>{t("gameWorkspaceUi.project.labels.issues", { defaultValue: "异常" })}</span><strong>{sourceIssueCount}</strong></div>
                  <div className={styles.metricItem}><span>{t("gameWorkspaceUi.project.labels.lastChecked", { defaultValue: "最近检查" })}</span><strong>{latestDiscoveryLabel}</strong></div>
                </div>
                {discoveryNotScanned ? <Alert type="info" showIcon message={t("gameWorkspaceUi.project.sourceStatus.notChecked", { defaultValue: "尚未检查数据源。" })} className={styles.workspaceAlert} /> : null}
                {!discoveryNotScanned && (discoverySummary.available_table_count ?? 0) <= 0 ? <Alert type="warning" showIcon message={t("gameWorkspaceUi.project.sourceStatus.noAvailable", { defaultValue: "当前没有可用于冷启动的可用数据表。" })} className={styles.workspaceAlert} /> : null}
                <div className={styles.workspaceCardActions}>
                  <Button onClick={handleDiscoverSources} loading={discoveringSources}>{t("gameWorkspaceUi.project.actions.discover", { defaultValue: "检查数据源" })}</Button>
                  <Button onClick={() => setSourceDrawerOpen(true)} disabled={sourceIssueCount <= 0 && !discoveryResult}>{t("gameWorkspaceUi.project.actions.viewIssues", { defaultValue: "查看异常" })}</Button>
                </div>
              </div>
            </div>

            <div className={styles.nextStepCard}>
              <div>
                <div className={styles.workspaceCardTitleRow}>
                  <span className={styles.workspaceCardTitleIcon}><SettingOutlined /></span>
                  <Text strong>{t("gameWorkspaceUi.project.nextStep.title", { defaultValue: "下一步操作" })}</Text>
                </div>
                <div className={styles.workspaceCardHint}>{t("gameWorkspaceUi.project.nextStep.hint", { defaultValue: "请按以下建议步骤完成项目准备，以便顺利进入冷启动构建流程。" })}</div>
              </div>
              <div className={styles.nextStepActions}>
                <Button
                  type="primary"
                  onClick={() => void handleSaveAndContinue()}
                  loading={savingProjectSetupRoot || savingProjectSetupTables}
                  disabled={!projectRootDirty && !tablesConfigDirty}
                >
                  {t("gameWorkspaceUi.project.actions.saveAndContinue", { defaultValue: "保存并继续" })}
                </Button>
                <Button onClick={handleDiscoverSources} loading={discoveringSources}>{t("gameWorkspaceUi.project.actions.discover", { defaultValue: "检查数据源" })}</Button>
                <Button onClick={handleStartColdStartJob} disabled={!canStartColdStartBuild || coldStartProgress.isRunning} loading={creatingColdStartJob}>{t("gameWorkspaceUi.project.actions.startColdStart", { defaultValue: "进入冷启动构建" })}</Button>
              </div>
            </div>
          </div>
        </Form>
      </div>

      <Drawer
        title={t("gameWorkspaceUi.project.advanced.title", { defaultValue: "高级配置" })}
        open={advancedDrawerOpen}
        onClose={() => setAdvancedDrawerOpen(false)}
        width={920}
        destroyOnHidden={false}
      >
        <div className={styles.drawerLayout}>
          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionHeader}>
              <Text strong>{t("gameWorkspaceUi.project.advanced.baseInfo", { defaultValue: "项目基础信息" })}</Text>
              <Space>
                <Button onClick={handleReset} disabled={saving}>{t("common.reset")}</Button>
                <Button onClick={handleValidate} disabled={saving}>{t("gameProject.validate")}</Button>
                <Button type="primary" onClick={handleSave} loading={saving}>{t("common.save")}</Button>
              </Space>
            </div>
            <Form.Item label={t("gameProject.projectName")} name="name" rules={[{ required: true, message: t("gameProject.projectNameRequired") }]}>
              <Input placeholder={t("gameProject.projectNamePlaceholder")} />
            </Form.Item>
            <Form.Item label={t("gameProject.projectDescription")} name="description">
              <TextArea rows={3} placeholder={t("gameProject.projectDescriptionPlaceholder")} />
            </Form.Item>
            <Form.Item label={t("gameProject.maintainerModeLabel", { defaultValue: "Maintainer mode" })} name="is_maintainer" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item label={t("gameProject.svnUrl")} name="svn_url">
              <Input placeholder={t("gameProject.svnUrl", { defaultValue: "SVN 地址" })} />
            </Form.Item>
            <div className={styles.drawerTwoColumn}>
              <Form.Item label={t("gameProject.svnUsername")} name="svn_username">
                <Input placeholder={t("gameProject.svnUsernamePlaceholder")} />
              </Form.Item>
              <Form.Item label={t("gameProject.svnPassword")} name="svn_password">
                <Input placeholder={t("gameProject.svnPasswordPlaceholder")} />
              </Form.Item>
            </div>
            <Form.Item label={t("gameProject.svnTrustCert")} name="svn_trust_cert" valuePropName="checked">
              <Switch />
            </Form.Item>
          </div>

          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionHeader}>
              <Text strong>{t("gameWorkspaceUi.project.advanced.tablesRules", { defaultValue: "数据源规则" })}</Text>
              <Button type="primary" onClick={handleSaveTablesSource} loading={savingProjectSetupTables}>{t("common.save")}</Button>
            </div>
            <Form.Item label={t("gameProject.projectSetupTablesRoots", { defaultValue: "Roots" })}>
              <TextArea rows={3} value={tablesRootsInput} onChange={(event) => setTablesRootsInput(event.target.value)} />
            </Form.Item>
            <div className={styles.drawerTwoColumn}>
              <Form.Item label={t("gameProject.projectSetupTablesInclude", { defaultValue: "Include Patterns" })}>
                <TextArea rows={4} value={tablesIncludeInput} onChange={(event) => setTablesIncludeInput(event.target.value)} />
              </Form.Item>
              <Form.Item label={t("gameProject.projectSetupTablesExclude", { defaultValue: "Exclude Patterns" })}>
                <TextArea rows={4} value={tablesExcludeInput} onChange={(event) => setTablesExcludeInput(event.target.value)} />
              </Form.Item>
            </div>
            <div className={styles.drawerTwoColumn}>
              <Form.Item label={t("gameProject.projectSetupHeaderRow", { defaultValue: "Header Row" })}>
                <InputNumber min={1} value={tablesHeaderRow} onChange={(value) => setTablesHeaderRow(Number(value || 1))} />
              </Form.Item>
              <Form.Item label={t("gameProject.projectSetupPrimaryKeys", { defaultValue: "Primary Key Candidates" })}>
                <TextArea rows={3} value={tablesPrimaryKeysInput} onChange={(event) => setTablesPrimaryKeysInput(event.target.value)} />
              </Form.Item>
            </div>
          </div>

          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionHeader}>
              <Text strong>{t("gameWorkspaceUi.project.advanced.pathsAndDiagnostics", { defaultValue: "项目路径与诊断" })}</Text>
              <Space>
                <Button icon={<CopyOutlined />} onClick={handleCopyDiagnostics}>{t("gameWorkspaceUi.project.actions.copyDiagnostics", { defaultValue: "复制诊断" })}</Button>
                <Button onClick={() => setSourceDrawerOpen(true)}>{t("gameWorkspaceUi.project.actions.viewIssues", { defaultValue: "查看异常" })}</Button>
              </Space>
            </div>
            <Descriptions column={1} size="small" className={styles.projectSetupMeta}>
              {advancedStorageItems.map(([label, value]) => (
                <Descriptions.Item key={String(label)} label={label}>{value}</Descriptions.Item>
              ))}
              <Descriptions.Item label={t("gameWorkspaceUi.project.labels.frontendBuild", { defaultValue: "Frontend Build" })}>{import.meta.env.VITE_FRONTEND_BUILD_ID || "dev"}</Descriptions.Item>
              <Descriptions.Item label={t("gameWorkspaceUi.project.labels.frontendBuildTime", { defaultValue: "Frontend Build Time" })}>{import.meta.env.VITE_FRONTEND_BUILD_TIME || "dev"}</Descriptions.Item>
              <Descriptions.Item label={t("gameWorkspaceUi.project.labels.apiBase", { defaultValue: "API Base" })}>{frontendRuntimeInfo?.api_base || "/api"}</Descriptions.Item>
              <Descriptions.Item label={t("gameWorkspaceUi.project.labels.capabilityRole", { defaultValue: "Role" })}>{projectCapabilityStatus?.role || "-"}</Descriptions.Item>
              <Descriptions.Item label={t("gameWorkspaceUi.project.labels.capabilitySource", { defaultValue: "Capability Source" })}>{projectCapabilityStatus?.capability_source || "-"}</Descriptions.Item>
            </Descriptions>
          </div>

          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionHeader}>
              <Text strong>{t("gameWorkspaceUi.project.advanced.automation", { defaultValue: "自动化与兼容设置" })}</Text>
            </div>
            <div className={styles.drawerTwoColumn}>
              <Form.Item name="auto_sync" valuePropName="checked"><Switch disabled /> {t("gameProject.autoSyncFrozen", { defaultValue: "SVN 自动同步（已冻结）" })}</Form.Item>
              <Form.Item name="auto_index" valuePropName="checked"><Switch /> {t("gameProject.autoIndex")}</Form.Item>
            </div>
            <Form.Item name="auto_resolve_dependencies" valuePropName="checked"><Switch /> {t("gameProject.autoResolveDependencies")}</Form.Item>
            <Form.Item label={t("gameProject.indexCommitMessageTemplate")} name="index_commit_message_template">
              <Input disabled placeholder={t("gameProject.indexCommitMessageTemplateFrozen")} />
            </Form.Item>
            <Form.Item label={t("gameProject.sourcePaths", { defaultValue: "Project source paths" })} name="watch_paths">
              <TextArea rows={4} placeholder={t("gameProject.sourcePathsPlaceholder")} />
            </Form.Item>
            <div className={styles.drawerTwoColumn}>
              <Form.Item label={t("gameProject.sourceIncludePatterns", { defaultValue: "Included file patterns" })} name="watch_patterns">
                <TextArea rows={4} placeholder={t("gameProject.sourceIncludePatternsPlaceholder")} />
              </Form.Item>
              <Form.Item label={t("gameProject.sourceExcludePatterns", { defaultValue: "Excluded file patterns" })} name="watch_exclude_patterns">
                <TextArea rows={4} placeholder={t("gameProject.sourceExcludePatternsPlaceholder")} />
              </Form.Item>
            </div>
          </div>

          <div className={styles.drawerSection}>
            <div className={styles.drawerSectionHeader}>
              <Text strong>{t("gameWorkspaceUi.project.advanced.storage", { defaultValue: "存储路径" })}</Text>
              <Button
                onClick={() => {
                  const cur = form.getFieldValue("name") || "";
                  wizardForm.setFieldsValue({ name: cur || t("gameWorkspaceUi.project.actions.newProjectName", { defaultValue: "新项目" }), id: "" });
                  setWizardOpen(true);
                }}
              >
                {t("gameProject.createAsAgent", { defaultValue: "另存为新项目 Agent" })}
              </Button>
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
            {coldStartJob ? (
              <div className={styles.jobSummaryPanel}>
                <div className={styles.drawerSectionHeader}>
                  <Text strong>{t("gameWorkspaceUi.project.advanced.coldStartJob", { defaultValue: "冷启动任务状态" })}</Text>
                  <Space>
                    <Button onClick={() => navigate("/game/map")} disabled={coldStartJob.status !== "succeeded"}>{t("gameWorkspaceUi.project.actions.openMap", { defaultValue: "进入 Map 编辑器" })}</Button>
                    {coldStartProgress.canRetry ? <Button onClick={handleRetryColdStartJob}>{t("common.retry", { defaultValue: "重试" })}</Button> : null}
                  </Space>
                </div>
                <Progress percent={coldStartProgress.percent} status={coldStartProgress.statusTone} />
                <Descriptions column={1} size="small" className={styles.projectSetupMeta}>
                  <Descriptions.Item label={t("gameProject.projectSetupJobId", { defaultValue: "Job ID" })}>{coldStartJob.job_id}</Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupJobStatus", { defaultValue: "Status" })}>{coldStartJob.status}</Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupJobStage", { defaultValue: "Stage" })}>{coldStartJob.stage}</Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupJobMessage", { defaultValue: "Message" })}>{coldStartJob.message}</Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupJobCurrentFile", { defaultValue: "Current File" })}>{coldStartJob.current_file || "-"}</Descriptions.Item>
                  <Descriptions.Item label={t("gameProject.projectSetupJobNextAction", { defaultValue: "Next Action" })}>{coldStartJob.next_action || "-"}</Descriptions.Item>
                </Descriptions>
              </div>
            ) : null}
          </div>
        </div>
      </Drawer>

      <Drawer
        title={t("gameWorkspaceUi.project.sourceDrawer.title", { defaultValue: "数据源详情" })}
        open={sourceDrawerOpen}
        onClose={() => setSourceDrawerOpen(false)}
        width={860}
        destroyOnHidden={false}
      >
        <Tabs
          items={sourceDrawerTabs.map((tab) => ({
            key: tab.key,
            label: tab.label,
            children: tab.items.length > 0 ? (
              <div className={styles.drawerList}>
                {tab.items.map((item) => (
                  <div key={item.key} className={styles.drawerListItem}>
                    <Text strong>{item.title}</Text>
                    <div className={styles.drawerListDetail}>{item.detail}</div>
                  </div>
                ))}
              </div>
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={t("gameWorkspaceUi.project.sourceDrawer.empty", { defaultValue: "当前没有可显示的项目。" })} />
            ),
          }))}
        />
      </Drawer>

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
