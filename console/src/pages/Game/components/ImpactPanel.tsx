import { Empty, Space, Spin, Tag, Tooltip, Typography } from "antd";
import { CheckCircleTwoTone, CloseCircleTwoTone } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import type {
  DamageChainResponse,
  PreviewItem,
  ReverseImpact,
} from "../../../api/modules/gameWorkbench";
import { DamageChain } from "./DamageChain";
import styles from "../NumericWorkbench.module.less";

const { Text } = Typography;

export interface ReverseImpactSummary {
  total: number;
  tables: string[];
  impacts: Array<{
    from_table: string;
    from_field: string;
    to_table: string;
    to_field: string;
    depth: number;
    path: string[];
    confidence?: string | number;
  }>;
}

export interface ImpactPanelProps {
  preview: PreviewItem[];
  previewLoading: boolean;
  damageChain: DamageChainResponse | null;
  damageChainLoading: boolean;
  affectedTables: string[];
  impacts: ReverseImpact[];
  reverseImpact: ReverseImpactSummary | null;
}

const formatVal = (v: unknown): string => {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
};

/**
 * 右栏 Drawer 内的「依赖 + 影响 + 公式链路」组合面板。
 * 三段同屏：
 *   1. 影响预览：dry-run 后端 preview 结果（按字段一行）
 *   2. 公式链路：DamageChain 可视化
 *   3. 反向依赖：受影响下游表/字段
 */
export function ImpactPanel(props: ImpactPanelProps) {
  const { t } = useTranslation();
  const {
    preview,
    previewLoading,
    damageChain,
    damageChainLoading,
    affectedTables,
    impacts,
    reverseImpact,
  } = props;

  const hasAny =
    preview.length > 0 ||
    damageChain ||
    affectedTables.length > 0 ||
    (reverseImpact && reverseImpact.total > 0);

  if (!hasAny && !previewLoading && !damageChainLoading) {
    return (
      <div className={styles.panelSection}>
        <Text strong>
          {t("gameWorkbench.impactTitle", { defaultValue: "影响预览" })}
        </Text>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={t("gameWorkbench.impactEmpty", {
            defaultValue: "改任何单元格 → 这里实时刷新影响、链路与下游依赖",
          })}
        />
      </div>
    );
  }

  return (
    <>
      <div className={styles.panelSection}>
        <Space>
          <Text strong>
            {t("gameWorkbench.previewTitle", { defaultValue: "效果预览" })}
          </Text>
          <Tag color={preview.length && preview.every((p) => p.ok) ? "green" : "default"}>
            {t("gameWorkbench.previewCount", {
              count: preview.length,
              defaultValue: `${preview.length} 条`,
            })}
          </Tag>
          {previewLoading && <Spin size="small" />}
        </Space>
        {preview.length > 0 && (
          <div className={styles.previewList}>
            {preview.map((item, idx) => (
              <div
                key={idx}
                className={`${styles.previewItem} ${item.ok ? styles.ok : styles.fail}`}
              >
                <Space size={4}>
                  {item.ok ? (
                    <CheckCircleTwoTone twoToneColor="#52c41a" />
                  ) : (
                    <Tooltip title={item.error ?? ""}>
                      <CloseCircleTwoTone twoToneColor="#ff4d4f" />
                    </Tooltip>
                  )}
                  <Text strong style={{ fontSize: 12 }}>
                    {item.table}.{item.field}[{String(item.row_id)}]
                  </Text>
                </Space>
                <div className={styles.delta}>
                  <Text type="secondary">{formatVal(item.old_value)}</Text>
                  <span className={styles.deltaArrow}>→</span>
                  <Text>{formatVal(item.new_value)}</Text>
                </div>
                {!item.ok && item.error && (
                  <Text type="danger" style={{ fontSize: 11 }}>
                    {item.error}
                  </Text>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {(damageChain || damageChainLoading) && (
        <div className={styles.panelSection}>
          <Text strong>
            {t("gameWorkbench.damageChainTitle", { defaultValue: "公式链路" })}
          </Text>
          <DamageChain data={damageChain} loading={damageChainLoading} />
        </div>
      )}

      {(affectedTables.length > 0 || (reverseImpact && reverseImpact.total > 0)) && (
        <div className={styles.panelSection}>
          <Space>
            <Text strong>
              {t("gameWorkbench.reverseDepTitle", {
                defaultValue: "反向依赖（下游影响）",
              })}
            </Text>
            <Tag color="orange">
              {t("gameWorkbench.impactCount", {
                count: affectedTables.length,
                defaultValue: `${affectedTables.length} 张表`,
              })}
            </Tag>
          </Space>
          {affectedTables.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {affectedTables.map((tbl) => {
                const refCount = impacts.filter((i) => i.from_table === tbl).length;
                return (
                  <Tooltip
                    key={tbl}
                    title={
                      impacts
                        .filter((i) => i.from_table === tbl)
                        .map(
                          (i) =>
                            `${i.from_table}.${i.from_field} ← ${i.to_table}.${i.to_field}`,
                        )
                        .join("\n") || tbl
                    }
                  >
                    <Tag color="gold" style={{ cursor: "help" }}>
                      {tbl} · {refCount}
                    </Tag>
                  </Tooltip>
                );
              })}
            </div>
          )}
          {reverseImpact && reverseImpact.total > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {reverseImpact.impacts.slice(0, 12).map((it, i) => (
                <Tooltip key={i} title={it.path.join(" → ")}>
                  <div style={{ fontSize: 12 }}>
                    <Tag color={it.depth === 1 ? "red" : "orange"}>d{it.depth}</Tag>
                    <Text code>{it.from_table}</Text>
                    <Text type="secondary"> .{it.from_field}</Text>
                    <Text type="secondary"> ← {it.to_field}</Text>
                  </div>
                </Tooltip>
              ))}
              {reverseImpact.total > 12 && (
                <Text type="secondary" style={{ fontSize: 11 }}>
                  … {reverseImpact.total - 12} more
                </Text>
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
}
