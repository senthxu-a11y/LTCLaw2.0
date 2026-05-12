import { Button, Card, Empty, Space, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";

const { Paragraph, Text } = Typography;

export default function KnowledgePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div style={{ padding: "0 0 16px" }}>
      <PageHeader
        parent={t("nav.game")}
        current={t("nav.gameKnowledge", "Knowledge")}
      />
      <Card>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <Space direction="vertical" size={8}>
              <Text strong>{t("nav.gameKnowledge", "Knowledge")}</Text>
              <Paragraph type="secondary" style={{ marginBottom: 0, maxWidth: 560 }}>
                {t(
                  "gameWorkspaceSkeleton.knowledge",
                  "This is the G.1 route skeleton. Knowledge runtime blocks stay in Project for now and will move in G.2.",
                )}
              </Paragraph>
            </Space>
          }
        >
          <Button type="primary" onClick={() => navigate("/game/project")}>
            {t("nav.gameProject")}
          </Button>
        </Empty>
      </Card>
    </div>
  );
}