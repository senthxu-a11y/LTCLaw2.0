import { useState } from "react";
import { Button, Dropdown, Input, Modal, Select, Space, Tooltip } from "antd";
import {
  DeleteOutlined,
  EditOutlined,
  HistoryOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import type { WorkbenchChatSession } from "../hooks/useWorkbenchChatSessions";

interface Props {
  sessions: WorkbenchChatSession[];
  currentId: string;
  onSwitch: (id: string) => void;
  onNew: () => void;
  onRename: (id: string, name: string) => void;
  onRemove: (id: string) => void;
}

export function WorkbenchChatSessionToolbar(props: Props) {
  const { sessions, currentId, onSwitch, onNew, onRename, onRemove } = props;
  const current = sessions.find((s) => s.id === currentId);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");

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
      <Dropdown
        trigger={["click"]}
        menu={{
          items: [
            {
              key: "rename",
              icon: <EditOutlined />,
              label: "重命名当前会话",
              onClick: () => {
                if (!current) return;
                setRenameValue(current.name);
                setRenaming(true);
              },
            },
            {
              key: "remove",
              icon: <DeleteOutlined />,
              label: "删除当前会话",
              danger: true,
              disabled: sessions.length <= 1,
              onClick: () => {
                if (!current) return;
                Modal.confirm({
                  title: "删除会话",
                  content: `删除会话「${current.name}」？此操作不可撤销。`,
                  okType: "danger",
                  okText: "删除",
                  cancelText: "取消",
                  onOk: () => onRemove(current.id),
                });
              },
            },
          ],
        }}
      >
        <Button size="small" type="text">
          ⋯
        </Button>
      </Dropdown>

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
