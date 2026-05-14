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
            "Map Editor now owns source Candidate Map review, Diff Review, explicit Save as Formal Map, release snapshot comparison, status-only edits, and relationship warnings. Candidate Map is suggested only, Formal Map is saved only after admin confirmation, and Release Map remains a review snapshot rather than the editing source.",
          )}
        </Paragraph>
        <FormalMapWorkspace mode="full" />
      </Card>
    </div>
  );
}