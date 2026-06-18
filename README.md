# The Rites of Zhou（wenyan-web）

一个轻量的本地 Web 小工具：输入现代语境下想表达的话，让大模型生成带有古意、但仍然适合直接发送的中文回应。

## 功能

- 提供 `V1` 极简界面和 `V2` 双栏界面
- 支持 `OpenAI` 兼容、`Gemini`、`Anthropic` 三类接口
- 支持在页面内保存 `API Type`、`API Base`、`Model`
- 支持历史记录、范例输入、结果复制

## 运行

```bash
python server.py
```

启动后可访问：

- `http://127.0.0.1:8765/V2`：卡片面板
- `http://127.0.0.1:8765/V1`：极简版本

## 配置

有两种方式：

1. 直接编辑 `apikey.py` 中的默认配置
2. 在页面中填写配置后点击“保存配置”

页面保存后会写入项目根目录的 `apikey.local.json`，并立即更新当前服务进程的默认配置。

额外说明：

- `apikey.local.json` 已加入 `.gitignore`，适合保存本地私密配置
- 也可通过环境变量 `WENYAN_API_KEY` 提供 API Key，优先级高于本地文件
- 现在支持在页面中清空已保存的 `API Key` / `API Base` / `Model`

## 提示词

- 提示词配置统一保存在项目根目录的 `input.json`
- 在 `V1` / `V2` 页面中打开“提示词设置”可查看、切换历史提示词，并保存为默认使用
- 修改内置默认提示词后保存，会自动新建一条自定义提示词，并切换为默认使用

## 项目结构

- `server.py`：HTTP 服务与不同模型接口的适配层
- `apikey.py`：默认配置与本地配置加载逻辑
- `apikey.local.json`：本地 API 配置（运行后按需生成，不提交仓库）
- `input.json`：提示词配置（默认提示词 + 历史提示词 + 当前默认）
- `style_prompt.py`：提示词加载与 prompt 构建
- `frontend_v1.html`：极简界面
- `frontend_v2.html`：双栏界面

## 说明

- 默认使用 Python 标准库，无额外依赖
- `API Key` 不会通过 `/api/config` 接口明文返回到前端
