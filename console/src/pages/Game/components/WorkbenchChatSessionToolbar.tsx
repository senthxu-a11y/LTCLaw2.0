import { useState } from "react";
import { Button, Input, Modal, Select, Space, Tooltip } from "antd";
import {
  DeleteOutlined,
  EditOutlined,
  HistoryOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import type { WorkbenchSession } from "../hooks/useWorkbenchSessions";

interface Props {
  sessions: WorkbenchSession[];
  currentId: string;
  currentDirty?: boolean;
  onSwitch: (id: string) => void;
  onNew: () => void;
  onRename: (id: string, name: string) => void;
  onRemove: (id: string) => void;
}

export function WorkbenchChatSessionToolbar(props: Props) {
  const {
    sessions,
    currentId,
    currentDirty,
    onSwitch,
    onNew,
    onRename,
    onRemove,
  } = props;
  const current = sessions.find((s) => s.id === currentId);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");

  const confirmRemoveCurrent = () => {
    if (!current) return;
    Modal.confirm({
      title: "删除会话",
      content: currentDirty
        ? `删除会话「${current.name}」？当前会话还有未手动保存的本地变更，删除后将无法恢复。`
        : `删除会话「${current.name}」？此操作不可撤销。`,
      okType: "danger",
      okText: "删除",
      cancelText: "取消",
      onOk: () => onRemove(current.id),
    });
  };

  return (
    <Space size={4}>
      <Tooltip title="切换历史会话">
        <Select
          size="small"
          value={currentId}
          style={{ minWidth: 180, maxWidth: 280 }}
          onChange={onSwitch}
          suffixIcon={<HistoryOutlined />}
          options={sessions.map((s) => ({
            value: s.id,
            label: (
              <span>
                {s.name}
                {s.messages.length > 0 && (
                  <span style={{ color: "#999", marginLeft: 6, fontSize: 12 }}>
                    · {s.messages.length}
                  </span>
                )}
              </span>
            ),
          }))}
        />
      </Tooltip>
      <Tooltip title="新建会话">
        <Button size="small" icon={<PlusOutlined />} onClick={onNew} />
      </Tooltip>
      <Tooltip title="重命名当前会话">
        <Button
          size="small"
          icon={<EditOutlined />}
          onClick={() => {
            if (!current) return;
            setRenameValue(current.name);
            setRenaming(true);
          }}
        />
      </Tooltip>
      <Tooltip title="删除当前会话">
        <Button
          size="small"
          danger
          icon={<DeleteOutlined />}
          onClick={confirmRemoveCurrent}
          disabled={sessions.length <= 1}
        />
      </Tooltip>

      <Modal
        title="重命名会话"
        open={renaming}
        onCancel={() => setRenaming(false)}
        onOk={() => {
          if (current && renameValue.trim()) {
            onRename(current.id, renameValue.trim());
          }
          setRenaming(false);
        }}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Input
          value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)}
          placeholder="输入会话名称"
          maxLength={60}
        />
      </Modal>
    </Space>
  );
}
