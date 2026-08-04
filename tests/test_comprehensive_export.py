"""
综合建议（融合分析）流水线 + 导出器 单元测试

覆盖：
1. 综合建议流水线（无网络，使用 mock 的 Agnes 客户端）：
   - 融合提示词正确汇编三方结论与元数据；
   - 非 JSON 文本回退解析产出 6 字段且类型正确；
   - 完整流程（mock 返回合法 JSON）产出 success=True 且 ai_analysis 含 6 字段、类型正确；
   - 缺少三方结论时不崩溃，返回 success=False 的错误结果。
2. 导出器（八字章节渲染）：
   - base_exporter.filter_export_data / has_chapter 行为；
   - Csv / Excel / Pdf 导出器对八字结果字典可无异常写出文件；
   - 当前导出章节不含 'zonghe'（综合建议未接入导出，见 P0-2b 修复目标）——此测试锁定该缺口。
"""

import sys
import os
import json
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analysis_pipeline import AnalysisPipeline
from api.agnes_client import AgnesClient
from core.ai_cache import clear_all
from ui.export.base_exporter import BaseExporter, filter_export_data, has_chapter, CHAPTERS
from ui.export.csv_exporter import CsvExporter
from ui.export.excel_exporter import ExcelExporter
from ui.export.pdf_exporter import PdfExporter

# 综合建议 6 字段契约
COMPREHENSIVE_REQUIRED = [
    'tri_method_overview', 'consistency_check', 'synthesis',
    'unified_plan', 'key_timing', 'disclaimer',
]

VALID_COMPREHENSIVE_JSON = json.dumps({
    "tri_method_overview": ["八字：日主身强，喜金水", "梅花：本卦乾，事可成", "六壬：三传申寅子，谋事有进"],
    "consistency_check": ["三家一致：事业向上", "分歧：梅花偏守、六壬偏进，尺度不同"],
    "synthesis": ["综合定论：当前宜进取但需守成"],
    "unified_plan": ["事业：把握下半年窗口", "情感：多沟通", "健康：规律作息", "修身：静坐", "时机：农历八月有利"],
    "key_timing": ["有利：秋冬金水旺", "禁忌：冲动决策"],
    "disclaimer": "命理咨询仅供参考，重大决策须理性判断。",
}, ensure_ascii=False)

SAMPLE_BAZI_DATA = {
    'basic_info': {'pan_type': '八字排盘', 'solar_date': '2000-01-01', 'lunar_date': '己卯年', 'hour': '12', 'location': '北京', 'gender': '男'},
    'bazi_types': {'strength': '身强', 'geju_type': '扶抑格', 'geju_name': '伤官生财', 'wuxing_summary': '金水偏旺'},
    'bazi': {'year_pillar': '己卯', 'month_pillar': '丙子', 'day_pillar': '甲子', 'hour_pillar': '庚午'},
    'wuxing': {'木': 30, '火': 20, '土': 15, '金': 20, '水': 15},
    'shishen': {'正官': 10, '正财': 8},
    'dayun': {'direction': '顺', 'qiyun_text': '8岁起运', 'periods': [{'period': 1, 'ganzhi': '丁丑', 'start_age': 8, 'end_age': 17, 'start_year': 2008, 'end_year': 2017, 'analysis': '平稳'}]},
    'ai_analysis': {
        'personality': ['坚韧', '好学'], 'career': ['宜技术'], 'marriage': ['晚婚吉'],
        'health': ['注意肝胆'], 'pattern_analysis': ['伤官生财'], 'wuxing_balance': ['金水旺'],
        'shishen_analysis': ['正官有力'], 'improvement_plan': ['补水'], 'suggestions': ['守静'],
    },
}


class FakeAgnes:
    """最小可替换的 Agnes 客户端：返回合法 JSON，且复用真实 _clean/_validate 静态方法。"""

    def __init__(self, content=VALID_COMPREHENSIVE_JSON, disclaimer_as_list=False):
        self._content = content
        self._disclaimer_as_list = disclaimer_as_list

    def chat_completion(self, messages, temperature=0.4, max_tokens=4096):
        content = self._content
        if self._disclaimer_as_list:
            # 模拟模型偶发把 disclaimer 返回成列表，验证类型兜转
            obj = json.loads(self._content)
            obj['disclaimer'] = [obj['disclaimer']]
            content = json.dumps(obj, ensure_ascii=False)
        return {'content': content, 'usage': {'total_tokens': 123, 'prompt_tokens': 50, 'completion_tokens': 73}}

    def _clean_json_response(self, content):
        return AgnesClient._clean_json_response(content)

    def _validate_json_result(self, analysis, required_fields):
        return AgnesClient._validate_json_result(analysis, required_fields)


