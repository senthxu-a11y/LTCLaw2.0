import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Form, Input, Button, Card } from "@agentscope-ai/design";
import { Alert, Checkbox, Modal, Space, Tag, Tooltip, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import type { FrontendCapabilityToken } from "@/api/types/permissions";
import { gameApi } from "../../../api/modules/game";
import { canUseGovernanceAction, hasCapabilityContext, isPermissionDeniedError } from "@/utils/permissions";
import { gameStructuredQueryApi } from "../../../api/modules/gameStructuredQuery";
import { gameKnowledgeReleaseApi } from "../../../api/modules/gameKnowledgeRelease";
import type {
  FormalKnowledgeMapResponse,
  KnowledgeManifest,
  KnowledgeMap,
  KnowledgeRagAnswerResponse,
  KnowledgeRagCitation,
  KnowledgeReleaseHistoryItem,
  ReleaseCandidateListItem,
  StructuredQueryItem,
  StructuredQueryResponse,
} from "../../../api/types/game";
import { useAgentStore } from "../../../stores/agentStore";
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
} from "../ragUiHelpers";
import { buildCitationWorkbenchTarget } from "../citationDeepLink";
import styles from "../GameProject.module.less";

const { TextArea } = Input;
const { Text } = Typography;

interface BuildReleaseFormData {
  release_id: string;
  release_notes?: string;
}

const NO_CURRENT_RELEASE_DETAIL = "No current knowledge release is set";
const LOCAL_PROJECT_DIRECTORY_ERROR = "Local project directory not configured";
const NO_FIRST_RELEASE_INDEXES_DETAIL = "Current table indexes are required to build the first knowledge release";
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

