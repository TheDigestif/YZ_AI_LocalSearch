# YZ Local Search (云智AI本地搜)

<p align="center">
  <b>一个安装包，双击即用，让 AI 助手拥有联网搜索能力</b>
</p>

---

## 简介

**云智AI本地搜** 是一款本地化的联网搜索服务，基于开源的 [SearXNG](https://github.com/searxng/searxng) 搜索引擎聚合器构建，通过 MCP (Model Context Protocol) 协议为 Claude Code、Claude Desktop 等 AI 助手提供实时互联网信息检索能力。

无需云端 API、无需复杂配置，一键安装即可让您的 AI 助手拥有"联网"能力。

### 为什么开发这个项目？

#### 1. 满足 AI 搜索需求，同时保障安全性

AI 助手在回答问题时需要实时联网搜索。目前市面上多数 MCP 搜索方案直接调用第三方搜索 API——你的搜索请求经过哪些链路、被如何处理、数据去了哪里，这些都不透明，存在安全隐患。

云智AI本地搜将搜索引擎**完全部署在本地**：搜索请求直接从你的电脑发出 → 到达搜索引擎 → 结果直接返回你的电脑。整个链路不经过任何中间服务器，从根源上杜绝了数据泄露风险。所有配置、搜索历史也完全存储在本地，安全可审计。

#### 2. UI 化设计降低使用门槛

常规 MCP 服务需要通过命令行启动和配置，对非技术用户来说有一定难度。我们为 SearXNG + MCP Server 包装了**图形化管理界面**：

- 🟢 一键启动/停止搜索服务
- 📋 一键复制 MCP 配置到剪贴板
- 🔧 可视化的代理和端口设置
- 📊 实时服务状态监控
- 📌 系统托盘常驻

用户无需接触命令行，像使用普通桌面软件一样使用 MCP 搜索服务。

#### 3. MCP 依然是 AI 连接搜索的主流方式

虽然部分 AI 产品（如 ChatGPT、Claude Web）已内置搜索功能，但大量通过 API 调用 AI 模型的开发者和企业用户，仍然依赖 MCP 协议来连接搜索服务。云智AI本地搜正是为这个场景而生——一个轻量、安全、开箱即用的本地 MCP 搜索方案。

#### 4. 零使用成本，告别费用焦虑

市面上几乎所有的在线搜索 API 都是"免费额度起步，用超了就要付费"的模式。刚开始觉得够用，但随着使用量增加，费用焦虑也随之而来——这个月会不会超？下个月要不要升级套餐？

本地部署的云智AI本地搜从根本上解决了这个问题：**搜索完全免费、无次数限制、无额度概念**。想搜多少搜多少，彻底告别用量焦虑。

诚然，本地自建搜索在结果质量上无法与 Google、Bing 等商业 API 相媲美，但它换来的是**零成本的搜索自由**——不用担心账户余额、不用纠结是否值得为一次搜索付费、不用在月底盯着账单。对于个人开发者和日常使用场景来说，这种"安心感"往往比搜索质量更重要。

---

## 核心优势

### 🚀 零门槛安装
- ❌ 不需要 Docker
- ❌ 不需要 Python 环境
- ❌ 不需要命令行操作
- ✅ 图形界面，双击即用
- ✅ 安装包仅 ~126MB，3 分钟完成安装

### 🔒 隐私安全
- **本地运行**：所有搜索请求从您的电脑发出，不经过第三方服务器
- **数据自主**：搜索历史、配置信息完全存储在本地
- **无账号体系**：无需注册、无需登录

---

## 快速开始

### Windows 用户
1. 从 [Releases](../../releases) 页面下载最新安装包
2. 双击运行，选择安装位置
3. 启动「云智AI本地搜」
4. 点击「启动服务」→「复制MCP配置」
5. 粘贴到 AI 助手配置文件中

### Docker 部署（跨平台）
```bash
docker compose up -d
```
SearXNG 将运行在 `http://localhost:18888`，MCP Server 在 `http://localhost:19000/sse`。

### 手动部署
```bash
# 1. 安装 SearXNG (参考 https://github.com/searxng/searxng)
# 2. 安装依赖
pip install -r requirements.txt
# 3. 启动 MCP Server
export SEARXNG_URL="http://localhost:18888"
python -m src.mcp_searxng.server
```

### MCP 客户端配置
在 Claude Code 的 `.claude.json` 或 `.mcp.json` 中添加：
```json
{
  "mcpServers": {
    "yz_local_search": {
      "type": "sse",
      "url": "http://localhost:19000/sse"
    }
  }
}
```

---

## 功能特性

### MCP 工具
| 工具 | 功能 | 参数 |
|------|------|------|
| `web_search` | 网页搜索 | query (必填), count, engines |
| `image_search` | 图片搜索 | query (必填), count |

### 桌面管理界面
- 实时服务状态监控
- 一键启动/停止服务
- 代理设置（可选，用于 Google 等）
- MCP 配置一键复制
- 系统托盘支持

---

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 |
| 磁盘空间 | 200MB 以上 |
| 内存 | 4GB 以上 |
| 网络 | 互联网连接 |

---

## 常见问题

**Q: 为什么需要这个工具？**
AI 助手通过 API 调用时默认无法联网。虽然部分 AI 产品已内置搜索，但直接调用 API 的用户仍需 MCP 连接搜索服务。云智AI本地搜为这个场景提供本地化、安全的搜索方案。

**Q: 和直接用搜索引擎 API 有什么区别？**
直接调用搜索 API 意味着你的搜索请求经过第三方云服务，链路不透明。云智AI本地搜将所有搜索请求保留在本地，数据流向完全可控。同时配合 AI 助手使用，可以让 AI 自动搜索、筛选、整理信息，直接给出答案。

**Q: 数据安全吗？**
完全安全。所有搜索请求直接从你的电脑发送到搜索引擎，不经过任何第三方服务器。软件开源（MIT），代码可审计。

---

## 免责声明

本软件仅作为信息检索工具。使用本软件进行搜索时，搜索结果由第三方搜索引擎提供，开发者不对搜索内容的准确性、合法性负责。用户应遵守相关法律法规，不得将本软件用于任何违法违规用途。

详见 [DISCLAIMER.md](DISCLAIMER.md)

---

## 开源协议

本项目采用 [MIT License](LICENSE)。

本项目基于以下开源项目构建：

| 项目 | 说明 | 许可证 |
|------|------|--------|
| [SearXNG](https://github.com/searxng/searxng) | 核心搜索引擎聚合器，提供多引擎搜索能力 | AGPL |
| [SearXNGforWindows](https://github.com/mbaozi/SearXNGforWindows) | SearXNG 的 Windows 原生适配版 | AGPL |
| [MCP](https://modelcontextprotocol.io/) | Model Context Protocol，AI 助手标准化连接协议 | MIT |

> **特别感谢 SearXNG 项目**：云智AI本地搜的核心搜索能力完全基于 SearXNG 构建。SearXNG 是一个尊重隐私、可自托管、功能强大的开源元搜索引擎。没有 SearXNG，就没有这个项目。

---

## 关于我们

<p align="center">
  <b>Powered by 云感数字科技 (YunGan Digital Technology)</b><br>
  <a href="https://www.yungantech.com">https://www.yungantech.com</a>
</p>

云感数字科技专注于 AI + XR 技术研发，为企业提供数字化转型解决方案。我们致力于通过技术创新让更多人享受 AI 带来的便利。

**关注我们：**
- 🌐 官网：[https://www.yungantech.com](https://www.yungantech.com)

---

*让 AI 助手拥有联网能力，从此告别信息孤岛*
