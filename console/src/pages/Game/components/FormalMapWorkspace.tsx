import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Select, Space, Tag, Tooltip, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useAppMessage } from "@/hooks/useAppMessage";
import type { FrontendCapabilityToken } from "@/api/types/permissions";
import { canUseGovernanceAction, hasCapabilityContext, isPermissionDeniedError } from "@/utils/permissions";
import { gameKnowledgeReleaseApi } from "../../../api/modules/gameKnowledgeRelease";
import type {
  FormalKnowledgeMapResponse,
  KnowledgeDocRef,
  KnowledgeMap,
  KnowledgeMapCandidateResponse,
  KnowledgeRelationship,
  KnowledgeScriptRef,
  KnowledgeStatus,
  KnowledgeSystem,
  KnowledgeTableRef,
} from "../../../api/types/game";
import { useAgentStore } from "../../../stores/agentStore";
import {
  buildDiffReviewSections,
  buildMapBuildArtifactStates,
  canSaveReviewedCandidateAsFormalMap,
  NO_FORMAL_MAP_MODE,
  summarizeKnowledgeMap,
} from "./mapBuildReview";
import styles from "../GameProject.module.less";

const { Text } = Typography;

const NO_CURRENT_RELEASE_DETAIL = "No current knowledge release is set";
const NO_SOURCE_CANDIDATE_DETAIL = "No source candidate map is available";
const LOCAL_PROJECT_DIRECTORY_ERROR = "Local project directory not configured";
const FORMAL_MAP_STATUS_OPTIONS: Array<{ label: KnowledgeStatus; value: KnowledgeStatus }> = [
  { label: "active", value: "active" },
  { label: "deprecated", value: "deprecated" },
  { label: "ignored", value: "ignored" },
];

