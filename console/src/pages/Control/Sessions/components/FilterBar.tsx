import { Input } from "@agentscope-ai/design";
import { useTranslation } from "react-i18next";
import styles from "../index.module.less";

interface FilterBarProps {
  filterUserId: string;
  onUserIdChange: (value: string) => void;
}

export function FilterBar({
  filterUserId,
  onUserIdChange,
}: FilterBarProps) {
  const { t } = useTranslation();

  return (
    <div className={styles.filterBar}>
      <Input
        placeholder={t("sessions.filterUserId")}
        value={filterUserId}
        onChange={(e) => onUserIdChange(e.target.value)}
        allowClear
        className="sessions-filter-input"
        style={{ width: 200, marginRight: 8 }}
      />
    </div>
  );
}
