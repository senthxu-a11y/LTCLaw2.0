import { useCallback, useMemo, useState } from "react";
import type { FieldChange } from "../../../api/modules/gameWorkbench";

/**
 * 单元格的 dirty 记录。
 *  - source = manual: 用户在表内直接编辑产生
 *  - source = ai:     从 Chat 的 AI 建议「接受写入」产生
 */
export interface DirtyCell {
  table: string;
  rowKey: string;     // 行的主键值，统一以字符串形式存储（用于稳定 key）
  field: string;
  oldValue: unknown;  // 原表里的值（用于撤销/对比）
  newValue: unknown;  // 待写入的新值（已做类型转换）
  source: "manual" | "ai";
  reason?: string;    // AI 来源时的建议理由
}

export type DirtyMap = Record<string, DirtyCell>;

export function dirtyKeyOf(
  table: string,
  rowKey: string | number,
  field: string,
): string {
  return `${table}::${String(rowKey)}::${field}`;
}

/**
 * 把字符串行键尽量还原为后端期望的 row_id（数字优先，否则原样字符串）。
 */
export function parseRowId(rowKey: string): string | number {
  if (rowKey === "") return rowKey;
  const n = Number(rowKey);
  if (Number.isFinite(n) && String(n) === rowKey) return n;
  return rowKey;
}

/**
 * 把任意单元格输入字符串规范化为目标类型值。
 * 数值字段：能转就转 number，转不动保留原 string（让后端校验）。
 * 字符串字段：原样返回。
 */
export function coerceCellValue(
  raw: string,
  fieldType?: string,
): { value: unknown; typeOk: boolean } {
  const t = (fieldType || "").toLowerCase();
  const numeric =
    t.includes("int") || t.includes("float") || t === "number" || t === "double";
  if (raw === "") return { value: "", typeOk: true };
  if (numeric) {
    const n = Number(raw);
    if (!Number.isFinite(n)) return { value: raw, typeOk: false };
    return { value: n, typeOk: true };
  }
  return { value: raw, typeOk: true };
}

export function useDirtyCells() {
  const [dirty, setDirty] = useState<DirtyMap>({});

  const setCell = useCallback((cell: DirtyCell) => {
    setDirty((prev) => ({
      ...prev,
      [dirtyKeyOf(cell.table, cell.rowKey, cell.field)]: cell,
    }));
  }, []);

  const clearCell = useCallback(
    (table: string, rowKey: string, field: string) => {
      setDirty((prev) => {
        const k = dirtyKeyOf(table, rowKey, field);
        if (!(k in prev)) return prev;
        const next = { ...prev };
        delete next[k];
        return next;
      });
    },
    [],
  );

  const clearTable = useCallback((table: string) => {
    setDirty((prev) => {
      const next: DirtyMap = {};
      Object.entries(prev).forEach(([k, v]) => {
        if (v.table !== table) next[k] = v;
      });
      return next;
    });
  }, []);

  const clearAll = useCallback(() => setDirty({}), []);

  const dirtyList = useMemo(() => Object.values(dirty), [dirty]);

  const validChanges = useMemo<FieldChange[]>(
    () =>
      dirtyList
        .filter((d) => d.newValue !== "" && d.newValue !== undefined && d.newValue !== null)
        .map((d) => ({
          table: d.table,
          row_id: parseRowId(d.rowKey),
          field: d.field,
          new_value: d.newValue,
        })),
    [dirtyList],
  );

  return {
    dirty,
    dirtyList,
    validChanges,
    setCell,
    clearCell,
    clearTable,
    clearAll,
  };
}
