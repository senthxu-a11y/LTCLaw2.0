import { Card, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import FormalMapWorkspace from "../components/FormalMapWorkspace";

const { Paragraph } = Typography;

export default function MapEditorPage() {
  const { t } = useTranslation();

  return (
    <div style={{ padding: "0 0 16px" }}>
      <PageHeader
        parent={t("nav.game")}
        current={t("nav.gameMapEditor", "Map Editor")}
      />
      <Card>
        <Paragraph type="secondary" style={{ marginBottom: 0, maxWidth: 720 }}>
          {t(
            "gameProject.mapEditorLandingHint",
            "Map Editor now owns formal map review, save-as-formal-map, status-only edits, and relationship warnings. Table index and dependency browsing remain a separate secondary route and are not the target of this lane.",
          )}
        </Paragraph>
        <FormalMapWorkspace mode="full" />
      </Card>
    </div>
  );
}