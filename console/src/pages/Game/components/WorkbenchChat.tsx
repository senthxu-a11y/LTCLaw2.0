import type React from "react";
import { Avatar, Button, Empty, Input, Space, Tag, Tooltip, Typography } from "antd";
import { CheckOutlined, RobotOutlined, SendOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import type { SuggestChange } from "../../../api/modules/gameWorkbench";
import {
  buildSuggestMessagePresentation,
  buildSuggestionEvidencePresentation,
  type WorkbenchSuggestMeta,
} from "./workbenchSuggestEvidence";
import styles from "../NumericWorkbench.module.less";

const { Text } = Typography;

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  ts: number;
  /** AI 建议条目，仅 assistant 消息才有；点击「接受」回写到表 */
  suggestions?: SuggestChange[];
  /** 响应级 evidence / validation 元信息。 */
  suggestMeta?: WorkbenchSuggestMeta;
  /** 已经接受过的 dirty key 集合（用于禁用按钮） */
  acceptedKeys?: string[];
}

export interface WorkbenchChatProps {
  messages: ChatMessage[];
  input: string;
  sending: boolean;
  disabled?: boolean;
  placeholder?: string;
  onInputChange: (v: string) => void;
  onSend: () => void;
  onAcceptSuggestion: (sug: SuggestChange) => void;
  onAcceptAll: (sugs: SuggestChange[]) => void;
  onJumpToCell: (table: string, rowId: string | number, field: string) => void;
  onClear?: () => void;
  /** Optional toolbar slot (session picker / model selector) rendered in the header right side. */
  headerExtra?: React.ReactNode;
  /** Optional second header row (e.g. session toolbar). */
  subHeader?: React.ReactNode;
}

const formatVal = (v: unknown): string => {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
};

/**
 * 工作台下半区的独立 Chat 组件。
 * 区别于 /chat：
 *   - 不写全局会话历史
 *   - assistant 回复内嵌「接受写入」按钮，直接把建议写进上方表格的 dirty 状态
 *   - 「定位」按钮把 Tab 切到目标表 + 滚到目标行 + 高亮目标字段
 */
