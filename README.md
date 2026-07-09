# Codex 额度重置工具

本地运行的 Codex 额度控制台，用于查询 ChatGPT Codex 邀请资格、查看 reset credits、发送邀请并消耗可用额度。

[English](README.en.md)

## 预览

![Codex 额度重置浅色界面](docs/assets/screenshot-light.png)

![Codex 额度重置暗色界面](docs/assets/screenshot-dark.png)

## 功能

- 查询 Codex 邀请资格
- 查询 rate limit reset credits
- 消耗可用 reset credit 来重置额度
- 查询当前使用状态
- 有邀请资格时发送邀请邮件
- 中文 / English 界面切换
- 亮色 / 暗色主题切换
- `https://chatgpt.com/api/auth/session` 可点击打开
- 不存储 Session JSON，仅用于当前页面发起的本地请求

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask curl_cffi
python3 app.py
```

浏览器访问：

```text
http://localhost:8080
```

如果 `8080` 端口被占用，可以换端口运行：

```bash
PORT=8081 python3 app.py
```

## 代理说明

项目默认使用本地代理：

```python
PROXIES = {"https": "http://127.0.0.1:10808", "http": "http://127.0.0.1:10808"}
```

如果你的代理端口或协议不同，请在 `app.py` 中修改 `PROXIES`。例如使用 Clash、V2Ray 或其他本地代理时，确保后端可以访问 `chatgpt.com`。

## 如何获取 Session JSON

1. 浏览器登录 [chatgpt.com](https://chatgpt.com)
2. 打开 DevTools 的 Network 面板
3. 访问 [https://chatgpt.com/api/auth/session](https://chatgpt.com/api/auth/session)
4. 复制 Response 的完整 JSON 内容
5. 粘贴到网页输入框，点击「查询资格」

## 隐私与安全

- 页面不会把 Session JSON 写入本地文件或数据库
- Session JSON 只会发送给本地 Flask 服务
- 后端会使用其中的 `accessToken` 请求 ChatGPT API
- 不建议直接公开部署到公网
- 如果部署到服务器，请务必增加访问控制、HTTPS、代理配置和日志脱敏

## 技术方案

- **前端**：纯 HTML / CSS / JavaScript
- **后端**：Flask + curl_cffi
- **请求方式**：模拟 Chrome TLS 指纹请求 ChatGPT API
- **界面**：响应式布局，支持中英文和亮暗主题

## API 端点

| 功能 | ChatGPT API |
| --- | --- |
| 查询邀请资格 | `GET /backend-api/referrals/invite/eligibility` |
| 查询 reset credits | `GET /backend-api/wham/rate-limit-reset-credits` |
| 消耗 reset credit | `POST /backend-api/wham/rate-limit-reset-credits/consume` |
| 查询使用状态 | `GET /backend-api/wham/usage` |
| 发送邀请 | `POST /backend-api/wham/referrals/invite` |

## 上游项目

Forked from [LImingcheng07/codex-reset](https://github.com/LImingcheng07/codex-reset).
