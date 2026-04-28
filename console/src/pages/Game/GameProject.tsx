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
      const config = await gameApi.getProjectConfig(selectedAgent);
      if (config) {
        const currentConfig = config as any;
        form.setFieldsValue({
          name: currentConfig.project?.name || "",
          description: currentConfig.project?.language || "",
          svn_url: currentConfig.svn?.root || "",
          svn_username: "",
          svn_password: "",
          svn_trust_cert: false,
          svn_working_copy_path: "",
          watch_paths: (currentConfig.paths || []).map((item: any) => item.path).join('\n'),
          watch_patterns: (currentConfig.filters?.include_ext || []).join('\n'),
          watch_exclude_patterns: (currentConfig.filters?.exclude_glob || []).join('\n'),
          auto_sync: false,
          auto_index: true,
          auto_resolve_dependencies: true,
          index_commit_message_template: "",
        });
      } else {
        // Set default values for new configuration
        form.setFieldsValue({
          name: '',
          description: '',
          svn_url: '',
          svn_username: '',
          svn_password: '',
          svn_trust_cert: false,
          svn_working_copy_path: '',
          watch_paths: 'Tables\nConfigs',
          watch_patterns: '*.xlsx\n*.csv\n*.json\n*.yaml',
          watch_exclude_patterns: '~$*\n*.tmp\n*.bak',
          auto_sync: true,
          auto_index: true,
          auto_resolve_dependencies: true,
          index_commit_message_template: 'Auto-index update: {files_changed} files',
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
      
      const config = {
        name: values.name,
        description: values.description,
        svn: {
          url: values.svn_url,
          username: values.svn_username,
          password: values.svn_password,
          trust_cert: values.svn_trust_cert,
          working_copy_path: values.svn_working_copy_path,
        },
        watch: {
          paths: values.watch_paths.split('\n').filter(p => p.trim()),
          patterns: values.watch_patterns.split('\n').filter(p => p.trim()),
          exclude_patterns: values.watch_exclude_patterns.split('\n').filter(p => p.trim()),
        },
        workflow: {
          auto_sync: values.auto_sync,
          auto_index: values.auto_index,
          auto_resolve_dependencies: values.auto_resolve_dependencies,
          index_commit_message_template: values.index_commit_message_template,
        },
      } as any as ProjectConfig;

      const result = await gameApi.saveProjectConfig(selectedAgent, config);
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