interface FormalMapWorkspaceProps {
  mode: "summary" | "full";
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

export default function FormalMapWorkspace({ mode }: FormalMapWorkspaceProps) {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const navigate = useNavigate();
  const { selectedAgent, agents } = useAgentStore();
  const selectedAgentSummary = agents.find((agent) => agent.id === selectedAgent);
  const capabilities: FrontendCapabilityToken[] | undefined = selectedAgentSummary?.capabilities;
  const hasExplicitCapabilityContext = hasCapabilityContext(capabilities);
  const canReadCandidate = canUseGovernanceAction(capabilities, "knowledge.candidate.read");
  const canWriteCandidate = canUseGovernanceAction(capabilities, "knowledge.candidate.write");
  const canReadMap = canUseGovernanceAction(capabilities, "knowledge.map.read");
  const canEditMap = canUseGovernanceAction(capabilities, "knowledge.map.edit");

  const [releaseSnapshotLoading, setReleaseSnapshotLoading] = useState(false);
  const [releaseSnapshotError, setReleaseSnapshotError] = useState<string | null>(null);
  const [releaseSnapshotResult, setReleaseSnapshotResult] = useState<KnowledgeMapCandidateResponse | null>(null);
  const [sourceCandidateLoading, setSourceCandidateLoading] = useState(false);
  const [sourceCandidateError, setSourceCandidateError] = useState<string | null>(null);
  const [sourceCandidateResult, setSourceCandidateResult] = useState<KnowledgeMapCandidateResponse | null>(null);
  const [formalMapLoading, setFormalMapLoading] = useState(false);
  const [formalMapError, setFormalMapError] = useState<string | null>(null);
  const [formalMap, setFormalMap] = useState<FormalKnowledgeMapResponse | null>(null);
  const [formalMapDraft, setFormalMapDraft] = useState<KnowledgeMap | null>(null);
  const [savingFormalMap, setSavingFormalMap] = useState(false);
  const [savingFormalMapDraft, setSavingFormalMapDraft] = useState(false);

  const permissionDeniedMessage = t("gameProject.permissionDenied", {
    defaultValue: "You do not have permission to perform this action.",
  });

  const candidateReadReason =
    hasExplicitCapabilityContext && !canReadCandidate
      ? t("gameProject.releaseCandidatePermissionRequired", {
          defaultValue: "Requires knowledge.candidate.read permission.",
        })
      : null;
  const candidateWriteReason =
    hasExplicitCapabilityContext && !canWriteCandidate
      ? t("gameProject.mapCandidateWritePermissionRequired", {
          defaultValue: "Requires knowledge.candidate.write permission.",
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

  const getErrorText = useCallback(
    (error: unknown, fallbackMessage: string) =>
      error instanceof Error ? error.message : fallbackMessage,
    [],
  );

  const resolveMapLoadError = useCallback(
    (error: unknown, fallbackMessage: string) => {
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
    },
    [getErrorText, permissionDeniedMessage],
  );

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

  const fetchReleaseSnapshot = useCallback(
    async (agentId: string) => {
      setReleaseSnapshotLoading(true);
      setReleaseSnapshotError(null);
      try {
        const response = await gameKnowledgeReleaseApi.getMapCandidate(agentId);
        setReleaseSnapshotResult(response);
      } catch (err) {
        setReleaseSnapshotResult(null);
        setReleaseSnapshotError(
          resolveMapLoadError(
            err,
            t("gameProject.mapReleaseSnapshotLoadFailed", {
              defaultValue: "Failed to load release map snapshot",
            }),
          ),
        );
      } finally {
        setReleaseSnapshotLoading(false);
      }
    },
    [resolveMapLoadError, t],
  );

  const fetchFormalMap = useCallback(
    async (agentId: string) => {
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
    },
    [resolveMapLoadError, t],
  );

  const fetchLatestSourceCandidate = useCallback(
    async (agentId: string) => {
      setSourceCandidateLoading(true);
      setSourceCandidateError(null);
      try {
        const response = await gameKnowledgeReleaseApi.getLatestSourceCandidate(agentId);
        setSourceCandidateResult(response);
      } catch (err) {
        const messageText = resolveMapLoadError(
          err,
          t("gameProject.mapBuildReviewFailed", {
            defaultValue: "Failed to load source candidate review",
          }),
        );
        setSourceCandidateResult(null);
        if (messageText.includes(NO_SOURCE_CANDIDATE_DETAIL)) {
          setSourceCandidateError(null);
        } else {
          setSourceCandidateError(messageText);
        }
      } finally {
        setSourceCandidateLoading(false);
      }
    },
    [resolveMapLoadError, t],
  );

  const fetchMapReviewData = useCallback(
    async (agentId: string) => {
      const tasks: Array<Promise<void>> = [];
      if (!hasExplicitCapabilityContext || canReadCandidate) {
        tasks.push(fetchReleaseSnapshot(agentId));
        tasks.push(fetchLatestSourceCandidate(agentId));
      } else {
        setReleaseSnapshotResult(null);
        setReleaseSnapshotError(null);
        setSourceCandidateResult(null);
        setSourceCandidateError(null);
      }
      if (!hasExplicitCapabilityContext || canReadMap) {
        tasks.push(fetchFormalMap(agentId));
      } else {
        setFormalMap(null);
        setFormalMapError(null);
        setFormalMapDraft(null);
      }
      if (tasks.length > 0) {
        await Promise.all(tasks);
      }
    },
    [canReadCandidate, canReadMap, fetchFormalMap, fetchLatestSourceCandidate, fetchReleaseSnapshot, hasExplicitCapabilityContext],
  );

  const handleBuildSourceCandidate = useCallback(async () => {
    if (!selectedAgent) {
      return;
    }
    setSourceCandidateLoading(true);
    setSourceCandidateError(null);
    try {
      const response = await gameKnowledgeReleaseApi.buildMapCandidateFromSource(selectedAgent, {
        use_existing_formal_map_as_hint: true,
      });
      setSourceCandidateResult(response);
      message.success(
        t("gameProject.mapBuildReviewSuccess", {
          defaultValue: "Built a source candidate review. Confirm it explicitly before saving a formal map.",
        }),
      );
    } catch (err) {
      setSourceCandidateResult(null);
      setSourceCandidateError(
        resolveMapLoadError(
          err,
          t("gameProject.mapBuildReviewFailed", {
            defaultValue: "Failed to build source candidate review",
          }),
        ),
      );
    } finally {
      setSourceCandidateLoading(false);
    }
  }, [message, resolveMapLoadError, selectedAgent, t]);

  const handleSaveFormalMap = async () => {
    if (!selectedAgent || !sourceCandidateResult?.map) {
      return;
    }
    try {
      setSavingFormalMap(true);
      await gameKnowledgeReleaseApi.saveFormalMap(
        selectedAgent,
        sourceCandidateResult.map,
        selectedAgentSummary?.name || selectedAgent,
      );
      await fetchFormalMap(selectedAgent);
      message.success(
        t("gameProject.formalMapSaveSuccess", {
          defaultValue: "Saved formal map. This does not build, publish, or set the current release.",
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
          defaultValue: "Saved formal map. This does not build, publish, or set the current release.",
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

  const renderDiffReviewSection = (
    label: string,
    refs: string[],
    emptyLabel: string,
  ) => (
    <div className={styles.mapReviewBlock}>
      <Text strong>{label}</Text>
      {refs.length === 0 ? (
        <div className={styles.mapReviewEmpty}>{emptyLabel}</div>
      ) : (
        <div className={styles.mapReviewRefList}>
          {refs.map((ref) => (
            <Tag key={ref}>{ref}</Tag>
          ))}
        </div>
      )}
    </div>
  );

  const savedFormalMap = useMemo(
    () => (formalMap?.mode === NO_FORMAL_MAP_MODE ? null : formalMap?.map ?? null),
    [formalMap],
  );
  const artifactStates = buildMapBuildArtifactStates({
    sourceCandidate: sourceCandidateResult,
    formalMap,
    releaseSnapshot: releaseSnapshotResult,
  });
  const candidateSummary = summarizeKnowledgeMap(sourceCandidateResult?.map ?? null);
  const releaseSummary = summarizeKnowledgeMap(releaseSnapshotResult?.map ?? null);
  const savedFormalSummary = summarizeKnowledgeMap(savedFormalMap);
  const formalSummary = summarizeKnowledgeMap(formalMapDraft);
  const hasCandidateMapSummary = !!sourceCandidateResult?.map && !sourceCandidateError;
  const hasFormalMapSummary = !!savedFormalMap && !formalMapError;
  const formalMapDraftDirty =
    !!savedFormalMap && !!formalMapDraft && JSON.stringify(formalMapDraft) !== JSON.stringify(savedFormalMap);
  const formalMapRelationshipWarnings = buildRelationshipWarningMessages(formalMapDraft);
  const diffReviewSections = buildDiffReviewSections(sourceCandidateResult?.diff_review);
  const saveFormalMapFirstReason = !savedFormalMap
    ? t("gameProject.formalMapSaveFirstBeforeEdit", {
        defaultValue: "Save a formal map first before editing statuses.",
      })
    : null;
  const saveFormalMapDisabledReason = mapReadReason || mapEditReason || candidateWriteReason || null;
  const canSaveFormalMap = canSaveReviewedCandidateAsFormalMap({
    agentId: selectedAgent,
    sourceCandidate: sourceCandidateResult,
    hasExplicitCapabilityContext,
    canReadMap,
    canEditMap,
  });
  const statusEditDisabledReason = mapEditReason || saveFormalMapFirstReason;
  const canEditFormalMapStatuses =
    !!savedFormalMap && (!hasExplicitCapabilityContext || (canReadMap && canEditMap));
  const canSaveFormalMapDraft =
    !!selectedAgent && !!formalMapDraft && formalMapDraftDirty && canEditFormalMapStatuses;

  useEffect(() => {
    if (!selectedAgent) {
      setReleaseSnapshotResult(null);
      setReleaseSnapshotError(null);
      setSourceCandidateResult(null);
      setSourceCandidateError(null);
      setFormalMap(null);
      setFormalMapDraft(null);
      setFormalMapError(null);
      setReleaseSnapshotLoading(false);
      setSourceCandidateLoading(false);
      setFormalMapLoading(false);
      return;
    }

    setSourceCandidateResult(null);
    setSourceCandidateError(null);
    void fetchMapReviewData(selectedAgent);
  }, [fetchMapReviewData, selectedAgent]);

  useEffect(() => {
    setFormalMapDraft(savedFormalMap ? cloneKnowledgeMap(savedFormalMap) : null);
  }, [savedFormalMap]);

  const renderSummaryText = (
    summary: ReturnType<typeof summarizeKnowledgeMap>,
    fallback: string,
  ) =>
    summary.systems || summary.tables || summary.docs || summary.scripts || summary.relationships
      ? t("gameProject.formalMapCompactCounts", {
          defaultValue: "{{systems}} systems / {{tables}} tables / {{docs}} docs / {{scripts}} scripts / {{relationships}} relationships",
          systems: summary.systems,
          tables: summary.tables,
          docs: summary.docs,
          scripts: summary.scripts,
          relationships: summary.relationships,
        })
      : fallback;

  if (mode === "summary") {
    return (
      <>
        <div className={styles.mapReviewTransitionLead}>
          <Text strong>
            {t("gameProject.formalMapWorkspaceLead", {
              defaultValue: "Map Build Review now lives on the dedicated Map Editor page.",
            })}
          </Text>
          <div className={styles.mapReviewHint}>
            {t("gameProject.formalMapWorkspaceSummaryHint", {
              defaultValue:
                "Build Candidate Map from canonical facts, compare it against Formal Map or Release Map, and save Formal Map only after explicit admin confirmation.",
            })}
          </div>
        </div>

        {mapReadReason ? (
          <Alert type="info" showIcon message={mapReadReason} className={styles.mapReviewAlert} />
        ) : null}
        {candidateReadReason ? (
          <Alert type="info" showIcon message={candidateReadReason} className={styles.mapReviewAlert} />
        ) : null}

        <div className={styles.mapReviewCompactSummary}>
          {artifactStates.map((item) => (
            <div key={item.key} className={styles.mapReviewCompactItem}>
              <Text type="secondary">
                {item.key === "candidate"
                  ? t("gameProject.mapBuildCandidateTitle", { defaultValue: "Candidate Map" })
                  : item.key === "formal"
                    ? t("gameProject.formalMapTitle", { defaultValue: "Formal Map" })
                    : t("gameProject.releaseMapTitle", { defaultValue: "Release Map" })}
              </Text>
              <div className={styles.mapReviewCompactValue}>
                {item.key === "candidate"
                  ? hasCandidateMapSummary
                    ? renderSummaryText(
                        candidateSummary,
                        t("gameProject.mapCandidateEmpty", { defaultValue: "No candidate map available" }),
                      )
                    : sourceCandidateLoading
                      ? t("common.loading")
                      : t("gameProject.mapBuildSummaryPending", {
                          defaultValue: "Build candidate review explicitly in Map Editor.",
                        })
                  : item.key === "formal"
                    ? hasFormalMapSummary
                      ? renderSummaryText(
                          savedFormalSummary,
                          t("gameProject.noSavedFormalMapTitle", { defaultValue: "no saved formal map" }),
                        )
                      : formalMapLoading
                        ? t("common.loading")
                        : formalMapError || t("gameProject.noSavedFormalMapTitle", { defaultValue: "no saved formal map" })
                    : releaseSnapshotLoading
                      ? t("common.loading")
                      : releaseSnapshotError || renderSummaryText(
                          releaseSummary,
                          t("gameProject.releaseMapSummaryEmpty", { defaultValue: "No release map snapshot available" }),
                        )}
              </div>
              <div className={styles.mapReviewHint}>
                {item.key === "candidate"
                  ? t("gameProject.mapBuildCandidateSummaryHint", {
                      defaultValue: "Suggested only. Not formal knowledge until an admin clicks save.",
                    })
                  : item.key === "formal"
                    ? t("gameProject.formalMapSummaryHint", {
                        defaultValue: "Saved structure only. It stays separate from release build and publish.",
                      })
                    : releaseSnapshotResult?.source_release_id || releaseSnapshotResult?.release_id
                      ? `release_id: ${releaseSnapshotResult?.source_release_id || releaseSnapshotResult?.release_id}`
                      : t("gameProject.releaseMapSummaryHint", {
                          defaultValue: "Published snapshot only. It is not the editing source.",
                        })}
              </div>
            </div>
          ))}
        </div>

        <div className={styles.mapReviewTransitionActions}>
          <Button size="small" type="primary" onClick={() => navigate("/game/map")}>
            {t("gameProject.openMapEditorWorkspaceButton", { defaultValue: "Open Map Editor" })}
          </Button>
          <Button
            size="small"
            onClick={() => selectedAgent && fetchMapReviewData(selectedAgent)}
            loading={releaseSnapshotLoading || formalMapLoading}
            disabled={!selectedAgent || !!mapReadReason || !!candidateReadReason}
          >
            {t("common.refresh")}
          </Button>
        </div>
      </>
    );
  }

  return (
    <div className={styles.mapReviewSection}>
      <div className={styles.mapReviewHeader}>
        <div>
          <Text strong>{t("gameProject.mapBuildReviewTitle", { defaultValue: "Map Build Review" })}</Text>
          <div className={styles.mapReviewHint}>
            {t("gameProject.mapBuildReviewHint", {
              defaultValue:
                "Candidate Map is suggested only, Formal Map is saved only after explicit admin confirmation, and Release Map remains a published snapshot rather than the editing source.",
            })}
          </div>
        </div>
        <Space size={8} wrap>
          <Button
            size="small"
            onClick={() => selectedAgent && fetchMapReviewData(selectedAgent)}
            loading={releaseSnapshotLoading || formalMapLoading}
            disabled={!selectedAgent || (!!mapReadReason && !!candidateReadReason)}
          >
            {t("common.refresh")}
          </Button>
          <Tooltip title={candidateWriteReason || undefined}>
            <span>
              <Button
                size="small"
                onClick={handleBuildSourceCandidate}
                loading={sourceCandidateLoading}
                disabled={!selectedAgent || !!candidateWriteReason}
              >
                {t("gameProject.buildCandidateFromSourceButton", { defaultValue: "Build Candidate Review" })}
              </Button>
            </span>
          </Tooltip>
          <Tooltip title={saveFormalMapDisabledReason || undefined}>
            <span>
              <Button
                size="small"
                type="primary"
                onClick={handleSaveFormalMap}
                loading={savingFormalMap}
                disabled={!canSaveFormalMap}
              >
                {t("gameProject.saveFormalMapButton", { defaultValue: "Save Candidate as Formal Map" })}
              </Button>
            </span>
          </Tooltip>
        </Space>
      </div>

      <div className={styles.mapReviewHint}>
        {t("gameProject.mapEditorPrimaryHint", {
          defaultValue:
            "Map Editor owns source candidate review, diff review, saved formal map review, explicit save-as-formal-map, status-only edits, and release snapshot comparison.",
        })}
      </div>

      <div className={styles.mapReviewCompactSummary}>
        {artifactStates.map((item) => (
          <div key={item.key} className={styles.mapReviewCompactItem}>
            <Text strong>
              {item.key === "candidate"
                ? t("gameProject.mapBuildCandidateTitle", { defaultValue: "Candidate Map" })
                : item.key === "formal"
                  ? t("gameProject.formalMapTitle", { defaultValue: "Formal Map" })
                  : t("gameProject.releaseMapTitle", { defaultValue: "Release Map" })}
            </Text>
            <div className={styles.mapReviewCompactValue}>
              {renderSummaryText(item.summary, t("gameProject.mapBuildArtifactEmpty", { defaultValue: "No map available" }))}
            </div>
            <div className={styles.mapReviewHint}>
              {item.key === "candidate"
                ? t("gameProject.mapBuildCandidateRoleHint", {
                    defaultValue: "Suggested structure only. It is never formal knowledge by itself.",
                  })
                : item.key === "formal"
                  ? t("gameProject.formalMapRoleHint", {
                      defaultValue: "Saved by explicit admin action only. It does not auto-build or auto-publish release.",
                    })
                  : t("gameProject.releaseMapRoleHint", {
                      defaultValue: "Published snapshot only. It is not the editing source for map review.",
                    })}
            </div>
          </div>
        ))}
      </div>

      {!selectedAgent ? (
        <Alert
          type="info"
          showIcon
          message={t("gameProject.noSelectedAgent", { defaultValue: "Select an Agent to load the map workspace." })}
          className={styles.mapReviewAlert}
        />
      ) : null}

      {candidateReadReason ? (
        <Alert
          type="info"
          showIcon
          message={candidateReadReason}
          className={styles.mapReviewAlert}
        />
      ) : null}

      {candidateWriteReason ? (
        <Alert
          type="info"
          showIcon
          message={candidateWriteReason}
          className={styles.mapReviewAlert}
        />
      ) : null}

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
            <Text strong>{t("gameProject.mapBuildCandidateTitle", { defaultValue: "Candidate Map Review" })}</Text>
            <Space size={8} wrap>
              {sourceCandidateResult?.candidate_source ? <Tag color="blue">{sourceCandidateResult.candidate_source}</Tag> : null}
              {typeof sourceCandidateResult?.uses_existing_formal_map_as_hint === "boolean" ? (
                <Tag color={sourceCandidateResult.uses_existing_formal_map_as_hint ? "gold" : "default"}>
                  {sourceCandidateResult.uses_existing_formal_map_as_hint
                    ? t("gameProject.formalHintUsedTag", { defaultValue: "formal map used as hint" })
                    : t("gameProject.formalHintSkippedTag", { defaultValue: "formal map hint skipped" })}
                </Tag>
              ) : null}
              {sourceCandidateResult ? (
                <Tag color={sourceCandidateResult.is_formal_map ? "error" : "default"}>
                  {sourceCandidateResult.is_formal_map
                    ? t("gameProject.mapBuildFormalTag", { defaultValue: "formal" })
                    : t("gameProject.mapBuildCandidateTag", { defaultValue: "candidate only" })}
                </Tag>
              ) : null}
            </Space>
          </div>

          {sourceCandidateLoading ? (
            <div className={styles.mapReviewEmpty}>{t("common.loading")}</div>
          ) : sourceCandidateError ? (
            <Alert
              type="warning"
              showIcon
              message={t("gameProject.mapBuildReviewWarning", { defaultValue: "Candidate review is temporarily unavailable" })}
              description={sourceCandidateError}
              className={styles.mapReviewAlert}
            />
          ) : !sourceCandidateResult ? (
            <Alert
              type="info"
              showIcon
              message={t("gameProject.mapBuildReviewStartTitle", { defaultValue: "Build a candidate review from source" })}
              description={t("gameProject.mapBuildReviewStartDescription", {
                defaultValue: "This reads canonical facts only, compares Candidate Map against Formal Map or Release Map, and waits for explicit admin save before any formal change.",
              })}
              className={styles.mapReviewAlert}
            />
          ) : !sourceCandidateResult.map ? (
            <Alert
              type="info"
              showIcon
              message={t("gameProject.mapBuildNoCanonicalFactsTitle", { defaultValue: "No canonical facts available" })}
              description={
                sourceCandidateResult.warnings.length > 0
                  ? sourceCandidateResult.warnings.join(" ")
                  : t("gameProject.mapBuildNoCanonicalFactsDescription", {
                      defaultValue: "Generate canonical facts first, then build a candidate review again.",
                    })
              }
              className={styles.mapReviewAlert}
            />
          ) : (
            <>
              <div className={styles.mapReviewMetaSummary}>
                <div>candidate_source: {sourceCandidateResult.candidate_source}</div>
                <div>is_formal_map: {String(sourceCandidateResult.is_formal_map)}</div>
                <div>uses_existing_formal_map_as_hint: {String(sourceCandidateResult.uses_existing_formal_map_as_hint ?? false)}</div>
                <div>base_map_source: {sourceCandidateResult.diff_review?.base_map_source || "none"}</div>
              </div>
              {sourceCandidateResult.warnings.length > 0 ? (
                <Alert
                  type="warning"
                  showIcon
                  message={t("gameProject.mapBuildWarningsTitle", { defaultValue: "Candidate review warnings" })}
                  description={
                    <div className={styles.mapReviewWarningList}>
                      {sourceCandidateResult.warnings.map((warning) => (
                        <div key={warning}>{warning}</div>
                      ))}
                    </div>
                  }
                  className={styles.mapReviewAlert}
                />
              ) : null}
              <div className={styles.mapReviewCounts}>
                <Tag color="blue">systems {candidateSummary.systems}</Tag>
                <Tag color="gold">tables {candidateSummary.tables}</Tag>
                <Tag color="green">docs {candidateSummary.docs}</Tag>
                <Tag color="purple">scripts {candidateSummary.scripts}</Tag>
                <Tag color="cyan">relationships {candidateSummary.relationships}</Tag>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapBuildDiffReviewTitle", { defaultValue: "Diff Review" })}</Text>
                <div className={styles.mapReviewDiffGrid}>
                  {renderDiffReviewSection(
                    t("gameProject.mapBuildDiffAddedTitle", { defaultValue: "added_refs" }),
                    diffReviewSections[0]?.refs || [],
                    t("gameProject.mapBuildDiffAddedEmpty", { defaultValue: "No added refs" }),
                  )}
                  {renderDiffReviewSection(
                    t("gameProject.mapBuildDiffRemovedTitle", { defaultValue: "removed_refs" }),
                    diffReviewSections[1]?.refs || [],
                    t("gameProject.mapBuildDiffRemovedEmpty", { defaultValue: "No removed refs" }),
                  )}
                  {renderDiffReviewSection(
                    t("gameProject.mapBuildDiffChangedTitle", { defaultValue: "changed_refs" }),
                    diffReviewSections[2]?.refs || [],
                    t("gameProject.mapBuildDiffChangedEmpty", { defaultValue: "No changed refs" }),
                  )}
                  {renderDiffReviewSection(
                    t("gameProject.mapBuildDiffUnchangedTitle", { defaultValue: "unchanged_refs" }),
                    diffReviewSections[3]?.refs || [],
                    t("gameProject.mapBuildDiffUnchangedEmpty", { defaultValue: "No unchanged refs" }),
                  )}
                </div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapSystemsTitle", { defaultValue: "Systems" })}</Text>
                <div className={styles.mapReviewList}>{renderSystemList(sourceCandidateResult.map.systems)}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapTablesTitle", { defaultValue: "Tables" })}</Text>
                <div className={styles.mapReviewList}>{renderTableList(sourceCandidateResult.map.tables)}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapDocsTitle", { defaultValue: "Docs" })}</Text>
                <div className={styles.mapReviewList}>{renderDocList(sourceCandidateResult.map.docs)}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapScriptsTitle", { defaultValue: "Scripts" })}</Text>
                <div className={styles.mapReviewList}>{renderScriptList(sourceCandidateResult.map.scripts)}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapRelationshipsTitle", { defaultValue: "Relationships" })}</Text>
                <div className={styles.mapReviewList}>{renderRelationshipList(sourceCandidateResult.map.relationships)}</div>
              </div>
            </>
          )}
        </div>

        <div className={styles.mapReviewPanel}>
          <div className={styles.mapReviewPanelHeader}>
            <Text strong>{t("gameProject.formalMapTitle", { defaultValue: "Formal Map" })}</Text>
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

          <div className={styles.mapReviewHint}>
            {t("gameProject.formalMapReviewBoundaryHint", {
              defaultValue: "Formal Map changes persist only after explicit save. They do not auto-build, auto-publish, or set current release.",
            })}
          </div>

          {mapReadReason ? (
            <Alert type="info" showIcon message={mapReadReason} className={styles.mapReviewAlert} />
          ) : formalMapLoading ? (
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
                defaultValue: "Use Save Candidate as Formal Map first. Status editing is available only on saved formal map.",
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
                <Tag color="blue">systems {formalSummary.systems}</Tag>
                <Tag color="gold">tables {formalSummary.tables}</Tag>
                <Tag color="green">docs {formalSummary.docs}</Tag>
                <Tag color="purple">scripts {formalSummary.scripts}</Tag>
                <Tag color="cyan">relationships {formalSummary.relationships}</Tag>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapSystemsTitle", { defaultValue: "Systems" })}</Text>
                <div className={styles.mapReviewList}>{renderSystemList(formalMapDraft?.systems ?? [], {
                  editable: true,
                  statusControlDisabled: !canEditFormalMapStatuses,
                  statusControlDisabledReason: statusEditDisabledReason,
                  onStatusChange: (systemId, nextStatus) => updateFormalMapDraftStatus("systems", systemId, nextStatus),
                })}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapTablesTitle", { defaultValue: "Tables" })}</Text>
                <div className={styles.mapReviewList}>{renderTableList(formalMapDraft?.tables ?? [], {
                  editable: true,
                  statusControlDisabled: !canEditFormalMapStatuses,
                  statusControlDisabledReason: statusEditDisabledReason,
                  onStatusChange: (tableId, nextStatus) => updateFormalMapDraftStatus("tables", tableId, nextStatus),
                })}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapDocsTitle", { defaultValue: "Docs" })}</Text>
                <div className={styles.mapReviewList}>{renderDocList(formalMapDraft?.docs ?? [], {
                  editable: true,
                  statusControlDisabled: !canEditFormalMapStatuses,
                  statusControlDisabledReason: statusEditDisabledReason,
                  onStatusChange: (docId, nextStatus) => updateFormalMapDraftStatus("docs", docId, nextStatus),
                })}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapScriptsTitle", { defaultValue: "Scripts" })}</Text>
                <div className={styles.mapReviewList}>{renderScriptList(formalMapDraft?.scripts ?? [], {
                  editable: true,
                  statusControlDisabled: !canEditFormalMapStatuses,
                  statusControlDisabledReason: statusEditDisabledReason,
                  onStatusChange: (scriptId, nextStatus) => updateFormalMapDraftStatus("scripts", scriptId, nextStatus),
                })}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapRelationshipsTitle", { defaultValue: "Relationships" })}</Text>
                <div className={styles.mapReviewList}>{renderRelationshipList(formalMapDraft?.relationships ?? [])}</div>
              </div>
            </>
          )}
        </div>

        <div className={styles.mapReviewPanel}>
          <div className={styles.mapReviewPanelHeader}>
            <Text strong>{t("gameProject.releaseMapTitle", { defaultValue: "Release Map" })}</Text>
            <Space size={8} wrap>
              {releaseSnapshotResult?.candidate_source ? <Tag color="cyan">{releaseSnapshotResult.candidate_source}</Tag> : null}
              {releaseSnapshotResult?.source_release_id || releaseSnapshotResult?.release_id ? (
                <Tag color="blue">release_id {releaseSnapshotResult?.source_release_id || releaseSnapshotResult?.release_id}</Tag>
              ) : null}
            </Space>
          </div>

          <div className={styles.mapReviewHint}>
            {t("gameProject.releaseMapReviewHint", {
              defaultValue: "Release Map is a published snapshot for review only. It is not used as the editing source for Map Build Review.",
            })}
          </div>

          {candidateReadReason ? (
            <Alert type="info" showIcon message={candidateReadReason} className={styles.mapReviewAlert} />
          ) : releaseSnapshotLoading ? (
            <div className={styles.mapReviewEmpty}>{t("common.loading")}</div>
          ) : releaseSnapshotError ? (
            <Alert
              type={releaseSnapshotError === NO_CURRENT_RELEASE_DETAIL ? "info" : "warning"}
              showIcon
              message={
                releaseSnapshotError === NO_CURRENT_RELEASE_DETAIL
                  ? t("gameProject.mapCandidateNoCurrentTitle", { defaultValue: "No current knowledge release" })
                  : t("gameProject.mapReleaseSnapshotWarning", { defaultValue: "Release map snapshot is temporarily unavailable" })
              }
              description={
                releaseSnapshotError === NO_CURRENT_RELEASE_DETAIL
                  ? t("gameProject.mapCandidateNoCurrentDescription", {
                      defaultValue: "Set a current release first if you want to compare against a release snapshot.",
                    })
                  : releaseSnapshotError
              }
              className={styles.mapReviewAlert}
            />
          ) : !releaseSnapshotResult?.map ? (
            <div className={styles.mapReviewEmpty}>{t("gameProject.releaseMapSummaryEmpty", { defaultValue: "No release map snapshot available" })}</div>
          ) : (
            <>
              <div className={styles.mapReviewMetaSummary}>
                <div>candidate_source: {releaseSnapshotResult.candidate_source}</div>
                <div>is_formal_map: {String(releaseSnapshotResult.is_formal_map)}</div>
                <div>source_release_id: {releaseSnapshotResult.source_release_id || releaseSnapshotResult.release_id || "-"}</div>
              </div>
              <div className={styles.mapReviewCounts}>
                <Tag color="blue">systems {releaseSummary.systems}</Tag>
                <Tag color="gold">tables {releaseSummary.tables}</Tag>
                <Tag color="green">docs {releaseSummary.docs}</Tag>
                <Tag color="purple">scripts {releaseSummary.scripts}</Tag>
                <Tag color="cyan">relationships {releaseSummary.relationships}</Tag>
              </div>
              {releaseSnapshotResult.warnings.length > 0 ? (
                <Alert
                  type="warning"
                  showIcon
                  message={t("gameProject.releaseMapWarningsTitle", { defaultValue: "Release snapshot warnings" })}
                  description={
                    <div className={styles.mapReviewWarningList}>
                      {releaseSnapshotResult.warnings.map((warning) => (
                        <div key={warning}>{warning}</div>
                      ))}
                    </div>
                  }
                  className={styles.mapReviewAlert}
                />
              ) : null}
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapSystemsTitle", { defaultValue: "Systems" })}</Text>
                <div className={styles.mapReviewList}>{renderSystemList(releaseSnapshotResult.map.systems)}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapTablesTitle", { defaultValue: "Tables" })}</Text>
                <div className={styles.mapReviewList}>{renderTableList(releaseSnapshotResult.map.tables)}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapDocsTitle", { defaultValue: "Docs" })}</Text>
                <div className={styles.mapReviewList}>{renderDocList(releaseSnapshotResult.map.docs)}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapScriptsTitle", { defaultValue: "Scripts" })}</Text>
                <div className={styles.mapReviewList}>{renderScriptList(releaseSnapshotResult.map.scripts)}</div>
              </div>
              <div className={styles.mapReviewBlock}>
                <Text strong>{t("gameProject.mapRelationshipsTitle", { defaultValue: "Relationships" })}</Text>
                <div className={styles.mapReviewList}>{renderRelationshipList(releaseSnapshotResult.map.relationships)}</div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
