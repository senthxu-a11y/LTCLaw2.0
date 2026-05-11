import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Form, Input, Switch, Button, Card } from "@agentscope-ai/design";
import { Alert, Checkbox, Modal, Select, Space, Tag, Tooltip, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import type { FrontendCapabilityToken } from "@/api/types/permissions";
import { canUseGovernanceAction, hasCapabilityContext, isPermissionDeniedError } from "@/utils/permissions";
import { gameApi } from "../../api/modules/game";
import { gameStructuredQueryApi } from "../../api/modules/gameStructuredQuery";
import { gameKnowledgeReleaseApi } from "../../api/modules/gameKnowledgeRelease";
import { agentsApi } from "../../api/modules/agents";
import type {
  FormalKnowledgeMapResponse,
  GameStorageSummary,
  KnowledgeDocRef,
  KnowledgeReleaseHistoryItem,
  KnowledgeManifest,
  KnowledgeMap,
  KnowledgeRagAnswerResponse,
  KnowledgeRagCitation,
  KnowledgeRelationship,
  KnowledgeScriptRef,
  KnowledgeStatus,
  KnowledgeSystem,
  KnowledgeTableRef,
  ProjectConfig,
  ReleaseCandidateListItem,
  StructuredQueryItem,
  StructuredQueryResponse,
  UserGameConfig,
  ValidationIssue,
} from "../../api/types/game";
import { useAgentStore } from "../../stores/agentStore";
import {
  CHANGE_QUERY_WARNING,
  buildCopyableRagText,
  buildRecentRagQuestions,
  formatCitationValue,
  getRagDisplayState,
  getRagNextStepHintKeys,
  groupRagCitations,
  isStructuredOrWorkbenchWarning,
  STRUCTURED_FACT_WARNING,
  type RecentRagQuestionItem,
} from "./ragUiHelpers";
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
const NO_CURRENT_RELEASE_DETAIL = "No current knowledge release is set";
const LOCAL_PROJECT_DIRECTORY_ERROR = "Local project directory not configured";
const NO_FORMAL_MAP_MODE = "no_formal_map";
const MAX_RECENT_RAG_QUESTIONS = 5;
const RAG_EXAMPLE_QUESTION_KEYS = [
  "gameProject.ragExampleQuestionCombatDamage",
  "gameProject.ragExampleQuestionSkillProgression",
  "gameProject.ragExampleQuestionEquipmentEnhancement",
];
const RAG_NEXT_STEP_HINT_DEFAULTS: Record<string, string> = {
  "gameProject.ragNextStepHintNarrowCurrentRelease": "Try a narrower question about the current release.",
  "gameProject.ragNextStepHintUseStructuredQuery": "Use structured query for exact row-level or numeric facts.",
  "gameProject.ragNextStepHintUseWorkbench": "Use workbench flow for change or edit intent.",
  "gameProject.ragNextStepHintCheckReleaseEvidence": "Check whether the current release contains the expected evidence.",
};
const FORMAL_MAP_STATUS_OPTIONS: Array<{ label: KnowledgeStatus; value: KnowledgeStatus }> = [
  { label: "active", value: "active" },
  { label: "deprecated", value: "deprecated" },
  { label: "ignored", value: "ignored" },
];

interface CitationWorkbenchTarget {
  table: string | null;
  row: string | null;
  field: string | null;
}

function isLikelyWorkbenchSourcePath(value?: string | null): boolean {
  if (!value) {
    return false;
  }

  const normalized = value.replace(/\\/g, "/").trim().toLowerCase();
  return /\.(xlsx|xls|csv|tsv)$/.test(normalized);
}

function normalizeWorkbenchTableName(value?: string | null): string | null {
  if (!value) {
    return null;
  }

  const normalized = value.replace(/\\/g, "/").trim();
  if (!normalized) {
    return null;
  }

  const tail = normalized.split("/").filter(Boolean).pop() || normalized;
  const withoutQuery = tail.split("?")[0]?.trim() || tail;
  const withoutExtension = withoutQuery.replace(/\.[^.]+$/, "").trim();
  return withoutExtension || null;
}

function buildCitationWorkbenchTarget(citation: KnowledgeRagCitation): CitationWorkbenchTarget {
  const sourcePathTable = normalizeWorkbenchTableName(citation.source_path);
  const titleMatch = (citation.title || "").trim().match(/^([A-Za-z0-9_-]+)\.([A-Za-z0-9_:-]+)$/);
  const titleTable = titleMatch?.[1] || null;
  const titleField = titleMatch?.[2] || null;
  const sourceType = (citation.source_type || "").trim().toLowerCase();
  const canUseSourcePath = isLikelyWorkbenchSourcePath(citation.source_path);
  const canUseTitleField = sourceType.includes("table") || sourceType.includes("field");

  return {
    table: (canUseSourcePath ? sourcePathTable : null) || (canUseTitleField ? titleTable : null),
    row: citation.row === null || citation.row === undefined ? null : String(citation.row),
    field: canUseTitleField ? titleField : null,
  };
}

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

function createDefaultReleaseId(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `v${now.getFullYear()}.${pad(now.getMonth() + 1)}.${pad(now.getDate())}.${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
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
  const [releaseLoading, setReleaseLoading] = useState(true);
  const [releaseError, setReleaseError] = useState<string | null>(null);
  const [releases, setReleases] = useState<KnowledgeReleaseHistoryItem[]>([]);
  const [currentRelease, setCurrentRelease] = useState<KnowledgeReleaseHistoryItem | null>(null);
  const [previousRelease, setPreviousRelease] = useState<KnowledgeReleaseHistoryItem | null>(null);
  const [settingCurrentId, setSettingCurrentId] = useState<string | null>(null);
  const [buildModalOpen, setBuildModalOpen] = useState(false);
  const [buildingRelease, setBuildingRelease] = useState(false);
  const [buildCandidatesLoading, setBuildCandidatesLoading] = useState(false);
  const [buildCandidatesError, setBuildCandidatesError] = useState<string | null>(null);
  const [buildCandidates, setBuildCandidates] = useState<ReleaseCandidateListItem[]>([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
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
  const [buildForm] = Form.useForm<BuildReleaseFormData>();
  const [wizardForm] = Form.useForm<{ id?: string; name: string }>();
  const [ragQuery, setRagQuery] = useState("");
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState<string | null>(null);
  const [ragAnswer, setRagAnswer] = useState<KnowledgeRagAnswerResponse | null>(null);
  const [structuredQueryPanelOpen, setStructuredQueryPanelOpen] = useState(false);
  const [structuredQueryDraft, setStructuredQueryDraft] = useState("");
  const [structuredQueryLoading, setStructuredQueryLoading] = useState(false);
  const [structuredQueryResponse, setStructuredQueryResponse] = useState<StructuredQueryResponse | null>(null);
  const [recentRagQuestions, setRecentRagQuestions] = useState<RecentRagQuestionItem[]>([]);
  const [highlightedCitationId, setHighlightedCitationId] = useState<string | null>(null);
  const citationsSectionRef = useRef<HTMLDivElement | null>(null);
  const citationRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const citationHighlightTimeoutRef = useRef<number | null>(null);

  const selectedAgentSummary = agents.find((agent) => agent.id === selectedAgent);
  const capabilities: FrontendCapabilityToken[] | undefined = selectedAgentSummary?.capabilities;
  const hasExplicitCapabilityContext = hasCapabilityContext(capabilities);
  const canBuildRelease = canUseGovernanceAction(capabilities, "knowledge.build");
  const canPublishRelease = canUseGovernanceAction(capabilities, "knowledge.publish");
  const canReadKnowledge = canUseGovernanceAction(capabilities, "knowledge.read");
  const canReadWorkbench = canUseGovernanceAction(capabilities, "workbench.read");
  const canReadReleaseCandidates = canUseGovernanceAction(capabilities, "knowledge.candidate.read");
  const canReadMap = canUseGovernanceAction(capabilities, "knowledge.map.read");
  const canEditMap = canUseGovernanceAction(capabilities, "knowledge.map.edit");

  const permissionDeniedMessage = t("gameProject.permissionDenied", {
    defaultValue: "You do not have permission to perform this action.",
  });

  const buildDisabledReason =
    hasExplicitCapabilityContext && !canBuildRelease
      ? t("gameProject.releaseBuildPermissionRequired", {
          defaultValue: "Requires knowledge.build permission.",
        })
      : null;
  const publishDisabledReason =
    hasExplicitCapabilityContext && !canPublishRelease
      ? t("gameProject.releasePublishPermissionRequired", {
          defaultValue: "Requires knowledge.publish permission.",
        })
      : null;
  const knowledgeReadReason =
    hasExplicitCapabilityContext && !canReadKnowledge
      ? t("gameProject.knowledgeReadPermissionRequired", {
          defaultValue: "Requires knowledge.read permission.",
        })
      : null;
  const workbenchReadReason =
    hasExplicitCapabilityContext && !canReadWorkbench
      ? t("gameProject.workbenchReadPermissionRequired", {
          defaultValue: "Requires workbench.read permission.",
        })
      : null;
  const releaseCandidateReadReason =
    hasExplicitCapabilityContext && !canReadReleaseCandidates
      ? t("gameProject.releaseCandidatePermissionRequired", {
          defaultValue: "Requires knowledge.candidate.read permission.",
        })
      : null;
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

  const formatGovernanceError = useCallback((error: unknown, fallbackMessage: string) => {
    if (isPermissionDeniedError(error)) {
      return permissionDeniedMessage;
    }
    return error instanceof Error ? error.message : fallbackMessage;
  }, [permissionDeniedMessage]);

  const getIndexCount = (manifest: Pick<KnowledgeManifest, "indexes"> | KnowledgeReleaseHistoryItem | null, indexName: string) =>
    manifest?.indexes?.[indexName]?.count ?? 0;

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

  const formatRecentQuestionTime = (timestamp: number) => {
    const parsed = new Date(timestamp);
    if (Number.isNaN(parsed.getTime())) {
      return "-";
    }
    return parsed.toLocaleTimeString();
  };

  const recordRecentRagQuestion = (query: string, mode: KnowledgeRagAnswerResponse["mode"]) => {
    setRecentRagQuestions((current) => buildRecentRagQuestions(current, query, mode, Date.now(), MAX_RECENT_RAG_QUESTIONS));
  };

  const formatRagMode = useCallback(
    (mode: KnowledgeRagAnswerResponse["mode"] | null | undefined) => {
      if (mode === "answer") {
        return t("gameProject.ragStateValueAnswer", { defaultValue: "answer" });
      }
      if (mode === "insufficient_context") {
        return t("gameProject.ragStateValueInsufficientContext", { defaultValue: "insufficient context" });
      }
      if (mode === "no_current_release") {
        return t("gameProject.ragStateValueNoCurrentRelease", { defaultValue: "no current release" });
      }
      return mode || "-";
    },
    [t],
  );

  const getLocalizedRagWarning = useCallback(
    (warning: string) => {
      if (warning === STRUCTURED_FACT_WARNING) {
        return t("gameProject.ragStructuredGuardrail", {
          defaultValue: "Exact numeric or row-level facts should go through structured query, not this RAG entry.",
        });
      }
      if (warning === CHANGE_QUERY_WARNING) {
        return t("gameProject.ragWorkbenchGuardrail", {
          defaultValue: "Change or edit intent should go through the workbench flow, not this RAG entry.",
        });
      }
      return warning;
    },
    [t],
  );

  const ragExampleQuestions = useMemo(
    () =>
      RAG_EXAMPLE_QUESTION_KEYS.map((key) =>
        t(key, {
          defaultValue:
            key === "gameProject.ragExampleQuestionCombatDamage"
              ? "How does combat damage work in the current release?"
              : key === "gameProject.ragExampleQuestionSkillProgression"
                ? "What systems are related to skill progression?"
                : "Where is equipment enhancement described?",
        }),
      ),
    [t],
  );

  const clearCitationHighlight = () => {
    if (citationHighlightTimeoutRef.current !== null) {
      window.clearTimeout(citationHighlightTimeoutRef.current);
      citationHighlightTimeoutRef.current = null;
    }
    setHighlightedCitationId(null);
  };

  const focusCitation = (citationId?: string | null) => {
    if (!citationId) {
      citationsSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    const target = citationRefs.current[citationId];
    if (!target) {
      citationsSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    clearCitationHighlight();
    setHighlightedCitationId(citationId);
    target.scrollIntoView({ behavior: "smooth", block: "nearest" });
    target.focus();
    citationHighlightTimeoutRef.current = window.setTimeout(() => {
      setHighlightedCitationId((current) => (current === citationId ? null : current));
      citationHighlightTimeoutRef.current = null;
    }, 2200);
  };

  const handleCopyRagAnswer = async () => {
    if (!ragAnswer) {
      return;
    }
    if (!navigator.clipboard?.writeText) {
      message.warning(
        t("gameProject.ragCopyUnavailable", {
          defaultValue: "Clipboard is unavailable in this environment.",
        }),
      );
      return;
    }
    try {
      await navigator.clipboard.writeText(buildCopyableRagText(ragAnswer));
      message.success(
        t("gameProject.ragCopySuccess", {
          defaultValue: "Copied the current knowledge answer.",
        }),
      );
    } catch (err) {
      message.warning(
        err instanceof Error
          ? err.message
          : t("gameProject.ragCopyFailed", {
              defaultValue: "Failed to copy the current knowledge answer.",
            }),
      );
    }
  };

  const handleGoToWorkbench = useCallback(() => {
    navigate("/numeric-workbench");
  }, [navigate]);

  const handleOpenCitationInWorkbench = useCallback(
    (citation: KnowledgeRagCitation) => {
      const target = buildCitationWorkbenchTarget(citation);
      if (!target.table) {
        return;
      }

      const params = new URLSearchParams({ table: target.table });
      if (target.row) {
        params.set("row", target.row);
      }
      if (target.field) {
        params.set("field", target.field);
      }
      navigate(`/numeric-workbench?${params.toString()}`);
    },
    [navigate],
  );

  const handleOpenStructuredQueryPanel = useCallback(() => {
    const nextDraft = ragQuery.trim();
    setStructuredQueryPanelOpen(true);
    setStructuredQueryDraft((currentDraft) => (currentDraft.trim() || !nextDraft ? currentDraft : nextDraft));
  }, [ragQuery]);

  const handleCloseStructuredQueryPanel = useCallback(() => {
    setStructuredQueryPanelOpen(false);
  }, []);

  const handleSubmitStructuredQuery = useCallback(async () => {
    if (!selectedAgent) {
      return;
    }

    const query = structuredQueryDraft.trim();
    if (!query) {
      return;
    }

    setStructuredQueryLoading(true);
    const response = await gameStructuredQueryApi.submit(selectedAgent, query);
    setStructuredQueryResponse(response);
    setStructuredQueryLoading(false);
  }, [selectedAgent, structuredQueryDraft]);

  const renderStructuredQueryAffordance = useCallback(
    (source: "guardrail" | "warning") => {
      const button = (
        <Button
          size="small"
          onClick={handleOpenStructuredQueryPanel}
          disabled={hasExplicitCapabilityContext && !canReadKnowledge}
        >
          {t(
            source === "guardrail"
              ? "gameProject.ragOpenStructuredQueryGuardrailButton"
              : "gameProject.ragOpenStructuredQueryWarningButton",
            { defaultValue: "Open structured query" },
          )}
        </Button>
      );

      return (
        <span className={styles.ragReadonlyPathActions}>
          <span className={styles.ragReadonlyPathLabel}>
            {t("gameProject.structuredQueryPanelPathLabel", { defaultValue: "Structured query panel" })}
          </span>
          <Tooltip title={knowledgeReadReason || undefined}>
            <span>{button}</span>
          </Tooltip>
        </span>
      );
    },
    [canReadKnowledge, handleOpenStructuredQueryPanel, hasExplicitCapabilityContext, knowledgeReadReason, t],
  );

  const renderWorkbenchAffordance = useCallback(
    (source: "guardrail" | "warning") => {
      const button = (
        <Button
          size="small"
          onClick={handleGoToWorkbench}
          disabled={hasExplicitCapabilityContext && !canReadWorkbench}
        >
          {t(
            source === "guardrail"
              ? "gameProject.ragGoToWorkbenchGuardrailButton"
              : "gameProject.ragGoToWorkbenchWarningButton",
            { defaultValue: "Go to workbench" },
          )}
        </Button>
      );

      return (
        <span className={styles.ragReadonlyPathActions}>
          <span className={styles.ragReadonlyPathLabel}>
            {t("gameProject.ragWorkbenchPathLabel", { defaultValue: "Workbench flow" })}
          </span>
          <Tooltip title={workbenchReadReason || undefined}>
            <span>{button}</span>
          </Tooltip>
        </span>
      );
    },
    [canReadWorkbench, handleGoToWorkbench, hasExplicitCapabilityContext, t, workbenchReadReason],
  );

  const fetchKnowledgeReleases = useCallback(async (agentId: string) => {
    setReleaseLoading(true);
    setReleaseError(null);
    try {
      const status = await gameKnowledgeReleaseApi.getReleaseStatus(agentId);
      setReleases(status.history);
      setCurrentRelease(status.current);
      setPreviousRelease(status.previous);
    } catch (err) {
      setReleaseError(err instanceof Error ? err.message : t("gameProject.releaseLoadFailed", { defaultValue: "Failed to load knowledge release status" }));
      setReleases([]);
      setCurrentRelease(null);
      setPreviousRelease(null);
    } finally {
      setReleaseLoading(false);
    }
  }, [t]);

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

  const fetchBuildCandidates = useCallback(async (agentId: string) => {
    if (hasExplicitCapabilityContext && !canReadReleaseCandidates) {
      setBuildCandidates([]);
      setBuildCandidatesError(null);
      return;
    }
    setBuildCandidatesLoading(true);
    setBuildCandidatesError(null);
    try {
      const items = await gameKnowledgeReleaseApi.listBuildCandidates(agentId);
      setBuildCandidates(items);
    } catch (err) {
      setBuildCandidates([]);
      setBuildCandidatesError(
        formatGovernanceError(
          err,
          t("gameProject.releaseCandidatesLoadFailed", { defaultValue: "Failed to load release candidates" }),
        ),
      );
    } finally {
      setBuildCandidatesLoading(false);
    }
  }, [canReadReleaseCandidates, formatGovernanceError, hasExplicitCapabilityContext, t]);

  const fetchConfig = useCallback(async () => {
    if (!selectedAgent) {
      setLoading(false);
      setReleaseLoading(false);
      setReleaseError(null);
      setReleases([]);
      setCurrentRelease(null);
      setPreviousRelease(null);
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
    void fetchKnowledgeReleases(selectedAgent);
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
  }, [canReadMap, fetchKnowledgeReleases, fetchMapReviewData, form, hasExplicitCapabilityContext, selectedAgent, t]);

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

  const confirmReleaseSwitch = useCallback(
    (releaseId: string) =>
      window.confirm(
        t("gameProject.releaseSetCurrentConfirm", {
          defaultValue:
            `Switch current knowledge release to ${releaseId}? This rollback only updates the current release pointer. It does not rebuild, publish, or modify formal knowledge assets or test plans.`,
        }),
      ),
    [t],
  );

  const handleSetCurrentRelease = async (releaseId: string) => {
    if (!selectedAgent) {
      return;
    }
    if (!confirmReleaseSwitch(releaseId)) {
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
        formatGovernanceError(
          err,
          t("gameProject.releaseSetCurrentFailed", { defaultValue: "Failed to set current knowledge release" }),
        ),
      );
    } finally {
      setSettingCurrentId(null);
    }
  };

  const handleRollbackToPreviousRelease = () => {
    if (!previousRelease) {
      return;
    }
    void handleSetCurrentRelease(previousRelease.release_id);
  };

  const openBuildReleaseModal = () => {
    if (!canBuildRelease) {
      return;
    }
    buildForm.setFieldsValue({
      release_id: createDefaultReleaseId(),
      release_notes: currentRelease ? `Build from current indexes based on ${currentRelease.release_id}` : "",
    });
    setSelectedCandidateIds([]);
    setBuildCandidates([]);
    setBuildCandidatesError(null);
    setBuildModalOpen(true);
    if (selectedAgent && canReadReleaseCandidates) {
      void fetchBuildCandidates(selectedAgent);
    } else {
      setBuildCandidates([]);
      if (releaseCandidateReadReason) {
        setBuildCandidatesError(releaseCandidateReadReason);
      }
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
      const errorMessage = formatGovernanceError(
        err,
        t("gameProject.releaseBuildFailed", { defaultValue: "Failed to build knowledge release" }),
      );
      setBuildCandidatesError(errorMessage);
      message.warning(errorMessage);
    } finally {
      setBuildingRelease(false);
    }
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

  const handleAskRagQuestion = async () => {
    if (!selectedAgent) {
      return;
    }
    if (hasExplicitCapabilityContext && !canReadKnowledge) {
      setRagAnswer(null);
      setRagError(knowledgeReadReason || permissionDeniedMessage);
      return;
    }
    const query = ragQuery.trim();
    if (!query) {
      setRagAnswer(null);
      setRagError(
        t("gameProject.ragQueryRequired", {
          defaultValue: "Please enter a knowledge question.",
        }),
      );
      return;
    }

    try {
      setRagLoading(true);
      setRagError(null);
      clearCitationHighlight();
      const response = await gameKnowledgeReleaseApi.answerRagQuestion(selectedAgent, {
        query,
      });
      setRagAnswer(response);
      recordRecentRagQuestion(query, response.mode);
    } catch (err) {
      setRagAnswer(null);
      setRagError(
        err instanceof Error
          ? err.message
          : t("gameProject.ragAnswerFailed", { defaultValue: "Failed to get knowledge answer" }),
      );
    } finally {
      setRagLoading(false);
    }
  };

  const ragDisplayState = useMemo(() => (ragAnswer ? getRagDisplayState(ragAnswer) : null), [ragAnswer]);
  const ragNextStepHints = useMemo(
    () =>
      ragAnswer
        ? getRagNextStepHintKeys(ragAnswer).map((key) =>
            t(key, {
              defaultValue: RAG_NEXT_STEP_HINT_DEFAULTS[key] || key,
            }),
          )
        : [],
    [ragAnswer, t],
  );
  const groupedRagCitations = useMemo(() => (ragAnswer ? groupRagCitations(ragAnswer.citations) : []), [ragAnswer]);
  const canSubmitStructuredQuery = !!selectedAgent && structuredQueryDraft.trim().length > 0 && (!hasExplicitCapabilityContext || canReadKnowledge);

  const getStructuredQueryMessage = (response: StructuredQueryResponse) => {
    if (response.status === "error") {
      return t("gameProject.structuredQueryFailed", { defaultValue: "Structured query failed." });
    }

    if (response.result_mode === "exact_table") {
      return response.items.length > 0
        ? t("gameProject.structuredQueryExactTableSuccess", { defaultValue: "Showing exact table matches from the current structured index." })
        : t("gameProject.structuredQueryExactTableEmpty", { defaultValue: "No exact table matches were returned for this query." });
    }

    if (response.result_mode === "exact_field") {
      return response.items.length > 0
        ? t("gameProject.structuredQueryExactFieldSuccess", { defaultValue: "Showing exact field matches from the current structured index." })
        : t("gameProject.structuredQueryExactFieldEmpty", { defaultValue: "No exact field matches were returned for this query." });
    }

    if (response.result_mode === "semantic_stub") {
      return t("gameProject.structuredQuerySemanticEmpty", { defaultValue: "No exact structured result was found for this query." });
    }

    if (response.result_mode === "not_configured") {
      return t("gameProject.structuredQueryNotConfigured", {
        defaultValue: "Structured query is unavailable because the current project index is not configured.",
      });
    }

    return t("gameProject.structuredQueryUnsupported", { defaultValue: "Structured query returned an unsupported response." });
  };

  const renderStructuredQueryItem = (item: StructuredQueryItem) => {
    if (item.kind === "table") {
      return (
        <div key={`table-${item.table_name}`} className={styles.structuredQueryItemCard}>
          <div className={styles.structuredQueryItemHeader}>
            <Text strong>{item.table_name}</Text>
            <Tag color="blue">{t("gameProject.structuredQueryTableTag", { defaultValue: "table" })}</Tag>
          </div>
          <div className={styles.structuredQueryItemMeta}>
            <span>{t("gameProject.structuredQuerySourcePathLabel", { defaultValue: "source_path" })}: {item.source_path}</span>
            <span>{t("gameProject.structuredQuerySystemLabel", { defaultValue: "system" })}: {item.system || "-"}</span>
            <span>{t("gameProject.structuredQueryRowCountLabel", { defaultValue: "row_count" })}: {item.row_count}</span>
            <span>{t("gameProject.structuredQueryPrimaryKeyLabel", { defaultValue: "primary_key" })}: {item.primary_key}</span>
          </div>
          <div className={styles.structuredQueryItemDescription}>
            {item.summary || t("gameProject.structuredQueryNoTableSummary", { defaultValue: "No table summary returned." })}
          </div>
        </div>
      );
    }

    return (
      <div key={`field-${item.table_name}-${item.field_name}`} className={styles.structuredQueryItemCard}>
        <div className={styles.structuredQueryItemHeader}>
          <Text strong>
            {item.table_name}.{item.field_name}
          </Text>
          <Tag color="cyan">{t("gameProject.structuredQueryFieldTag", { defaultValue: "field" })}</Tag>
        </div>
        <div className={styles.structuredQueryItemMeta}>
          <span>{t("gameProject.structuredQueryTypeLabel", { defaultValue: "type" })}: {item.field_type}</span>
          <span>{t("gameProject.structuredQueryConfidenceLabel", { defaultValue: "confidence" })}: {item.confidence}</span>
          <span>{t("gameProject.structuredQueryReferencesLabel", { defaultValue: "references" })}: {item.references.length > 0 ? item.references.join(", ") : "-"}</span>
          <span>{t("gameProject.structuredQueryTagsLabel", { defaultValue: "tags" })}: {item.tags.length > 0 ? item.tags.join(", ") : "-"}</span>
        </div>
        <div className={styles.structuredQueryItemDescription}>
          {item.description || t("gameProject.structuredQueryNoFieldDescription", { defaultValue: "No field description returned." })}
        </div>
      </div>
    );
  };

  const renderStructuredQueryResultStatus = (response: StructuredQueryResponse) => {
    const alertType =
      response.status === "success"
        ? "success"
        : response.status === "unavailable"
          ? "info"
          : response.status === "empty"
            ? "warning"
            : "error";

    return (
      <Alert
        type={alertType}
        showIcon
        message={getStructuredQueryMessage(response)}
        description={response.error || undefined}
      />
    );
  };

  const renderRagCitationList = (citations: KnowledgeRagCitation[]) => {
    if (citations.length === 0) {
      return <div className={styles.ragEmpty}>{t("gameProject.ragNoCitations", { defaultValue: "No citations returned." })}</div>;
    }

    return groupedRagCitations.map((group) => (
      <div key={group.key} className={styles.ragCitationGroup}>
        <div className={styles.ragCitationGroupHeader}>
          <div className={styles.ragCitationGroupTitle}>
            <Text strong>
              {group.key === "other"
                ? t("gameProject.ragCitationGroupOtherLabel", { defaultValue: "other" })
                : group.label}
            </Text>
            <Tag>{group.citations.length}</Tag>
          </div>
          <Text type="secondary">
            {t("gameProject.ragCitationGroupHint", {
              defaultValue: "Grouped from returned citations only.",
            })}
          </Text>
        </div>
        <div className={styles.ragCitationList}>
          {group.citations.map((citation) => (
            (() => {
              const workbenchTarget = buildCitationWorkbenchTarget(citation);
              const canOpenCitationInWorkbench = !!workbenchTarget.table;
              const workbenchDisabledReason = !canOpenCitationInWorkbench
                ? t("gameProject.ragCitationWorkbenchUnavailable", {
                    defaultValue: "This citation does not include enough table context to open the workbench.",
                  })
                : hasExplicitCapabilityContext && !canReadWorkbench
                  ? workbenchReadReason || permissionDeniedMessage
                  : null;

              return (
                <div
                  key={citation.citation_id}
                  ref={(element) => {
                    citationRefs.current[citation.citation_id] = element;
                  }}
                  className={`${styles.ragCitationRow} ${highlightedCitationId === citation.citation_id ? styles.ragCitationRowHighlighted : ""}`}
                  tabIndex={-1}
                >
                  <div className={styles.ragCitationTitleRow}>
                    <div className={styles.ragCitationTitleContent}>
                      <Text strong>{citation.title || citation.citation_id}</Text>
                      {citation.source_type ? <Tag color="blue">{citation.source_type}</Tag> : null}
                    </div>
                    <Space size={8}>
                      <Tooltip title={workbenchDisabledReason || undefined}>
                        <span>
                          <Button
                            size="small"
                            onClick={() => handleOpenCitationInWorkbench(citation)}
                            disabled={!!workbenchDisabledReason}
                          >
                            {t("gameProject.ragOpenCitationWorkbenchButton", { defaultValue: "Open in workbench" })}
                          </Button>
                        </span>
                      </Tooltip>
                      <Button
                        size="small"
                        onClick={() => focusCitation(citation.citation_id)}
                      >
                        {t("gameProject.ragFocusCitationButton", { defaultValue: "Focus citation" })}
                      </Button>
                    </Space>
                  </div>
                  <div className={styles.ragCitationMeta}>
                    <span>
                      {t("gameProject.ragCitationSourcePathLabel", { defaultValue: "source path" })}: {formatCitationValue(citation.source_path)}
                    </span>
                    <span>
                      {t("gameProject.ragCitationArtifactPathLabel", { defaultValue: "artifact path" })}: {formatCitationValue(citation.artifact_path)}
                    </span>
                    <span>{t("gameProject.ragCitationRowLabel", { defaultValue: "row" })}: {formatCitationValue(citation.row)}</span>
                    <span>
                      {t("gameProject.ragCitationWorkbenchTargetLabel", { defaultValue: "workbench target" })}: {formatCitationValue(workbenchTarget.table)}
                    </span>
                    <span>
                      {t("gameProject.ragCitationReleaseIdLabel", { defaultValue: "release id" })}: {formatCitationValue(citation.release_id)}
                    </span>
                  </div>
                </div>
              );
            })()
          ))}
        </div>
      </div>
    ));
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

  useEffect(() => {
    setStructuredQueryPanelOpen(false);
    setStructuredQueryDraft("");
    setStructuredQueryLoading(false);
    setStructuredQueryResponse(null);
  }, [selectedAgent]);

  useEffect(() => () => {
    if (citationHighlightTimeoutRef.current !== null) {
      window.clearTimeout(citationHighlightTimeoutRef.current);
    }
  }, []);

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
              <Tooltip title={buildDisabledReason || undefined}>
                <span>
                  <Button size="small" type="primary" onClick={openBuildReleaseModal} disabled={!selectedAgent || !canBuildRelease}>
                    {t("gameProject.releaseBuildButton", { defaultValue: "Build release" })}
                  </Button>
                </span>
              </Tooltip>
              <Text type="secondary">
                {t("gameProject.releaseBuildHint", {
                  defaultValue: "Build uses the safe server-side endpoint and does not auto-set current.",
                })}
              </Text>
              {buildDisabledReason ? <Text type="secondary">{buildDisabledReason}</Text> : null}
            </div>

            <div className={styles.releaseActions}>
              <Tooltip
                title={
                  previousRelease
                    ? publishDisabledReason || undefined
                    : t("gameProject.releaseRollbackUnavailable", {
                        defaultValue: "No previous knowledge release is available for rollback.",
                      })
                }
              >
                <span>
                  <Button
                    size="small"
                    onClick={handleRollbackToPreviousRelease}
                    loading={previousRelease ? settingCurrentId === previousRelease.release_id : false}
                    disabled={!selectedAgent || !canPublishRelease || !previousRelease}
                  >
                    {t("gameProject.releaseRollbackButton", { defaultValue: "Rollback to previous" })}
                  </Button>
                </span>
              </Tooltip>
              <Text type="secondary">
                {t("gameProject.releaseRollbackHint", {
                  defaultValue: "Rollback only switches the current release pointer. It does not rebuild, publish, or modify formal knowledge state.",
                })}
              </Text>
              {!previousRelease && !releaseLoading ? (
                <Text type="secondary">
                  {t("gameProject.releaseNoPrevious", { defaultValue: "No previous knowledge release" })}
                </Text>
              ) : null}
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
                  {t("gameProject.releasePreviousLabel", { defaultValue: "previous release id" })}
                </div>
                <div className={styles.releaseSummaryValue}>
                  {releaseLoading ? t("common.loading") : previousRelease?.release_id || "No previous knowledge release"}
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
                        <Tooltip title={!isCurrent ? publishDisabledReason || undefined : undefined}>
                          <span>
                            <Button
                              size="small"
                              onClick={() => handleSetCurrentRelease(release.release_id)}
                              loading={settingCurrentId === release.release_id}
                              disabled={isCurrent || !canPublishRelease}
                            >
                              {isCurrent
                                ? t("gameProject.releaseCurrentButton", { defaultValue: "Current" })
                                : t("gameProject.releaseSetCurrentButton", { defaultValue: "Set current" })}
                            </Button>
                          </span>
                        </Tooltip>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className={styles.ragSection}>
              <div className={styles.ragHeader}>
                <div>
                  <Text strong>{t("gameProject.ragTitle", { defaultValue: "Knowledge Q&A" })}</Text>
                  <div className={styles.ragHint}>
                    {t("gameProject.ragHint", {
                      defaultValue:
                        "Ask a current-release knowledge question. This entry point does not expose provider or model selection and uses the existing grounded RAG answer path.",
                    })}
                  </div>
                </div>
                <Space size={8}>
                  <Button
                    size="small"
                    onClick={() => {
                      setRagQuery("");
                      setRagAnswer(null);
                      setRagError(null);
                    }}
                    disabled={ragLoading}
                  >
                    {t("common.reset")}
                  </Button>
                  <Tooltip title={knowledgeReadReason || undefined}>
                    <span>
                      <Button
                        size="small"
                        type="primary"
                        onClick={handleAskRagQuestion}
                        loading={ragLoading}
                        disabled={!selectedAgent || (hasExplicitCapabilityContext && !canReadKnowledge)}
                      >
                        {t("gameProject.ragAskButton", { defaultValue: "Ask" })}
                      </Button>
                    </span>
                  </Tooltip>
                </Space>
              </div>

              <TextArea
                rows={3}
                value={ragQuery}
                onChange={(event) => setRagQuery(event.target.value)}
                placeholder={t("gameProject.ragQueryPlaceholder", {
                  defaultValue: "Example: How does combat damage work in the current release?",
                })}
              />

              <div className={styles.ragExamplesSection}>
                <div className={styles.ragSectionLabel}>{t("gameProject.ragExamplesTitle", { defaultValue: "Example questions" })}</div>
                <div className={styles.ragExamplesList}>
                  {ragExampleQuestions.map((exampleQuestion) => (
                    <Button
                      key={exampleQuestion}
                      size="small"
                      onClick={() => setRagQuery(exampleQuestion)}
                    >
                      {exampleQuestion}
                    </Button>
                  ))}
                </div>
              </div>

              <div className={styles.ragHistorySection}>
                <div className={styles.ragSectionLabel}>{t("gameProject.ragRecentQuestionsTitle", { defaultValue: "Recent questions" })}</div>
                {recentRagQuestions.length === 0 ? (
                  <div className={styles.ragHistoryEmpty}>
                    {t("gameProject.ragRecentQuestionsEmpty", {
                      defaultValue: "Your last submitted questions will appear here for quick reuse.",
                    })}
                  </div>
                ) : (
                  <div className={styles.ragHistoryList}>
                    {recentRagQuestions.map((item) => (
                      <button
                        key={`${item.query}-${item.askedAt}`}
                        type="button"
                        className={styles.ragHistoryItem}
                        onClick={() => setRagQuery(item.query)}
                      >
                        <span className={styles.ragHistoryQuestion}>{item.query}</span>
                        <span className={styles.ragHistoryMeta}>
                          <span>{formatRagMode(item.mode)}</span>
                          <span>{formatRecentQuestionTime(item.askedAt)}</span>
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className={styles.ragGuardrailHints}>
                <Alert
                  type="info"
                  showIcon
                  message={t("gameProject.ragStructuredGuardrail", {
                    defaultValue: "Exact numeric or row-level facts should go through structured query, not this RAG entry.",
                  })}
                  description={renderStructuredQueryAffordance("guardrail")}
                />
                <Alert
                  type="info"
                  showIcon
                  message={t("gameProject.ragWorkbenchGuardrail", {
                    defaultValue: "Change or edit intent should go through the workbench flow, not this RAG entry.",
                  })}
                  description={renderWorkbenchAffordance("guardrail")}
                />
              </div>

              {structuredQueryPanelOpen ? (
                <div className={styles.structuredQueryPanel}>
                  <div className={styles.structuredQueryPanelHeader}>
                    <div className={styles.structuredQueryPanelTitleBlock}>
                      <Text strong>{t("gameProject.structuredQueryPanelTitle", { defaultValue: "Structured query" })}</Text>
                      <Text type="secondary">
                        {t("gameProject.structuredQueryPanelHint", {
                          defaultValue: "Read-only exact table and field lookup. Submit runs only when you click the button below.",
                        })}
                      </Text>
                    </div>
                    <Button size="small" onClick={handleCloseStructuredQueryPanel}>
                      {t("gameProject.structuredQueryCloseButton", { defaultValue: "Close" })}
                    </Button>
                  </div>
                  <TextArea
                    value={structuredQueryDraft}
                    onChange={(event) => setStructuredQueryDraft(event.target.value)}
                    autoSize={{ minRows: 2, maxRows: 5 }}
                    placeholder={t("gameProject.structuredQueryPlaceholder", {
                      defaultValue: "Ask for an exact table or field, for example: equipment table fields",
                    })}
                  />
                  <div className={styles.structuredQueryPanelActions}>
                    <Tooltip title={knowledgeReadReason || undefined}>
                      <span>
                        <Button
                          type="primary"
                          onClick={handleSubmitStructuredQuery}
                          loading={structuredQueryLoading}
                          disabled={!canSubmitStructuredQuery}
                        >
                          {t("gameProject.structuredQuerySubmitButton", { defaultValue: "Submit structured query" })}
                        </Button>
                      </span>
                    </Tooltip>
                  </div>

                  {structuredQueryResponse ? (
                    <div className={styles.structuredQueryResultBlock}>
                      <div className={styles.structuredQuerySummary}>
                        <div className={styles.releaseSummaryRow}>
                          <div className={styles.releaseSummaryLabel}>{t("gameProject.structuredQueryQueryLabel", { defaultValue: "query" })}</div>
                          <div className={styles.releaseSummaryValue}>{structuredQueryResponse.query}</div>
                        </div>
                        <div className={styles.releaseSummaryRow}>
                          <div className={styles.releaseSummaryLabel}>{t("gameProject.structuredQueryRequestModeLabel", { defaultValue: "request_mode" })}</div>
                          <div className={styles.releaseSummaryValue}>{structuredQueryResponse.request_mode}</div>
                        </div>
                        <div className={styles.releaseSummaryRow}>
                          <div className={styles.releaseSummaryLabel}>{t("gameProject.structuredQueryResultModeLabel", { defaultValue: "result_mode" })}</div>
                          <div className={styles.releaseSummaryValue}>{structuredQueryResponse.result_mode}</div>
                        </div>
                        <div className={styles.releaseSummaryRow}>
                          <div className={styles.releaseSummaryLabel}>{t("gameProject.structuredQueryStatusLabel", { defaultValue: "status" })}</div>
                          <div className={styles.releaseSummaryValue}>{structuredQueryResponse.status}</div>
                        </div>
                        <div className={styles.releaseSummaryRow}>
                          <div className={styles.releaseSummaryLabel}>{t("gameProject.structuredQueryItemsLabel", { defaultValue: "items" })}</div>
                          <div className={styles.releaseSummaryValue}>{structuredQueryResponse.items.length}</div>
                        </div>
                      </div>
                      {renderStructuredQueryResultStatus(structuredQueryResponse)}
                      {structuredQueryResponse.warnings.length > 0 ? (
                        <div className={styles.structuredQueryWarnings}>
                          {structuredQueryResponse.warnings.map((warning) => (
                            <Alert key={warning} type="warning" showIcon message={warning} />
                          ))}
                        </div>
                      ) : null}
                      {structuredQueryResponse.items.length > 0 ? (
                        <div className={styles.structuredQueryItemList}>
                          {structuredQueryResponse.items.map((item) => renderStructuredQueryItem(item))}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ) : null}

              {ragError ? (
                <Alert
                  type="warning"
                  showIcon
                  message={t("gameProject.ragAnswerWarning", { defaultValue: "Knowledge answer is temporarily unavailable" })}
                  description={ragError}
                  className={styles.ragAlert}
                />
              ) : null}

              {ragAnswer ? (
                <div className={styles.ragResultBlock}>
                  <div className={styles.ragResultActions}>
                    <Button size="small" onClick={handleCopyRagAnswer}>
                      {t("gameProject.ragCopyButton", { defaultValue: "Copy result" })}
                    </Button>
                    {ragAnswer.citations.length > 0 ? (
                      <Button
                        size="small"
                        onClick={() => focusCitation(ragAnswer.citations[0]?.citation_id ?? null)}
                      >
                        {t("gameProject.ragFocusCitationsButton", { defaultValue: "Focus citations" })}
                      </Button>
                    ) : null}
                  </div>

                  {ragDisplayState === "answer" && ragAnswer.answer ? (
                    <div className={styles.ragAnswerBox}>
                      <Text strong>{t("gameProject.ragAnswerTitle", { defaultValue: "Answer" })}</Text>
                      <div className={styles.ragAnswerText}>{ragAnswer.answer}</div>
                    </div>
                  ) : null}

                  {ragDisplayState === "no_current_release" ? (
                    <div className={`${styles.ragStatePanel} ${styles.ragStatePanelBlocked}`}>
                      <Text strong>{t("gameProject.ragNoCurrentReleaseTitle", { defaultValue: "No current knowledge release" })}</Text>
                      <div className={styles.ragStateDescription}>
                        {t("gameProject.ragNoCurrentReleaseDescription", {
                          defaultValue: "Build or set a current knowledge release before using this RAG entry.",
                        })}
                      </div>
                    </div>
                  ) : null}

                  {ragDisplayState === "insufficient_context" ? (
                    <div className={`${styles.ragStatePanel} ${styles.ragStatePanelRecoverable}`}>
                      <Text strong>{t("gameProject.ragInsufficientContextTitle", { defaultValue: "Insufficient grounded context" })}</Text>
                      <div className={styles.ragStateDescription}>
                        {t("gameProject.ragInsufficientContextDescription", {
                          defaultValue: "The current release did not provide enough grounded evidence for a safe answer.",
                        })}
                      </div>
                      {ragNextStepHints.length > 0 ? (
                        <div className={styles.ragNextStepsBlock}>
                          <Text strong>{t("gameProject.ragNextStepsTitle", { defaultValue: "Next-step hints" })}</Text>
                          <div className={styles.ragNextStepsList}>
                            {ragNextStepHints.map((hint) => (
                              <div key={hint} className={styles.ragNextStepItem}>
                                {hint}
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  <div className={styles.ragResultSummary}>
                    <div className={styles.releaseSummaryRow}>
                      <div className={styles.releaseSummaryLabel}>
                        {t("gameProject.ragStateLabel", { defaultValue: "state" })}
                      </div>
                      <div className={styles.releaseSummaryValue}>{formatRagMode(ragDisplayState || ragAnswer.mode)}</div>
                    </div>
                    <div className={styles.releaseSummaryRow}>
                      <div className={styles.releaseSummaryLabel}>
                        {t("gameProject.ragReleaseIdLabel", { defaultValue: "release id" })}
                      </div>
                      <div className={styles.releaseSummaryValue}>{ragAnswer.release_id || "-"}</div>
                    </div>
                  </div>

                  {ragAnswer.warnings.length > 0 ? (
                    <div className={styles.ragWarningsBlock}>
                      <Text strong>{t("gameProject.ragWarningsTitle", { defaultValue: "Warnings" })}</Text>
                      <div className={styles.ragWarningList}>
                        {ragAnswer.warnings.map((warning) => {
                          const alertType = isStructuredOrWorkbenchWarning(warning) ? "info" : "warning";
                          return (
                            <Alert
                              key={warning}
                              type={alertType}
                              showIcon
                              message={getLocalizedRagWarning(warning)}
                              description={
                                warning === STRUCTURED_FACT_WARNING ? (
                                  renderStructuredQueryAffordance("warning")
                                ) : warning === CHANGE_QUERY_WARNING ? (
                                  renderWorkbenchAffordance("warning")
                                ) : undefined
                              }
                            />
                          );
                        })}
                      </div>
                    </div>
                  ) : null}

                  <div className={styles.ragCitationsBlock} ref={citationsSectionRef}>
                    <div className={styles.ragCitationsHeader}>
                      <Text strong>{t("gameProject.ragCitationsTitle", { defaultValue: "Citations" })}</Text>
                      {ragAnswer.citations.length > 0 ? (
                        <Text type="secondary">
                          {t("gameProject.ragCitationsHint", {
                            defaultValue: "Focus stays within the returned citation list only.",
                          })}
                        </Text>
                      ) : null}
                    </div>
                    <div className={styles.ragCitationList}>{renderRagCitationList(ragAnswer.citations)}</div>
                  </div>
                </div>
              ) : (
                <div className={styles.ragEmpty}>
                  {t("gameProject.ragEmptyState", {
                    defaultValue: "Ask a question to see the current-release RAG answer, release id, citations, and warnings here.",
                  })}
                </div>
              )}
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
                <Space size={8}>
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
                </Space>
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
              <Button
                size="small"
                onClick={() => void refreshBuildCandidates()}
                loading={buildCandidatesLoading}
                disabled={!canReadReleaseCandidates}
              >
                {t("common.refresh")}
              </Button>
            </div>

            <div className={styles.releaseCandidateHint}>
              {t("gameProject.releaseCandidateHint", {
                defaultValue:
                  "Only accepted and selected candidates are shown here. Leaving all items unchecked keeps the existing build behavior.",
              })}
            </div>

            {releaseCandidateReadReason ? (
              <Alert
                type="info"
                showIcon
                message={t("gameProject.releaseCandidatePermissionMessage", {
                  defaultValue: "Release candidates are unavailable for this session.",
                })}
                description={releaseCandidateReadReason}
                className={styles.releaseCandidateAlert}
              />
            ) : null}

            {buildCandidatesError ? (
              <Alert
                type="warning"
                showIcon
                message={t("gameProject.releaseCandidateWarning", { defaultValue: "Release candidate list is temporarily unavailable" })}
                description={buildCandidatesError}
                className={styles.releaseCandidateAlert}
              />
            ) : null}

            {releaseCandidateReadReason ? (
              <div className={styles.releaseCandidateEmpty}>
                {t("gameProject.releaseCandidatePermissionEmpty", {
                  defaultValue: "Candidate selection is unavailable without release-candidate read permission.",
                })}
              </div>
            ) : buildCandidatesLoading ? (
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
