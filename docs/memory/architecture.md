# LTCLAW-GY.X 架构吃透笔记

> 适用项目：LTCLAW-GY.X (Python 包名 `ltclaw_gy_x`)。源码根：`src/ltclaw_gy_x`。
>
> 本文档由 `/memories/ltclaw-architecture.md` + `/memories/repo/architecture.md` 整理而来，是新成员或新协作 agent 接手时的**首读文档**。

## 1. 启动链 (CLI -> uvicorn -> FastAPI)
- 入口脚本：`pyproject.toml [project.scripts]` -> `ltclaw_gy_x.cli.main:cli`。
- `__main__.py` 转发到 CLI；CLI 是 `LazyGroup`，所有子命令懒加载。
- `cli/main.py` 在 Windows 下强制 stdout/stderr UTF-8；记录最近 host/port。
- `cli/app_cmd.py` 真正起服务：写 last_api、设 `QWENPAW_LOG_LEVEL`、`uvicorn.run("ltclaw_gy_x.app._app:app", workers=1)`。
- `cli/desktop_cmd.py` 选空闲端口后用 pywebview 打开本地壳；Windows 用 pythonw 重拉。

## 2. FastAPI 装配中心 (`app/_app.py`)
- 模块导入期：`load_envs_into_environ()` 把持久化 env 倒回 `os.environ`；`setup_logger`；补 MIME。
- `DynamicMultiAgentRunner`：通过 `agent_context._current_agent_id` 选择正确 workspace 的 runner，把 stream_query/query_handler 委派出去；同时用 workspace.task_tracker.register_external_task 让 reload 能感知活跃任务。
- `agent_app = AgentApp(... runner=runner ...)` 来自 agentscope_runtime。
- `lifespan` 两阶段：
  1. 快路径：`auto_register_from_env`、迁移 (`migrate_legacy_workspace_to_default_agent`、`ensure_default_agent_exists`、`migrate_legacy_skills_to_skill_pool`、`ensure_qa_agent_exists`)、构造 MultiAgentManager / ProviderManager.get_instance() / LocalModelManager.get_instance()、TokenUsageManager.start(10)、把这些挂到 `app.state.*`、设 runner.set_multi_agent_manager。
  2. 后台 `_background_startup`：`multi_agent_manager.start_all_configured_agents()` -> `provider_manager.start_local_model_resume(local_model_manager)` -> 加载插件 (`PluginLoader(plugin_dirs=[get_plugins_dir()]).load_all_plugins(configs=config.plugins)`) -> 把 `plugin_loader.registry.get_all_providers()` 全部 `provider_manager.register_plugin_provider(...)` -> 把 `get_control_commands()` 通过 `app.runner.control_commands.register_command` + `app.channels.command_registry.CommandRegistry.register_command("/{name}", priority_level)` -> 跑 startup hooks -> `get_approval_service().set_channel_manager(default_agent.channel_manager)` -> 打印就绪 banner。
- shutdown：跑 shutdown hooks；`local_model_manager.shutdown_server()`；`multi_agent_manager.stop_all()`；`token_usage_manager.stop()`。
- 中间件顺序：`AgentContextMiddleware` -> `AuthMiddleware` -> 可选 CORS。
- 路由挂载：`/api` 普通、`/api` approval、`/api` agent-scoped (`create_agent_scoped_router()`)、`/api/agent` 是 `agent_app.router`。
- 静态资源：根路径与 `/console` 都返回内嵌控制台。`_resolve_console_static_dir()` 优先 env `QWENPAW_CONSOLE_STATIC_DIR`，再包内 `console/`，再仓库 `console/dist`，再 cwd 兜底。
- DOCS：仅当 `QWENPAW_OPENAPI_DOCS=true` 才暴露 `/docs /redoc /openapi.json`。

## 3. 多 Agent 运行时
### 3.1 MultiAgentManager (`app/multi_agent_manager.py`)
- 字典 `agents: {agent_id: Workspace}`，`asyncio.Lock`，`_pending_starts: {agent_id: Event}`，`_cleanup_tasks`。
- `get_agent`：fast path 无锁；锁内复检 + 若已有 pending 则等 event；首发者读 config.profiles 校验、登记 pending、释放锁，去外面创建 Workspace 并 start，再加锁写入字典。失败也清理 pending、set event。
- `reload_agent`：锁外构造新 Workspace，复用旧 workspace `service_manager.get_reusable_services()` 中可复用的 (memory/context/chat) -> `set_reusable_components` -> start；锁内原子换；旧实例走 `_graceful_stop_old_instance`：有活跃任务则后台 `wait_all_done(60s)` 后 stop(final=False)，无则立刻 stop。

