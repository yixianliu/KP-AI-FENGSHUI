"""
数据整合模块 - 全面收集、清洗、统一和关联所有分析相关数据

功能：
1. 收集原始数据（输入信息、排盘结果、卦象数据）
2. 收集中间处理结果（五行分析、十神分析、命理分析、大运流年）
3. 收集历史分析记录
4. 数据清洗和格式统一
5. 建立数据关联关系
6. 生成完整的分析数据集供AI模型使用
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class DataIntegrator:
    """数据整合器 - 统一管理分析所需的所有数据"""

    def __init__(self):
        self.raw_data = {}
        self.processed_data = {}
        self.historical_records = []
        self.knowledge_context = {}
        self.relationships = {}
        self.cleaned_data = {}

    def collect_raw_data(self, input_data: Dict[str, Any], chart_data: Dict[str, Any] = None):
        """收集原始数据"""
        logger.info("[数据整合] 开始收集原始数据...")

        self.raw_data['input'] = {
            'name': input_data.get('name', '').strip(),
            'gender': input_data.get('gender', '').strip(),
            'year': input_data.get('year'),
            'month': input_data.get('month'),
            'day': input_data.get('day'),
            'hour': input_data.get('hour', 0),
            'minute': input_data.get('minute', 0),
            'city': input_data.get('city', '').strip(),
            'longitude': input_data.get('longitude', 120.0),
            'is_lunar': input_data.get('is_lunar', False),
            'question': input_data.get('question', '').strip(),
            'method': input_data.get('method', '').strip(),
            'timestamp': datetime.now().isoformat()
        }

        self.raw_data['chart'] = chart_data or {}

        logger.info(f"[数据整合] 原始数据收集完成，输入字段: {list(self.raw_data['input'].keys())}")

    def collect_processed_data(self, wuxing_result: Dict[str, Any] = None,
                               shishen_result: Dict[str, Any] = None,
                               mingli_result: Dict[str, Any] = None,
                               major_fortune: Dict[str, Any] = None):
        """收集中间处理结果"""
        logger.info("[数据整合] 开始收集中间处理结果...")

        self.processed_data['wuxing'] = wuxing_result or {}
        self.processed_data['shishen'] = shishen_result or {}
        self.processed_data['mingli'] = mingli_result or {}
        self.processed_data['major_fortune'] = major_fortune or {}

        logger.info(f"[数据整合] 中间结果收集完成，五行字段: {list(self.processed_data['wuxing'].keys()) if self.processed_data['wuxing'] else '无'}")
        logger.info(f"[数据整合] 中间结果收集完成，十神字段: {list(self.processed_data['shishen'].keys()) if self.processed_data['shishen'] else '无'}")
        logger.info(f"[数据整合] 中间结果收集完成，命理字段: {list(self.processed_data['mingli'].keys()) if self.processed_data['mingli'] else '无'}")

    def collect_historical_records(self, storage, limit: int = 5):
        """收集历史分析记录"""
        logger.info(f"[数据整合] 开始收集历史分析记录，限制: {limit}")

        try:
            records = storage.get_recent_reports(limit=limit)
            self.historical_records = records
            logger.info(f"[数据整合] 历史记录收集完成，共 {len(records)} 条")
        except Exception as e:
            logger.warning(f"[数据整合] 历史记录收集失败: {e}")
            self.historical_records = []

    def collect_knowledge_context(self, knowledge_base, analysis_type: str = 'bazi'):
        """收集知识库上下文"""
        logger.info(f"[数据整合] 开始收集知识库上下文，类型: {analysis_type}")

        if analysis_type == 'bazi':
            bazi_data = {
                'rizhu': self.processed_data.get('wuxing', {}).get('rizhu_wx', '') or
                         self.raw_data.get('chart', {}).get('bazi', {}).get('rizhu', ''),
                'wuxing': self.processed_data.get('wuxing', {}),
                'shishen': self.processed_data.get('shishen', {})
            }
            self.knowledge_context = knowledge_base.build_bazi_knowledge_context(bazi_data)
        else:
            self.knowledge_context = knowledge_base.build_meihua_knowledge_context(
                self.raw_data.get('chart', {})
            )

        logger.info(f"[数据整合] 知识库上下文收集完成，长度: {len(self.knowledge_context)}")

    def clean_and_unify(self):
        """数据清洗和格式统一"""
        logger.info("[数据整合] 开始数据清洗和格式统一...")

        self.cleaned_data = {}

        self.cleaned_data['input'] = self._clean_input_data()
        self.cleaned_data['bazi'] = self._clean_bazi_data()
        self.cleaned_data['wuxing'] = self._clean_wuxing_data()
        self.cleaned_data['shishen'] = self._clean_shishen_data()
        self.cleaned_data['mingli'] = self._clean_mingli_data()
        self.cleaned_data['major_fortune'] = self._clean_major_fortune_data()
        self.cleaned_data['historical'] = self._clean_historical_data()
        self.cleaned_data['knowledge'] = self.knowledge_context

        logger.info("[数据整合] 数据清洗和格式统一完成")

    def _clean_input_data(self) -> Dict[str, Any]:
        """清洗输入数据"""
        input_data = self.raw_data.get('input', {})
        cleaned = {}

        for key in ['name', 'gender', 'city']:
            cleaned[key] = str(input_data.get(key, '')).strip() or '未提供'

        for key in ['year', 'month', 'day', 'hour', 'minute']:
            cleaned[key] = int(input_data.get(key) or 0)

        cleaned['longitude'] = float(input_data.get('longitude', 120.0))
        cleaned['is_lunar'] = bool(input_data.get('is_lunar', False))
        cleaned['question'] = str(input_data.get('question', '')).strip() or '未指定'
        cleaned['method'] = str(input_data.get('method', '')).strip() or '未指定'

        return cleaned

    def _clean_bazi_data(self) -> Dict[str, Any]:
        """清洗八字排盘数据"""
        chart = self.raw_data.get('chart', {})
        bazi = chart.get('bazi', chart)

        cleaned = {
            'year_pillar': str(bazi.get('year_pillar', bazi.get('year', ''))).strip(),
            'month_pillar': str(bazi.get('month_pillar', bazi.get('month', ''))).strip(),
            'day_pillar': str(bazi.get('day_pillar', bazi.get('day', ''))).strip(),
            'hour_pillar': str(bazi.get('hour_pillar', bazi.get('hour', ''))).strip(),
            'rizhu': str(bazi.get('rizhu', '')).strip(),
            'month_zhi': str(bazi.get('month_zhi', '')).strip(),
            'hour_zhi': str(bazi.get('hour_zhi', '')).strip(),
            'solar_date': str(bazi.get('solar_date', '')).strip(),
            'lunar_date': str(bazi.get('lunar_date', '')).strip(),
            'solar_time': str(bazi.get('solar_time', '')).strip(),
            'original_time': str(bazi.get('original_time', '')).strip(),
        }

        return cleaned

    def _clean_wuxing_data(self) -> Dict[str, Any]:
        """清洗五行分析数据"""
        wuxing = self.processed_data.get('wuxing', {})
        cleaned = {}

        cleaned['summary'] = str(wuxing.get('summary', '')).strip()
        cleaned['total_score'] = float(wuxing.get('total_score', 0))
        cleaned['rizhu_wx'] = str(wuxing.get('rizhu_wx', '')).strip()

        elements = {}
        for wx in ['木', '火', '土', '金', '水']:
            wx_data = wuxing.get(wx, {})
            if isinstance(wx_data, dict):
                elements[wx] = {
                    'score': float(wx_data.get('score', 0)),
                    'percentage': float(wx_data.get('percentage', 0)),
                    'count': int(wx_data.get('count', 0)),
                    'strength': str(wx_data.get('strength', '')).strip(),
                    'description': str(wx_data.get('description', '')).strip(),
                }
            elif isinstance(wx_data, int):
                elements[wx] = {
                    'score': float(wx_data),
                    'percentage': 0,
                    'count': wx_data,
                    'strength': '',
                    'description': '',
                }
        cleaned['elements'] = elements

        tonggen = wuxing.get('tonggen', {})
        cleaned['tonggen'] = {
            'has_tonggen': bool(tonggen.get('has_tonggen', False)),
            'description': str(tonggen.get('description', '')).strip(),
            'details': tonggen.get('details', []),
        }

        return cleaned

    def _clean_shishen_data(self) -> Dict[str, Any]:
        """清洗十神分析数据"""
        shishen = self.processed_data.get('shishen', {})
        cleaned = {}

        cleaned['summary'] = {k: int(v) for k, v in shishen.get('summary', {}).items()}
        cleaned['weight_summary'] = {k: float(v) for k, v in shishen.get('weight_summary', {}).items()}
        cleaned['total_weights'] = {k: float(v) for k, v in shishen.get('total_weights', {}).items()}
        cleaned['analysis'] = str(shishen.get('analysis', '')).strip()

        pillars = shishen.get('pillars', {})
        cleaned['pillars'] = {}
        for pillar, items in pillars.items():
            cleaned['pillars'][pillar] = [
                {'gan': str(item.get('gan', '')), 'zhi': str(item.get('zhi', '')),
                 'shishen': str(item.get('shishen', '')), 'weight': float(item.get('weight', 0))}
                for item in items if isinstance(item, dict)
            ]

        return cleaned

    def _clean_mingli_data(self) -> Dict[str, Any]:
        """清洗命理分析数据"""
        mingli = self.processed_data.get('mingli', {})
        cleaned = {}

        shensha = mingli.get('shensha', {})
        cleaned['shensha'] = {
            'positive': [{'name': str(s.get('name', '')), 'description': str(s.get('description', ''))}
                         for s in shensha.get('positive', [])],
            'negative': [{'name': str(s.get('name', '')), 'description': str(s.get('description', ''))}
                         for s in shensha.get('negative', [])],
        }

        nayin = mingli.get('nayin', '')
        if isinstance(nayin, dict):
            nayin_lines = []
            for pillar, info in nayin.items():
                if isinstance(info, dict):
                    nayin_lines.append(f"{info.get('pillar', '')}{info.get('ganzhi', '')}，纳音{info.get('nayin', '')}（{info.get('element', '')}）")
                else:
                    nayin_lines.append(f"{pillar}: {info}")
            cleaned['nayin'] = '；'.join(nayin_lines)
        else:
            cleaned['nayin'] = str(nayin).strip()

        cleaned['ganzhi_relation'] = str(mingli.get('ganzhi_relation', '')).strip()

        kongwang = mingli.get('kongwang', '')
        if isinstance(kongwang, dict):
            cleaned['kongwang'] = kongwang.get('description', str(kongwang))
        else:
            cleaned['kongwang'] = str(kongwang).strip()

        cleaned['pattern'] = str(mingli.get('pattern', '')).strip()
        cleaned['analysis'] = str(mingli.get('analysis', '')).strip()

        return cleaned

    def _clean_major_fortune_data(self) -> Dict[str, Any]:
        """清洗大运数据"""
        fortune = self.processed_data.get('major_fortune', {})
        cleaned = {}

        cleaned['direction'] = str(fortune.get('direction', '')).strip()
        cleaned['start_age'] = int(fortune.get('start_age', 0))

        periods = []
        for period in fortune.get('periods', []):
            periods.append({
                'ganzhi': str(period.get('ganzhi', '')).strip(),
                'start_age': int(period.get('start_age', 0)),
                'end_age': int(period.get('end_age', 0)),
                'analysis': str(period.get('analysis', '')).strip(),
                'description': str(period.get('description', '')).strip(),
            })
        cleaned['periods'] = periods[:10]

        return cleaned

    def _clean_historical_data(self) -> List[Dict[str, Any]]:
        """清洗历史记录数据"""
        cleaned = []
        for record in self.historical_records:
            cleaned.append({
                'report_id': record.get('id', 0),
                'type': record.get('type', ''),
                'created_at': str(record.get('created_at', '')),
                'key_fields': record.get('key_fields', {}),
            })
        return cleaned

    def build_relationships(self):
        """建立数据关联关系"""
        logger.info("[数据整合] 开始建立数据关联关系...")

        relationships = {}

        bazi = self.cleaned_data.get('bazi', {})
        wuxing = self.cleaned_data.get('wuxing', {})
        shishen = self.cleaned_data.get('shishen', {})
        mingli = self.cleaned_data.get('mingli', {})

        relationships['rizhu_wuxing'] = {
            'rizhu': bazi.get('rizhu', ''),
            'wuxing': wuxing.get('rizhu_wx', ''),
            'score': wuxing.get('elements', {}).get(wuxing.get('rizhu_wx', ''), {}).get('score', 0),
        }

        relationships['month_zhi_influence'] = {
            'month_zhi': bazi.get('month_zhi', ''),
            'influence': '月令力量最强，对五行平衡影响最大',
        }

        relationships['wuxing_balance'] = {
            'strong': [wx for wx in ['木', '火', '土', '金', '水']
                       if wuxing.get('elements', {}).get(wx, {}).get('score', 0) >
                       wuxing.get('total_score', 1) * 0.25],
            'weak': [wx for wx in ['木', '火', '土', '金', '水']
                     if wuxing.get('elements', {}).get(wx, {}).get('score', 0) <
                     wuxing.get('total_score', 1) * 0.15],
        }

        total_weights = {k: v for k, v in shishen.get('total_weights', {}).items() if k != 'total'}
        dominant_category = max(total_weights, key=total_weights.get, default='')
        relationships['shishen_dominant'] = {
            'category': dominant_category,
            'weight': total_weights.get(dominant_category, 0),
        }

        relationships['shensha_impact'] = {
            'positive_count': len(mingli.get('shensha', {}).get('positive', [])),
            'negative_count': len(mingli.get('shensha', {}).get('negative', [])),
        }

        self.relationships = relationships
        logger.info("[数据整合] 数据关联关系建立完成")

    def build_comprehensive_prompt(self, analysis_type: str = 'bazi') -> str:
        """构建完整的综合提示词"""
        logger.info(f"[数据整合] 开始构建综合提示词，类型: {analysis_type}")

        parts = []

        if analysis_type == 'bazi':
            parts = self._build_bazi_prompt_parts()
        else:
            parts = self._build_meihua_prompt_parts()

        return '\n'.join(parts)

    def _build_bazi_prompt_parts(self) -> List[str]:
        """构建八字分析提示词"""
        parts = []

        input_data = self.cleaned_data.get('input', {})
        bazi = self.cleaned_data.get('bazi', {})
        wuxing = self.cleaned_data.get('wuxing', {})
        shishen = self.cleaned_data.get('shishen', {})
        mingli = self.cleaned_data.get('mingli', {})
        fortune = self.cleaned_data.get('major_fortune', {})
        relationships = self.relationships

        parts.append("=" * 70)
        parts.append("【命主基本信息】")
        parts.append("=" * 70)
        parts.append(f"姓名：{input_data.get('name', '')}")
        parts.append(f"性别：{input_data.get('gender', '')}")
        parts.append(f"出生日期：{input_data.get('year')}年{input_data.get('month')}月{input_data.get('day')}日")
        parts.append(f"出生时间：{input_data.get('hour'):02d}:{input_data.get('minute'):02d}")
        parts.append(f"出生地：{input_data.get('city')}（经度：{input_data.get('longitude')}°）")
        parts.append(f"是否农历：{'是' if input_data.get('is_lunar') else '否'}")

        parts.append("\n" + "=" * 70)
        parts.append("【八字排盘详情】")
        parts.append("=" * 70)
        parts.append(f"年柱：{bazi.get('year_pillar', '')}")
        parts.append(f"月柱：{bazi.get('month_pillar', '')}")
        parts.append(f"日柱：{bazi.get('day_pillar', '')}")
        parts.append(f"时柱：{bazi.get('hour_pillar', '')}")
        parts.append(f"日主：{bazi.get('rizhu', '')}")
        parts.append(f"月令：{bazi.get('month_zhi', '')}")
        parts.append(f"时支：{bazi.get('hour_zhi', '')}")
        parts.append(f"公历日期：{bazi.get('solar_date', '')}")
        parts.append(f"农历日期：{bazi.get('lunar_date', '')}")
        if bazi.get('solar_time'):
            parts.append(f"真太阳时：{bazi.get('solar_time')}")
            parts.append(f"原时间：{bazi.get('original_time')}")

        parts.append("\n" + "=" * 70)
        parts.append("【五行分析】")
        parts.append("=" * 70)
        parts.append(f"五行总结：{wuxing.get('summary', '')}")
        parts.append(f"总评分：{wuxing.get('total_score', 0):.2f}")
        parts.append(f"日主五行：{wuxing.get('rizhu_wx', '')}")

        elements = wuxing.get('elements', {})
        for wx in ['木', '火', '土', '金', '水']:
            elem = elements.get(wx, {})
            parts.append(f"  {wx}：分值={elem.get('score', 0):.2f}，占比={elem.get('percentage', 0):.1f}%，"
                         f"强度={elem.get('strength', '')}，{elem.get('description', '')}")

        tonggen = wuxing.get('tonggen', {})
        if tonggen.get('description'):
            parts.append(f"通根情况：{tonggen.get('description')}")
            for detail in tonggen.get('details', []):
                parts.append(f"  - {detail}")

        parts.append("\n" + "=" * 70)
        parts.append("【十神分析】")
        parts.append("=" * 70)

        shishen_summary = shishen.get('summary', {})
        if shishen_summary:
            shishen_list = [f"{k}={v}个" for k, v in shishen_summary.items()]
            parts.append(f"十神数量分布：{'、'.join(shishen_list)}")

        shishen_weights = shishen.get('weight_summary', {})
        if shishen_weights:
            weight_list = [f"{k}权重={v:.2f}" for k, v in shishen_weights.items()]
            parts.append(f"十神权重分布：{'、'.join(weight_list)}")

        total_weights = shishen.get('total_weights', {})
        if total_weights:
            parts.append(f"十神类别权重：")
            for category, weight in total_weights.items():
                parts.append(f"  {category}：{weight:.2f}")

        if shishen.get('analysis'):
            parts.append(f"十神综合分析：{shishen.get('analysis')}")

        pillars = shishen.get('pillars', {})
        if pillars:
            parts.append(f"各柱十神详情：")
            for pillar_name, items in pillars.items():
                pillar_items = [f"{item.get('gan')}{item.get('zhi')}({item.get('shishen')},权重{item.get('weight', 0):.2f})"
                                for item in items]
                parts.append(f"  {pillar_name}：{'、'.join(pillar_items)}")

        parts.append("\n" + "=" * 70)
        parts.append("【命理特征】")
        parts.append("=" * 70)

        shensha = mingli.get('shensha', {})
        positive_shensha = [s['name'] for s in shensha.get('positive', [])]
        negative_shensha = [s['name'] for s in shensha.get('negative', [])]
        if positive_shensha:
            parts.append(f"吉神：{'、'.join(positive_shensha)}")
        if negative_shensha:
            parts.append(f"凶煞：{'、'.join(negative_shensha)}")

        if mingli.get('nayin'):
            parts.append(f"纳音：{mingli.get('nayin')}")
        if mingli.get('kongwang'):
            parts.append(f"空亡：{mingli.get('kongwang')}")
        if mingli.get('pattern'):
            parts.append(f"格局：{mingli.get('pattern')}")
        if mingli.get('analysis'):
            parts.append(f"命理分析：{mingli.get('analysis')}")

        parts.append("\n" + "=" * 70)
        parts.append("【大运走势】")
        parts.append("=" * 70)
        parts.append(f"大运方向：{fortune.get('direction', '')}")
        parts.append(f"起运年龄：{fortune.get('start_age', 0)}岁")

        periods = fortune.get('periods', [])
        if periods:
            for period in periods[:6]:
                parts.append(f"  {period['start_age']}-{period['end_age']}岁：{period['ganzhi']} - "
                             f"{period['analysis'] or period['description']}")

        parts.append("\n" + "=" * 70)
        parts.append("【数据关联关系】")
        parts.append("=" * 70)

        rizhu_wuxing = relationships.get('rizhu_wuxing', {})
        parts.append(f"日主与五行：日主{bazi.get('rizhu', '')}属{rizhu_wuxing.get('wuxing', '')}，分值{rizhu_wuxing.get('score', 0):.2f}")

        wuxing_balance = relationships.get('wuxing_balance', {})
        if wuxing_balance.get('strong'):
            parts.append(f"五行偏旺：{'、'.join(wuxing_balance['strong'])}")
        if wuxing_balance.get('weak'):
            parts.append(f"五行偏弱：{'、'.join(wuxing_balance['weak'])}")

        shishen_dominant = relationships.get('shishen_dominant', {})
        parts.append(f"主导十神类别：{shishen_dominant.get('category', '')}，权重{shishen_dominant.get('weight', 0):.2f}")

        shensha_impact = relationships.get('shensha_impact', {})
        parts.append(f"神煞影响：吉神{shensha_impact.get('positive_count', 0)}个，凶煞{shensha_impact.get('negative_count', 0)}个")

        if self.cleaned_data.get('knowledge'):
            parts.append("\n" + "=" * 70)
            parts.append("【命理知识库参考】")
            parts.append("=" * 70)
            parts.append(self.cleaned_data['knowledge'])

        if self.cleaned_data.get('historical'):
            parts.append("\n" + "=" * 70)
            parts.append("【历史分析记录】")
            parts.append("=" * 70)
            for record in self.cleaned_data['historical'][:3]:
                parts.append(f"  ID:{record.get('report_id')} | 类型:{record.get('type')} | "
                             f"时间:{record.get('created_at', '')[:10]}")

        return parts

    def _build_meihua_prompt_parts(self) -> List[str]:
        """构建梅花易数提示词"""
        parts = []

        input_data = self.cleaned_data.get('input', {})
        chart = self.raw_data.get('chart', {})

        parts.append("=" * 70)
        parts.append("【求测信息】")
        parts.append("=" * 70)
        parts.append(f"所问之事：{input_data.get('question', '')}")
        parts.append(f"起卦方式：{input_data.get('method', '')}")

        base = chart.get('base', {})
        hu = chart.get('hu', {})
        bian = chart.get('bian', {})

        parts.append("\n" + "=" * 70)
        parts.append("【本卦】")
        parts.append("=" * 70)
        parts.append(f"卦名：{base.get('name', '')}")
        parts.append(f"上卦：{base.get('upper_name', '')}({base.get('upper_nature', '')})")
        parts.append(f"下卦：{base.get('lower_name', '')}({base.get('lower_nature', '')})")
        parts.append(f"卦辞：{base.get('gua_ci', '')}")
        parts.append(f"卦义：{base.get('description', '')}")

        changing_yao = base.get('changing_yao', 0)
        if changing_yao:
            parts.append(f"动爻：第{changing_yao}爻 - {base.get('changing_yao_name', '')}")
            parts.append(f"爻辞：{base.get('changing_yao_text', '')}")
            parts.append(f"爻义：{base.get('changing_yao_meaning', '')}")

        parts.append("\n" + "=" * 70)
        parts.append("【互卦】")
        parts.append("=" * 70)
        parts.append(f"卦名：{hu.get('name', '')}")
        parts.append(f"卦义：{hu.get('description', '')}")

        parts.append("\n" + "=" * 70)
        parts.append("【变卦】")
        parts.append("=" * 70)
        parts.append(f"卦名：{bian.get('name', '')}")
        parts.append(f"卦义：{bian.get('description', '')}")
        parts.append(f"判断：{bian.get('judgment', '')}")

        wuxing_analysis = chart.get('wuxing_analysis', {})
        if wuxing_analysis:
            parts.append("\n" + "=" * 70)
            parts.append("【五行生克分析】")
            parts.append("=" * 70)
            parts.append(f"本卦体用关系：{wuxing_analysis.get('base_relation', '')}")
            parts.append(f"变卦体用关系：{wuxing_analysis.get('bian_relation', '')}")

        parts.append("\n" + "=" * 70)
        parts.append("【综合判断】")
        parts.append("=" * 70)
        parts.append(f"综合吉凶：{chart.get('overall_judgment', '')}")

        if self.cleaned_data.get('knowledge'):
            parts.append("\n" + "=" * 70)
            parts.append("【梅花易数知识库参考】")
            parts.append("=" * 70)
            parts.append(self.cleaned_data['knowledge'])

        return parts

    def get_integrated_data(self) -> Dict[str, Any]:
        """获取整合后的完整数据集"""
        return {
            'raw': self.raw_data,
            'processed': self.processed_data,
            'cleaned': self.cleaned_data,
            'relationships': self.relationships,
            'knowledge': self.knowledge_context,
            'historical': self.historical_records,
        }

    def save_integrated_data(self, filepath: str):
        """保存整合后的数据到文件"""
        data = self.get_integrated_data()
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"[数据整合] 整合数据已保存到: {filepath}")
