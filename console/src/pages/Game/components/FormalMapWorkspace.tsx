import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  AlertOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  NodeIndexOutlined,
  RightOutlined,
  ApartmentOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { Alert, Button, Drawer, Empty, Select, Space, Tabs, Tag, Tooltip, Typography } from "antd";
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

type MapTabKey = "candidate" | "formal" | "release" | "warnings";

type DetailDrawerState = {
  title: string;
  subtitle?: string;
  lines: Array<{ label: string; value: string }>;
};

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

  for (const item of map.systems) appendWarning(`system:${item.system_id}`, item.title, item.status);
  for (const item of map.tables) appendWarning(`table:${item.table_id}`, item.title, item.status);
  for (const item of map.docs) appendWarning(`doc:${item.doc_id}`, item.title, item.status);
  for (const item of map.scripts) appendWarning(`script:${item.script_id}`, item.title, item.status);

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
  const [activeMapTab, setActiveMapTab] = useState<MapTabKey>("candidate");
  const [detailDrawer, setDetailDrawer] = useState<DetailDrawerState | null>(null);
  const [expandedDiffKeys, setExpandedDiffKeys] = useState<Record<string, boolean>>({});

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
    (error: unknown, fallbackMessage: string) => (error instanceof Error ? error.message : fallbackMessage),
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
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
  };

  const formatStatusLabel = (value: KnowledgeStatus) =>
    t(`gameWorkspaceUi.map.statusValues.${value}`, { defaultValue: value });

  const fetchReleaseSnapshot = useCallback(
    async (agentId: string) => {
      setReleaseSnapshotLoading(true);
      setReleaseSnapshotError(null);
      try {
        setReleaseSnapshotResult(await gameKnowledgeReleaseApi.getMapCandidate(agentId));
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
        setFormalMap(await gameKnowledgeReleaseApi.getFormalMap(agentId));
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
        setSourceCandidateResult(await gameKnowledgeReleaseApi.getLatestSourceCandidate(agentId));
      } catch (err) {
        const messageText = resolveMapLoadError(
          err,
          t("gameProject.mapBuildReviewFailed", {
            defaultValue: "Failed to load source candidate review",
          }),
        );
        setSourceCandidateResult(null);
        setSourceCandidateError(messageText.includes(NO_SOURCE_CANDIDATE_DETAIL) ? null : messageText);
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
      setActiveMapTab("formal");
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
  const formalSummary = summarizeKnowledgeMap(formalMapDraft);
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
    void fetchMapReviewData(selectedAgent);
  }, [fetchMapReviewData, selectedAgent]);

  useEffect(() => {
    setFormalMapDraft(savedFormalMap ? cloneKnowledgeMap(savedFormalMap) : null);
  }, [savedFormalMap]);

  const openDetailDrawer = (title: string, subtitle: string, lines: Array<{ label: string; value: string }>) => {
    setDetailDrawer({ title, subtitle, lines });
  };

  const renderNumberBadge = (value: number) => <span className={styles.mapWorkspaceSectionNumber}>{value}</span>;

  const renderStatusCard = (options: {
    icon: ReactNode;
    label: string;
    value: string;
    detail: string;
  }) => (
    <div className={styles.mapWorkspaceStatusCard}>
      <div className={styles.mapWorkspaceStatusIcon}>{options.icon}</div>
      <div className={styles.mapWorkspaceStatusContent}>
        <span className={styles.mapWorkspaceStatusLabel}>{options.label}</span>
        <strong className={styles.mapWorkspaceStatusValue}>{options.value}</strong>
        <small className={styles.mapWorkspaceStatusMeta}>{options.detail}</small>
      </div>
      <RightOutlined className={styles.mapWorkspaceStatusArrow} />
    </div>
  );

  const renderMetricCard = (label: string, value: string | number, detail?: string) => (
    <div className={styles.metricItem}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <span>{detail}</span> : null}
    </div>
  );

  const renderEntitySection = <T extends KnowledgeSystem | KnowledgeTableRef | KnowledgeDocRef | KnowledgeScriptRef>(
    title: string,
    typeLabel: string,
    items: T[],
    options: {
      getId: (item: T) => string;
      getLines: (item: T) => Array<{ label: string; value: string }>;
      editable?: boolean;
      onStatusChange?: (id: string, status: KnowledgeStatus) => void;
      statusDisabled?: boolean;
      statusDisabledReason?: string | null;
    },
  ) => (
    <div className={styles.mapWorkspaceSection}>
      <div className={styles.mapWorkspaceSectionHeader}>
        <Text strong>{title}</Text>
        <Text type="secondary">{t("common.total", { count: items.length })}</Text>
      </div>
      {items.length > 0 ? (
        <div className={styles.mapWorkspaceEntityList}>
          {items.map((item) => {
            const itemId = options.getId(item);
            return (
              <div key={itemId} className={styles.mapWorkspaceEntityRow}>
                <div className={styles.mapWorkspaceEntityMain}>
                  <Text strong>{item.title}</Text>
                  <div className={styles.mapWorkspaceEntityMeta}>
                    <span>{typeLabel}</span>
                    <span>
                      {t("gameWorkspaceUi.map.labels.status", { defaultValue: "状态" })}: {formatStatusLabel(item.status)}
                    </span>
                  </div>
                </div>
                <div className={styles.mapWorkspaceEntityActions}>
                  {options.editable && options.onStatusChange ? (
                    <Tooltip title={options.statusDisabledReason || undefined}>
                      <span className={styles.mapReviewStatusControlWrap}>
                        <Select
                          size="small"
                          value={item.status}
                          options={FORMAL_MAP_STATUS_OPTIONS.map((option) => ({
                            value: option.value,
                            label: formatStatusLabel(option.label),
                          }))}
                          onChange={(nextValue) => options.onStatusChange?.(itemId, nextValue as KnowledgeStatus)}
                          disabled={!!options.statusDisabled}
                          className={styles.mapReviewStatusSelect}
                        />
                      </span>
                    </Tooltip>
                  ) : null}
                  <Button
                    size="small"
                    onClick={() => openDetailDrawer(item.title, typeLabel, options.getLines(item))}
                  >
                    {t("gameWorkspaceUi.map.actions.viewDetails", { defaultValue: "查看详情" })}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={t("gameWorkspaceUi.map.emptySection", { defaultValue: "当前没有可显示的内容。" })}
        />
      )}
    </div>
  );

  const renderDiffGroup = (groupKey: string, title: string, refs: string[]) => {
    const expanded = !!expandedDiffKeys[groupKey];
    const visibleRefs = expanded ? refs : refs.slice(0, 5);
    return (
      <div className={styles.mapWorkspaceDiffCard}>
        <div className={styles.mapWorkspaceSectionHeader}>
          <Text strong>{title}</Text>
          <Text type="secondary">{t("common.total", { count: refs.length })}</Text>
        </div>
        {refs.length > 0 ? (
          <>
            <div className={styles.mapWorkspaceRefList}>
              {visibleRefs.map((ref) => (
                <Tag key={ref}>{ref}</Tag>
              ))}
            </div>
            {refs.length > 5 ? (
              <Button
                size="small"
                type="link"
                onClick={() =>
                  setExpandedDiffKeys((current) => ({ ...current, [groupKey]: !current[groupKey] }))
                }
              >
                {expanded
                  ? t("gameWorkspaceUi.map.actions.collapseChanges", { defaultValue: "收起" })
                  : t("gameWorkspaceUi.map.actions.expandChanges", {
                      count: refs.length,
                      defaultValue: "查看全部 {{count}} 项变更",
                    })}
              </Button>
            ) : null}
          </>
        ) : (
          <div className={styles.mapReviewEmpty}>
            {t("gameWorkspaceUi.map.emptyChanges", { defaultValue: "暂无变更。" })}
          </div>
        )}
      </div>
    );
  };

  if (mode === "summary") {
    return (
      <div className={styles.mapWorkspaceSummaryShell}>
        <div className={styles.mapWorkspaceSummaryLead}>
          <Text strong>{t("gameWorkspaceUi.map.summary.title", { defaultValue: "Map 编辑器现在独立承担地图决策。" })}</Text>
          <div className={styles.mapReviewHint}>
            {t("gameWorkspaceUi.map.summary.hint", {
              defaultValue: "候选地图、正式地图、发布快照和关系警告已经迁移到独立页面查看。",
            })}
          </div>
        </div>
        <div className={styles.mapWorkspaceStatusGrid}>
          {artifactStates.map((item) => (
            <div key={item.key} className={styles.mapWorkspaceStatusCard}>
              <span>{item.key}</span>
              <strong>{item.summary.systems + item.summary.tables + item.summary.relationships}</strong>
              <small>{item.source}</small>
            </div>
          ))}
        </div>
        <Button type="primary" onClick={() => navigate("/game/map")}>
          {t("gameProject.openMapEditorWorkspaceButton", { defaultValue: "Open Map Editor" })}
        </Button>
      </div>
    );
  }

  const candidateTab = (
    <div className={styles.mapWorkspaceTabGrid}>
      <div className={styles.mapWorkspacePanel}>
        <div className={styles.mapWorkspaceSectionHeader}>
          <div className={styles.mapWorkspaceSectionTitleGroup}>
            {renderNumberBadge(1)}
            <Text strong>{t("gameWorkspaceUi.map.candidate.overview", { defaultValue: "候选地图概览" })}</Text>
          </div>
          <Space size={8} wrap>
            {sourceCandidateResult?.candidate_source ? <Tag>{sourceCandidateResult.candidate_source}</Tag> : null}
            {sourceCandidateResult?.uses_existing_formal_map_as_hint ? (
              <Tag>{t("gameWorkspaceUi.map.candidate.formalHintUsed", { defaultValue: "使用正式地图提示" })}</Tag>
            ) : null}
          </Space>
        </div>
        {sourceCandidateLoading ? <div className={styles.mapReviewEmpty}>{t("common.loading")}</div> : null}
        {sourceCandidateError ? (
          <Alert type="warning" showIcon message={sourceCandidateError} className={styles.mapReviewAlert} />
        ) : null}
        <div className={styles.mapWorkspaceBlockLabel}>{t("gameWorkspaceUi.map.labels.contentStats", { defaultValue: "内容统计" })}</div>
        <div className={styles.mapWorkspaceMetricGrid}>
          {renderMetricCard(t("gameWorkspaceUi.map.labels.systems", { defaultValue: "系统" }), candidateSummary.systems)}
          {renderMetricCard(t("gameWorkspaceUi.map.labels.tables", { defaultValue: "表格" }), candidateSummary.tables)}
          {renderMetricCard(t("gameWorkspaceUi.map.labels.docs", { defaultValue: "文档" }), candidateSummary.docs)}
          {renderMetricCard(t("gameWorkspaceUi.map.labels.scripts", { defaultValue: "脚本" }), candidateSummary.scripts)}
          {renderMetricCard(t("gameWorkspaceUi.map.labels.relationships", { defaultValue: "关系" }), candidateSummary.relationships)}
        </div>
        <div className={styles.mapWorkspaceBlockLabel}>{t("gameWorkspaceUi.map.labels.changeSummary", { defaultValue: "变更摘要" })}</div>
        <div className={styles.mapWorkspaceMetricGridCompact}>
          {renderMetricCard(t("gameWorkspaceUi.map.labels.added", { defaultValue: "新增" }), diffReviewSections[0]?.refs.length || 0)}
          {renderMetricCard(t("gameWorkspaceUi.map.labels.removed", { defaultValue: "删除" }), diffReviewSections[1]?.refs.length || 0)}
          {renderMetricCard(t("gameWorkspaceUi.map.labels.changed", { defaultValue: "变更" }), diffReviewSections[2]?.refs.length || 0)}
        </div>
        <div className={styles.mapWorkspaceFooterMeta}>
          <span>{t("gameWorkspaceUi.map.labels.generatedAt", { defaultValue: "生成时间" })}: -</span>
          <span>{t("gameWorkspaceUi.map.labels.candidateSource", { defaultValue: "来源" })}: {sourceCandidateResult?.candidate_source || "-"}</span>
        </div>
      </div>
      <div className={styles.mapWorkspacePanel}>
        <div className={styles.mapWorkspaceSectionHeader}>
          <div className={styles.mapWorkspaceSectionTitleGroup}>
            {renderNumberBadge(2)}
            <Text strong>{t("gameWorkspaceUi.map.candidate.diff", { defaultValue: "差异详情" })}</Text>
          </div>
          <Select
            size="small"
            value="type"
            disabled
            options={[{ value: "type", label: t("gameWorkspaceUi.map.actions.filterByType", { defaultValue: "按类型筛选" }) }]}
            className={styles.mapWorkspaceFilterSelect}
          />
        </div>
        <div className={styles.mapWorkspaceDiffColumn}>
          {renderDiffGroup("added", t("gameWorkspaceUi.map.labels.added", { defaultValue: "新增" }), diffReviewSections[0]?.refs || [])}
          {renderDiffGroup("removed", t("gameWorkspaceUi.map.labels.removed", { defaultValue: "删除" }), diffReviewSections[1]?.refs || [])}
          {renderDiffGroup("changed", t("gameWorkspaceUi.map.labels.changed", { defaultValue: "变更" }), diffReviewSections[2]?.refs || [])}
        </div>
      </div>
      <div className={styles.mapWorkspacePanel}>
        <div className={styles.mapWorkspaceSectionHeader}>
          <div className={styles.mapWorkspaceSectionTitleGroup}>
            {renderNumberBadge(3)}
            <Text strong>{t("gameWorkspaceUi.map.candidate.warningsPreview", { defaultValue: "冲突与警告（预览）" })}</Text>
          </div>
          <Button size="small" type="link" onClick={() => setActiveMapTab("warnings")}>
            {t("gameWorkspaceUi.map.actions.openWarningsTab", { defaultValue: "查看全部" })}
          </Button>
        </div>
        {formalMapRelationshipWarnings.length > 0 ? (
          <div className={styles.mapWorkspaceWarningList}>
            {formalMapRelationshipWarnings.slice(0, 3).map((warning) => (
              <div key={warning} className={styles.mapWorkspaceWarningItem}>
                {warning}
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.mapReviewEmpty}>
            {t("gameWorkspaceUi.map.warnings.empty", { defaultValue: "暂无关系警告" })}
          </div>
        )}
      </div>
    </div>
  );

  const formalTab = (
    <div className={styles.mapWorkspacePanelStack}>
      {formalMapLoading ? <div className={styles.mapReviewEmpty}>{t("common.loading")}</div> : null}
      {formalMapError ? <Alert type="warning" showIcon message={formalMapError} className={styles.mapReviewAlert} /> : null}
      {formalMap?.mode === NO_FORMAL_MAP_MODE ? (
        <Alert
          type="info"
          showIcon
          message={t("gameWorkspaceUi.map.formal.noFormalMap", { defaultValue: "当前还没有正式地图，请先从候选地图保存。" })}
          className={styles.mapReviewAlert}
        />
      ) : null}
      {formalMapDraftDirty ? (
        <Alert
          type="warning"
          showIcon
          message={t("gameWorkspaceUi.map.formal.unsavedTitle", { defaultValue: "有未保存的状态修改。" })}
          action={
            <Space>
              <Button size="small" onClick={() => setFormalMapDraft(savedFormalMap ? cloneKnowledgeMap(savedFormalMap) : null)}>
                {t("gameWorkspaceUi.map.actions.discardDraft", { defaultValue: "放弃修改" })}
              </Button>
              <Button
                size="small"
                type="primary"
                onClick={handleSaveFormalMapDraft}
                loading={savingFormalMapDraft}
                disabled={!canSaveFormalMapDraft}
              >
                {t("gameWorkspaceUi.map.actions.saveDraft", { defaultValue: "保存状态修改" })}
              </Button>
            </Space>
          }
        />
      ) : null}
      {formalMapRelationshipWarnings.length > 0 ? (
        <Alert
          type="warning"
          showIcon
          message={t("gameWorkspaceUi.map.warnings.relationships", { defaultValue: "当前正式地图存在关系警告。" })}
          className={styles.mapReviewAlert}
        />
      ) : null}
      <div className={styles.mapWorkspaceMetricGrid}>
        {renderMetricCard(t("gameWorkspaceUi.map.labels.systems", { defaultValue: "系统" }), formalSummary.systems)}
        {renderMetricCard(t("gameWorkspaceUi.map.labels.tables", { defaultValue: "表格" }), formalSummary.tables)}
        {renderMetricCard(t("gameWorkspaceUi.map.labels.docs", { defaultValue: "文档" }), formalSummary.docs)}
        {renderMetricCard(t("gameWorkspaceUi.map.labels.scripts", { defaultValue: "脚本" }), formalSummary.scripts)}
        {renderMetricCard(t("gameWorkspaceUi.map.labels.relationships", { defaultValue: "关系" }), formalSummary.relationships)}
        {renderMetricCard(t("gameWorkspaceUi.map.labels.updatedAt", { defaultValue: "更新时间" }), formatDateTime(formalMap?.updated_at))}
      </div>
      {renderEntitySection(
        t("gameWorkspaceUi.map.sections.systems", { defaultValue: "系统" }),
        t("gameWorkspaceUi.map.labels.system", { defaultValue: "系统" }),
        formalMapDraft?.systems ?? [],
        {
          getId: (item) => item.system_id,
          getLines: (item) => [
            { label: "system_id", value: item.system_id },
            { label: "table_ids", value: item.table_ids.join(", ") || "-" },
            { label: "doc_ids", value: item.doc_ids.join(", ") || "-" },
            { label: "script_ids", value: item.script_ids.join(", ") || "-" },
          ],
          editable: true,
          onStatusChange: (id, status) => updateFormalMapDraftStatus("systems", id, status),
          statusDisabled: !canEditFormalMapStatuses,
          statusDisabledReason: mapEditReason || saveFormalMapFirstReason,
        },
      )}
      {renderEntitySection(
        t("gameWorkspaceUi.map.sections.tables", { defaultValue: "表格" }),
        t("gameWorkspaceUi.map.labels.table", { defaultValue: "表格" }),
        formalMapDraft?.tables ?? [],
        {
          getId: (item) => item.table_id,
          getLines: (item) => [
            { label: "table_id", value: item.table_id },
            { label: "source_path", value: item.source_path },
            { label: "source_hash", value: item.source_hash },
            { label: "system_id", value: item.system_id || "-" },
          ],
          editable: true,
          onStatusChange: (id, status) => updateFormalMapDraftStatus("tables", id, status),
          statusDisabled: !canEditFormalMapStatuses,
          statusDisabledReason: mapEditReason || saveFormalMapFirstReason,
        },
      )}
      {renderEntitySection(
        t("gameWorkspaceUi.map.sections.docs", { defaultValue: "文档" }),
        t("gameWorkspaceUi.map.labels.doc", { defaultValue: "文档" }),
        formalMapDraft?.docs ?? [],
        {
          getId: (item) => item.doc_id,
          getLines: (item) => [
            { label: "doc_id", value: item.doc_id },
            { label: "source_path", value: item.source_path },
            { label: "source_hash", value: item.source_hash },
            { label: "system_id", value: item.system_id || "-" },
          ],
          editable: true,
          onStatusChange: (id, status) => updateFormalMapDraftStatus("docs", id, status),
          statusDisabled: !canEditFormalMapStatuses,
          statusDisabledReason: mapEditReason || saveFormalMapFirstReason,
        },
      )}
      {renderEntitySection(
        t("gameWorkspaceUi.map.sections.scripts", { defaultValue: "脚本" }),
        t("gameWorkspaceUi.map.labels.script", { defaultValue: "脚本" }),
        formalMapDraft?.scripts ?? [],
        {
          getId: (item) => item.script_id,
          getLines: (item) => [
            { label: "script_id", value: item.script_id },
            { label: "source_path", value: item.source_path },
            { label: "source_hash", value: item.source_hash },
            { label: "system_id", value: item.system_id || "-" },
          ],
          editable: true,
          onStatusChange: (id, status) => updateFormalMapDraftStatus("scripts", id, status),
          statusDisabled: !canEditFormalMapStatuses,
          statusDisabledReason: mapEditReason || saveFormalMapFirstReason,
        },
      )}
    </div>
  );

  const releaseTab = (
    <div className={styles.mapWorkspacePanelStack}>
      {releaseSnapshotLoading ? <div className={styles.mapReviewEmpty}>{t("common.loading")}</div> : null}
      {releaseSnapshotError ? (
        <Alert
          type={releaseSnapshotError === NO_CURRENT_RELEASE_DETAIL ? "info" : "warning"}
          showIcon
          message={releaseSnapshotError}
          className={styles.mapReviewAlert}
        />
      ) : null}
      {!releaseSnapshotLoading && !releaseSnapshotError && !releaseSnapshotResult?.map ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={t("gameWorkspaceUi.map.release.empty", { defaultValue: "暂无发布快照" })}
        />
      ) : null}
      {releaseSnapshotResult?.map ? (
        <>
          <div className={styles.mapWorkspaceMetricGrid}>
            {renderMetricCard(t("gameWorkspaceUi.map.labels.systems", { defaultValue: "系统" }), releaseSummary.systems)}
            {renderMetricCard(t("gameWorkspaceUi.map.labels.tables", { defaultValue: "表格" }), releaseSummary.tables)}
            {renderMetricCard(t("gameWorkspaceUi.map.labels.docs", { defaultValue: "文档" }), releaseSummary.docs)}
            {renderMetricCard(t("gameWorkspaceUi.map.labels.scripts", { defaultValue: "脚本" }), releaseSummary.scripts)}
            {renderMetricCard(t("gameWorkspaceUi.map.labels.relationships", { defaultValue: "关系" }), releaseSummary.relationships)}
            {renderMetricCard(
              t("gameWorkspaceUi.map.labels.releaseId", { defaultValue: "发布 ID" }),
              releaseSnapshotResult.source_release_id || releaseSnapshotResult.release_id || "-",
            )}
          </div>
          {renderEntitySection(
            t("gameWorkspaceUi.map.sections.systems", { defaultValue: "系统" }),
            t("gameWorkspaceUi.map.labels.system", { defaultValue: "系统" }),
            releaseSnapshotResult.map.systems,
            {
              getId: (item) => item.system_id,
              getLines: (item) => [
                { label: "system_id", value: item.system_id },
                { label: "status", value: formatStatusLabel(item.status) },
              ],
            },
          )}
          {renderEntitySection(
            t("gameWorkspaceUi.map.sections.tables", { defaultValue: "表格" }),
            t("gameWorkspaceUi.map.labels.table", { defaultValue: "表格" }),
            releaseSnapshotResult.map.tables,
            {
              getId: (item) => item.table_id,
              getLines: (item) => [
                { label: "table_id", value: item.table_id },
                { label: "source_path", value: item.source_path },
                { label: "source_hash", value: item.source_hash },
              ],
            },
          )}
        </>
      ) : null}
    </div>
  );

  const warningsTab = (
    <div className={styles.mapWorkspacePanelStack}>
      <div className={styles.mapWorkspacePanel}>
        <div className={styles.mapWorkspaceSectionHeader}>
          <Text strong>{t("gameWorkspaceUi.map.warnings.title", { defaultValue: "冲突与警告" })}</Text>
          <Text type="secondary">
            {t("gameWorkspaceUi.map.warnings.countHint", {
              count: formalMapRelationshipWarnings.length,
              defaultValue: `当前发现 ${formalMapRelationshipWarnings.length} 个问题`,
            })}
          </Text>
        </div>
        {formalMapRelationshipWarnings.length > 0 ? (
          <div className={styles.mapWorkspaceWarningList}>
            {formalMapRelationshipWarnings.map((warning) => (
              <div key={warning} className={styles.mapWorkspaceWarningItem}>
                {warning}
              </div>
            ))}
          </div>
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={t("gameWorkspaceUi.map.warnings.empty", { defaultValue: "暂无关系警告" })}
          />
        )}
      </div>
    </div>
  );

  return (
    <div className={styles.mapWorkspaceShell}>
      {!selectedAgent ? (
        <Alert
          type="info"
          showIcon
          message={t("gameProject.noSelectedAgent", { defaultValue: "Select an Agent to load the map workspace." })}
          className={styles.mapReviewAlert}
        />
      ) : null}
      {candidateReadReason ? <Alert type="info" showIcon message={candidateReadReason} className={styles.mapReviewAlert} /> : null}
      {mapReadReason ? <Alert type="info" showIcon message={mapReadReason} className={styles.mapReviewAlert} /> : null}

      <div className={styles.mapWorkspaceStatusGrid}>
        {renderStatusCard({
          icon: <NodeIndexOutlined />,
          label: t("gameWorkspaceUi.map.statusCards.candidate", { defaultValue: "Candidate Map" }),
          value: sourceCandidateResult?.map
            ? t("gameWorkspaceUi.map.states.pendingCandidate", { count: 1, defaultValue: "待确认 1" })
            : t("gameWorkspaceUi.map.states.missing", { defaultValue: "暂无" }),
          detail: sourceCandidateResult?.map
            ? t("gameWorkspaceUi.map.statusDetails.candidate", { defaultValue: "发现新的候选地图" })
            : t("gameWorkspaceUi.map.statusDetails.noCandidate", { defaultValue: "当前没有候选地图" }),
        })}
        {renderStatusCard({
          icon: <ApartmentOutlined />,
          label: t("gameWorkspaceUi.map.statusCards.formal", { defaultValue: "Formal Map" }),
          value: savedFormalMap
            ? t("gameWorkspaceUi.map.states.saved", { defaultValue: "已存在" })
            : t("gameWorkspaceUi.map.states.missing", { defaultValue: "暂无" }),
          detail: savedFormalMap
            ? t("gameWorkspaceUi.map.statusDetails.formal", {
                value: formatDateTime(formalMap?.updated_at),
                defaultValue: `上次更新：${formatDateTime(formalMap?.updated_at)}`,
              })
            : t("gameWorkspaceUi.map.statusDetails.noFormal", { defaultValue: "还没有正式地图" }),
        })}
        {renderStatusCard({
          icon: <ClockCircleOutlined />,
          label: t("gameWorkspaceUi.map.statusCards.release", { defaultValue: "Release Map" }),
          value: releaseSnapshotResult?.map
            ? t("gameWorkspaceUi.map.states.readonly", { defaultValue: "只读" })
            : t("gameWorkspaceUi.map.states.missing", { defaultValue: "暂无" }),
          detail: releaseSnapshotResult?.map
            ? t("gameWorkspaceUi.map.statusDetails.release", {
                value: releaseSnapshotResult?.source_release_id || releaseSnapshotResult?.release_id || "-",
                defaultValue: `快照：${releaseSnapshotResult?.source_release_id || releaseSnapshotResult?.release_id || "-"}`,
              })
            : t("gameWorkspaceUi.map.statusDetails.noRelease", { defaultValue: "当前没有发布快照" }),
        })}
        {renderStatusCard({
          icon: <AlertOutlined />,
          label: t("gameWorkspaceUi.map.statusCards.warnings", { defaultValue: "关系警告" }),
          value: String(formalMapRelationshipWarnings.length),
          detail: formalMapRelationshipWarnings.length > 0
            ? t("gameWorkspaceUi.map.statusDetails.warnings", { defaultValue: "需要关注的关系问题" })
            : t("gameWorkspaceUi.map.statusDetails.noWarnings", { defaultValue: "当前没有关系警告" }),
        })}
      </div>

      <div className={styles.mapWorkspaceRecommendation}>
        <div>
          <div className={styles.mapWorkspaceRecommendationLead}>
            <ExclamationCircleOutlined className={styles.mapWorkspaceRecommendationIcon} />
            <div>
              <Text strong>{t("gameWorkspaceUi.map.recommendation.title", { defaultValue: "发现新的候选地图，请先查看差异，再决定是否保存为正式地图。" })}</Text>
              <div className={styles.mapReviewHint}>
                {sourceCandidateResult?.map
                  ? t("gameWorkspaceUi.map.recommendation.hasCandidate", {
                      defaultValue: "候选地图包含了新的数据变更，建议先查看差异与冲突，再进行决策。",
                    })
                  : t("gameWorkspaceUi.map.recommendation.noCandidate", {
                      defaultValue: "当前没有新的候选地图，必要时重新从 source canonical 生成。",
                    })}
              </div>
            </div>
          </div>
        </div>
        <div className={styles.mapWorkspaceRecommendationActions}>
          <Button onClick={() => setActiveMapTab("candidate") }>
            {t("gameWorkspaceUi.map.actions.viewDiff", { defaultValue: "查看差异" })}
          </Button>
          <Tooltip title={saveFormalMapDisabledReason || undefined}>
            <span>
              <Button type="primary" onClick={handleSaveFormalMap} loading={savingFormalMap} disabled={!canSaveFormalMap}>
                {t("gameWorkspaceUi.map.actions.saveFormal", { defaultValue: "保存为正式地图" })}
              </Button>
            </span>
          </Tooltip>
          <Tooltip title={candidateWriteReason || undefined}>
            <span>
              <Button
                onClick={handleBuildSourceCandidate}
                loading={sourceCandidateLoading}
                disabled={!selectedAgent || !!candidateWriteReason}
              >
                {t("gameWorkspaceUi.map.actions.rebuildCandidate", { defaultValue: "重新生成候选地图" })}
              </Button>
            </span>
          </Tooltip>
        </div>
      </div>

      <Tabs
        className={styles.mapWorkspaceTabs}
        activeKey={activeMapTab}
        onChange={(nextKey) => setActiveMapTab(nextKey as MapTabKey)}
        tabBarExtraContent={
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={() => selectedAgent && fetchMapReviewData(selectedAgent)}
            loading={releaseSnapshotLoading || formalMapLoading || sourceCandidateLoading}
            disabled={!selectedAgent}
          >
            {t("common.refresh")}
          </Button>
        }
        items={[
          {
            key: "candidate",
            label: t("gameWorkspaceUi.map.tabs.candidate", { defaultValue: "候选地图" }),
            children: candidateTab,
          },
          {
            key: "formal",
            label: t("gameWorkspaceUi.map.tabs.formal", { defaultValue: "正式地图" }),
            children: formalTab,
          },
          {
            key: "release",
            label: t("gameWorkspaceUi.map.tabs.release", { defaultValue: "发布快照" }),
            children: releaseTab,
          },
          {
            key: "warnings",
            label: t("gameWorkspaceUi.map.tabs.warnings", { defaultValue: "冲突与警告" }),
            children: warningsTab,
          },
        ]}
      />

      <Drawer
        title={detailDrawer?.title || t("gameWorkspaceUi.map.labels.details", { defaultValue: "详情" })}
        open={!!detailDrawer}
        onClose={() => setDetailDrawer(null)}
        width={560}
        destroyOnHidden={false}
      >
        {detailDrawer ? (
          <div className={styles.drawerLayout}>
            {detailDrawer.subtitle ? <Text type="secondary">{detailDrawer.subtitle}</Text> : null}
            <div className={styles.drawerList}>
              {detailDrawer.lines.map((line) => (
                <div key={`${line.label}-${line.value}`} className={styles.drawerListItem}>
                  <Text strong>{line.label}</Text>
                  <div className={styles.drawerListDetail}>{line.value || "-"}</div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </Drawer>
    </div>
  );
}
