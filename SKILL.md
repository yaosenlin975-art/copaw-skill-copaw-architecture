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
