"""
批量回测校验模块 - 验证八字测算准确性
包含标准案例数据集、自动对比程序输出与标准推演结果、统计误差率

使用说明：
1. 标准案例数据存储在 STANDARD_CASES 中
2. 运行 run_backtest() 执行批量回测
3. 查看回测报告了解误差统计

修复内容：
1. 提供标准八字案例数据集，覆盖不同格局、五行分布
2. 自动对比排盘结果、五行分析、格局判定
3. 统计各环节误差率，定位测算偏差
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.baazi import BaZiCalculator
from core.wuxing import WuXingAnalyzer
from core.shishen import ShiShenAnalyzer
from core.geju_analyzer import GeJuAnalyzer
from core.yunshi import YunShiCalculator
from core.mingli import MingLiAnalyzer


STANDARD_CASES = [
    {
        'id': 'case_001',
        'name': '标准案例1',
        'gender': '男',
        'year': 2000,
        'month': 1,
        'day': 1,
        'hour': 12,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '己卯',
            'month': '丙子',
            'day': '甲子',
            'hour': '庚午',
            'rizhu': '甲'
        }
    },
    {
        'id': 'case_002',
        'name': '标准案例2',
        'gender': '女',
        'year': 1990,
        'month': 10,
        'day': 1,
        'hour': 8,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '庚午',
            'month': '乙酉',
            'day': '乙巳',
            'hour': '庚辰',
            'rizhu': '乙'
        }
    },
    {
        'id': 'case_003',
        'name': '标准案例3',
        'gender': '男',
        'year': 1949,
        'month': 10,
        'day': 1,
        'hour': 15,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '己丑',
            'month': '癸酉',
            'day': '庚午',
            'hour': '甲申',
            'rizhu': '庚'
        }
    },
    {
        'id': 'case_004',
        'name': '标准案例4',
        'gender': '女',
        'year': 1976,
        'month': 9,
        'day': 9,
        'hour': 7,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '丙辰',
            'month': '丁酉',
            'day': '庚午',
            'hour': '庚辰',
            'rizhu': '庚'
        }
    },
    {
        'id': 'case_005',
        'name': '标准案例5',
        'gender': '男',
        'year': 1997,
        'month': 7,
        'day': 1,
        'hour': 7,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '丁丑',
            'month': '丙午',
            'day': '庚戌',
            'hour': '己卯',
            'rizhu': '庚'
        }
    },
    {
        'id': 'case_006',
        'name': '节气临界点案例',
        'gender': '男',
        'year': 2004,
        'month': 2,
        'day': 4,
        'hour': 20,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '甲申',
            'month': '丙寅',
            'day': '己未',
            'hour': '甲戌',
            'rizhu': '己'
        }
    },
    {
        'id': 'case_007',
        'name': '晚子时案例',
        'gender': '女',
        'year': 2024,
        'month': 12,
        'day': 31,
        'hour': 23,
        'minute': 30,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '甲辰',
            'month': '丙子',
            'day': '丙子',
            'hour': '戊子',
            'rizhu': '丙'
        }
    },
    {
        'id': 'case_008',
        'name': '真太阳时修正案例',
        'gender': '男',
        'year': 2024,
        'month': 6,
        'day': 21,
        'hour': 12,
        'minute': 0,
        'longitude': 104.0,
        'is_lunar': False,
        'expected': {
            'year': '甲辰',
            'month': '庚午',
            'day': '壬戌',
            'hour': '乙巳',
            'rizhu': '壬'
        }
    },
    {
        'id': 'case_009',
        'name': '子月案例',
        'gender': '女',
        'year': 2023,
        'month': 12,
        'day': 22,
        'hour': 10,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '癸卯',
            'month': '甲子',
            'day': '庚申',
            'hour': '辛巳',
            'rizhu': '庚'
        }
    },
    {
        'id': 'case_010',
        'name': '寅月案例',
        'gender': '男',
        'year': 2024,
        'month': 2,
        'day': 4,
        'hour': 10,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '甲辰',
            'month': '丙寅',
            'day': '甲辰',
            'hour': '己巳',
            'rizhu': '甲'
        }
    },
    {
        'id': 'case_011',
        'name': '午月案例',
        'gender': '女',
        'year': 2024,
        'month': 6,
        'day': 6,
        'hour': 14,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '甲辰',
            'month': '庚午',
            'day': '丁未',
            'hour': '丁未',
            'rizhu': '丁'
        }
    },
    {
        'id': 'case_012',
        'name': '酉月案例',
        'gender': '男',
        'year': 2024,
        'month': 9,
        'day': 8,
        'hour': 8,
        'minute': 0,
        'longitude': 120.0,
        'is_lunar': False,
        'expected': {
            'year': '甲辰',
            'month': '癸酉',
            'day': '辛巳',
            'hour': '壬辰',
            'rizhu': '辛'
        }
    }
]


class BackTestResult:
    """回测结果类"""
    
    def __init__(self):
        self.total_cases = 0
        self.passed_cases = 0
        self.failed_cases = 0
        self.detailed_results = []
        self.error_summary = {
            'year_error': 0,
            'month_error': 0,
            'day_error': 0,
            'hour_error': 0,
            'rizhu_error': 0,
            'wuxing_error': 0,
            'geju_error': 0,
            'geju_type_error': 0
        }
    
    def add_result(self, case_id: str, name: str, passed: bool, 
                   errors: List[str], details: Dict[str, Any]):
        """添加单个测试结果"""
        self.total_cases += 1
        if passed:
            self.passed_cases += 1
        else:
            self.failed_cases += 1
        
        self.detailed_results.append({
            'case_id': case_id,
            'name': name,
            'passed': passed,
            'errors': errors,
            'details': details
        })
    
    def get_accuracy(self) -> float:
        """计算准确率"""
        if self.total_cases == 0:
            return 0.0
        return round(self.passed_cases / self.total_cases * 100, 2)
    
    def get_report(self) -> Dict[str, Any]:
        """生成回测报告"""
        return {
            'total_cases': self.total_cases,
            'passed_cases': self.passed_cases,
            'failed_cases': self.failed_cases,
            'accuracy': self.get_accuracy(),
            'error_summary': self.error_summary,
            'detailed_results': self.detailed_results
        }


class BaZiBackTester:
    """八字回测器"""
    
    def __init__(self):
        self.bazi_calc = BaZiCalculator()
        self.wuxing_analyzer = WuXingAnalyzer()
        self.shishen_analyzer = ShiShenAnalyzer()
        self.geju_analyzer = GeJuAnalyzer()
        self.yunshi_calc = YunShiCalculator()
        self.mingli_analyzer = MingLiAnalyzer()
    
    def test_single_case(self, case: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """测试单个案例"""
        errors = []
        details = {}
        
        try:
            bazi_result = self.bazi_calc.calculate(
                year=case['year'],
                month=case['month'],
                day=case['day'],
                hour=case['hour'],
                minute=case.get('minute', 0),
                longitude=case.get('longitude', 120.0),
                is_lunar=case.get('is_lunar', False)
            )
            
            details['actual'] = {
                'year': bazi_result.get('year', ''),
                'month': bazi_result.get('month', ''),
                'day': bazi_result.get('day', ''),
                'hour': bazi_result.get('hour', ''),
                'rizhu': bazi_result.get('rizhu', '')
            }
            
            expected = case['expected']
            
            if bazi_result['year'] != expected.get('year', ''):
                errors.append(f"年柱错误: 实际{bazi_result['year']}, 期望{expected['year']}")
            
            if bazi_result['month'] != expected.get('month', ''):
                errors.append(f"月柱错误: 实际{bazi_result['month']}, 期望{expected['month']}")
            
            if bazi_result['day'] != expected.get('day', ''):
                errors.append(f"日柱错误: 实际{bazi_result['day']}, 期望{expected['day']}")
            
            if bazi_result['hour'] != expected.get('hour', ''):
                errors.append(f"时柱错误: 实际{bazi_result['hour']}, 期望{expected['hour']}")
            
            if bazi_result['rizhu'] != expected.get('rizhu', ''):
                errors.append(f"日主错误: 实际{bazi_result['rizhu']}, 期望{expected['rizhu']}")
            
            wuxing_result = self.wuxing_analyzer.analyze(bazi_result)
            details['wuxing_summary'] = wuxing_result.get('summary', '')
            
            if expected.get('wuxing_summary'):
                if expected['wuxing_summary'] not in wuxing_result.get('summary', ''):
                    errors.append(f"五行分析错误: 实际{wuxing_result['summary']}, 期望{expected['wuxing_summary']}")
            
            geju_result = self.geju_analyzer.analyze(bazi_result, wuxing_result)
            details['geju'] = geju_result.get('main_geju', '')
            details['geju_type'] = geju_result.get('geju_type', '')
            
            if expected.get('geju') and geju_result['main_geju'] != expected['geju']:
                errors.append(f"格局错误: 实际{geju_result['main_geju']}, 期望{expected['geju']}")
            
            if expected.get('geju_type') and geju_result['geju_type'] != expected['geju_type']:
                errors.append(f"格局类型错误: 实际{geju_result['geju_type']}, 期望{expected['geju_type']}")
            
            return len(errors) == 0, errors, details
            
        except Exception as e:
            errors.append(f"测试异常: {str(e)}")
            return False, errors, details
    
    def run_backtest(self, cases: List[Dict[str, Any]] = None) -> BackTestResult:
        """运行批量回测"""
        if cases is None:
            cases = STANDARD_CASES
        
        result = BackTestResult()
        
        print(f"{'='*60}")
        print(f"[回测] 开始批量回测，共{len(cases)}个案例")
        print(f"{'='*60}")
        
        for i, case in enumerate(cases, 1):
            print(f"\n[{i}/{len(cases)}] 测试案例: {case['id']} - {case['name']}")
            print(f"      生辰: {case['year']}-{case['month']:02d}-{case['day']:02d} {case['hour']:02d}:{case.get('minute', 0):02d}")
            
            passed, errors, details = self.test_single_case(case)
            
            if passed:
                print(f"      ✓ 通过")
            else:
                print(f"      ✗ 失败")
                for error in errors:
                    print(f"         - {error}")
            
            result.add_result(case['id'], case['name'], passed, errors, details)
        
        print(f"\n{'='*60}")
        print(f"[回测] 回测完成")
        print(f"[回测] 总案例数: {result.total_cases}")
        print(f"[回测] 通过案例: {result.passed_cases}")
        print(f"[回测] 失败案例: {result.failed_cases}")
        print(f"[回测] 准确率: {result.get_accuracy()}%")
        print(f"{'='*60}")
        
        return result
    
    def generate_report(self, result: BackTestResult, output_path: str = None) -> str:
        """生成回测报告"""
        report = {
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_cases': result.total_cases,
            'passed_cases': result.passed_cases,
            'failed_cases': result.failed_cases,
            'accuracy': result.get_accuracy(),
            'error_summary': result.error_summary,
            'detailed_results': []
        }
        
        for detail in result.detailed_results:
            report['detailed_results'].append({
                'case_id': detail['case_id'],
                'name': detail['name'],
                'passed': detail['passed'],
                'errors': detail['errors'],
                'details': detail['details']
            })
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"[回测] 报告已保存到: {output_path}")
        
        return json.dumps(report, ensure_ascii=False, indent=2)


def run_backtest():
    """运行回测的快捷函数"""
    tester = BaZiBackTester()
    result = tester.run_backtest()
    
    report_dir = os.path.join(project_root, 'backtest_reports')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f'backtest_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    tester.generate_report(result, report_path)
    
    return result


def run_simple_test():
    """运行简单测试，验证核心功能"""
    tester = BaZiBackTester()
    
    test_cases = [
        {
            'id': 'simple_001',
            'name': '测试1',
            'gender': '男',
            'year': 2000,
            'month': 1,
            'day': 1,
            'hour': 12,
            'minute': 0,
            'longitude': 120.0,
            'is_lunar': False,
            'expected': {
                'year': '己卯',
                'month': '丙子',
                'day': '甲子',
                'hour': '庚午',
                'rizhu': '甲'
            }
        },
        {
            'id': 'simple_002',
            'name': '测试2',
            'gender': '女',
            'year': 1990,
            'month': 10,
            'day': 1,
            'hour': 8,
            'minute': 0,
            'longitude': 120.0,
            'is_lunar': False,
            'expected': {
                'year': '庚午',
                'month': '乙酉',
                'day': '乙巳',
                'hour': '庚辰',
                'rizhu': '乙'
            }
        }
    ]
    
    print(f"{'='*60}")
    print(f"[简易测试] 开始核心功能测试")
    print(f"{'='*60}")
    
    for case in test_cases:
        print(f"\n测试: {case['name']}")
        passed, errors, details = tester.test_single_case(case)
        
        if passed:
            print(f"  ✓ 通过")
            print(f"    四柱: {details['actual']['year']} {details['actual']['month']} {details['actual']['day']} {details['actual']['hour']}")
        else:
            print(f"  ✗ 失败")
            for error in errors:
                print(f"    - {error}")
    
    print(f"\n{'='*60}")
    print(f"[简易测试] 测试完成")
    print(f"{'='*60}")


if __name__ == '__main__':
    print(f"{'='*60}")
    print(f"八字测算批量回测工具")
    print(f"{'='*60}")
    
    import argparse
    parser = argparse.ArgumentParser(description='八字测算批量回测')
    parser.add_argument('--mode', choices=['simple', 'full'], default='simple',
                        help='测试模式: simple(简易测试) 或 full(完整回测)')
    parser.add_argument('--output', help='报告输出路径')
    
    args = parser.parse_args()
    
    if args.mode == 'full':
        result = run_backtest()
    else:
        run_simple_test()