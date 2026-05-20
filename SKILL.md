---
name: copaw-architecture
description: "QwenPaw/CoPaw 工作站架构指南（v1.3.0）。涵盖目录结构、配置、技能/插件系统、Cron、记忆、安全。当用户询问架构、目录、配置、插件开发、技能系统时触发。"
metadata:
  copaw:
    emoji: "🐾"
  skill_version: "6.0.0"
  author: "CoPaw Expert"
  license: "MIT"
  scanned_version: "QwenPaw v1.1.0"
  scan_date: "2026-04-15"
  update_notes: "v6.0.0：修正agent.json必须包含完整结构（channels/mcp/running等），provider_id必须是minimax-cn"
---

# QwenPaw 架构指南

> 📦 v1.3.0 | `qwenpaw` 包

## 路径体系

| 类型 | Windows | Docker |
|------|---------|--------|
| **WORKING_DIR** | `~/.copaw` | `/app/working` |
| **SECRETS_DIR** | `~/.copaw.secret/` | `/app/working.secret` |
| **工作区** | `~/.copaw/workspaces/<ws>/` | `/app/working/workspaces/<ws>/` |

## 目录结构

```
/app/working/
├── config.json              # 全局配置（agent注册表）
├── plugin_pool/             # 全局插件池（解压后的插件包）
│   ├── gpt-image2-tool/     # 图像生成工具插件
│   ├── qwen-image-tool/     # 通义图像工具插件
│   ├── wan27-tool/          # 文生视频工具插件
│   ├── qwenpaw-pet/         # QwenPaw 伴侣宠物插件
│   └── cloudpaw/            # 云部署能力增强插件
├── skill_pool/              # 全局技能仓库
│   └── skill.json           # 全局技能索引
└── workspaces/
    └── <workspace>/
        ├── agent.json       # Agent 配置（必须完整结构）
        ├── skill.json       # 工作区技能清单（数组格式）
        ├── AGENTS.md / SOUL.md / PROFILE.md / RULES.md / MEMORY.md
        ├── memory/
        └── skills/
```

