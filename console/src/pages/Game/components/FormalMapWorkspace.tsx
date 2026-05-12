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
  KnowledgeRelationship,
  KnowledgeScriptRef,
  KnowledgeStatus,
  KnowledgeSystem,
  KnowledgeTableRef,
} from "../../../api/types/game";
import { useAgentStore } from "../../../stores/agentStore";
import styles from "../GameProject.module.less";

const { Text } = Typography;

const NO_CURRENT_RELEASE_DETAIL = "No current knowledge release is set";
const LOCAL_PROJECT_DIRECTORY_ERROR = "Local project directory not configured";
const NO_FORMAL_MAP_MODE = "no_formal_map";
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
  const canReadMap = canUseGovernanceAction(capabilities, "knowledge.map.read");
  const canEditMap = canUseGovernanceAction(capabilities, "knowledge.map.edit");

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

  const fetchCandidateMap = useCallback(
    async (agentId: string) => {
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

  const fetchMapReviewData = useCallback(
    async (agentId: string) => {
      await Promise.all([fetchCandidateMap(agentId), fetchFormalMap(agentId)]);
    },
    [fetchCandidateMap, fetchFormalMap],
  );

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
  const savedFormalSummary = summarizeMap(savedFormalMap);
  const formalSummary = summarizeMap(formalMapDraft);
  const hasCandidateMapSummary = !!candidateMap && !candidateMapError;
  const hasFormalMapSummary = !!savedFormalMap && !formalMapError;
  const formalMapDraftDirty =
    !!savedFormalMap && !!formalMapDraft && JSON.stringify(formalMapDraft) !== JSON.stringify(savedFormalMap);
  const formalMapRelationshipWarnings = buildRelationshipWarningMessages(formalMapDraft);
  const saveFormalMapFirstReason = !savedFormalMap
    ? t("gameProject.formalMapSaveFirstBeforeEdit", {
        defaultValue: "Save a formal map first before editing statuses.",
      })
    : null;
  const saveFormalMapDisabledReason = mapReadReason || mapEditReason || null;
  const canSaveFormalMap =
    !!selectedAgent && !!candidateMap && (!hasExplicitCapabilityContext || (canReadMap && canEditMap));
  const statusEditDisabledReason = mapEditReason || saveFormalMapFirstReason;
  const canEditFormalMapStatuses =
    !!savedFormalMap && (!hasExplicitCapabilityContext || (canReadMap && canEditMap));
  const canSaveFormalMapDraft =
    !!selectedAgent && !!formalMapDraft && formalMapDraftDirty && canEditFormalMapStatuses;

  useEffect(() => {
    if (!selectedAgent) {
      setCandidateMap(null);
      setCandidateMapReleaseId(null);
      setCandidateMapError(null);
      setFormalMap(null);
      setFormalMapDraft(null);
      setFormalMapError(null);
      setCandidateMapLoading(false);
      setFormalMapLoading(false);
      return;
    }

    if (hasExplicitCapabilityContext && !canReadMap) {
      setCandidateMap(null);
      setCandidateMapReleaseId(null);
      setCandidateMapError(null);
      setFormalMap(null);
      setFormalMapDraft(null);
      setFormalMapError(null);
      setCandidateMapLoading(false);
      setFormalMapLoading(false);
      return;
    }

    void fetchMapReviewData(selectedAgent);
  }, [canReadMap, fetchMapReviewData, hasExplicitCapabilityContext, selectedAgent]);

  useEffect(() => {
    setFormalMapDraft(savedFormalMap ? cloneKnowledgeMap(savedFormalMap) : null);
  }, [savedFormalMap]);

  const renderSummaryText = (
    summary: ReturnType<typeof summarizeMap>,
    fallback: string,
  ) =>
    summary.systems.length || summary.tables.length || summary.docs.length || summary.scripts.length || summary.relationships.length
      ? t("gameProject.formalMapCompactCounts", {
          defaultValue: "{{systems}} systems / {{tables}} tables / {{docs}} docs / {{scripts}} scripts / {{relationships}} relationships",
          systems: summary.systems.length,
          tables: summary.tables.length,
          docs: summary.docs.length,
          scripts: summary.scripts.length,
          relationships: summary.relationships.length,
        })
      : fallback;

  if (mode === "summary") {
    return (
      <>
        <div className={styles.mapReviewTransitionLead}>
          <Text strong>
            {t("gameProject.formalMapWorkspaceLead", {
              defaultValue: "Formal map review and save flows now live on the dedicated Map Editor page.",
            })}
          </Text>
          <div className={styles.mapReviewHint}>
            {t("gameProject.formalMapWorkspaceSummaryHint", {
              defaultValue:
                "Project keeps only a compact candidate and saved-map summary. Save-as-formal-map and status-only edits remain unchanged, but now run in Map Editor.",
            })}
          </div>
        </div>

        {mapReadReason ? (
          <Alert type="info" showIcon message={mapReadReason} className={styles.mapReviewAlert} />
        ) : null}

        <div className={styles.mapReviewCompactSummary}>
          <div className={styles.mapReviewCompactItem}>
            <Text type="secondary">{t("gameProject.mapCandidateTitle", { defaultValue: "Candidate map" })}</Text>
            <div className={styles.mapReviewCompactValue}>
              {hasCandidateMapSummary
                ? renderSummaryText(
                    candidateSummary,
                    t("gameProject.mapCandidateEmpty", { defaultValue: "No candidate map available" }),
                  )
                : candidateMapLoading
                  ? t("common.loading")
                  : candidateMapError || t("gameProject.mapCandidateEmpty", { defaultValue: "No candidate map available" })}
            </div>
            <div className={styles.mapReviewHint}>
              {candidateMapReleaseId
                ? `release_id: ${candidateMapReleaseId}`
                : t("gameProject.mapCandidateSummaryNoRelease", {
                    defaultValue: "No current release id available.",
                  })}
            </div>
          </div>
          <div className={styles.mapReviewCompactItem}>
            <Text type="secondary">{t("gameProject.formalMapTitle", { defaultValue: "Saved formal map" })}</Text>
            <div className={styles.mapReviewCompactValue}>
              {hasFormalMapSummary
                ? renderSummaryText(
                    savedFormalSummary,
                    t("gameProject.noSavedFormalMapTitle", { defaultValue: "no saved formal map" }),
                  )
                : formalMapLoading
                  ? t("common.loading")
                  : formalMapError || t("gameProject.noSavedFormalMapTitle", { defaultValue: "no saved formal map" })}
            </div>
            <div className={styles.mapReviewHint}>
              {formalMap?.map_hash
                ? `map_hash: ${formalMap.map_hash}`
                : t("gameProject.formalMapSummaryNoHash", {
                    defaultValue: "No saved formal map hash available.",
                  })}
            </div>
          </div>
        </div>

        <div className={styles.mapReviewTransitionActions}>
          <Button size="small" type="primary" onClick={() => navigate("/game/map")}>
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
        </div>
      </>
    );
  }

  return (
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
        <Space size={8} wrap>
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

      <div className={styles.mapReviewHint}>
        {t("gameProject.mapEditorPrimaryHint", {
          defaultValue:
            "Map Editor owns candidate review, saved formal map review, save-as-formal-map, status-only edits, and relationship warnings in G.4.",
        })}
      </div>

      {!selectedAgent ? (
        <Alert
          type="info"
          showIcon
          message={t("gameProject.noSelectedAgent", { defaultValue: "Select an Agent to load the map workspace." })}
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
  );
}