### 3.2 Workspace (`app/workspace/workspace.py`)
- 每个 agent 一个 Workspace；目录约定：`workspace_dir = ~ / .ltclaw_gy_x / workspaces / {agent_id}` (来自 migration)。
- 自有：`runner` (`AgentRunner`)、`memory_manager`、`context_manager`、`mcp_manager` (`MCPClientManager`)、`chat_manager`、`channel_manager`、`cron_manager` (`CronManager+JsonJobRepository`)、`agent_config_watcher`、`mcp_config_watcher`，加非服务态 `task_tracker` (`TaskTracker`)、`config` (`load_agent_config(agent_id)`).
- `set_manager(mgr)` 把 manager 引用透传给 runner，用于 /daemon restart。

### 3.3 ServiceManager (`app/workspace/service_manager.py`)
- `ServiceDescriptor` 字段：name, service_class (类或返回类的 callable), init_args (callable), post_init (sync/async), start_method, stop_method, reusable, reload_func, dependencies, priority, concurrent_init。
- `start_all`：按 priority 升序分组；同优先级中 concurrent_init 的 `asyncio.gather`，sequential 的串行；每组之间 `await asyncio.sleep(0)` 让出事件循环。
- `_get_or_create_service` 用 `asyncio.to_thread(partial(cls, **kwargs))` 跑同步构造，避免阻塞 loop。
- 优先级布局 (workspace.py 中注册)：
  - 10 runner (sequential)
  - 20 memory_manager (reusable, concurrent), context_manager (reusable, concurrent), mcp_manager (concurrent), chat_manager (reusable, concurrent)
  - 25 runner_start (sequential, post_init 调 runner.start())
  - 30 channel_manager (sequential, start_method=start_all)
  - 40 cron_manager (sequential)
  - 50 agent_config_watcher (sequential, conditional)
  - 51 mcp_config_watcher (sequential, conditional)
- service_factories 中：`create_mcp_service` 把 mcp 注入 runner；`create_chat_service` 复用或新建 ChatManager+JsonChatRepository；`create_channel_service` 用 `ChannelManager.from_config` + `make_process_from_runner`，并 `cm.set_workspace(ws)` + `runner.set_workspace(ws)`；watcher 类条件创建。

## 4. Agent 实现 (`agents/react_agent.py`)
- `LTClawGYXAgent(ToolGuardMixin, ReActAgent)` (MRO: 自身 -> ToolGuardMixin -> ReActAgent)；继承 agentscope ReActAgent。
- 构造：从 `agent_config` 取 running、language；`_create_toolkit` 按 `agent_config.tools.builtin_tools[name].enabled` 注册工具，`async_execution` 仅对 `execute_shell_command`；若有任意 async 工具，自动注册 `view_task/wait_task` 等任务管理工具。
- `_register_skills` 从 workspace 拉技能；`_build_sys_prompt` 用 `prompt.build_system_prompt_from_working_dir`；`create_model_and_formatter(agent_id)` 构造 model+formatter。
- 内置工具列表 (注意改造时不要破坏命名)：execute_shell_command, read_file, write_file, edit_file, grep_search, glob_search, browser_use, desktop_screenshot, view_image, view_video, send_file_to_user, get_current_time, set_user_timezone, get_token_usage, delegate_external_agent, list_agents, chat_with_agent, submit_to_agent, check_agent_task。
- memory_manager 提供的工具通过 `memory_manager.list_memory_tools()` 注册；context_manager 替换 `self.memory` 为其 AgentContext。
- `CommandHandler` 处理 `/compact /new` 等系统命令。

## 5. Skills (`agents/skills_manager.py`)
- 路径：包内内置 `agents/skills/`；workspace 内 `{workspace_dir}/skills/` (兼容 legacy `skill/`)；池 `{WORKING_DIR}/skill_pool/`。
- 内置技能命名：`<name>-<lang>` 其中 lang ∈ {en, zh}；`get_builtin_skill_language_preference()` 读 `{WORKING_DIR}/settings.json` 的 `builtin_skill_language` 或 `language`。
- Manifest：workspace `skill.json`、pool `skill_pool/skill.json`；schema_version 分别为 `workspace-skill-manifest.v1` / `skill-pool-manifest.v1`；用文件锁 (fcntl/msvcrt) + 原子写。
- frontmatter via `python-frontmatter`；安全扫描 `security/skill_scanner`；技能可声明 requirements (`require_bins`, `require_envs`)；运行时通过 `_skill_config_env_var_name` (`QWENPAW_SKILL_CONFIG_<NAME>`) 注入 JSON 配置。
- `ALL_SKILL_ROUTING_CHANNELS = [console, discord, telegram, dingtalk, feishu, imessage, qq, mattermost, wecom, mqtt]`。

