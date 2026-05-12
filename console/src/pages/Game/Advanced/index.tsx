import { Button, Card, Space, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";

const { Paragraph, Text, Title } = Typography;

export default function AdvancedPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div style={{ padding: "0 0 16px" }}>
      <PageHeader
        parent={t("nav.game")}
        current={t("nav.gameAdvanced", "Advanced")}
      />
      <Card>
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <div>
            <Title level={4} style={{ marginBottom: 8 }}>
              {t("nav.gameAdvanced", "Advanced")}
            </Title>
            <Paragraph type="secondary" style={{ marginBottom: 0, maxWidth: 640 }}>
              {t(
                "gameWorkspaceSkeleton.advanced",
                "Advanced groups low-frequency tools under a separate route so daily project workflow stays unchanged.",
              )}
            </Paragraph>
          </div>
          <Card size="small">
            <Space direction="vertical" size={8} style={{ width: "100%" }}>
              <Text strong>{t("nav.svnSync")}</Text>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                {t(
                  "gameWorkspaceSkeleton.advancedSvn",
                  "SVN stays a low-frequency Advanced tool entry. Existing sync, update, and commit behavior is unchanged.",
                )}
              </Paragraph>
              <Space>
                <Button type="primary" onClick={() => navigate("/game/advanced/svn")}>
                  {t("nav.svnSync")}
                </Button>
                <Button onClick={() => navigate("/game/project")}>
                  {t("nav.gameProject")}
                </Button>
              </Space>
            </Space>
          </Card>
        </Space>
      </Card>
    </div>
  );
}