function createDefaultReleaseId(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `v${now.getFullYear()}.${pad(now.getMonth() + 1)}.${pad(now.getDate())}.${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

export default function KnowledgePage() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const navigate = useNavigate();
  const { selectedAgent, agents } = useAgentStore();
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
  const [indexStatusLoading, setIndexStatusLoading] = useState(false);
  const [indexStatus, setIndexStatus] = useState<{ configured: boolean; table_count?: number } | null>(null);
  const [isRebuildingIndexes, setIsRebuildingIndexes] = useState(false);
  const [rebuildIndexesError, setRebuildIndexesError] = useState<string | null>(null);
  const [rebuildIndexesSuccess, setRebuildIndexesSuccess] = useState<string | null>(null);
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
  const [buildForm] = Form.useForm<BuildReleaseFormData>();
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
      params.set("from", "rag-citation");
      params.set("citationId", target.citationId);
      if (target.citationTitle) {
        params.set("citationTitle", target.citationTitle);
      }
      if (target.citationSource) {
        params.set("citationSource", target.citationSource);
      }
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
    try {
      const response = await gameStructuredQueryApi.submit(selectedAgent, query);
      setStructuredQueryResponse(response);
    } finally {
      setStructuredQueryLoading(false);
    }
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

  const fetchMapSummaryData = useCallback(async (agentId: string) => {
    await Promise.all([fetchCandidateMap(agentId), fetchFormalMap(agentId)]);
  }, [fetchCandidateMap, fetchFormalMap]);

  const fetchIndexStatus = useCallback(async (agentId: string) => {
    setIndexStatusLoading(true);
    try {
      const status = await gameApi.getIndexStatus(agentId);
      setIndexStatus(status);
    } catch {
      setIndexStatus(null);
    } finally {
      setIndexStatusLoading(false);
    }
  }, []);

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
      release_notes: currentRelease
        ? `Build from current indexes based on ${currentRelease.release_id}`
        : "Bootstrap first knowledge release from current server-side indexes",
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

  const refreshKnowledgeColdStartState = useCallback(async (agentId: string) => {
    const mapRefresh = hasExplicitCapabilityContext && !canReadMap
      ? Promise.resolve()
      : fetchMapSummaryData(agentId);
    const candidateRefresh = buildModalOpen && canReadReleaseCandidates
      ? fetchBuildCandidates(agentId)
      : Promise.resolve();

    await Promise.all([
      fetchKnowledgeReleases(agentId),
      mapRefresh,
      candidateRefresh,
      fetchIndexStatus(agentId),
    ]);
  }, [buildModalOpen, canReadMap, canReadReleaseCandidates, fetchBuildCandidates, fetchIndexStatus, fetchKnowledgeReleases, fetchMapSummaryData, hasExplicitCapabilityContext]);

  const handleRebuildCurrentIndexes = useCallback(async () => {
    if (!selectedAgent) {
      return;
    }

    try {
      setIsRebuildingIndexes(true);
      setRebuildIndexesError(null);
      setRebuildIndexesSuccess(null);
      const result = await gameApi.rebuildIndex(selectedAgent);
      setBuildCandidatesError(null);
      await refreshKnowledgeColdStartState(selectedAgent);
      const successMessage = t("gameProject.rebuildIndexesSuccess", {
        defaultValue: `Current table indexes rebuilt. Indexed ${result.indexed} table files.`,
      });
      setRebuildIndexesSuccess(successMessage);
      message.success(successMessage);
    } catch (err) {
      const errorMessage = formatGovernanceError(
        err,
        t("gameProject.rebuildIndexesFailed", { defaultValue: "Failed to rebuild current table indexes" }),
      );
      setRebuildIndexesError(errorMessage);
      message.warning(errorMessage);
    } finally {
      setIsRebuildingIndexes(false);
    }
  }, [formatGovernanceError, message, refreshKnowledgeColdStartState, selectedAgent, t]);

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
      setRebuildIndexesError(null);
      setRebuildIndexesSuccess(null);
      await refreshKnowledgeColdStartState(selectedAgent);
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
  const shouldShowEmptyDocContextHint = useMemo(
    () => ragDisplayState === "insufficient_context" && getIndexCount(currentRelease, "doc_knowledge") === 0,
    [currentRelease, ragDisplayState],
  );
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
  const candidateSummary = useMemo(() => summarizeMap(candidateMap), [candidateMap]);
  const savedFormalMap = useMemo(
    () => (formalMap?.mode === NO_FORMAL_MAP_MODE ? null : formalMap?.map ?? null),
    [formalMap],
  );
  const savedFormalSummary = useMemo(() => summarizeMap(savedFormalMap), [savedFormalMap]);
  const isBootstrapBuildState = !currentRelease && formalMap?.mode === NO_FORMAL_MAP_MODE;
  const hasCurrentTableIndexes = useMemo(() => {
    if (!indexStatus?.configured) {
      return false;
    }
    return (indexStatus.table_count ?? 0) > 0;
  }, [indexStatus]);
  const isColdStartIndexesMissing = isBootstrapBuildState && !indexStatusLoading && indexStatus !== null && !hasCurrentTableIndexes;
  const isColdStartIndexesReady = isBootstrapBuildState && !indexStatusLoading && indexStatus !== null && hasCurrentTableIndexes;

  const renderRebuildIndexesAction = useCallback((context: "page" | "modal") => {
    const hint = context === "page"
      ? t("gameProject.rebuildIndexesPageHint", {
          defaultValue: "Rebuild current table indexes here, then return to Build release when the prerequisite is ready.",
        })
      : t("gameProject.rebuildIndexesModalHint", {
          defaultValue: "Rebuild current table indexes first. Release build remains a separate explicit action after refresh.",
        });

    return (
      <Space direction="vertical" size={8}>
        <Text type="secondary">{hint}</Text>
        <Button
          size="small"
          onClick={() => void handleRebuildCurrentIndexes()}
          loading={isRebuildingIndexes}
          disabled={!selectedAgent}
        >
          {t("gameProject.rebuildIndexesButton", { defaultValue: "Rebuild current indexes" })}
        </Button>
      </Space>
    );
  }, [handleRebuildCurrentIndexes, isRebuildingIndexes, selectedAgent, t]);

  useEffect(() => {
    if (!selectedAgent) {
      setReleaseLoading(false);
      setReleaseError(null);
      setReleases([]);
      setCurrentRelease(null);
      setPreviousRelease(null);
      setCandidateMap(null);
      setCandidateMapReleaseId(null);
      setCandidateMapError(null);
      setCandidateMapLoading(false);
      setFormalMap(null);
      setFormalMapError(null);
      setFormalMapLoading(false);
      setIndexStatus(null);
      setIndexStatusLoading(false);
      setRebuildIndexesError(null);
      setRebuildIndexesSuccess(null);
      setIsRebuildingIndexes(false);
      return;
    }

    void fetchKnowledgeReleases(selectedAgent);
    void fetchIndexStatus(selectedAgent);
    if (hasExplicitCapabilityContext && !canReadMap) {
      setCandidateMap(null);
      setCandidateMapReleaseId(null);
      setCandidateMapError(null);
      setCandidateMapLoading(false);
      setFormalMap(null);
      setFormalMapError(null);
      setFormalMapLoading(false);
    } else {
      void fetchMapSummaryData(selectedAgent);
    }
  }, [canReadMap, fetchIndexStatus, fetchKnowledgeReleases, fetchMapSummaryData, hasExplicitCapabilityContext, selectedAgent]);

  useEffect(() => {
    setStructuredQueryPanelOpen(false);
    setStructuredQueryDraft("");
    setStructuredQueryLoading(false);
    setStructuredQueryResponse(null);
    setRebuildIndexesError(null);
    setRebuildIndexesSuccess(null);
  }, [selectedAgent]);

  useEffect(() => () => {
    if (citationHighlightTimeoutRef.current !== null) {
      window.clearTimeout(citationHighlightTimeoutRef.current);
    }
  }, []);

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
          {group.citations.map((citation) => {
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
          })}
        </div>
      </div>
    ));
  };

  return (
    <div className={styles.gamePage}>
      <PageHeader parent={t("nav.game")} current={t("nav.gameKnowledge", "Knowledge")} />

      <div className={styles.content}>
        <div className={styles.form}>
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

            {!selectedAgent ? (
              <Alert
                type="info"
                showIcon
                message={t("gameProject.noSelectedAgent", { defaultValue: "Select an Agent to load the knowledge workspace." })}
                className={styles.releaseAlert}
              />
            ) : null}

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
                  defaultValue:
                    "Build uses the safe server-side endpoint and does not auto-set current. If there is no saved formal map and no current release yet, the first build bootstraps from current server-side indexes.",
                })}
              </Text>
              {buildDisabledReason ? <Text type="secondary">{buildDisabledReason}</Text> : null}
            </div>

            {isColdStartIndexesMissing ? (
              <Alert
                type="warning"
                showIcon
                message={t("gameProject.coldStartIndexesMissingTitle", {
                  defaultValue: "Current table indexes are required before the first release build",
                })}
                description={renderRebuildIndexesAction("page")}
                className={styles.releaseAlert}
              />
            ) : isColdStartIndexesReady ? (
              <Alert
                type="info"
                showIcon
                message={t("gameProject.coldStartIndexesReadyTitle", {
                  defaultValue: "Current table indexes are ready for first-release bootstrap",
                })}
                description={t("gameProject.coldStartIndexesReadyDescription", {
                  defaultValue: "Current table indexes are available. Click Build release to initialize release history and candidate map when you are ready.",
                })}
                className={styles.releaseAlert}
              />
            ) : null}

            {rebuildIndexesError ? (
              <Alert
                type="warning"
                showIcon
                message={t("gameProject.rebuildIndexesWarningTitle", {
                  defaultValue: "Current table index rebuild is temporarily unavailable",
                })}
                description={rebuildIndexesError}
                className={styles.releaseAlert}
              />
            ) : null}

            {rebuildIndexesSuccess ? (
              <Alert
                type="success"
                showIcon
                message={t("gameProject.rebuildIndexesSuccessTitle", {
                  defaultValue: "Current table indexes rebuilt",
                })}
                description={rebuildIndexesSuccess}
                className={styles.releaseAlert}
              />
            ) : null}

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
                      {shouldShowEmptyDocContextHint ? (
                        <div className={styles.ragStateDescription}>
                          {t("gameProject.ragEmptyDocContextDescription", {
                            defaultValue:
                              "No document-library context is available in the current release. Document-style questions cannot produce a grounded answer until doc_knowledge is built.",
                          })}
                        </div>
                      ) : null}
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
          </Card>

          <Card
            title={t("gameProject.knowledgeStatusTitle", { defaultValue: "Knowledge Status" })}
            className={styles.section}
          >
            <div className={styles.releaseHint}>
              {t("gameProject.knowledgeStatusHint", {
                defaultValue: "Readonly status summary for candidate and saved formal map assets. Editing stays on the Project page in this lane.",
              })}
            </div>

            {mapReadReason ? (
              <Alert
                type="info"
                showIcon
                message={mapReadReason}
                className={styles.releaseAlert}
              />
            ) : null}

            <div className={styles.releaseListBlock}>
              <div className={styles.releaseListHeader}>
                <Text strong>{t("gameProject.mapCandidateTitle", { defaultValue: "Candidate map" })}</Text>
                <Space size={8}>
                  <Button
                    size="small"
                    onClick={() => selectedAgent && fetchMapSummaryData(selectedAgent)}
                    loading={candidateMapLoading || formalMapLoading}
                    disabled={!selectedAgent || !!mapReadReason}
                  >
                    {t("common.refresh")}
                  </Button>
                </Space>
              </div>

              {candidateMapLoading ? (
                <div className={styles.releaseEmpty}>{t("common.loading")}</div>
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
                      ? isColdStartIndexesMissing
                        ? renderRebuildIndexesAction("page")
                        : isColdStartIndexesReady
                          ? t("gameProject.mapCandidateNoCurrentIndexesReadyDescription", {
                              defaultValue:
                                "No current release is set yet. Current table indexes are ready. Build the first knowledge release to initialize release history and candidate map.",
                            })
                          : t("gameProject.mapCandidateNoCurrentDescription", {
                              defaultValue:
                                "No current release is set yet. Build the first knowledge release from current server-side indexes to initialize release history and candidate map.",
                            })
                      : candidateMapError
                  }
                  className={styles.releaseAlert}
                />
              ) : !candidateMap ? (
                <div className={styles.releaseEmpty}>{t("gameProject.mapCandidateEmpty", { defaultValue: "No candidate map available" })}</div>
              ) : (
                <>
                  <div className={styles.releaseSummary}>
                    <div className={styles.releaseSummaryRow}>
                      <div className={styles.releaseSummaryLabel}>{t("gameProject.mapCandidateTitle", { defaultValue: "Candidate map" })}</div>
                      <div className={styles.releaseSummaryValue}>{candidateMapReleaseId || "-"}</div>
                    </div>
                  </div>
                  <div className={styles.mapReviewCounts}>
                    <Tag color="blue">systems {candidateSummary.systems.length}</Tag>
                    <Tag color="gold">tables {candidateSummary.tables.length}</Tag>
                    <Tag color="green">docs {candidateSummary.docs.length}</Tag>
                    <Tag color="purple">scripts {candidateSummary.scripts.length}</Tag>
                    <Tag color="cyan">relationships {candidateSummary.relationships.length}</Tag>
                  </div>
                </>
              )}
            </div>

            <div className={styles.releaseListBlock}>
              <div className={styles.releaseListHeader}>
                <Text strong>{t("gameProject.formalMapTitle", { defaultValue: "Saved formal map" })}</Text>
              </div>

              {formalMapLoading ? (
                <div className={styles.releaseEmpty}>{t("common.loading")}</div>
              ) : formalMapError ? (
                <Alert
                  type="warning"
                  showIcon
                  message={t("gameProject.formalMapLoadWarning", { defaultValue: "Formal map is temporarily unavailable" })}
                  description={formalMapError}
                  className={styles.releaseAlert}
                />
              ) : formalMap?.mode === NO_FORMAL_MAP_MODE ? (
                <Alert
                  type="info"
                  showIcon
                  message={t("gameProject.noSavedFormalMapTitle", { defaultValue: "no saved formal map" })}
                  description={t("gameProject.noSavedFormalMapDescription", {
                    defaultValue: "Use Save as formal map first. Status editing is available only on saved formal map.",
                  })}
                  className={styles.releaseAlert}
                />
              ) : !savedFormalMap ? (
                <div className={styles.releaseEmpty}>{t("gameProject.formalMapEmpty", { defaultValue: "No saved formal map" })}</div>
              ) : (
                <>
                  <div className={styles.releaseSummary}>
                    <div className={styles.releaseSummaryRow}>
                      <div className={styles.releaseSummaryLabel}>{t("gameProject.formalMapHashLabel", { defaultValue: "map hash" })}</div>
                      <div className={styles.releaseSummaryValue}>{formalMap?.map_hash || "-"}</div>
                    </div>
                    <div className={styles.releaseSummaryRow}>
                      <div className={styles.releaseSummaryLabel}>{t("gameProject.formalMapUpdatedAt", { defaultValue: "updated_at" })}</div>
                      <div className={styles.releaseSummaryValue}>{formatDateTime(formalMap?.updated_at)}</div>
                    </div>
                    <div className={styles.releaseSummaryRow}>
                      <div className={styles.releaseSummaryLabel}>{t("gameProject.formalMapUpdatedBy", { defaultValue: "updated_by" })}</div>
                      <div className={styles.releaseSummaryValue}>{formalMap?.updated_by || "-"}</div>
                    </div>
                  </div>
                  <div className={styles.mapReviewCounts}>
                    <Tag color="blue">systems {savedFormalSummary.systems.length}</Tag>
                    <Tag color="gold">tables {savedFormalSummary.tables.length}</Tag>
                    <Tag color="green">docs {savedFormalSummary.docs.length}</Tag>
                    <Tag color="purple">scripts {savedFormalSummary.scripts.length}</Tag>
                    <Tag color="cyan">relationships {savedFormalSummary.relationships.length}</Tag>
                  </div>
                </>
              )}
            </div>
          </Card>
        </div>
      </div>

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
          {isBootstrapBuildState ? (
            <Alert
              type={isColdStartIndexesMissing ? "warning" : "info"}
              showIcon
              message={isColdStartIndexesMissing
                ? t("gameProject.releaseBuildBootstrapIndexesRequiredTitle", {
                    defaultValue: "Current table indexes are required before first-release bootstrap",
                  })
                : t("gameProject.releaseBuildBootstrapTitle", { defaultValue: "Initialize the first knowledge release" })}
              description={isColdStartIndexesMissing
                ? renderRebuildIndexesAction("modal")
                : isColdStartIndexesReady
                  ? t("gameProject.releaseBuildBootstrapReadyDescription", {
                      defaultValue:
                        "This project has no saved formal map and no current release yet. Current table indexes are ready, so Build can bootstrap the first release from current server-side indexes without an existing current release.",
                    })
                  : t("gameProject.releaseBuildBootstrapDescription", {
                      defaultValue:
                        "This project has no saved formal map and no current release yet. Build will bootstrap the first release from current server-side indexes only; it does not require an existing current release.",
                    })}
              className={styles.releaseCandidateAlert}
            />
          ) : null}
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
                type={buildCandidatesError === NO_CURRENT_RELEASE_DETAIL ? "info" : "warning"}
                showIcon
                message={
                  buildCandidatesError === NO_CURRENT_RELEASE_DETAIL
                    ? t("gameProject.releaseBuildNoCurrentTitle", { defaultValue: "No current release is set yet" })
                    : buildCandidatesError === NO_FIRST_RELEASE_INDEXES_DETAIL
                      ? t("gameProject.releaseBuildBootstrapIndexesRequiredTitle", {
                          defaultValue: "Current table indexes are required before first-release bootstrap",
                        })
                    : t("gameProject.releaseCandidateWarning", { defaultValue: "Release candidate list is temporarily unavailable" })
                }
                description={
                  buildCandidatesError === NO_CURRENT_RELEASE_DETAIL
                    ? t("gameProject.releaseBuildNoCurrentDescription", {
                        defaultValue:
                          "First-release bootstrap does not require an existing current release. Refresh indexes and build again if initialization prerequisites are met.",
                      })
                    : buildCandidatesError === NO_FIRST_RELEASE_INDEXES_DETAIL
                      ? renderRebuildIndexesAction("modal")
                      : buildCandidatesError
                }
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