> 📁 **插件路径**（Windows）：`C:\Users\<user>\.copaw\plugins\`  
> 📁 **插件路径**（Docker）：`/app/working/plugin_pool/`  
> 插件不由 QwenPaw 内置索引管理，而是通过 `qwenpaw plugin install` 命令解压安装到该目录，运行时动态加载。

---

## Agent 注册机制（⭐关键）

### config.json agents 结构

```json
{
  "agents": {
    "active_agent": "default",
    "agent_order": ["default", "agent_id"],
    "profiles": {
      "agent_id": {
        "id": "agent_id",           // ✅ 必填，必须与 key 一致
        "workspace_dir": "/app/working/workspaces/agent_id",  // ✅ 必填
        "enabled": true               // ✅ 必填
      }
    }
  }
}
```

### agent.json 完整结构（⭐必须完整！）

**⚠️ 重要发现**：agent.json 不能只有精简字段，必须包含完整的 channels/mcp/running 等结构，否则会报错 "Failed to save active model to agent config"。

```json
{
  "id": "agent_id",
  "name": "显示名称",
  "description": "描述",
  "workspace_dir": "/app/working/workspaces/agent_id",
  "channels": {
    "console": {
      "enabled": true,
      "bot_prefix": "",
      "filter_tool_messages": false,
      "filter_thinking": false,
      "dm_policy": "open",
      "group_policy": "open",
      "allow_from": [],
      "deny_message": "",
      "require_mention": false
    }
  },
  "mcp": { "clients": {} },
  "heartbeat": { "enabled": false, "every": "6h", "target": "main" },
  "running": {
    "max_iters": 100,
    "llm_retry_enabled": true,
    "llm_max_retries": 3,
    "llm_backoff_base": 1.0,
    "llm_backoff_cap": 10.0,
    "llm_max_concurrent": 10,
    "llm_max_qpm": 600,
    "llm_rate_limit_pause": 5.0,
    "llm_rate_limit_jitter": 1.0,
    "llm_acquire_timeout": 300.0,
    "max_input_length": 131072,
    "history_max_length": 10000,
    "context_compact": {
      "token_count_model": "default",
      "token_count_use_mirror": false,
      "token_count_estimate_divisor": 4,
      "context_compact_enabled": true,
      "memory_compact_ratio": 0.75,
      "memory_reserve_ratio": 0.1,
      "compact_with_thinking_block": true
    },
    "tool_result_compact": {
      "enabled": true,
      "recent_n": 2,
      "old_max_bytes": 3000,
      "recent_max_bytes": 50000,
      "retention_days": 5
    },
    "memory_summary": {
      "memory_summary_enabled": true,
      "memory_prompt_enabled": true,
      "force_memory_search": false,
      "force_max_results": 1,
      "force_min_score": 0.3,
      "force_memory_search_timeout": 10.0,
      "rebuild_memory_index_on_start": false
    },
    "embedding_config": {
      "backend": "openai",
      "api_key": "",
      "base_url": "",
      "model_name": "",
      "dimensions": 1024,
      "enable_cache": true,
      "use_dimensions": false,
      "max_cache_size": 3000,
      "max_input_length": 8192,
      "max_batch_size": 10
    },
    "memory_manager_backend": "remelight"
  },
  "llm_routing": {
    "enabled": false,
    "mode": "local_first",
    "local": { "provider_id": "", "model": "" }
  },
  "active_model": {
    "provider_id": "minimax-cn",     // ⭐ 必须是 minimax-cn
    "model": "MiniMax-M2.7"
  },
  "language": "zh",
  "system_prompt_files": ["AGENTS.md", "SOUL.md", "PROFILE.md", "RULES.md"],
  "tools": {
    "builtin_tools": {
      "execute_shell_command": { "name": "execute_shell_command", "enabled": false, "description": "Execute shell commands", "display_to_user": true, "async_execution": false, "icon": "💻" },
      "read_file": { "name": "read_file", "enabled": false, "description": "Read file contents", "display_to_user": true, "async_execution": false, "icon": "📄" },
      "write_file": { "name": "write_file", "enabled": false, "description": "Write content to file", "display_to_user": true, "async_execution": false, "icon": "✍️" },
      "edit_file": { "name": "edit_file", "enabled": false, "description": "Edit file using find-and-replace", "display_to_user": true, "async_execution": false, "icon": "🖊️" },
      "grep_search": { "name": "grep_search", "enabled": false, "description": "Search file contents by pattern", "display_to_user": true, "async_execution": false, "icon": "🔍" },
      "glob_search": { "name": "glob_search", "enabled": false, "description": "Find files matching a glob pattern", "display_to_user": true, "async_execution": false, "icon": "📁" },
      "browser_use": { "name": "browser_use", "enabled": false, "description": "Browser automation", "display_to_user": true, "async_execution": false, "icon": "🌐" },
      "desktop_screenshot": { "name": "desktop_screenshot", "enabled": false, "description": "Capture desktop screenshots", "display_to_user": true, "async_execution": false, "icon": "📸" },
      "view_image": { "name": "view_image", "enabled": false, "description": "Load image into LLM context", "display_to_user": false, "async_execution": false, "icon": "🖼️" },
      "view_video": { "name": "view_video", "enabled": false, "description": "Load video into LLM context", "display_to_user": false, "async_execution": false, "icon": "🎥" },
      "send_file_to_user": { "name": "send_file_to_user", "enabled": false, "description": "Send files to user", "display_to_user": true, "async_execution": false, "icon": "📤" },
      "get_current_time": { "name": "get_current_time", "enabled": false, "description": "Get current date and time", "display_to_user": true, "async_execution": false, "icon": "🕐" },
      "set_user_timezone": { "name": "set_user_timezone", "enabled": false, "description": "Set user timezone", "display_to_user": true, "async_execution": false, "icon": "🌍" },
      "get_token_usage": { "name": "get_token_usage", "enabled": false, "description": "Get token usage", "display_to_user": true, "async_execution": false, "icon": "📊" },
      "list_agents": { "name": "list_agents", "enabled": false, "description": "List configured agents", "display_to_user": true, "async_execution": false, "icon": "🤖" },
      "chat_with_agent": { "name": "chat_with_agent", "enabled": false, "description": "Send message to another agent", "display_to_user": true, "async_execution": false, "icon": "💬" }
    }
  }
}
```

> ⚠️ **精简版 agent.json 会导致 "Failed to save active model" 错误！必须使用完整结构。**

---

## 插件系统（⭐核心新增）

QwenPaw v1.1.7+ 支持通过插件机制扩展 Agent 能力。插件以独立包形式安装，可注册工具、Agent、HTTP 路由、生命周期钩子、Provider、工具调用策略和控制命令。

### 插件包文件结构

```
<plugin-name>/
├── plugin.json             # 插件清单（必填，定义元数据、入口、工具描述）
├── entry.py                # 入口文件（entry.backend 指向的文件，含 PluginApi 注册逻辑）
├── tool.py                 # 工具实现文件（两步式插件，含 ToolResponse 逻辑）
├── config.py               # 配置管理（可选，config_fields 的读取/校验逻辑）
├── utils/                  # 工具函数目录（可选）
│   ├── __init__.py
│   └── helper.py
└── assets/                 # 静态资源（可选，图片/字体等）
    └── icon.png
