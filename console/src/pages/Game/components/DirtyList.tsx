import { Button, Empty, Space, Tag, Tooltip, Typography } from "antd";
import { DeleteOutlined, EditOutlined, RobotOutlined, SaveOutlined, UndoOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import type { DirtyCell } from "../hooks/useDirtyCells";
import styles from "../NumericWorkbench.module.less";

const { Text } = Typography;

export interface DirtyListProps {
  items: DirtyCell[];
  onJump: (table: string, rowKey: string, field: string) => void;
  onRevert: (table: string, rowKey: string, field: string) => void;
  onClearAll: () => void;
  onSave: () => void;
  saveDisabled?: boolean;
  saving?: boolean;
}

const formatVal = (v: unknown): string => {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
};

export function DirtyList(props: DirtyListProps) {
  const { t } = useTranslation();
  const { items, onJump, onRevert, onClearAll, onSave, saveDisabled, saving } = props;

  return (
    <div className={styles.panelSection}>
      <div className={styles.dirtyHeader}>
        <Space>
          <Text strong>
            {t("gameWorkbench.dirtyTitle", { defaultValue: "修改条目" })}
          </Text>
          <Tag color={items.length ? "orange" : "default"}>
            {t("gameWorkbench.dirtyCount", {
              count: items.length,
              defaultValue: `${items.length} 项`,
            })}
          </Tag>
        </Space>
        <Space size={4}>
          <Button
            size="small"
            icon={<UndoOutlined />}
            onClick={onClearAll}
            disabled={items.length === 0}
          >
            {t("gameWorkbench.revertAll", { defaultValue: "全部撤销" })}
          </Button>
          <Button
            size="small"
            type="primary"
            icon={<SaveOutlined />}
            onClick={onSave}
            disabled={saveDisabled || items.length === 0}
            loading={saving}
          >
            {t("gameWorkbench.saveDraft", { defaultValue: "保存为变更草稿" })}
          </Button>
        </Space>
      </div>

      {items.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={t("gameWorkbench.dirtyEmpty", {
            defaultValue: "双击单元格即可直接编辑；AI 建议的「接受写入」也会出现在这里",
          })}
        />
      ) : (
        <div className={styles.dirtyItemList}>
          {items.map((d) => {
            const k = `${d.table}::${d.rowKey}::${d.field}`;
            return (
              <div
                key={k}
                className={`${styles.dirtyItem} ${
                  d.source === "ai" ? styles.dirtyAi : styles.dirtyManual
                }`}
              >
                <div className={styles.dirtyItemRow}>
                  <Space size={4} wrap>
                    {d.source === "ai" ? (
                      <Tooltip title={d.reason || "来自 AI 建议"}>
                        <Tag color="purple" icon={<RobotOutlined />}>
                          AI
                        </Tag>
                      </Tooltip>
                    ) : (
                      <Tag color="blue" icon={<EditOutlined />}>
                        {t("gameWorkbench.dirtySrcManual", { defaultValue: "手动" })}
                      </Tag>
                    )}
                    <Tag color="gold">{d.table}</Tag>
                    <Text code style={{ fontSize: 11 }}>{d.rowKey}</Text>
                    <Text strong style={{ fontSize: 12 }}>{d.field}</Text>
                  </Space>
                  <Space size={2}>
                    <Button
                      size="small"
                      type="link"
                      onClick={() => onJump(d.table, d.rowKey, d.field)}
                    >
                      {t("gameWorkbench.jumpToCell", { defaultValue: "定位" })}
                    </Button>
                    <Tooltip title={t("gameWorkbench.revertOne", { defaultValue: "撤销" })}>
                      <Button
                        size="small"
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => onRevert(d.table, d.rowKey, d.field)}
                      />
                    </Tooltip>
                  </Space>
                </div>
                <div className={styles.dirtyItemDelta}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {formatVal(d.oldValue)}
                  </Text>
                  <span className={styles.deltaArrow}>→</span>
                  <Text strong style={{ fontSize: 12, color: "var(--ant-color-warning-text)" }}>
                    {formatVal(d.newValue)}
                  </Text>
                </div>
                {d.source === "ai" && d.reason && (
                  <Text type="secondary" style={{ fontSize: 11 }} ellipsis>
                    {d.reason}
                  </Text>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
