import sys
import os
import unittest
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBaZiCalculator(unittest.TestCase):
    """八字计算器测试"""
    
    def setUp(self):
        from core.baazi import BaZiCalculator
        self.calculator = BaZiCalculator()
    
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
        """测试十二长生查询（优化后）"""
        result = self.calculator.get_shier_shen('甲', '甲子')
        self.assertIsNotNone(result)
        self.assertIn('name', result)
        self.assertIn('description', result)
    
    def test_get_year_ganzhi(self):
        """测试年干支计算"""
        ganzhi = self.calculator.get_year_ganzhi(2024)
        self.assertEqual(len(ganzhi), 2)
    
    def test_get_month_ganzhi(self):
        """测试月干支计算"""
        ganzhi = self.calculator.get_month_ganzhi('甲', 1)
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


class TestErrors(unittest.TestCase):
    """错误处理模块测试"""
    
    def test_error_code_enum(self):
        """测试错误码枚举"""
        from core.errors import ErrorCode
        self.assertEqual(ErrorCode.SUCCESS.value, 0)
        self.assertEqual(ErrorCode.VALIDATION_ERROR.value, 1001)
    
    def test_validation_error(self):
        """测试校验异常"""
        from core.errors import ValidationError
        try:
            raise ValidationError('测试错误', 'field')
        except ValidationError as e:
            self.assertEqual(e.error_code.value, 1001)
            self.assertEqual(e.message, '测试错误')
    
    def test_build_error_result(self):
        """测试构建错误结果"""
        from core.errors import build_error_result
        result = build_error_result(1, 'TestError', '测试错误')
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'TestError')
    
    def test_build_success_result(self):
        """测试构建成功结果"""
        from core.errors import build_success_result
        result = build_success_result(1, {'data': 'test'})
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['data'], 'test')


class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def test_get_shier_shen_performance(self):
        """测试十二长生查询性能（优化后）"""
        from core.baazi import BaZiCalculator
        calculator = BaZiCalculator()
        
        start = time.time()
        for _ in range(10000):
            calculator.get_shier_shen('甲', '甲子')
        elapsed = time.time() - start
        
        print(f"[性能测试] get_shier_shen 10000次调用耗时: {elapsed:.4f}秒")
        self.assertTrue(elapsed < 0.1, f"性能不达标，耗时{elapsed:.4f}秒")


class TestSecurity(unittest.TestCase):
    """安全测试"""
    
    def test_api_key_from_config(self):
        """测试API密钥从配置文件读取"""
        from api.agnes_client import load_agnes_config
        config = load_agnes_config()
        self.assertIn('api_key', config)
        self.assertTrue(config['api_key'], "API密钥未在config.ini中配置")
    
    def test_db_password_from_config(self):
        """测试数据库密码从配置文件读取"""
        import configparser
        from pathlib import Path
        
        config_path = Path(__file__).resolve().parent.parent / 'config.ini'
        parser = configparser.ConfigParser()
        parser.read(config_path, encoding='utf-8')
        
        self.assertIn('database', parser)
        self.assertTrue(parser['database'].get('password'), "数据库密码未在config.ini中配置")
    

if __name__ == '__main__':
    print("=" * 60)
    print("KP-AI-FENGSHUI 验证测试套件")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBaZiCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestMeihuaCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestErrors))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("所有测试通过！")
    else:
        print(f"测试失败: {len(result.failures)} 失败, {len(result.errors)} 错误")
    print("=" * 60)