```

**两步式工具插件**（最常见模式）由 `plugin.json` + 入口文件 + 工具实现文件组成：

| 文件 | 作用 | 示例 |
|------|------|------|
| `plugin.json` | 声明元数据、工具注册信息、用户配置字段 | `gpt-image2-tool/plugin.json` |
| `entry.py` | 实例化 `PluginApi`，调用 `register_tool` 等方法注册能力 | `gpt_image2.py` |
| `tool.py` | 实现工具函数逻辑，使用 `ToolResponse` 返回结果 | 内部实现 |

### plugin.json 完整 Schema（⭐基于真实插件）

所有字段均从 5 个真实生产插件（`gpt-image2-tool`、`qwen-image-tool`、`wan27-tool`、`qwenpaw-pet`、`cloudpaw`）提取。

```json
{
  // ===== 基础元数据 =====
  "id": "gpt-image2-tool",              // ✅ 必填，唯一标识符（目录名通常与其一致）
  "name": "GPT Image 2 Tool",          // ✅ 必填，显示名称
  "version": "1.1.1",                   // ✅ 必填，语义化版本
  "type": "tool",                       // ✅ 必填，插件类型：tool | general | provider | lifecycle
  "description": "简短英文描述",        // ✅ 必填
  "description_i18n": {                 // ✅ 推荐，国际化描述
    "zh-CN": "中文描述",
    "en-US": "English description"
  },
  "author": "QwenPaw Team",             // ✅ 推荐

  // ===== 入口配置 =====
  "entry": {
    "backend": "plugin_entry.py"        // ✅ 必填，入口 Python 文件（相对于插件根目录）
    // "frontend": "ui/index.html"      // 🔄 可选，前端页面（未来扩展）
  },

  // ===== 依赖与兼容性 =====
  "dependencies": [                     // 🔄 可选，Python 依赖（pip 包名）
    "httpx>=0.24.0",
    "Pillow>=10.0.0"
  ],
  "min_version": "1.1.7",               // ✅ 推荐，最低 QwenPaw 版本要求

  // ===== 工具元信息（type=tool 时必填） =====
  "meta": {
    "tools": [                          // 🔄 可选，注册的工具列表
      {
        "name": "generate_image",       // ✅ 必填，工具名（Agent 调用时的标识）
        "description": "工具描述",       // ✅ 必填
        "icon": "🎨",                   // 🔄 可选，表情图标
        "requires_config": true,        // 🔄 可选，是否需要用户配置才能使用
        "config_fields": [              // 🔄 可选，用户配置字段列表
          {
            "name": "api_key",          // ✅ 必填，字段名
            "label": "API Key",         // ✅ 必填，显示标签
            "type": "password",         // ✅ 必填，字段类型：text | password | number | select
            "required": true,            // 🔄 可选，是否必填
            "placeholder": "sk-...",    // 🔄 可选，占位提示
            "help": "使用说明",          // 🔄 可选，帮助文本
            "default": "默认值",         // 🔄 可选，默认值
            "min": 1,                   // 🔄 可选（type=number），最小值
            "max": 300,                 // 🔄 可选（type=number），最大值
            "options": [                // 🔄 可选（type=select），选项列表
              {"label": "选项1", "value": "opt1"}
            ]
          }
        ],
        "config_sections": [            // 🔄 可选，配置分组（qwenpaw-pet 模式）
          {
            "title": "基础设置",
            "description": "基础配置说明",
            "fields": ["api_key", "endpoint"]
          }
        ]
      }
    ],
    "api_key_url": "https://...",       // 🔄 可选，API Key 获取地址
    "api_key_hint": "获取说明",          // 🔄 可选，API Key 提示文字
    "model_url": "https://..."          // 🔄 可选，模型信息地址（wan27-tool 用）
  },

  // ===== 废弃字段（❌ 不要再使用） =====
  // ❌ "entry_point": "plugin.py"       → 已废弃，改用 "entry": { "backend": "plugin.py" }
  // ❌ "capabilities": []               → 已废弃，改用 "meta.tools"
  // ❌ "permissions": []                → 已废弃，QwenPaw 不校验此字段
  // ❌ "config_schema": {}              → 已废弃，改用 "meta.tools[].config_fields"
}
```

#### 插件类型（`type` 字段）

| 类型 | 用途 | 代表插件 | 典型注册方法 |
|------|------|---------|------------|
| `tool` | 注册工具给 Agent 使用 | `gpt-image2-tool`、`qwen-image-tool`、`wan27-tool` | `register_tool()` |
| `general` | 综合型插件，可注册多种能力 | `cloudpaw`、`qwenpaw-pet` | `register_tool` + `register_agent` + `register_http_router` 等 |
| `provider` | 提供 LLM Provider | - | `register_provider()` |
| `lifecycle` | 生命周期挂钩 | - | `register_startup_hook()` + `register_shutdown_hook()` |

### PluginApi 参考（9 个方法）

插件入口文件通过 `PluginApi` 实例注册能力。以下是 v1.1.7+ 所有可用方法：

#### `register_tool(tool_name, tool_func, ...)` — 注册工具

最重要的方法。将 Python 函数注册为 Agent 可直接调用的工具。

```python
from qwenpaw.plugin_api import PluginApi

