# 🐾 QwenPaw Architecture Skill

QwenPaw/CoPaw 个人 AI 助手工作站架构指南（v1.1.0）。

## 安装

复制到工作区技能目录（Docker）：

```bash
cp -r . /app/working/workspaces/default/skills/copaw-architecture/
cp -r . /app/working/skill_pool/copaw-architecture/
```

Windows（conda-pack 安装）：

```bash
cp -r . ~/.copaw/skill_pool/copaw-architecture/
```

## 内容

- **SKILL.md** — 架构指南（插件系统、技能系统、Cron、记忆、路径对比 Windows/Docker）
- **scripts/** — 自检脚本 `inspect_copaw.py`

## 触发条件

- "QwenPaw 架构" / "CoPaw 架构"
- "QwenPaw 目录结构"
- "如何配置 QwenPaw"
- "插件怎么开发" / "Plugin API"
- "技能怎么开发"
- "Cron 定时任务"
- "帮我检查 QwenPaw 配置"

## 路径速查

| | Windows | Docker |
|---|---------|--------|
| WORKING_DIR | `~/.copaw` | `/app/working` |
| SECRETS_DIR | `~/.copaw.secret` | `/app/working.secret` |
| 插件目录 | `~/.copaw/plugins/` | `/app/working/plugins` |
