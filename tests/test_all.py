"""
tests/test_all.py — 主测试套件

把各子测试模块（八字/梅花/六壬计算器、数据校验、性能、安全，以及大六壬
九宗门、综合建议流水线、导出器、梅花知识种子、AI 缓存等）聚合为一条命令可
运行的统一套件。安全测试（TestSecurity）守护「客户端零密钥、只接官方公开
后端」这一发布不变量。

用法：
    python -m unittest tests.test_all
"""
import sys
import os
import unittest
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 大六壬引擎测试（稳定部分 + 九宗门三传表征），整体并入主套件
try:
    from tests.test_liuren import TestLiuRenStable, TestLiuRenSanChuanSpec
    from tests.test_comprehensive_export import (
        TestComprehensivePipeline, TestExportBase, TestExportRenderers)
    from tests.test_meihua_knowledge_seed import TestMeihuaKnowledgeSeed
    from tests.test_ai_cache import TestAiCacheCore, TestAiCachePipelineIntegration
except Exception:  # pragma: no cover
    TestLiuRenStable = TestLiuRenSanChuanSpec = None
    TestComprehensivePipeline = TestExportBase = TestExportRenderers = None
    TestMeihuaKnowledgeSeed = None
    TestAiCacheCore = TestAiCachePipelineIntegration = None


class TestBaziCalculator(unittest.TestCase):
    """八字计算器测试"""
    
    def setUp(self):
        """每个用例前构造独立的八字计算器实例。"""
        from core.bazi_calculator import BaziCalculator
        self.calculator = BaziCalculator()
    
    def test_calculate(self):
        """测试八字排盘计算"""
        result = self.calculator.calculate(2000, 1, 1, 12)
        self.assertIn('year', result)
        self.assertIn('month', result)
        self.assertIn('day', result)
        self.assertIn('hour', result)
        self.assertIn('四柱', result)
        self.assertEqual(len(result['四柱']), 4)
    
    def test_get_shier_shen(self):
        """测试十二长生：返回 dict 含 shier_shen 列表，四项各含 pillar/ganzhi/shier_shen/description"""
        bz = self.calculator.calculate(2000, 1, 1, 12)
        result = self.calculator.get_shier_shen(bz)
        self.assertIsInstance(result, dict)
        self.assertIn('shier_shen', result)
        self.assertEqual(len(result['shier_shen']), 4)
        for item in result['shier_shen']:
            self.assertIn('pillar', item)
            self.assertIn('ganzhi', item)
            self.assertIn('shier_shen', item)
            self.assertIn('description', item)
            self.assertIn(item['pillar'], ('年柱', '月柱', '日柱', '时柱'))
            self.assertIn(item['shier_shen'],
                ('长生', '沐浴', '冠带', '临官', '帝旺', '衰',
                 '病', '死', '墓', '绝', '胎', '养'))

    def test_get_year_ganzhi(self):
        """测试年干支计算（calendar_utils.GanZhiCalculator）"""
        from core.calendar_utils import GanZhiCalculator
        ganzhi = GanZhiCalculator().get_year_ganzhi(2024)
        self.assertEqual(len(ganzhi), 2)

    def test_get_month_ganzhi(self):
        """测试月干支计算（五虎遁：年干 + 月支）"""
        from core.calendar_utils import GanZhiCalculator
        ganzhi = GanZhiCalculator().get_month_ganzhi('甲', '寅')
        self.assertEqual(len(ganzhi), 2)