api = PluginApi()

@api.register_tool(
    tool_name="generate_image",
    description="Generate images from text prompts",
    icon="🎨",
    requires_config=True
)
async def generate_image(ctx, prompt: str, size: str = "1024x1024") -> dict:
    """工具实现。ctx 为 ToolContext，包含 get_tool_config() 等方法。"""
    config = ctx.get_tool_config("generate_image")
    api_key = config.get("api_key")
    # ... 业务逻辑
    from qwenpaw.plugin_api import ToolResponse
    return ToolResponse.success(result={"url": "..."})
```

**`register_tool` 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tool_name` | `str` | ✅ | 工具标识符，需与 `plugin.json` `meta.tools[].name` 一致 |
| `description` | `str` | 🔄 | 工具描述（建议填，覆盖 plugin.json 中的 description） |
| `icon` | `str` | 🔄 | 表情图标 |
| `requires_config` | `bool` | 🔄 | 是否依赖用户配置 |

**工具函数签名**：

```python
# 同步
def my_tool(ctx: ToolContext, param1: str, param2: int = 0) -> dict: ...

# 异步（推荐）
async def my_tool(ctx: ToolContext, param1: str, param2: int = 0) -> dict: ...
```

- 第一个参数必须是 `ctx: ToolContext`
- 后续参数对应工具输入参数（Agent 按需填充）
- 返回值：`ToolResponse.success(result=...)` 或 `ToolResponse.error(message=...)`

**`ToolContext` 方法**：

| 方法 | 说明 |
|------|------|
| `get_tool_config(tool_name=None)` | 获取当前工具的用户配置（需 `requires_config=True`） |
| `get_plugin_config()` | 获取整个插件的全局配置 |
| `log_info(msg)` / `log_error(msg)` | 日志记录 |

#### `register_provider(provider_name, provider_cls, ...)` — 注册 LLM Provider

```python
api.register_provider(
    provider_name="my_provider",
    provider_cls=MyModelProvider,
    description="Custom LLM provider"
)
```

#### `register_startup_hook(hook_func)` — 注册启动钩子

插件加载后、首次使用前执行。

```python
@api.register_startup_hook
async def on_startup():
    """初始化连接、加载模型、检查依赖等。"""
    await db.connect()
    logger.info("Plugin startup complete")
```

#### `register_shutdown_hook(hook_func)` — 注册关闭钩子

QwenPaw 退出前执行，用于资源清理。

```python
@api.register_shutdown_hook
async def on_shutdown():
    await db.close()
    logger.info("Plugin shutdown complete")
```

#### `register_agent(agent_spec)` — 注册专用 Agent

注册一个可在多 Agent 协作中被调用的 Agent 角色。

```python
api.register_agent({
    "name": "image-agent",
    "description": "Specialized image generation agent",
    "system_prompt": "You are an image generation expert...",
    "tools": ["generate_image_gpt"]
})
```

#### `register_http_router(prefix, router)` — 注册 HTTP 路由

为插件提供 HTTP API 端点，常用于管理面板或外部调用。

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def status():
    return {"status": "ok"}