class TestComprehensivePipeline(unittest.TestCase):
    """综合建议流水线（mock AI，无网络）。"""

    def setUp(self):
        clear_all()  # 清理缓存，防止前后测试相互污染
        self.pipeline = AnalysisPipeline()
        self.pipeline.agnes_client = FakeAgnes()

    def test_build_prompt_includes_three_methods(self):
        """融合提示词应汇编八字/梅花/六壬三段结论及元数据。"""
        parts = {
            'bazi': {'personality': ['坚韧'], 'suggestions': ['守静']},
            'meihua': {'final_verdict': '事可成'},
            'liuren': {'ke_overview': ['课体平']},
        }
        meta = {'name': '张三', 'gender': '男', 'question': '事业', 'bazi_summary': '己卯 丙子 甲子 庚午'}
        prompt = self.pipeline._build_comprehensive_prompt(parts, meta)
        self.assertIn('【八字分析结论】', prompt)
        self.assertIn('【梅花易数分析结论】', prompt)
        self.assertIn('【大六壬分析结论】', prompt)
        self.assertIn('张三', prompt)
        self.assertIn('事业', prompt)

    def test_parse_text_fallback_fields(self):
        """非 JSON 文本回退解析应产出 6 字段，且 disclaimer 为字符串、其余为列表。"""
        text = (
            "一、三方概览\n- 八字根基稳\n- 梅花机缘现\n二、矛盾与印证\n- 三家一致向上\n"
            "三、综合定论\n- 宜进取守成\n四、统一方案\n- 事业抓窗口\n五、关键时机\n- 秋冬有利\n六、免责\n- 仅供参考\n"
        )
        result = self.pipeline._parse_text_to_comprehensive_fields(text, COMPREHENSIVE_REQUIRED)
        for f in COMPREHENSIVE_REQUIRED:
            self.assertIn(f, result)
        self.assertIsInstance(result['disclaimer'], str)
        for f in COMPREHENSIVE_REQUIRED:
            if f != 'disclaimer':
                self.assertIsInstance(result[f], list)

    def test_full_run_success_contract(self):
        """完整流程（mock 合法 JSON）：success=True 且 ai_analysis 含 6 字段、类型正确。"""
        parts = {'bazi': {'personality': ['坚韧']}, 'meihua': {'final_verdict': 'x'}, 'liuren': {'ke_overview': ['y']}}
        out = self.pipeline.run_comprehensive_analysis(parts, {'name': '张三'}, task_id='t1')
        self.assertTrue(out.get('success'))
        ai = out.get('ai_analysis', {})
        for f in COMPREHENSIVE_REQUIRED:
            self.assertIn(f, ai)
        self.assertIsInstance(ai['disclaimer'], str)
        self.assertIsInstance(ai['unified_plan'], list)
        self.assertGreater(out.get('token_usage', 0), 0)

    def test_full_run_disclaimer_list_coerced(self):
        """模型把 disclaimer 返回为列表时，应被兜转为字符串（类型兜转修复验证）。"""
        self.pipeline.agnes_client = FakeAgnes(disclaimer_as_list=True)
        parts = {'bazi': {'personality': ['坚韧']}}
        out = self.pipeline.run_comprehensive_analysis(parts, {}, task_id='t2')
        ai = out.get('ai_analysis', {})
        self.assertIsInstance(ai['disclaimer'], str)

    def test_missing_parts_returns_error(self):
        """缺少三方结论：不抛异常，返回 success=False 的错误结果（含 error_type/error_message）。"""
        out = self.pipeline.run_comprehensive_analysis({}, {})
        self.assertFalse(out.get('success'))
        self.assertIn('error_type', out)
        self.assertIn('error_message', out)
        self.assertEqual(out.get('error_type'), 'AnalysisPipelineError')


class TestExportBase(unittest.TestCase):
    """导出器基础函数与章节契约。"""

    def test_filter_export_data(self):
        """filter_export_data 仅保留所选章节数据键；神煞(mingli)始终保留。"""
        data = dict(SAMPLE_BAZI_DATA)
        data['mingli'] = {'shensha': [{'name': '天乙贵人', 'description': '吉'}]}
        filtered = filter_export_data(data, ['basic_info', 'bazi', 'ai_analysis'])
        self.assertIn('basic_info', filtered)
        self.assertIn('bazi', filtered)
        self.assertIn('ai_analysis', filtered)
        self.assertIn('mingli', filtered)  # 始终保留
        self.assertNotIn('wuxing', filtered)

    def test_has_chapter(self):
        """has_chapter 对各章节的可渲染判定。"""
        self.assertTrue(has_chapter(SAMPLE_BAZI_DATA, 'ai_analysis'))
        self.assertTrue(has_chapter(SAMPLE_BAZI_DATA, 'bazi'))
        self.assertFalse(has_chapter({'ai_analysis': []}, 'ai_analysis'))  # 空列表不算
        self.assertFalse(has_chapter({}, 'bazi'))

    def test_chapters_includes_zonghe_meihua_liuren(self):
        """导出章节清单已包含 'zonghe'/'meihua'/'liuren'（综合/梅花/六壬均接入导出，见 P0-2b/P2-1）。"""
        keys = [k for k, _ in CHAPTERS]
        self.assertIn('zonghe', keys)
        self.assertIn('meihua', keys)
        self.assertIn('liuren', keys)


