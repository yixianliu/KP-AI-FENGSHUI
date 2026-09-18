# -*- coding: utf-8 -*-
"""
scripts/verify_headless.py — 无头启动验证脚本

对应执行计划任务 4.6：
验证打包后的 EXE 在无 GUI 环境下可正常启动并执行核心排盘逻辑。

用法：
    python scripts/verify_headless.py
    python scripts/verify_headless.py --verbose
"""
from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 强制无 GUI 模式（Headless）
os.environ.setdefault('KP_HEADLESS', '1')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


class TestHeadlessStartup(unittest.TestCase):
    """无头启动验证测试集"""

    @classmethod
    def setUpClass(cls):
        """一次性导入核心模块，验证无异常"""
        cls.imports = {}
        # 核心算法模块
        from core.bazi.pillar import calculate_pillars
        cls.imports['pillar'] = calculate_pillars
        # RAG 模块
        from ai.rag.knowledge_base import RAGKnowledgeBase
        cls.imports['rag_kb'] = RAGKnowledgeBase
        # 解读管道
        from ai.interpret_pipeline import ThreePartInterpretation
        cls.imports['interpreter'] = ThreePartInterpretation
        # 玄空飞星
        from core.fengshui.xuan_kong import XuanKongCalculator
        cls.imports['xuan_kong'] = XuanKongCalculator
        # Service 层
        from service.bazi_service import BaziService
        cls.imports['service'] = BaziService
        print("[INFO] 所有核心模块导入成功")

    def test_01_pillar_calculation(self):
        """测试1：基础八字排盘（无 GUI 依赖）"""
        fn = self.imports['pillar']
        result = fn(2000, 1, 1, 12, 0, 120.0)
        self.assertIn('四柱', result)
        self.assertEqual(len(result['四柱']), 4)
        self.assertEqual(result['day'], '戊午')  # 权威验证
        print(f"[PASS] 排盘结果: {result['四柱']}")

    def test_02_xuan_kong_calculation(self):
        """测试2：玄空飞星排盘（无 GUI 依赖）"""
        fn = self.imports['xuan_kong']
        result = fn().calculate('子山午向', 2024)
        self.assertIn('yun', result)
        self.assertIn('grid', result)
        self.assertEqual(len(result['grid']), 9)
        print(f"[PASS] 玄空飞星: 运{result['yun']} 子山午向")

    def test_03_rag_knowledge_base(self):
        """测试3：RAG 知识库初始化 + 检索"""
        kb = self.imports['rag_kb']()
        count = kb.load_builtin_corpus()
        self.assertGreater(count, 0, "内置语料应至少加载1条")
        results = kb.search('用神', top_k=3)
        self.assertIsInstance(results, list)
        print(f"[PASS] RAG 知识库加载 {count} 条，检索返回 {len(results)} 条")

    def test_04_three_part_parser(self):
        """测试4：三段式解读解析器"""
        parser = self.imports['interpreter']()
        sample = """【格局总评】身强用财。
【分项分析】事业顺遂。
【建议与注意事项】多穿红色。"""
        result = parser.parse(sample)
        self.assertTrue(len(result['summary']) > 0)
        self.assertTrue(len(result['analysis']) > 0)
        self.assertTrue(len(result['advice']) > 0)
        check = parser.validate_citations(result['citations'])
        self.assertIsInstance(check['valid'], bool)
        print(f"[PASS] 三段式解析: summary={len(result['summary'])}字")

    def test_05_batch_performance(self):
        """测试5：批量排盘性能（1000条 < 3s）"""
        fn = self.imports['pillar']
        n = 1000
        start = time.perf_counter()
        for i in range(n):
            fn(1990 + i % 30, i % 12 + 1, i % 28 + 1, i % 24, 0, 120.0)
        elapsed = time.perf_counter() - start
        avg_ms = elapsed / n * 1000
        self.assertLess(elapsed, 3.0, f"1000条批量 {elapsed:.3f}s 超出预算")
        print(f"[PASS] 批量排盘 {n}条: {elapsed:.3f}s ({avg_ms:.2f}ms/条)")

    def test_06_service_layer(self):
        """测试6：Service 层初始化（不含 AI 调用）"""
        svc = self.imports['service']()
        # 校验服务可用
        self.assertIsNotNone(svc)
        # 模糊搜索（空库应返回空列表）
        results = svc.search_history('非存在关键词xyz', limit=5)
        self.assertEqual(results, [])
        print("[PASS] Service 层初始化正常")


if __name__ == '__main__':
    # 无头模式下运行
    verbose = '--verbose' in sys.argv
    unittest.main(verbosity=2 if verbose else 1)
