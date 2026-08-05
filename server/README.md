# AI 中转服务

桌面客户端与上游 Agnes AI 之间的代理层。**上游 API 密钥只存在于本服务的环境变量中，永远不下发到用户设备。**

## 为什么必须有这一层

客户端软件运行在用户完全掌控的机器上。任何随 exe 分发的密钥，都可以被以下方式取走，且**代码混淆与反调试对前两种完全无效**：

| 攻击方式 | 成本 | 混淆是否有效 |
|---|---|---|
| 装本机根证书抓 HTTPS 请求头 | 几分钟 | 无效 |
| 扫描进程内存搜 `sk-` 字符串 | 几分钟 | 无效 |
| `pyinstxtractor` 解包后反编译 | 几分钟 | 仅能拖慢 |

根本原因：密钥在发出请求的那一刻必须还原成明文。这是无法用客户端技术绕过的事实。
唯一的解法是让密钥根本不出现在客户端——也就是这个中转服务。

## 信任模型

请准确理解各凭据的安全等级，避免高估防护强度：

| 凭据 | 存放位置 | 是否会泄露 | 作用 |
|---|---|---|---|
| `AGNES_API_KEY` | 仅服务器环境变量 | **不会** | 真正需要保护的资产 |
| `APP_KEYS` | 随 exe 分发 | **必然会** | 只是门槛，不是秘密 |
| 设备令牌 | 用户本机，一机一份 | 单机可见 | 可单独吊销、单独限额 |
| `ADMIN_TOKEN` | 仅服务器 | 不会 | 管理接口鉴权 |

关键点：`APP_KEYS` 泄露不会造成实质损失。攻击者最多能注册设备并消耗配额，
而你可以随时吊销该设备、调低配额、或轮换 `APP_KEYS`——**上游密钥始终安全**。

## 部署

```bash
cd server
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# 编辑 .env 填入真实密钥
```

生成随机凭据：

```bash
python -c "import secrets;print('APP_KEYS=' + secrets.token_urlsafe(24))"
python -c "import secrets;print('ADMIN_TOKEN=' + secrets.token_urlsafe(32))"
```

启动：

```bash
set -a && . ./.env && set +a          # Windows PowerShell 见下方说明
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

生产环境务必：

1. **走 HTTPS**。用 Nginx/Caddy 反代并配好证书，绝不裸跑 HTTP，否则设备令牌会在链路上明文传输。
2. **限制来源**。如有条件，在上游 Agnes 控制台把调用 IP 白名单锁到本服务器出口 IP。
3. **设置账单告警**。配额是第一道防线，账单告警是最后一道。

systemd 示例：

```ini
[Service]
EnvironmentFile=/etc/fengshui-relay/.env
ExecStart=/opt/fengshui-relay/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
WorkingDirectory=/opt/fengshui-relay
Restart=always
```

## 接口

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/healthz` | 无 | 健康检查 |
| POST | `/v1/register` | `X-App-Key` | 设备注册，换取设备令牌 |
| POST | `/v1/chat` | `Authorization: Bearer <设备令牌>` | AI 转发 |
| GET | `/admin/stats` | `X-Admin-Token` | 运营概览 |
| POST | `/admin/revoke` | `X-Admin-Token` | 吊销指定设备 |
| POST | `/admin/revoke-all` | `X-Admin-Token` | 应急：一键吊销全部 |

交互式文档（`/docs`、`/openapi.json`）已刻意关闭，减少信息暴露面。

## 日常运维

查看用量：

```bash
curl -H "X-Admin-Token: $ADMIN_TOKEN" https://your-domain/admin/stats
```

发现某设备滥用，精确切断：

```bash
curl -X POST -H "X-Admin-Token: $ADMIN_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"device_id": 42, "note": "abuse"}' \
     https://your-domain/admin/revoke
```

怀疑 `APP_KEYS` 被大规模滥用时的处置顺序：

1. `POST /admin/revoke-all` 吊销全部设备令牌（正常用户下次启动会自动重新注册，无感知）
2. 轮换 `APP_KEYS`，随新版客户端发布
3. 观察 `/admin/stats`，确认用量回落

注意这套流程**全程不需要更换上游密钥、不需要重新发版救火**——这正是中转层带来的运维价值。

## 内置安全措施

- 设备令牌只存 SHA-256 摘要，库被拖走也拿不到可用令牌
- 所有密钥比较使用常量时间算法，防计时侧信道
- 上游响应体绝不原样透传，错误一律映射为通用文案（防止上游报错回显密钥片段）
- 模型名由服务端强制指定，客户端无权选择，防止被诱导调用高价模型
- `max_tokens` 服务端二次封顶，请求体长度与消息条数均有上限
- 配额检查在调用上游**之前**完成，超限直接拒绝，不产生费用
- 全局日志脱敏过滤器，兜底拦截 `sk-`/`Bearer`/`token` 等模式
- 全局异常处理器，堆栈只进服务端日志，客户端只收到通用错误
- IP 仅以摘要形式留存，不存明文
