# AI 调用链路与故障排查手册

## 1. 调用链路概览

```
排盘输入 → 主窗口按钮 → AiAnalysisWorker 后台线程 → analysis_storage.run_*_analysis
  → AIThrottle.enter（限速/熔断）→ AgnesClient.chat_completion（OpenAI 兼容）
     → 成功：parse_json_response → _deep_clean_json → _smart_fix_json → 返回结构化结果
     → 失败：重试/超时 → parse 失败 → 本地 analysis_fallback → 统一用户提示
```

关键文件
- `api/agnes_client.py`：AgnesClient、_deep_clean_json、parse_json_response
- `api/ai_throttle.py`：令牌桶限速 + 熔断器
- `core/knowledge/analysis_storage.py`：三大板块统一入口、_smart_fix_json
- `core/ai_cache.py`：输入哈希缓存，节省重复调用
- `ui/main_window.py`：按钮状态、失败回调统一文案
- `core/log_handler.py`：RotatingFileHandler 日志切割

## 2. 关键流程细节

### 2.1 缓存
缓存键 `(pan_type, input_hash, question_hash)`，命中直接返回，无 API 调用。
`get_cache_stats()` 提供条目数、命中数、命中率、节省调用数。

### 2.2 限速与熔断
`AIThrottle.enter()` 先检查熔断器状态，再获取令牌桶令牌。
熔断 OPEN 时日志 `[熔断告警]`，限速等待超时日志 `[限速告警]`。

### 2.3 解析降级
1. `_deep_clean_json` 去除 ``` 围栏、`<think>`/ `[thinking]` 思考标签、空白。
2. `parse_json_response` 尝试 json.loads。
3. 失败则 `_smart_fix_json` 补全截断/缺失括号。
4. 仍失败 → `generate_fallback_analysis` 本地规则兜底。

## 3. 日志关键词速查

- `[AI] 请求成功 model=... endpoint=... 耗时=...ms attempts=... tokens=...`
- `[AI] 调用失败 type=... status=... model=... 耗时=...ms attempts=... err=...`
- `[AI] HTTP 429/500 瞬时错误（第 N 次），...秒后重试，当前耗时=...ms`
- `AI分析[bazi/meihua/liuren] ... 已降级为本地兜底`
- `[熔断告警]` / `[限速告警]`
- `[日志] 全局日志已接入`

## 4. 常见故障与处理

| 现象 | 常见原因 | 排查步骤 |
|------|----------|----------|
| 按钮不可点，提示“AI 未配置” | `AIConfigManager.is_ai_configured()` 为 False，密钥空或损坏 | 设置 → 查看密钥状态，`key_status()` 返回 corrupted 则重填 |
| `[AI] 调用失败 type=request status=401/403` | API Key 错误或权限不足 | 检查 `api_key`、权限范围、订阅状态 |
| `[AI] 调用失败 type=quota` | 配额用尽 | 服务商后台查看用量 |
| `[AI] 调用失败 type=timeout` | 网络延迟/端点不可达 | 测试 endpoint 连通性，VPN/防火墙 |
| 解析失败但结果仍显示 | 模型返回含思考标签或截断 | 日志查看 cleaned 文本，确认 `_deep_clean_json` 已生效 |
| 日志被 DB 校验刷屏 | 历史问题，已降级日志级别 | 确认 `core/database_manager` 日志为 DEBUG |
| 频繁触发熔断 | QPS 超限或连续错误 | 查看设置界面熔断状态与 QPS 配置，调整 `qps_capacity/refill` |

## 5. 快速验证脚本

- `scripts/ai_parse_stress_test.py`：验证解析降级路径
- `tests/test_ai_parse_fallback.py`：单元测试覆盖思考标签、截断修复

## 6. 运维建议

- 日志默认 RotatingFileHandler：5MB/文件，保留 5 个备份。
- 生产环境保持 INFO 级别，调试时可临时把 `core.database_manager` 调为 DEBUG。
- 定期清理旧缓存 `clear_old(min_hit_count_to_keep=...)`。
- 设置界面可实时查看熔断状态与缓存命中率。