export function WorkbenchChat(props: WorkbenchChatProps) {
  const { t } = useTranslation();
  const {
    messages,
    input,
    sending,
    disabled,
    placeholder,
    onInputChange,
    onSend,
    onAcceptSuggestion,
    onAcceptAll,
    onJumpToCell,
    onClear,
    headerExtra,
    subHeader,
  } = props;

  return (
    <div className={styles.workbenchChat}>
      <div className={styles.chatHeader}>
        <Space>
          <RobotOutlined />
          <Text strong>
            {t("gameWorkbench.chatTitle", { defaultValue: "工作台 AI 对话" })}
          </Text>
          <Tag color="blue">
            {t("gameWorkbench.chatScopeTag", {
              defaultValue: "独立会话 · 不进入全局聊天",
            })}
          </Tag>
        </Space>
        <Space size={4}>
          {headerExtra}
          {onClear && messages.length > 0 && (
            <Button size="small" type="text" onClick={onClear}>
              {t("gameWorkbench.chatClear", { defaultValue: "清空对话" })}
            </Button>
          )}
        </Space>
      </div>
      {subHeader && <div className={styles.chatSubHeader}>{subHeader}</div>}

      <div className={styles.chatHistory}>
        {messages.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              placeholder ||
              t("gameWorkbench.chatPlaceholder", {
                defaultValue: "向 AI 描述你的需求，例如：把所有 Sword 类装备的 SellPrice 提升 20%",
              })
            }
          />
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`${styles.chatMsg} ${styles[m.role]}`}>
              <Avatar
                size="small"
                icon={m.role === "user" ? undefined : <RobotOutlined />}
                style={{ background: m.role === "user" ? "#1677ff" : "#52c41a" }}
              >
                {m.role === "user" ? "U" : null}
              </Avatar>
              <div className={styles.chatBubbleWrap}>
                <span className={styles.chatBubble}>{m.content}</span>
                {m.role === "assistant" && m.suggestions && m.suggestions.length > 0 && (
                  (() => {
                    const summary = buildSuggestMessagePresentation(m.suggestions, m.suggestMeta);
                    return (
                      <div className={styles.suggestionList}>
                    <div className={styles.suggestionListHeader}>
                        <div className={styles.suggestionSummaryBlock}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {t("gameWorkbench.suggestionListLabel", {
                              count: m.suggestions.length,
                              defaultValue: `共 ${m.suggestions.length} 条建议（点击逐条接受 / 一键全部接受）`,
                            })}
                          </Text>
                          <Space size={[4, 4]} wrap>
                            {summary.hasFormalEvidence ? (
                              <Tag color="green">
                                {t("gameWorkbench.formalEvidenceTag", { defaultValue: "Formal evidence" })}
                              </Tag>
                            ) : null}
                            {summary.usesDraftOverlay ? (
                              <Tag color="gold">
                                {t("gameWorkbench.draftOverlayTag", { defaultValue: "Draft Overlay" })}
                              </Tag>
                            ) : null}
                            {summary.hasRuntimeOnlySuggestion ? (
                              <Tag color="default">
                                {t("gameWorkbench.runtimeOnlySuggestionTag", { defaultValue: "Runtime-only suggestion" })}
                              </Tag>
                            ) : null}
                            {summary.formalContextStatus ? (
                              <Tag>
                                {t("gameWorkbench.formalContextStatusTag", {
                                  defaultValue: `formal_context_status: ${summary.formalContextStatus}`,
                                })}
                              </Tag>
                            ) : null}
                            {summary.sourceReleaseId ? (
                              <Tag color="blue">
                                {t("gameWorkbench.sourceReleaseTag", {
                                  defaultValue: `knowledge version: ${summary.sourceReleaseId}`,
                                })}
                              </Tag>
                            ) : null}
                          </Space>
                          {summary.evidenceRefs.length > 0 ? (
                            <div className={styles.suggestionEvidenceStrip}>
                              {summary.evidenceRefs.map((ref) => (
                                <Tag key={ref}>{ref}</Tag>
                              ))}
                            </div>
                          ) : null}
                        </div>
                        <Button
                          size="small"
                          type="primary"
                          icon={<CheckOutlined />}
                          onClick={() => onAcceptAll(m.suggestions!)}
                        >
                          {t("gameWorkbench.adoptAll", { defaultValue: "全部接受" })}
                        </Button>
                    </div>
                    {m.suggestions.map((s, j) => {
                      const k = `${s.table}::${String(s.row_id)}::${s.field}`;
                      const accepted = (m.acceptedKeys || []).includes(k);
                      const presentation = buildSuggestionEvidencePresentation(s, m.suggestMeta);
                      return (
                        <div key={j} className={styles.suggestionInlineCard}>
                          <Space wrap size={4}>
                            <Tag color="gold">{s.table}</Tag>
                            <Tag>{String(s.row_id)}</Tag>
                            <Text strong style={{ color: "var(--ant-color-warning-text)" }}>
                              {s.field}
                            </Text>
                            <Text>=</Text>
                            <Text code style={{ fontWeight: 600 }}>
                              {formatVal(s.new_value)}
                            </Text>
                          </Space>
                          <Space size={[4, 4]} wrap>
                            <Tag color={presentation.evidenceKind === "formal" ? "green" : "default"}>
                              {presentation.evidenceKind === "formal"
                                ? t("gameWorkbench.formalEvidenceTag", { defaultValue: "Formal evidence" })
                                : t("gameWorkbench.runtimeOnlySuggestionTag", { defaultValue: "Runtime-only suggestion" })}
                            </Tag>
                            {presentation.usesDraftOverlay ? (
                              <Tag color="gold">
                                {t("gameWorkbench.draftOverlayAssistTag", {
                                  defaultValue: "Draft Overlay assist only",
                                })}
                              </Tag>
                            ) : null}
                            {presentation.confidenceText ? (
                              <Tag>
                                {t("gameWorkbench.suggestConfidenceTag", {
                                  defaultValue: `confidence: ${presentation.confidenceText}`,
                                })}
                              </Tag>
                            ) : null}
                            {presentation.validationStatus ? (
                              <Tag>
                                {t("gameWorkbench.suggestValidationStatusTag", {
                                  defaultValue: `validation: ${presentation.validationStatus}`,
                                })}
                              </Tag>
                            ) : null}
                            {presentation.sourceReleaseId ? (
                              <Tag color="blue">
                                {t("gameWorkbench.sourceReleaseTag", {
                                  defaultValue: `knowledge version: ${presentation.sourceReleaseId}`,
                                })}
                              </Tag>
                            ) : null}
                          </Space>
                          {presentation.evidenceRefs.length > 0 ? (
                            <div className={styles.suggestionEvidenceBlock}>
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                {t("gameWorkbench.suggestEvidenceLabel", {
                                  defaultValue: "formal evidence_refs",
                                })}
                              </Text>
                              <div className={styles.suggestionEvidenceStrip}>
                                {presentation.evidenceRefs.map((ref) => (
                                  <Tag key={ref}>{ref}</Tag>
                                ))}
                              </div>
                            </div>
                          ) : null}
                          {s.reason && (
                            <Tooltip title={s.reason}>
                              <Text type="secondary" style={{ fontSize: 12 }} ellipsis>
                                {s.reason}
                              </Text>
                            </Tooltip>
                          )}
                          <Space size={4}>
                            <Button
                              size="small"
                              type={accepted ? "default" : "primary"}
                              icon={<CheckOutlined />}
                              disabled={accepted}
                              onClick={() => onAcceptSuggestion(s)}
                            >
                              {accepted
                                ? t("gameWorkbench.accepted", { defaultValue: "已接受" })
                                : t("gameWorkbench.acceptToCell", {
                                    defaultValue: "接受写入",
                                  })}
                            </Button>
                            <Button
                              size="small"
                              type="link"
                              onClick={() => onJumpToCell(s.table, s.row_id, s.field)}
                            >
                              {t("gameWorkbench.jumpToCell", { defaultValue: "定位" })}
                            </Button>
                          </Space>
                        </div>
                      );
                    })}
                      </div>
                    );
                  })()
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <div className={styles.chatInputRow}>
        <Input.TextArea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          placeholder={
            placeholder ||
            t("gameWorkbench.chatPlaceholder", {
              defaultValue: "描述需求，AI 会自动定位字段并给出建议值",
            })
          }
          autoSize={{ minRows: 1, maxRows: 4 }}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              if (!sending && input.trim()) onSend();
            }
          }}
          disabled={sending || disabled}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={onSend}
          loading={sending}
          disabled={!input.trim() || disabled}
        >
          {t("gameWorkbench.send", { defaultValue: "发送" })}
        </Button>
      </div>
    </div>
  );
}
