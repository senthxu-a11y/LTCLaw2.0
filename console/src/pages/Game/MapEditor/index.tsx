import { useEffect, useState } from "react";
import { Alert, Card, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { gameKnowledgeReleaseApi } from "@/api/modules/gameKnowledgeRelease";
import { useAgentStore } from "@/stores/agentStore";
import FormalMapWorkspace from "../components/FormalMapWorkspace";

const { Paragraph } = Typography;

export default function MapEditorPage() {
  const { t } = useTranslation();
  const { selectedAgent } = useAgentStore();
  const [hasSourceCandidate, setHasSourceCandidate] = useState(false);

  useEffect(() => {
    if (!selectedAgent) {
      setHasSourceCandidate(false);
      return;
    }
    void gameKnowledgeReleaseApi.getLatestSourceCandidate(selectedAgent)
      .then((candidate) => setHasSourceCandidate(Boolean(candidate?.map)))
      .catch(() => setHasSourceCandidate(false));
  }, [selectedAgent]);

  return (
    <div style={{ padding: "0 0 16px" }}>
      <PageHeader
        parent={t("nav.game")}
        current={t("nav.gameMapEditor", "Map Editor")}
      />
      <Card>
        {hasSourceCandidate ? (
          <Alert
            type="info"
            showIcon
            message={t(
              "gameProject.mapEditorSourceCandidateHint",
              "发现冷启动候选地图，请保存为正式地图。系统不会自动保存 Formal Map。",
            )}
            style={{ marginBottom: 16 }}
          />
        ) : null}
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