import { Layout, Space } from "antd";
import LanguageSwitcher from "../components/LanguageSwitcher/index";
import ThemeToggleButton from "../components/ThemeToggleButton";
import styles from "./index.module.less";
import { useTheme } from "../contexts/ThemeContext";

const { Header: AntHeader } = Layout;
const DISPLAY_VERSION = "v1.0.0";

export default function Header() {
  useTheme();

  return (
    <AntHeader className={styles.header}>
      <div className={styles.logoWrapper}>
        <span className={styles.logoText}>LTClaw</span>
        <div className={styles.logoDivider} />
        <span className={styles.logoVersion}>{DISPLAY_VERSION}</span>
      </div>
      <Space size="middle">
        <LanguageSwitcher />
        <ThemeToggleButton />
      </Space>
    </AntHeader>
  );
}