api.register_http_router(prefix="/my-plugin", router=router)
```

#### `register_hook_point(point_name, handler_func)` — 注册自定义 Hook 点

向 QwenPaw 的 Hook 系统注册自定义回调点。

```python
@api.register_hook_point("pre_process_image")
async def pre_process_image_handler(image_data: bytes) -> bytes:
    """在处理图像前调用。"""
    return processed_data
```

#### `register_tool_calling_strategy(name, strategy_cls)` — 注册工具调用策略

注册自定义的工具调用策略（如并行调用、顺序调用、ReAct 等）。

```python
api.register_tool_calling_strategy(
    name="my_strategy",
    strategy_cls=MyCallingStrategy
)
```

#### `register_control_command(name, handler_func, ...)` — 注册控制命令

在 `qwenpaw plugin` CLI 下注册子命令。

```python
@api.register_control_command(
    name="status",
    help="Show plugin status"
)
async def status_command(args: list[str]) -> str:
    return "Plugin is running"
```

### 插件生命周期

```
用户运行 qwenpaw plugin install <package.zip>
     │
     ▼
[1. 安装] → 解压到 plugin_pool/<plugin-id>/
     │
     ▼
[2. 解析] → 读取 plugin.json，校验 schema
     │           │
     │     ┌─────┴─────┐
     │     │ 校验失败   │ 校验通过
     │     │ (拒绝加载) │
     │     └───────────┘
     │           │
     ▼           ▼
[3. 加载] → Python import getattr(entry.backend)
     │
     ▼
[4. 初始化] → 执行入口文件，实例化 PluginApi
     │           调用 register_* 方法注册能力
     │
     ▼
[5. 启动钩子] → 执行所有 register_startup_hook
     │           （异步，可等待完成）
     │
     ▼
[6. 运行] → 注册的工具/Agent/路由对外可用
     │
     ▼
[7. 关闭钩子] → QwenPaw 退出时执行 register_shutdown_hook
```

### 插件开发模式（实战总结）

#### 模式 A：工具插件（两步式）— 最常见

3 个真实工具插件（`gpt-image2-tool`、`qwen-image-tool`、`wan27-tool`）均采用此模式。

```
plugin.json         → 声明 meta.tools（工具列表 + config_fields）
entry.py            → PluginApi.register_tool() 注册
tool_impl.py        → 异步工具函数 + ToolResponse
```

**特点**：`requires_config: true` 的工具有独立的配置面板（从 `plugin.json` 的 `config_fields` 渲染），用户需先配置再使用。

#### 模式 B：综合插件（多能力）— cloudpaw

```
plugin.json         → type: "general"，注册多种能力
entry.py            → register_tool + register_http_router + register_agent
skills/             → 内置技能包，安装时注入 skill_pool（⭐关键模式）
```

**核心模式**：插件可通过 `register_startup_hook` 向 `skill_pool/` 写入技能文件，使 Agent 直接获得全新的 Skill 能力，而不仅仅是工具。

#### 模式 C：功能增强插件 — qwenpaw-pet

```
plugin.json         → type: "general"，带 config_sections 分组
entry.py            → register_http_router + register_tool + register_startup_hook
```

**特点**：通过 HTTP 路由提供管理界面 + 注册有限工具 + 启动钩子执行初始化。

### 插件开发 SOP

```bash
# 1. 脚手架生成（使用 plugin-forge skill）
# 详见 skills/plugin-forge/SKILL.md

# 2. 本地安装测试
qwenpaw plugin install ./my-plugin.zip

# 3. 查看已安装插件
qwenpaw plugin list

# 4. 卸载插件
qwenpaw plugin uninstall my-plugin