## 6. Provider 系统 (`providers/provider_manager.py`)
- 单例：`ProviderManager.get_instance()`；三类 dict：`builtin_providers`, `custom_providers`, `plugin_providers`；`active_model: ModelSlotConfig`。
- 持久化路径：`SECRET_DIR/providers/{builtin,custom,plugin}/`；目录 700。
- builtin 在 `_init_builtins` 内逐个 add：ltclaw_gy_x-local, ollama, lmstudio, openrouter, modelscope, dashscope, aliyun-codingplan(+intl), opencode, openai, azure-openai, anthropic, gemini, deepseek, kimi-cn/intl, minimax-cn/intl, zhipu-cn(+codingplan)/intl(+codingplan), siliconflow-cn/intl。
- 类型：`OpenAIProvider`(默认), `AnthropicProvider`(anthropic/minimax), `GeminiProvider`(gemini), `OllamaProvider`, `LMStudioProvider`, `OpenRouterProvider`。
- `_normalize_provider_id`：`ltclaw-local` -> `ltclaw_gy_x-local`。
- `activate_model(provider_id, model_id)`：校验 -> 写 `active_model` -> `save_active_model` -> `maybe_probe_multimodal` (后台 `_auto_probe_multimodal`)。
- `add_custom_provider/remove_custom_provider/update_provider/fetch_provider_models/add_model_to_provider/update_model_config` 写各自 path；插件 provider 写 plugin_path 且 in-memory 存 `ProviderInfo`。
- 加密：敏感字段经 `security.secret_store.encrypt_dict_fields(PROVIDER_SECRET_FIELDS)`；读时 `decrypt_dict_fields`，自动迁移明文 -> 加密。
- 易踩点：`ProviderManager.active_model` 字段名是 `model` 不是 `model_id`；`minimax-cn` 是 AnthropicProvider 类型，base_url=`https://api.minimaxi.com/anthropic`。

## 7. 插件系统 (`plugins/`)
- `architecture.py`：`PluginManifest{ id, name, version, description, author, entry: PluginEntryPoints{frontend, backend}, dependencies, min_version, meta }`；`PluginRecord{ manifest, source_path, enabled, instance, diagnostics }`。`from_dict` 兼容 legacy `entry_point`。
- `loader.py`：扫 `plugin_dirs` 下子目录里的 `plugin.json`；`load_plugin` 支持 frontend-only；backend 用 `importlib.util.spec_from_file_location`，独立 `module_name=plugin_<id>`，设 `__package__/__path__` 让相对导入工作；要求模块导出 `plugin` 对象并实现 `register(api)` (sync/async)。
- `api.py PluginApi`：`register_provider(provider_id, provider_class, label, base_url, **metadata)`、`register_startup_hook(name, cb, priority)`、`register_shutdown_hook(...)`、`register_control_command(handler, priority_level=10)`，`runtime` 属性返回 `RuntimeHelpers`。
- `registry.py PluginRegistry` 单例：`_providers/_startup_hooks/_shutdown_hooks/_control_commands/_runtime_helpers`；hook 列表按 priority 升序排序。
- `runtime.py RuntimeHelpers(provider_manager)` 暴露 `get_provider/list_providers/log_*`。
- 启动期由 `app/_app.py` 把所有插件 provider 注入 ProviderManager、把 control commands 注入 `app.runner.control_commands.register_command` + `app.channels.command_registry.CommandRegistry.register_command("/<name>", priority_level)`，并跑 startup hooks。

## 8. Channel 系统 (`app/channels/registry.py`)
- 内建 specs：imessage, discord (`.discord_`), dingtalk, feishu, qq, telegram, mattermost, mqtt, console, matrix, voice, sip, wecom, xiaoyi, weixin, onebot；required = {console}。
- `get_channel_registry()` = builtin 缓存 + `_discover_custom_channels()` (扫 `WORKING_DIR/custom_channels`，把 BaseChannel 子类按 `cls.channel` 注册)。
- `register_custom_channel_routes(app)`：在主 app 加载之前调用；每个 custom 模块可定义 `register_app_routes(app)` 注入路由；强制要求 `/api/` 前缀，否则会被 SPA catch-all 吃掉，会打 warning。
- 配置模型 (`config/config.py`)：BaseChannelConfig + 各 channel 子类；DM/Group policy = open|allowlist；require_mention；filter_*。

