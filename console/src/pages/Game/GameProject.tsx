import { useEffect, useState } from "react";
import { Form, Input, Switch, Button, Card } from "@agentscope-ai/design";
import { Space } from "antd";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/PageHeader";
import { useAppMessage } from "@/hooks/useAppMessage";
import { gameApi } from "../../api/modules/game";
import type { ProjectConfig, ValidationIssue } from "../../api/types/game";
import { useAgentStore } from "../../stores/agentStore";
import styles from "./GameProject.module.less";

const { TextArea } = Input;

interface GameProjectFormData {
  name: string;
  description?: string;
  is_maintainer: boolean;
  svn_url: string;
  svn_username?: string;
  svn_password?: string;
  svn_trust_cert?: boolean;
  svn_working_copy_path?: string;
  watch_paths: string;
  watch_patterns: string;
  watch_exclude_patterns: string;
  auto_sync: boolean;
  auto_index: boolean;
  auto_resolve_dependencies: boolean;
  index_commit_message_template: string;
}

export default function GameProject() {
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { selectedAgent } = useAgentStore();
  const [form] = Form.useForm<GameProjectFormData>();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = async () => {
    if (!selectedAgent) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [projectConfig, userConfig] = await Promise.all([
        gameApi.getProjectConfig(selectedAgent),
        gameApi.getUserConfig(selectedAgent).catch(() => null),
      ]);
      if (projectConfig) {
        const pc = projectConfig as any;
        const uc = (userConfig || {}) as any;
        form.setFieldsValue({
          name: pc.project?.name || "",
          description: pc.project?.engine || "",
          is_maintainer: uc.my_role === "maintainer",
          svn_url: uc.svn_url || "",
          svn_username: uc.svn_username || "",
          svn_password: uc.svn_password || "",
          svn_trust_cert: !!uc.svn_trust_cert,
          svn_working_copy_path: uc.svn_local_root || pc.svn?.root || "",
          watch_paths: (pc.paths || []).map((item: any) => item.path).join("\n"),
          watch_patterns: (pc.filters?.include_ext || []).join("\n"),
          watch_exclude_patterns: (pc.filters?.exclude_glob || []).join("\n"),
          auto_sync: false,
          auto_index: true,
          auto_resolve_dependencies: true,
          index_commit_message_template: "Auto-index update: {files_changed} files",
        });
      } else {
        // Set default values for new configuration
        form.setFieldsValue({
          name: "",
          description: "Unity",
          is_maintainer: false,
          svn_url: "",
          svn_username: "",
          svn_password: "",
          svn_trust_cert: false,
          svn_working_copy_path: "",
          watch_paths: "Tables\nConfigs",
          watch_patterns: ".xlsx\n.xls\n.csv\n.md\n.txt\n.docx",
          watch_exclude_patterns: "**/temp/**\n**/.svn/**\n**/~$*",
          auto_sync: true,
          auto_index: true,
          auto_resolve_dependencies: true,
          index_commit_message_template: "Auto-index update: {files_changed} files",
        });
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.loadFailed");
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);

      const splitLines = (s: string | undefined) =>
        (s || "")
          .split(/\r?\n/)
          .map((p) => p.trim())
          .filter((p) => p.length > 0);

      const workingCopyPath = (values.svn_working_copy_path || "").trim();
      if (!workingCopyPath) {
        message.error(t("gameProject.svnWorkingCopyPathRequired", { defaultValue: "请填写本地SVN工作副本路径（先 svn checkout 到本地）" }));
        setSaving(false);
        return;
      }

      // 1) 用户级配置（账号密码不入 SVN）
      const userPayload = {
        my_role: (values.is_maintainer ? "maintainer" : "consumer") as "maintainer" | "consumer",
        svn_local_root: workingCopyPath,
        svn_url: values.svn_url || null,
        svn_username: values.svn_username || null,
        svn_password: values.svn_password || null,
        svn_trust_cert: !!values.svn_trust_cert,
      };
      await gameApi.saveUserConfig(selectedAgent!, userPayload as any);

      // 2) 项目级配置（落 .ltclaw_index/project_config.yaml，入 SVN 共享）
      const paths = splitLines(values.watch_paths).map((p) => ({
        path: p,
        semantic: "table" as const,
      }));
      const projectPayload: any = {
        schema_version: "project-config.v1",
        project: {
          name: values.name,
          engine: values.description || "Unity",
          language: "zh",
        },
        svn: {
          root: workingCopyPath,
          poll_interval_seconds: 300,
          jitter_seconds: 30,
        },
        paths,
        filters: {
          include_ext: splitLines(values.watch_patterns),
          exclude_glob: splitLines(values.watch_exclude_patterns),
        },
        table_convention: {
          header_row: 1,
          comment_row: null,
          primary_key_field: "ID",
          id_ranges: [],
        },
        doc_templates: {},
        models: {},
      };
      const result = await gameApi.saveProjectConfig(selectedAgent!, projectPayload as ProjectConfig);
      message.success(result.message || t("gameProject.saveSuccess"));
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.saveFailed");
      message.error(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleValidate = async () => {
    if (!selectedAgent) {
      return;
    }
    try {
      await form.validateFields();
      setSaving(true);
      const issues = await gameApi.validateProjectConfig(selectedAgent);
      const errors = issues.filter((issue: ValidationIssue) => issue.severity === "error");
      if (errors.length === 0) {
        message.success(t("gameProject.validationSuccess"));
      } else {
        message.error(
          `${t("gameProject.validationFailed")}: ${errors
            .map((issue) => `${issue.path}: ${issue.message}`)
            .join(", ")}`
        );
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : t("gameProject.validationFailed");
      message.error(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    fetchConfig();
  };

  useEffect(() => {
    fetchConfig();
  }, [selectedAgent]);

  if (loading) {
    return (
      <div className={styles.gamePage}>
        <div className={styles.centerState}>
          <span className={styles.stateText}>{t("common.loading")}</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.gamePage}>
        <div className={styles.centerState}>
          <span className={styles.stateTextError}>{error}</span>
          <Button size="small" onClick={fetchConfig} style={{ marginTop: 12 }}>
            {t("common.retry")}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.gamePage}>
      <PageHeader parent={t("nav.game")} current={t("gameProject.title")} />

      <div className={styles.content}>
        <Form form={form} layout="vertical" className={styles.form}>
          
          {/* Basic Info Section */}
          <Card title={t("gameProject.basicInfo")} className={styles.section}>
            <Form.Item
              label={t("gameProject.projectName")}
              name="name"
              rules={[{ required: true, message: t("gameProject.projectNameRequired") }]}
            >
              <Input placeholder={t("gameProject.projectNamePlaceholder")} />
            </Form.Item>
            
            <Form.Item
              label={t("gameProject.projectDescription")}
              name="description"
            >
              <TextArea 
                rows={3} 
                placeholder={t("gameProject.projectDescriptionPlaceholder")} 
              />
            </Form.Item>
          </Card>

          {/* SVN Configuration Section */}
          <Card title={t("gameProject.svnConfig")} className={styles.section}>
            <Form.Item
              label="我是维护者 (允许提交索引到 SVN)"
              name="is_maintainer"
              valuePropName="checked"
              tooltip="开启=维护者maintainer (可写回索引/提案)；关闭=使用者consumer (只读)"
            >
              <Switch />
            </Form.Item>
            <Form.Item
              label={t("gameProject.svnUrl")}
              name="svn_url"
              rules={[{ required: true, message: t("gameProject.svnUrlRequired") }]}
            >
              <Input placeholder="svn://server/path/to/project" />
            </Form.Item>
            
            <Form.Item label={t("gameProject.svnUsername")} name="svn_username">
              <Input placeholder={t("gameProject.svnUsernamePlaceholder")} />
            </Form.Item>
            
            <Form.Item label={t("gameProject.svnPassword")} name="svn_password">
              <Input.Password placeholder={t("gameProject.svnPasswordPlaceholder")} />
            </Form.Item>
            
            <Form.Item label={t("gameProject.svnWorkingCopyPath")} name="svn_working_copy_path">
              <Input placeholder={t("gameProject.svnWorkingCopyPathPlaceholder")} />
            </Form.Item>
            
            <Form.Item name="svn_trust_cert" valuePropName="checked">
              <Switch /> {t("gameProject.svnTrustCert")}
            </Form.Item>
          </Card>

          {/* Watch Configuration Section */}
          <Card title={t("gameProject.watchConfig")} className={styles.section}>
            <Form.Item label={t("gameProject.watchPaths")} name="watch_paths">
              <TextArea 
                rows={4} 
                placeholder={t("gameProject.watchPathsPlaceholder")} 
              />
            </Form.Item>
            
            <Form.Item label={t("gameProject.watchPatterns")} name="watch_patterns">
              <TextArea 
                rows={4} 
                placeholder={t("gameProject.watchPatternsPlaceholder")} 
              />
            </Form.Item>
            
            <Form.Item label={t("gameProject.watchExcludePatterns")} name="watch_exclude_patterns">
              <TextArea 
                rows={4} 
                placeholder={t("gameProject.watchExcludePatternsPlaceholder")} 
              />
            </Form.Item>
          </Card>

          {/* Workflow Configuration Section */}
          <Card title={t("gameProject.workflowConfig")} className={styles.section}>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Form.Item name="auto_sync" valuePropName="checked">
                <Switch /> {t("gameProject.autoSync")}
              </Form.Item>
              
              <Form.Item name="auto_index" valuePropName="checked">
                <Switch /> {t("gameProject.autoIndex")}
              </Form.Item>
              
              <Form.Item name="auto_resolve_dependencies" valuePropName="checked">
                <Switch /> {t("gameProject.autoResolveDependencies")}
              </Form.Item>
              
              <Form.Item 
                label={t("gameProject.indexCommitMessageTemplate")} 
                name="index_commit_message_template"
              >
                <Input placeholder={t("gameProject.indexCommitMessageTemplatePlaceholder")} />
              </Form.Item>
            </Space>
          </Card>

        </Form>
      </div>

      <div className={styles.footerActions}>
        <Button onClick={handleReset} disabled={saving} style={{ marginRight: 8 }}>
          {t("common.reset")}
        </Button>
        <Button onClick={handleValidate} disabled={saving} style={{ marginRight: 8 }}>
          {t("gameProject.validate")}
        </Button>
        <Button type="primary" onClick={handleSave} loading={saving}>
          {t("common.save")}
        </Button>
      </div>
    </div>
  );
}
