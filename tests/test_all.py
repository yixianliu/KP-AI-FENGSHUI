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
    """安全测试"""
    
    def test_api_key_from_config(self):
        """测试API密钥从配置文件读取"""
        from api.agnes_client import load_agnes_config
        config = load_agnes_config()
        self.assertIn('api_key', config)
        self.assertTrue(config['api_key'], "API密钥未在config.ini中配置")
    
    def test_storage_config_from_config(self):
        """测试 AI 模型配置段（agnes）从配置文件读取；存储已统一为本地 SQLite，无独立配置段"""
        import configparser
        from pathlib import Path

        config_path = Path(__file__).resolve().parent.parent / 'config.ini'
        parser = configparser.ConfigParser()
        parser.read(config_path, encoding='utf-8')

        self.assertIn('agnes', parser)
        self.assertTrue(parser['agnes'].get('api_key'), "API密钥未在config.ini中配置")
    

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