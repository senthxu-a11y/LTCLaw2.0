import { Empty, Tag, Typography } from "antd";
import type { DamageChainResponse } from "../../../api/modules/gameWorkbench";
import styles from "./DamageChain.module.less";

interface Props {
  data: DamageChainResponse | null;
  loading?: boolean;
}

const { Text } = Typography;

/** 伤害链路可视化 (Phase-1 stub: 默认公式 ATK*DamageCoeff*(1-DefenseRatio)) */
export function DamageChain({ data, loading }: Props) {
  if (!data) {
    return (
      <div className={styles.container}>
        <Empty description={loading ? "计算中..." : "暂无公式数据"} />
      </div>
    );
  }
  const { formula, variables, resultBefore, resultAfter, deltaPercent } = data;
  const isUp = deltaPercent > 0;
  const isDown = deltaPercent < 0;
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Text strong>伤害链路</Text>
        <Text code className={styles.formula}>{formula}</Text>
      </div>
      <div className={styles.variables}>
        {variables.map((v) => (
          <div
            key={v.name}
            className={`${styles.variableRow} ${v.isChanged ? styles.changedVariable : ""}`}
          >
            <Text strong className={styles.varName}>{v.name}</Text>
            <Text className={styles.varValue}>{v.value}</Text>
            <Text type="secondary" className={styles.varSource}>
              {v.sourceTable}
            </Text>
            {v.isChanged && <Tag color="gold">本次改动</Tag>}
          </div>
        ))}
      </div>
      <div className={styles.resultRow}>
        <Text type="secondary">改动前: </Text>
        <Text>{resultBefore}</Text>
        <Text type="secondary" style={{ marginLeft: 16 }}>改动后: </Text>
        <Text strong>{resultAfter}</Text>
        <Tag
          className={isUp ? styles.deltaUp : isDown ? styles.deltaDown : ""}
          color={isUp ? "green" : isDown ? "red" : "default"}
          style={{ marginLeft: 12 }}
        >
          {deltaPercent > 0 ? "+" : ""}{deltaPercent}%
        </Tag>
      </div>
    </div>
  );
}

export default DamageChain;
