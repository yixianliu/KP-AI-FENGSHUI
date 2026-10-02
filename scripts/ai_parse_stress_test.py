# -*- coding: utf-8 -*-
"""
scripts/ai_parse_stress_test.py
AI 解析降级路径集成压测与日志样本采集
用于验证 _deep_clean_json / parse_json_response / _smart_fix_json 在各种污染场景下的表现
"""
import sys
sys.path.insert(0, '.')
from api.agnes_client import _deep_clean_json, AgnesClient
from core.knowledge.analysis_storage import _smart_fix_json

parse_json_response = AgnesClient.parse_json_response

samples = [
    ("clean", '{"a":1}'),
    ("fence", "```json\n{\"a\":2}\n```"),
    ("think_tag", "<think>思考</think>{\"a\":3}"),
    ("thinking_brackets", "[thinking]blah[/thinking]{\"b\":4}"),
    ("truncated", '{"intro":"x","arr":[1,2,3]'),
    ("mixed", "输出如下：<think>分析</think>```json\n{\"c\":5}\n```"),
]

print("=== AI 解析降级压测 ===")
for name, raw in samples:
    cleaned = _deep_clean_json(raw)
    parsed = parse_json_response(cleaned)
    fixed = None
    if parsed is None:
        fixed = _smart_fix_json(cleaned)
    print(f"[{name}] cleaned={cleaned[:60]!r} parsed={parsed} fixed={fixed}")
    if parsed is None and fixed is None:
        print(f"  WARN: 无法解析样本 {name}")

print("压测完成")