## 9. 路由层 (`app/routers/`)
- 全局聚合 (`__init__.py`): agents, config, console, cron, local_models, mcp, messages, providers, runner, skills, skills_stream, tools, workspace, envs, token_usage, agent_stats, auth, files, settings, plugins, backup, plan。
- `create_agent_scoped_router()` (`agent_scoped.py`) 在 `/agents/{agentId}` 下挂：chats(=runner), config, cron, mcp, skills, tools, workspace, console, plugins, plan。
- `AgentContextMiddleware`：从 path `/api/agents/{agentId}/...` 抓 agent_id（设 request.state 与 ContextVar），否则取 `X-Agent-Id` 头；读 `X-Root-Session-Id` 写 request.request_context['root_session_id']。
- `agent_context.get_agent_for_request(request, agent_id?)`：优先 override -> request.state.agent_id -> X-Agent-Id -> `config.agents.active_agent or "default"`；校验 profile.enabled；通过 `request.app.state.multi_agent_manager.get_agent()` 拿 Workspace。

## 10. 配置体系 (`config/config.py`, `constant.py`)
- agent_id 校验：`^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$`，长度 2-64，`default` 保留；`generate_short_agent_id` 6 位 shortuuid。
- 主要模型：ModelSlotConfig, ActiveModelsInfo, ACPConfig (默认含 opencode/qwen_code/claude_code/codex)，BaseChannelConfig 与各 channel 子类，AgentProfileConfig/Ref，AgentsConfig，AgentsRunningConfig，AgentsLLMRoutingConfig。
- `constant.py` 重要常量：
  - `WORKING_DIR` = `~/.ltclaw_gy_x` (env `QWENPAW_WORKING_DIR` 优先，存在 legacy 目录则继续用)。
  - `SECRET_DIR` = `WORKING_DIR + ".secret"` (`QWENPAW_SECRET_DIR` 可覆盖)。
  - `CUSTOM_CHANNELS_DIR` = `WORKING_DIR/custom_channels`，`PLUGINS_DIR` = `WORKING_DIR/plugins`，`MODELS_DIR` = `WORKING_DIR/models`，`MEMORY_DIR` = `WORKING_DIR/memory`，`BACKUP_DIR` = `WORKING_DIR + ".backups"`。
  - 文件名：CONFIG_FILE=config.json, CHATS_FILE=chats.json, JOBS_FILE=jobs.json, TOKEN_USAGE_FILE=token_usage.json, HEARTBEAT_FILE=HEARTBEAT.md, DEBUG_HISTORY_FILE=debug_history.jsonl。
  - BUILTIN_QA_AGENT_ID="LTCLAW-GY.X_QA_Agent_0.2"; BUILTIN_QA_AGENT_NAME="LTClaw QA"; BUILTIN_QA_AGENT_SKILL_NAMES=("guidance","QA_source_index"); LEGACY_QA_AGENT_ID="LTCLAW-GY.X_QA_Agent_0.1beta1"。
  - 环境变量前缀：`QWENPAW_*`，自动回退 `COPAW_*`。
  - DOCS_ENABLED=`QWENPAW_OPENAPI_DOCS`；CORS_ORIGINS=`QWENPAW_CORS_ORIGINS`。
- 迁移 (`app/migration.py`)：legacy 单 agent -> default agent workspace；目录 `WORKING_DIR/workspaces/default`；搬 sessions/memory/active_skills/customized_skills + chats.json/jobs.json/feishu_receive_ids.json/dingtalk_session_webhooks.json；写 agent.json (atomic)。

## 11. 安全
- `app/auth.py`：单用户；`QWENPAW_AUTH_ENABLED` 控开关；`auth.json` 在 `SECRET_DIR`；用 stdlib HMAC-SHA256 自签 token (无 PyJWT)；token jti 支持吊销；7 天默认，最长 100 年；`_PUBLIC_PATHS={/api/auth/login, /api/auth/status, /api/auth/register, /api/version, /api/settings/language, /api/plugins}`，`_PUBLIC_PREFIXES=(/assets/, /logo.png, /ltclaw_gy_x-symbol.svg, /api/plugins/)`。改造时**不要**把新 API 加进 _PUBLIC_PATHS。
- `security/secret_store.py`：master key Fernet (AES-128-CBC + HMAC-SHA256)；优先 `keyring._KEYRING_SERVICE="ltclaw_gy_x"`，回退 `SECRET_DIR/.master_key` (mode 0o600)；容器/headless Linux/CI 自动跳过 keyring；密文前缀 `ENC:`；解密失败原样返回不崩。提供 `PROVIDER_SECRET_FIELDS / AUTH_SECRET_FIELDS / encrypt_dict_fields / decrypt_dict_fields / is_encrypted / reload_master_key_from_disk`。
- `security/tool_guard/` + `agents/tool_guard_mixin.py`：在 ReActAgent 的 `_acting/_reasoning` 上拦截工具调用做审批/拒绝。
- `security/skill_scanner/`：技能目录扫描，导入 zip 时强制路径越权与 symlink 检查。