# 5. 插件调试
# - 查看日志：检查 QwenPaw 日志输出
# - 验证注册：qwenpaw tools list（查看注册的工具）
```

---

## 技能系统（两种 skill.json 格式）

### 全局 skill_pool/skill.json（对象格式）

```json
{ "skills": { "<skill_name>": { "name": "...", "description": "...", "version_text": "1.0.0", "source": "customized", "protected": false, "updated_at": "..." } } }
```

### 工作区 skill.json（对象格式）

```json
{
  "skills": {
    "skill_name": {
      "name": "skill_name",
      "enabled": true,
      "source": "copaw_default"
    }
  }
}
```

> ⚠️ **两种格式都是对象！** 全局的 key 是 skill 名称，workspace 的 key 也是 skill 名称。

---

## 记忆系统

| 文件 | 用途 |
|------|------|
| `memory/YYYY-MM-DD.md` | 每日笔记 |
| `MEMORY.md` | 长期记忆 |
| `AGENTS.md` | 行为规范 |
| `SOUL.md` | 个性定义 |
| `PROFILE.md` | 用户资料 |
| `RULES.md` | 铁律 |

## CLI 命令

```bash
qwenpaw agent list               # 列出 Agent
qwenpaw agents chat              # 与其他 Agent 通信
qwenpaw plugin list              # 列出插件
qwenpaw skills list              # 列出技能
qwenpaw cron list                # 列出定时任务
```

---

## 常见错误与排查（⭐实操经验汇总）

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 新 agent 不在 `qwenpaw agent list` | profile 缺少 `id`/`workspace_dir`/`enabled` | 按正确格式补全三个字段 |
| "Failed to save active model" | agent.json 结构不完整（缺少 channels/mcp/running 等） | 必须使用完整结构（见上方模板） |
| "Failed to save active model" | `provider_id` 用了 `minimax-custom` | 必须用 `minimax-cn` |
| 聊天型 agent 能用工具 | 没配置 `tools.builtin_tools` | 显式禁用所有工具 |
| MD 文件不生效 | 没在 `system_prompt_files` 声明 | 显式列出文件名 |
| 技能不生效 | 全局 `skill_pool/skill.json` 没注册 | 必须注册到全局索引 |
| skill.json 格式错误 | 全局和工作区格式混淆 | 全局是对象，workspace 是数组 |
| Windows zip 路径问题 | 解压后路径带反斜杠 | Python zipfile 处理 |
| `agents chat` 返回 200 但无文本 | 正常现象，异步返回 | 检查 session 是否创建 |

---

## Hook 机制（AgentScope 回调）

QwenPaw 基于 **AgentScope** 的 Hook 接口，支持在 Agent 生命周期 8 个关键节点插入自定义回调。

### 可用 Hook 类型

| Hook 类型 | 触发时机 | 签名 |
|-----------|----------|------|
| `pre_reasoning` | 🔁 推理之前 | `(agent, kwargs) -> dict \| None` |
| `post_reasoning` | 🔁 推理之后 | `(agent, kwargs, result) -> dict \| None` |
| `pre_acting` | 🎭 执行动作前 | `(agent, kwargs) -> dict \| None` |
| `post_acting` | 🎭 执行动作后 | `(agent, kwargs, result) -> dict \| None` |
| `pre_reply` | 💬 回复前 | `(agent, kwargs) -> dict \| None` |
| `post_reply` | 💬 回复后 | `(agent, kwargs, result) -> dict \| None` |
| `pre_print` | 🖨️ 打印前 | `(agent, kwargs) -> dict \| None` |
| `post_print` | 🖨️ 打印后 | `(agent, kwargs, result) -> dict \| None` |

### 内置 Hook（已注册）

| Hook | 类型 | 功能 |
|------|------|------|
| `BootstrapHook` | `pre_reasoning` | 检测 BOOTSTRAP.md，首次交互时引导用户配置身份 |
| `MemoryCompactionHook` | `pre_reasoning` | 上下文窗口接近上限时自动压缩旧消息 |
| `MemPalaceImportHook` | `post_reply` | 每次回复后自动将会话导入记忆宫殿 |

### 在 Skill 中注册 Hook

```python
# 1. 创建 Hook 类
class MyHook:
    async def __call__(
        self,
        agent,                     # Agent 实例
        kwargs: dict[str, Any],    # 输入参数
    ) -> dict[str, Any] | None:
        # 你的逻辑
        return None  # 或返回修改后的 kwargs

class MyPostHook:
    async def __call__(
        self,
        agent,
        kwargs: dict[str, Any],
        result,                    # 执行结果
    ) -> dict[str, Any] | None:
        # 你的逻辑
        return None

# 2. 在 Agent 初始化时注册
my_hook = MyHook()
agent.register_instance_hook(
    hook_type="post_reply",        # 触发时机
    hook_name="my_hook",           # 唯一名称
    hook=my_hook.__call__,
)
```

### 典型用途

| Hook | 适用场景 |
|------|----------|
| `pre_reasoning` | 修改输入参数、检查上下文、注入引导 |
| `post_reasoning` | 记录推理结果、分析思考过程 |
| `pre_acting` | 拦截/修改工具调用、安全检查 |
| `post_acting` | 记录工具执行结果、后处理 |
| `post_reply` | 自动保存会话、分析回复、触发下游任务 |