class TestExportRenderers(unittest.TestCase):
    """三个导出器对八字结果字典的可写性（不产生异常）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _path(self, name):
        return os.path.join(self.tmp, name)

    def test_csv_export_bazi(self):
        """CsvExporter 写出八字结果，文件含关键章节标题。"""
        p = self._path('bazi.csv')
        ok = CsvExporter().export(dict(SAMPLE_BAZI_DATA), p)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(p))
        with open(p, encoding='utf-8-sig') as f:
            content = f.read()
        self.assertIn('命局类型', content)
        self.assertIn('龙虎山大师兄智能深度分析', content)
        self.assertIn('甲子', content)  # 日柱

    def test_excel_export_bazi(self):
        """ExcelExporter 写出八字结果且不抛异常。"""
        p = self._path('bazi.xlsx')
        ok = ExcelExporter().export(dict(SAMPLE_BAZI_DATA), p)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(p))

    def test_pdf_export_bazi(self):
        """PdfExporter 写出八字结果且不抛异常。"""
        p = self._path('bazi.pdf')
        ok = PdfExporter().export(dict(SAMPLE_BAZI_DATA), p)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(p))

    def test_csv_export_zonghe(self):
        """CsvExporter 渲染综合建议章节：含关键小节标题与免责说明。"""
        zonghe = {
            'tri_method_overview': ['八字：身强', '梅花：可成', '六壬：有进'],
            'consistency_check': ['三家一致'],
            'synthesis': ['宜进取守成'],
            'unified_plan': ['事业抓窗口'],
            'key_timing': ['秋冬有利'],
            'disclaimer': '命理咨询仅供参考。',
        }
        p = self._path('zonghe.csv')
        ok = CsvExporter().export({'zonghe': zonghe}, p)
        self.assertTrue(ok)
        with open(p, encoding='utf-8-sig') as f:
            content = f.read()
        self.assertIn('综合建议（龙虎山大师兄融合）', content)
        self.assertIn('三方概览', content)
        self.assertIn('统一趋吉避凶方案', content)
        self.assertIn('命理咨询仅供参考。', content)

    def test_excel_export_zonghe(self):
        """ExcelExporter 渲染综合建议章节且不抛异常。"""
        zonghe = {'synthesis': ['综合定论x'], 'disclaimer': '免责'}
        p = self._path('zonghe.xlsx')
        ok = ExcelExporter().export({'zonghe': zonghe}, p)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(p))

    def test_pdf_export_zonghe(self):
        """PdfExporter 渲染综合建议章节且不抛异常。"""
        zonghe = {'synthesis': ['综合定论x'], 'disclaimer': '免责'}
        p = self._path('zonghe.pdf')
        ok = PdfExporter().export({'zonghe': zonghe}, p)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(p))

    def test_csv_export_meihua(self):
        """CsvExporter 渲染梅花易数章节且不抛异常。"""
        data = {
            'meihua_data': {'method': '时间起卦', 'base_hex': '乾为天', 'changed_hex': '天风姤',
                            'ti_gong': '乾', 'yong_gong': '巽'},
            'meihua_ai': {'personality': ['主人刚健']},
        }
        p = self._path('meihua.csv')
        ok = CsvExporter().export(data, p)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(p))

    def test_csv_export_liuren(self):
        """CsvExporter 渲染大六壬章节且不抛异常。"""
        data = {
            'liuren_data': {'pan_date': '2024-06-15', 'san_chuan': '申→辰→子',
                            'gate': '贼克', 'yue_jiang': '亥'},
            'liuren_ai': {'personality': ['课体刚毅']},
        }
        p = self._path('liuren.csv')
        ok = CsvExporter().export(data, p)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(p))

    def test_excel_export_meihua_liuren(self):
        """ExcelExporter 渲染梅花 + 大六壬章节且不抛异常。"""
        data = {
            'meihua_data': {'method': '时间起卦', 'base_hex': '乾为天'},
            'meihua_ai': {'personality': ['刚健']},
            'liuren_data': {'san_chuan': '申→辰→子', 'gate': '贼克'},
            'liuren_ai': {'personality': ['课体刚毅']},
        }
        p = self._path('ml.xlsx')
        ok = ExcelExporter().export(data, p)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(p))


if __name__ == '__main__':
    unittest.main(verbosity=2)
