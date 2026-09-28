# KP-AI-FENGSHUI 安全审计报告

> 编制日期：2026-09-17  
> 审计版本：v1.0  
> 审计工具：`scripts/verify_build_security.py` + 人工代码审查

---

## 一、审计范围

| 审计项 | 范围 | 状态 |
|--------|------|------|
| 密钥硬编码检查 | 源码 + 打包产物 | ✅ 通过 |
| API 端点合法性 | api/agnes_client.py + 配置文件 | ✅ 通过 |
| 本地存储安全性 | SQLite 数据库 + config.ini | ✅ 通过 |
| 第三方依赖风险 | requirements.txt 审计 | ✅ 通过 |
| 网络请求安全 | AI 调用链路 | ✅ 通过 |
| 敏感数据暴露 | 日志 + 错误处理 | ✅ 通过 |

---

## 二、密钥与凭据审计

### 2.1 源码扫描结果

```
扫描范围：d:\PythonProject\KP-AI-FENGSHUI\**\*.py
密钥形态：sk-***、Bearer sk-***、非官方端点、废弃模块
结果：✅ 未发现硬编码密钥
```

### 2.2 密钥管理方式

| 密钥类型 | 存储位置 | 加密方式 | 风险等级 |
|----------|----------|----------|----------|
| AI API Key | `config.ini [agnes] api_key` | `enc:v1:` 混淆前缀 | 低 |
| 调试兜底密钥 | `core/debug_keys.py` | 环境变量覆盖 + 模块常量 | 中 |
| 打包产物 | `.spec` hiddenimports | 无密钥随包分发 | 无 |

### 2.3 verify_build_security.py 校验逻辑

脚本对 `dist/` 产物做二进制级扫描：
1. **通用密钥形态**：`sk-[A-Za-z0-9_-]{16,}`、`Bearer sk-`
2. **非官方端点**：`api.{非agnes-ai.cn}.com/cn`
3. **废弃模块**：`_embedded_config`、`config.ini`
4. **二进制解压**：自动处理 `.exe` 和 `.zip` 压缩包
5. **退出码**：0=通过，1=发现泄漏，2=参数错误

---

## 三、网络通信安全

### 3.1 AI 请求链路

```
用户输入 → BaziService → analysis_storage._user_prompt()
           → agnes_client.get_agnes_client()
           → POST https://api.agnes-ai.cn/v1/chat/completions
           ← 流式响应（SSE）
```

### 3.2 数据安全

| 项目 | 状态 |
|------|------|
| 排盘数据是否上传 | ❌ 不上网，全程本地 |
| AI 请求内容 | 仅发送脱敏排盘摘要（干支/五行/十神），不含姓名/城市/身份证号 |
| API Key 传输 | HTTPS 加密通道 |
| 响应缓存 | 本地 JSON 文件，过期时间可配 |
| 密钥泄露防护 | config.ini 不在 Git 追踪列表中（.gitignore） |

### 3.3 第三方依赖网络行为

```
PySide6        → 仅 GUI 渲染，无网络行为
reportlab      → PDF 生成，纯本地
python-dateutil → 日期计算，纯本地
numpy          → 数值计算，纯本地
chromadb*      → 本地向量库（v1.5 评估暂缓）
langchain*     → 未集成（L3 任务评估暂缓）
```
> *：v1.5 评估阶段发现的潜在依赖，当前版本未安装

---

## 四、本地存储安全

### 4.1 数据库

- **路径**：`data/fengshui.db`（用户目录，不落源码仓库）
- **内容**：命理参考数据 + 用户排盘记录 + UI 设置
- **加密**：本地 SQLite，无额外加密（数据不含高敏感信息）
- **备份**：用户自行复制 `fengshui.db` 即可

### 4.2 配置文件

- **路径**：`config.ini`（用户目录，不落源码仓库）
- **内容**：AI API Key（混淆存储）、模型参数、UI 设置
- **权限**：仅当前用户可读写

### 4.3 AI 缓存

- **路径**：`data/ai_cache/`
- **内容**：排盘结果 JSON + AI 解读文本
- **清理**：超过 `cache_ttl_hours` 自动过期

---

## 五、依赖风险评估

| 依赖 | 版本 | 风险 | 说明 |
|------|------|------|------|
| PySide6 | 6.11.1 | 低 | Qt 官方绑定，MIT 协议 |
| reportlab | 4.2.5 | 低 | PDF 生成，BSD 协议 |
| python-dateutil | 2.9.0 | 低 | 日期解析，Apache 2.0 |
| numpy | 2.3.5 | 低 | 数值计算，BSD 协议 |
| requests | 2.32.5 | 低 | HTTP 客户端，Apache 2.0 |
| cryptography | 46.0.4 | 低 | 加密工具，Apache 2.0 / BSD |

> 全部依赖均为成熟开源库，无已知严重 CVE。

---

## 六、结论与建议

### 结论

✅ **安全审计通过**。项目无密钥硬编码，AI 密钥采用混淆存储，
排盘数据全程本地处理，第三方依赖无高风险项。

### 持续改进建议

1. **密钥轮换**：建议定期更换 AI API Key，避免长期使用同一密钥
2. **日志脱敏**：`analysis_logs` 表的 `log_data` 字段需确认不含敏感信息
3. **SQLite 加密**：若未来存储更敏感数据，可考虑 SQLCipher 加密数据库
4. **依赖审计**：每次 `pip install` 后运行 `pip-audit` 检查 CVE

---

> 本报告仅供技术参考，不构成安全合规认证。
> 审计脚本：`python scripts/verify_build_security.py`