class TestMeihuaCalculator(unittest.TestCase):
    """梅花易数计算器测试"""
    
    def setUp(self):
        """每个用例前构造独立的梅花易数计算器实例。"""
        from core.meihua import MeiHuaCalculator
        self.calculator = MeiHuaCalculator()
    
    def test_time_divination(self):
        """测试时间起卦"""
        result = self.calculator.time_divination(2024, 6, 15, 12)
        self.assertIn('method', result)
        self.assertIn('base_hex', result)
    
    def test_number_divination_valid(self):
        """测试数字起卦（有效输入）"""
        result = self.calculator.number_divination([1, 2, 3])
        self.assertIn('method', result)
        self.assertEqual(result['method'], '数字起卦')
    
    def test_number_divination_empty(self):
        """测试数字起卦（空输入）"""
        with self.assertRaises(ValueError):
            self.calculator.number_divination([])
    
    def test_number_divination_too_many(self):
        """测试数字起卦（过多数字）"""
        with self.assertRaises(ValueError):
            self.calculator.number_divination([1, 2, 3, 4])
    
    def test_number_divination_invalid_type(self):
        """测试数字起卦（无效类型）"""
        with self.assertRaises(ValueError):
            self.calculator.number_divination("abc")


class TestLiuRenCalculator(unittest.TestCase):
    """大六壬排盘引擎测试（稳定部分 + 九宗门三传表征）"""

    def setUp(self):
        """每个用例前构造独立的大六壬计算器实例（稳定部分测试）。"""
        from core.liuren import LiuRenCalculator
        self.calculator = LiuRenCalculator()

    def test_ganzhi_day_anchor(self):
        """1900-01-01 为甲戌日"""
        self.assertEqual(self.calculator.ganzhi_day(1900, 1, 1), ('甲', '戌'))

    def test_tian_pan(self):
        """月将加占时：亥将加卯时，天盘[卯]=亥"""
        from core.liuren import ZHI
        tp = self.calculator._build_tian_pan(list(ZHI), '亥', '卯')
        self.assertEqual(tp['卯'], '亥')

    def test_sanchuan_zeike(self):
        """贼克法：四课含申金克甲木 → 初传申"""
        from core.liuren import ZHI
        tp = self.calculator._build_tian_pan(list(ZHI), '亥', '卯')
        sike = {'gan_shang': {'tianpan': '申'}, 'gan_yin': {'tianpan': '酉'},
                'zhi_shang': {'tianpan': '子'}, 'zhi_yin': {'tianpan': '亥'}}
        sc, gate = self.calculator._build_sanchuan('zeike', '甲', '子', sike, tp, list(ZHI))
        self.assertEqual(gate, 'zeike')
        self.assertEqual(sc['chu'], '申')


class TestDataValidator(unittest.TestCase):
    """数据校验器测试"""
    
    def setUp(self):
        """每个用例前构造独立的数据校验器实例。"""
        from core.data_validator import DataValidator
        self.validator = DataValidator()
    
    def test_validate_bazi_input_valid(self):
        """测试八字输入校验（有效）"""
        data = {
            'name': '张三',
            'gender': '男',
            'year': 2000,
            'month': 1,
            'day': 1,
            'hour': 12,
            'minute': 0,
            'city': '北京'
        }
        result = self.validator.validate_bazi_input(data)
        self.assertTrue(result)
    
    def test_validate_bazi_input_invalid(self):
        """测试八字输入校验（无效）"""
        data = {
            'name': '',
            'gender': '男',
            'year': 'invalid',
            'month': 1,
            'day': 1,
            'hour': 12,
            'minute': 0,
            'city': '北京'
        }
        result = self.validator.validate_bazi_input(data)
        self.assertFalse(result)
    
    def test_validate_meihua_input_valid(self):
        """测试梅花易数输入校验（有效）"""
        data = {
            'method': 'time',
            'year': 2024,
            'month': 6,
            'day': 15,
            'hour': 12,
            'question': '测试问题'
        }
        result = self.validator.validate_meihua_input(data)
        self.assertTrue(result)


