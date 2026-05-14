import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Col, Empty, Row, Space, Spin, Tag, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { gameApi } from "@/api/modules/game";
import { gameKnowledgeReleaseApi } from "@/api/modules/gameKnowledgeRelease";
import type { FrontendCapabilityToken } from "@/api/types/permissions";
import type {
  FormalKnowledgeMapResponse,
  GameStorageSummary,
  KnowledgeReleaseHistoryItem,
} from "@/api/types/game";
import { useAgentStore } from "@/stores/agentStore";
import { hasCapabilityContext, isPermissionDeniedError } from "@/utils/permissions";
import { buildAdminPanelActions, buildAdminStatusCards } from "../components/adminPanel";
import styles from "./Advanced.module.less";

const { Paragraph, Text, Title } = Typography;

function getReadableStatusError(error: unknown): string {
  if (isPermissionDeniedError(error)) {
    return "Some admin status fields are hidden by current capability settings.";
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return "Failed to load admin panel status.";
}

export default function AdvancedPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { selectedAgent, agents } = useAgentStore();
  const selectedAgentSummary = agents.find((agent) => agent.id === selectedAgent);
  const capabilities: FrontendCapabilityToken[] | undefined = selectedAgentSummary?.capabilities;
  const hasExplicitCapabilityContext = hasCapabilityContext(capabilities);

  const [storageSummary, setStorageSummary] = useState<GameStorageSummary | null>(null);
  const [currentRelease, setCurrentRelease] = useState<KnowledgeReleaseHistoryItem | null>(null);
  const [formalMap, setFormalMap] = useState<FormalKnowledgeMapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);

  useEffect(() => {
    let disposed = false;

    async function loadPanelStatus() {
      if (!selectedAgent) {
        return;
      }

      setLoading(true);
      setStatusError(null);

      const [storageResult, releaseResult, formalMapResult] = await Promise.allSettled([
        gameApi.getStorageSummary(selectedAgent),
        gameKnowledgeReleaseApi.getReleaseStatus(selectedAgent),
        gameKnowledgeReleaseApi.getFormalMap(selectedAgent),
      ]);

      if (disposed) {
        return;
      }

      setStorageSummary(storageResult.status === "fulfilled" ? storageResult.value : null);
      setCurrentRelease(releaseResult.status === "fulfilled" ? releaseResult.value.current : null);
      setFormalMap(formalMapResult.status === "fulfilled" ? formalMapResult.value : null);

      const failures = [storageResult, releaseResult, formalMapResult].filter(
        (result): result is PromiseRejectedResult => result.status === "rejected",
      );
      setStatusError(failures.length > 0 ? getReadableStatusError(failures[0].reason) : null);
      setLoading(false);
    }

    void loadPanelStatus();

    return () => {
      disposed = true;
    };
  }, [selectedAgent]);

  const ragStatus = currentRelease
    ? t("gameAdminPanel.ragReady", { defaultValue: "ready" })
    : t("gameAdminPanel.ragNoCurrentRelease", { defaultValue: "no current release" });

  const statusCards = useMemo(
    () =>
      buildAdminStatusCards({
        storageSummary,
        currentRelease,
        formalMap,
        ragStatus,
      }),
    [currentRelease, formalMap, ragStatus, storageSummary],
  );

  const adminActions = useMemo(
    () => buildAdminPanelActions(capabilities, hasExplicitCapabilityContext),
    [capabilities, hasExplicitCapabilityContext],
  );

  return (
    <div className={styles.page}>
      <PageHeader
        parent={t("nav.game")}
        current={t("nav.gameAdvanced", "Advanced")}
      />
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        <Card>
          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            <div className={styles.heroRow}>
              <div>
                <Title level={4} style={{ marginBottom: 8 }}>
                  {t("gameAdminPanel.title", { defaultValue: "Admin Panel" })}
                </Title>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  {t(
                    "gameAdminPanel.description",
                    "Advanced now serves as a local admin panel: readonly bundle/config/release/map/version status is aggregated here, while write operations stay on the existing Knowledge and Map pages.",
                  )}
                </Paragraph>
              </div>
              <Space>
                <Tag color="blue">
                  {selectedAgentSummary?.display_name || selectedAgentSummary?.name || selectedAgent}
                </Tag>
                <Button onClick={() => navigate("/game/project")}>
                  {t("nav.gameProject")}
                </Button>
              </Space>
            </div>
            <Paragraph className={styles.scopeNote}>
              {t(
                "gameAdminPanel.scopeNote",
                "This slice is intentionally read-only for status aggregation. Build Release, Publish / Set Current, Candidate Map Review, and Save Formal Map still require explicit entry into their existing workspaces.",
              )}
            </Paragraph>
          </Space>
        </Card>

        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Card
            title={t("gameAdminPanel.statusTitle", { defaultValue: "System status" })}
            extra={
              <Button onClick={() => window.location.reload()}>
                {t("common.refresh", { defaultValue: "Refresh" })}
              </Button>
            }
          >
            {loading ? (
              <div className={styles.loadingWrap}>
                <Spin />
              </div>
            ) : (
              <Space direction="vertical" size={16} style={{ width: "100%" }}>
                {statusError ? <Alert type="warning" message={statusError} showIcon /> : null}
                <Row gutter={[16, 16]}>
                  {statusCards.map((card) => (
                    <Col key={card.key} xs={24} md={12} xl={8}>
                      <Card size="small" className={styles.statusCard}>
                        <Space direction="vertical" size={8} style={{ width: "100%" }}>
                          <Space align="center">
                            <Text strong>{card.label}</Text>
                            <Tag color={card.tone === "success" ? "green" : card.tone === "warning" ? "gold" : "default"}>
                              {card.tone}
                            </Tag>
                          </Space>
                          <Text className={styles.statusValue}>{card.value}</Text>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Space>
            )}
          </Card>

          <Card title={t("gameAdminPanel.actionsTitle", { defaultValue: "Admin entries" })}>
            {adminActions.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={t(
                  "gameAdminPanel.noAdminEntries",
                  "Current capability set does not expose admin operations. Daily planning roles should not see release/map admin entry points in this panel.",
                )}
              />
            ) : (
              <Space direction="vertical" size={16} style={{ width: "100%" }}>
                <Row gutter={[16, 16]}>
                  {adminActions.map((action) => (
                    <Col key={action.key} xs={24} md={12}>
                      <Card size="small" className={styles.actionCard}>
                        <Space direction="vertical" size={8} style={{ width: "100%" }}>
                          <Text strong>{action.label}</Text>
                          <Text type="secondary">{action.requiredCapabilities.join(", ")}</Text>
                          <Button type="primary" disabled={!action.enabled} onClick={() => navigate(action.path)}>
                            {t("gameAdminPanel.openWorkspace", { defaultValue: "Open workspace" })}
                          </Button>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
                <Alert
                  type="info"
                  showIcon
                  message={t("gameAdminPanel.auditTitle", { defaultValue: "Audit aggregation boundary" })}
                  description={t(
                    "gameAdminPanel.auditPlaceholder",
                    "This slice does not add a centralized audit service. Existing write-time audit files remain where they are produced, and Admin Panel only reserves a read-only aggregation slot until a backend read API already exists.",
                  )}
                />
              </Space>
            )}
          </Card>

          <Card size="small">
            <Space direction="vertical" size={8} style={{ width: "100%" }}>
              <Text strong>
                {t(
                  "gameProject.legacySvnSectionTitle",
                  "Legacy SVN notes",
                )}
              </Text>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                {t(
                  "gameWorkspaceSkeleton.advancedSvnFrozen",
                  "SVN runtime is frozen in the current phase. Use LTClaw for local project loading only, and run update, commit, restore, and conflict handling in your external SVN workflow.",
                )}
              </Paragraph>
            </Space>
          </Card>
        </Space>
      </Space>
    </div>
  );
}