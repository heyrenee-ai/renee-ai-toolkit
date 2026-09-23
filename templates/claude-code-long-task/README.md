# Claude Code 长任务三件套

用于跨会话续做项目的三份独立指令模板。按当前阶段选择一份，复制其中「可直接复用的指令模板」代码块到 Claude Code，结合自己的文件名使用。

| 什么时候用 | 模板 | 用途 |
| --- | --- | --- |
| 开始或接续任务 | [Prime](prime-template.md) | 从项目文件恢复目标、进度与下一步 |
| 暂停或完成阶段 | [Wrap / Handoff](wrap-handoff-template.md) | 更新进度，留下下一会话可接手的交接 |
| 文件变多或结构调整后 | [Route Audit](route-audit-template.md) | 检查重复、错放、过载与失效引用 |

## 怎么使用

直接复制指令即可，不需要安装 Skill。也可以按你使用的 Claude Code 版本，将指令保存为自己的自定义命令；文中的 `/prime`、`/wrap`、`/route-audit` 是建议名称，下载仓库不会自动注册命令。

项目文件按需准备：`CLAUDE.md` 保存稳定规则，`HANDOFF.md` 保存当前交接，`PLANS.md` 保存计划，`PLAYBOOK.md` 保存可复用经验。不要为了套用模板创建不需要的文件。各模板包含具体准备说明和执行边界。

这组三件套与 [海外账号与起号调研 Skill](../../skills/account-launch-research/README.md) 独立，可单独使用。请勿把私人交接、客户资料或凭据提交到公开仓库。

[返回 Renee AI Toolkit](../../README.md) · [MIT 许可](../../LICENSE)