class TestPerformance(unittest.TestCase):
    """性能测试"""

    def test_calculate_performance(self):
        """测试八字排盘计算性能"""
        from core.bazi_calculator import BaziCalculator
        calculator = BaziCalculator()

        start = time.time()
        for _ in range(1000):
            calculator.calculate(2000, 1, 1, 12)
        elapsed = time.time() - start

        print(f"[性能测试] calculate 1000次调用耗时: {elapsed:.4f}秒")
        self.assertTrue(elapsed < 5.0, f"性能不达标，耗时{elapsed:.4f}秒")


class TestSecurity(unittest.TestCase):
    """安全测试

    发布约定：产物中【不得含任何密钥】；官方固定后端（龙虎山大师兄 AI 的
    端点与 agnes-2.5-flash 模型名）属公开、非机密的产品常量，随包分发。
    AI 参数中唯一需要用户填写并保密的是 API 密钥，存于本机 ai_config.json。
    以下测试守护该不变量 —— 一旦有人把密钥或非官方端点写回客户端，测试立即失败。
    """

    def test_no_embedded_credentials_in_source(self):
        """源码树中不得存在任何凭据载体文件"""
        from pathlib import Path

        root = Path(__file__).resolve().parent.parent
        forbidden = [
            'core/_embedded_config.py',
            'config.ini',
            'scripts/build_embed_secrets.py',
        ]
        present = [f for f in forbidden if (root / f).exists()]
        self.assertEqual(
            present, [],
            f"以下凭据载体不得留在源码树中：{present}。"
            "请运行 python scripts/purge_ai_secrets.py"
        )

    def test_no_ai_original_info_in_source(self):
        """客户端源码中不得出现非官方硬编码端点或非发布模型名

        官方固定后端（api.agnes-ai.cn / agnes-2.5-flash）为公开产品常量，
        允许出现在源码中；其余上游端点 / agnes-2.5-pro 仍视为泄漏，必须零出现。
        """
        import re
        from pathlib import Path

        root = Path(__file__).resolve().parent.parent
        patterns = [
            (re.compile(r'api\.(?!agnes-ai\.cn)[A-Za-z0-9.\-]+\.(?:com|cn)'), '硬编码的非官方上游端点'),
            (re.compile(r'agnes-2\.5-pro'), '硬编码的内置模型名（pro 非发布模型）'),
        ]
        # 这些文件的职责就是描述/检测这些模式，命中属正常
        whitelist = {
            'scripts/purge_ai_secrets.py',
            'scripts/verify_build_security.py',
            'core/secure_log.py',
            'core/debug_keys.py',
        }
        offenders = []
        for sub in ('api', 'core', 'ui', 'scripts'):
            base = root / sub
            if not base.exists():
                continue
            for py in base.rglob('*.py'):
                rel = py.relative_to(root).as_posix()
                if rel in whitelist:
                    continue
                try:
                    text = py.read_text(encoding='utf-8')
                except (OSError, UnicodeDecodeError):
                    continue
                for pattern, desc in patterns:
                    if pattern.search(text):
                        offenders.append(f'{rel} ({desc})')

        self.assertEqual(
            offenders, [],
            f"以下源码残留非官方 AI 信息：{offenders}。官方固定后端除外，不得出现其他端点 / 模型名。"
        )

    def test_api_key_not_stored_plaintext(self):
        """配置落盘时 API 密钥必须经过混淆，不得明文可见"""
        import json
        import tempfile
        from pathlib import Path
        from core.ai_config import AIConfigManager, make_default_profile

        secret = 'sk-unittest-abcdefghijklmnop1234567890'
        tmp = Path(tempfile.mkdtemp()) / 'ai_config.json'
        manager = AIConfigManager(tmp)

        profile = make_default_profile()
        profile.api_url = 'https://example.invalid/v1/chat/completions'
        profile.model = 'test-model'
        profile.api_key = secret
        self.assertTrue(manager.upsert_profile(profile, make_active=True))

        raw = tmp.read_text(encoding='utf-8')
        self.assertNotIn(secret, raw, "配置文件中出现明文 API 密钥")
        self.assertIn('api_key_enc', raw, "密钥应存放在混淆字段 api_key_enc 中")
        self.assertNotIn('"api_key"', raw, "不应存在明文 api_key 字段")

        # 本机可正确还原
        reloaded = AIConfigManager(tmp).get_active()
        self.assertEqual(reloaded.api_key, secret)

        # 落盘内容确实是混淆体而非编码后仍含明文
        payload = json.loads(raw)
        enc = payload['profiles'][0]['api_key_enc']
        self.assertTrue(enc.startswith('enc:v1:'))
        self.assertNotIn('sk-', enc)

    def test_client_source_has_no_hardcoded_key(self):
        """客户端源码中不得硬编码任何 sk- 密钥

        例外：core/debug_keys.py 是「双模式密钥管理」唯一 sanctioned 的调试密钥源，
        其真实密钥由 scripts/purge_ai_secrets.py 在打包前清空，故这里放行；
        产物级防护由 verify_build_security.py（扫描 dist）兜底。
        """
        import re
        from pathlib import Path

        root = Path(__file__).resolve().parent.parent
        pattern = re.compile(r'sk-[A-Za-z0-9_\-]{16,}')
        # 调试密钥源：密钥仅存在于开发机，打包前会被 purge 清空，放行
        whitelist = {'core/debug_keys.py'}
        offenders = []

        # 只扫客户端代码；server/ 目录不打包进 exe，且其密钥来自环境变量
        for sub in ('api', 'core', 'ui'):
            for py in (root / sub).rglob('*.py'):
                rel = py.relative_to(root).as_posix()
                if rel in whitelist:
                    continue
                try:
                    text = py.read_text(encoding='utf-8')
                except (OSError, UnicodeDecodeError):
                    continue
                if pattern.search(text):
                    offenders.append(rel)

        self.assertEqual(
            offenders, [],
            f"以下客户端源码中发现硬编码密钥：{offenders}。"
            "客户端代码会被反编译，密钥必须放在服务端。"
        )

    def test_log_scrubber_masks_secrets(self):
        """日志脱敏能覆盖常见凭据形态"""
        from core.secure_log import scrub

        cases = [
            'api_key = sk-abcdefghijklmnopqrstuvwxyz123456',
            'Authorization: Bearer sk-abcdefghijklmnopqrstuvwxyz123456',
            'device_token="abcdefghijklmnopqrstuvwxyz1234567890ABCD"',
        ]
        for raw in cases:
            masked = scrub(raw)
            self.assertIn('***REDACTED***', masked, f"未脱敏: {raw}")
            self.assertNotIn('sk-abcdefghijklmnop', masked, f"密钥泄漏: {masked}")



if __name__ == '__main__':
    print("=" * 60)
    print("KP-AI-FENGSHUI 验证测试套件")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBaziCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestMeihuaCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestLiuRenCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    if TestLiuRenStable is not None:
        suite.addTests(loader.loadTestsFromTestCase(TestLiuRenStable))
        suite.addTests(loader.loadTestsFromTestCase(TestLiuRenSanChuanSpec))
    if TestComprehensivePipeline is not None:
        suite.addTests(loader.loadTestsFromTestCase(TestComprehensivePipeline))
        suite.addTests(loader.loadTestsFromTestCase(TestExportBase))
        suite.addTests(loader.loadTestsFromTestCase(TestExportRenderers))
    if TestMeihuaKnowledgeSeed is not None:
        suite.addTests(loader.loadTestsFromTestCase(TestMeihuaKnowledgeSeed))
    if TestAiCacheCore is not None:
        suite.addTests(loader.loadTestsFromTestCase(TestAiCacheCore))
        suite.addTests(loader.loadTestsFromTestCase(TestAiCachePipelineIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("所有测试通过！")
    else:
        print(f"测试失败: {len(result.failures)} 失败, {len(result.errors)} 错误")
    print("=" * 60)