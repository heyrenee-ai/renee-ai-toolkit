# Renee AI Toolkit

Renee 实际使用并持续迭代的 AI 工作流模板与 Skills。内容面向 AI 初学者，尽量使用自然语言说明，可以按自己的项目修改。

## 当前内容

### Claude Code 长任务三件套

用项目文件承接跨会话上下文，减少 AI 在复杂长任务中遗忘进度、重复犯错和读错文件的问题。

| 模板 | 什么时候用 | 解决什么问题 |
| --- | --- | --- |
| [`/prime`](claude-code/long-task-workflow/prime-template.md) | 开启新会话或换 Agent 接手时 | 从项目文件恢复目标、进度和下一步 |
| [`/wrap`](claude-code/long-task-workflow/wrap-handoff-template.md) | 阶段收尾、暂停或准备交接时 | 更新状态、待办、交接和长期经验 |
| [`/route-audit`](claude-code/long-task-workflow/route-audit-template.md) | 文件变多、结构变化或定期整理时 | 检查重复、错放、过载、过期和断链 |

## 怎么使用

1. 打开需要的模板文件；
2. 复制其中“可直接复用的指令模板”；
3. 根据自己的项目文件名和工作方式调整；
4. 可以直接作为 Prompt 使用，也可以保存为 Claude Code 自定义命令。

如果保存为项目级自定义命令，可以将调整后的命令放入项目的 `.claude/commands/` 目录，例如：

```text
.claude/commands/
├── prime.md
├── wrap.md
└── route-audit.md
```

## 重要说明

- `/prime`、`/wrap`、`/route-audit` 是 Renee 自定义的工作流模板，不是 Claude Code 默认内置命令；
- 模板提供的是结构和思路，不代表每个项目都必须创建相同文件；
- 执行移动、删除、合并或重写前，应先检查真实文件并获得用户确认；
- 请勿把密码、Token、Cookie、客户资料或其他私人信息写入公开仓库。

## License

[MIT License](LICENSE)