## 12. TaskTracker (`app/runner/task_tracker.py`)
- 每 workspace 一个；`run_key -> _RunState{task, queues[], buffer[]}`；锁内修改。
- 用途：聊天 SSE 多订阅 + 重连 (buffer 回放)；reload 时检查 in-flight。
- 关键 API：`get_status / has_active_tasks / list_active_tasks / wait_all_done(timeout=300) / register_external_task(run_key) / unregister_external_task / attach / detach_subscriber / request_stop / attach_or_start`。
- DynamicMultiAgentRunner 在 stream_query/query_handler 里用 `register_external_task("ext-<uuid>")`。

## 13. 控制台前端 (`console/`)
- React 18 + Vite + AntD + `@agentscope-ai/{chat,design,icons}`；`react-router-dom@7`；i18n (zh/en/ja/ru)。
- `main.tsx`：`installHostExternals()` 把 React/AntD 等挂 window 给插件 UI 共享；`registerHostModulesDynamic()` 异步注册 host modules。
- `App.tsx`：ThemeProvider + PluginProvider + ApprovalProvider；`getRouterBasename` 检测 `/console` 自适应；AuthGuard 走 `/api/auth/status` + `/auth/verify`；`pluginsLoading` 时不渲染路由 (避免插件 patch 时序问题)。
- API 模块在 `console/src/api/modules/`；plugin 系统在 `console/src/plugins/`。

## 14. 官网 (`website/`)
- 独立 Vite + React 站，完全脱离后端；用 PM2 部署，默认端口 8088 (与后端冲突，部署时选一边)；`scripts/website_build.sh` 构建。

## 15. 测试
- `pyproject.toml` markers: slow/unit/contract/integration；`asyncio_mode=auto`；coverage `fail_under=30`，omit `*/tests/*`。
- `tests/contract/`：`BaseContractTest` -> `ChannelContractTest` -> 各 channel；防止改基类只修一个子类时打坏其它。
- `tests/integration/test_app_startup.py`：subprocess `python -m qwenpaw app --port=free --log-level info`，轮询 `/api/version`，再 GET `/console/` 校验 HTML。
- `tests/unit/` 按域分：agents/app/channels/cli/local_models/providers/routers/security/token_usage/utils/workspace。

## 16. 改造扩展面 (开工速查)
- 新功能后端落点：`src/ltclaw_gy_x/<domain>/` (纯新增包) + `src/ltclaw_gy_x/app/routers/<domain>.py` (在 `routers/__init__.py` 的两处都 include) + `src/ltclaw_gy_x/agents/tools/<domain>_tools.py` + 在 react_agent 的 `tool_functions` dict 里加条目（受 `enabled_tools` 开关控制，默认开关在 `agent_config.tools.builtin_tools`）。
- 新模板/方法论：放 `agents/skills/<name>-zh|en/SKILL.md` (frontmatter 必填)，自动被 skills_manager 发现。
- 新外部系统集成：优先做插件，落 `WORKING_DIR/plugins/<id>/plugin.json + backend.py`，通过 PluginApi 注册 provider/hook/control command。
- 新 channel：放 `WORKING_DIR/custom_channels/<name>.py`，子类化 `app.channels.base.BaseChannel`，类属性 `channel="<key>"`；如需 HTTP 路由定义模块级 `register_app_routes(app)` 且必须 `/api/` 前缀。
- 新 agent 角色：通过 `config.agents.profiles` 增配置，不要新建 Agent 类；用 system prompt + 启用工具集 + 默认 skill 集合区分角色。
- 工作区子目录扩展：直接在自己包里定义路径常量，不动全局 `constant.py`；建议落 `{workspace_dir}/<domain>/`；备份 (`backup/`)、卸载 (`cli/uninstall_cmd.py`、`cli/clean_cmd.py`) 要同步纳入。
- **不要动**：`app/_app.py` lifespan 主链、`multi_agent_manager`、`workspace/*`、`providers/provider_manager`、`plugins/loader`、`security/secret_store`、`auth.py` 的 `_PUBLIC_PATHS`、`agents/react_agent.py` 主类（按扩展点加东西即可）。
- 同步阻塞 IO 走 `asyncio.to_thread`（参考 `service_manager._get_or_create_service`）。
