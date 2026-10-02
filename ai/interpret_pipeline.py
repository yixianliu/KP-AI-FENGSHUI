# -*- coding: utf-8 -*-
"""
ai/interpret_pipeline.py — AI 解读管道

对应执行计划任务 3.12 + 3.13：
- 接收排盘数据 + RAG 检索结果
- 调用 AI 生成三段式解读（格局总评 / 分项分析 / 建议与注意事项）
- 强制校验古籍出处引用（3.13）
- 输出结构化 JSON，尾部附加免责声明

设计原则：
  确定性计算（core/bazi）与 AI 解读完全分离；AI 仅负责通俗化解读。
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional

from api.agnes_client import AgnesClient


# ---------------------------------------------------------------- 常量

#: 免责声明（每次 AI 输出末尾强制追加）
DISCLAIMER = (
    "\n\n---\n"
    "【免责说明】本解读仅供传统文化研究参考，不构成任何决策依据。"
    "涉及健康、法律、投资等重大事项，请咨询相关专业人士。"
)

#: 古籍出处正则（用于校验）
CITATION_PATTERN = re.compile(
    r'《([^《》]+)》(?:[·.．]\s*[^，。]*?)?',
    re.UNICODE,
)

#: 必填古籍名（用于校验是否引用了至少一部权威典籍）
REQUIRED_CITATIONS = [
    '子平真诠', '滴天髓', '穷通宝鉴', '三命通会',
    '渊海子平', '沈氏玄空学', '地理辩证疏',
]

# ---------------------------------------------------------------- 三段式结构


class ThreePartInterpretation:
    """AI 解读三段式结构化解析器。

    将 AI 原始输出按「格局总评 / 分项分析 / 建议与注意事项」三段拆解，
    并强制校验古籍出处引用。
    """

    # 段标题匹配模式（兼容多种写法）
    SECTION_PATTERNS: List[tuple] = [
        (re.compile(r'格局总评|总评|格局分析', re.UNICODE), 'summary'),
        (re.compile(r'分项分析|分项|分项解析', re.UNICODE), 'analysis'),
        (re.compile(r'建议与注意事项|注意事项|建议事项', re.UNICODE), 'advice'),
    ]

    def __init__(self, rag_context: str = ''):
        """
        Args:
            rag_context: RAG 检索到的古籍原文上下文（用于出处校验）
        """
        self.rag_context = rag_context
        self._citations_found: List[str] = []

    # ---------------------------------------------------------------- 解析

    def parse(self, raw_text: str) -> Dict[str, Any]:
        """解析 AI 原始输出为三段式结构。

        解析策略（优先级从高到低）：
        1. 若输入为合法 JSON，直接返回各字段
        2. 按段标题正则拆分，提取三段内容
        3. 兜底：将全文归入 summary，analysis/advice 为空

        Args:
            raw_text: AI 返回的原始文本

        Returns:
            dict: {'summary': str, 'analysis': str, 'advice': str,
                    'citations': list[str], 'has_disclaimer': bool}
        """
        raw_text = raw_text.strip()

        # 1) 尝试 JSON 解析（结构化输出）
        parsed_json = self._try_parse_json(raw_text)
        if parsed_json is not None:
            citations = self._extract_citations(raw_text)
            return {
                'summary': parsed_json.get('summary', parsed_json.get('total_eval', '')),
                'analysis': parsed_json.get('analysis', parsed_json.get('detail', '')),
                'advice': parsed_json.get('advice', parsed_json.get('suggestions', '')),
                'citations': citations,
                'has_disclaimer': DISCLAIMER.split('\n')[0] in raw_text,
                'source': 'json',
            }

        # 2) 按段标题正则拆分
        sections = self._split_by_sections(raw_text)
        citations = self._extract_citations(raw_text)

        return {
            'summary': sections.get('summary', ''),
            'analysis': sections.get('analysis', ''),
            'advice': sections.get('advice', ''),
            'citations': citations,
            'has_disclaimer': DISCLAIMER.split('\n')[0] in raw_text,
            'source': 'text',
        }

    # ---------------------------------------------------------------- 私有方法

    def _try_parse_json(self, text: str) -> Optional[dict]:
        """尝试从文本中提取 JSON 对象。"""
        # 直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 提取 { ... } 子串
        match = re.search(r'\{[^{}]*"summary"[^{}]*"analysis"[^{}]*"advice"[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None

    def _split_by_sections(self, text: str) -> Dict[str, str]:
        """按段标题正则拆分文本。"""
        sections: Dict[str, str] = {}
        segments = re.split(
            r'(?=格局总评|总评|分项分析|分项解析|建议与注意事项|注意事项)',
            text,
            flags=re.UNICODE,
        )
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            for pattern, key in self.SECTION_PATTERNS:
                if pattern.search(seg):
                    # 移除段标题行，保留正文
                    content = re.sub(pattern, '', seg, count=1).strip()
                    sections[key] = content
                    break
            else:
                # 未匹配任何段标题，归入 summary
                if 'summary' not in sections:
                    sections['summary'] = seg
        return sections

    def _extract_citations(self, text: str) -> List[str]:
        """提取所有古籍引用（《xxx》格式）。"""
        citations = CITATION_PATTERN.findall(text)
        self._citations_found = list(dict.fromkeys(citations))  # 去重保序
        return self._citations_found

    # ---------------------------------------------------------------- 校验

    def validate_citations(self, citations: List[str]) -> Dict[str, Any]:
        """校验古籍出处引用完整性。

        规则：
        - 必须引用至少 1 部权威典籍（来自 REQUIRED_CITATIONS）
        - 不得引用不存在的典籍（不在 REQUIRED_CITATIONS 且不在 rag_context 中提及）

        Args:
            citations: 从解读文本中提取的古籍名列表

        Returns:
            dict: {'valid': bool, 'warnings': list[str], 'missing_required': list[str]}
        """
        warnings: List[str] = []
        missing_required = []

        # 检查是否有权威典籍引用
        found_authoritative = [c for c in citations if c in REQUIRED_CITATIONS]
        if not found_authoritative:
            missing_required = REQUIRED_CITATIONS[:3]  # 提示缺少前3部
            warnings.append('未引用任何权威典籍，建议引用《子平真诠》《滴天髓》等')

        # 检查是否有疑似编造的典籍（不在权威列表中且 rag_context 中未出现）
        rag_sources = {r['source'] for r in self._get_rag_sources()}
        all_known = set(REQUIRED_CITATIONS) | rag_sources
        suspicious = [c for c in citations if c not in all_known]
        if suspicious:
            warnings.append(f'可能存在未核实典籍引用：{", ".join(suspicious[:3])}')

        return {
            'valid': len(found_authoritative) >= 1 and len(suspicious) == 0,
            'warnings': warnings,
            'missing_required': missing_required,
            'found_citations': citations,
        }

    def _get_rag_sources(self) -> List[Dict]:
        """获取 RAG 检索来源（从 rag_context 中提取）。"""
        if not self.rag_context:
            return []
        sources = re.findall(r'《([^《》]+)》', self.rag_context)
        return [{'source': s} for s in set(sources)]


# ---------------------------------------------------------------- 主入口

def generate_interpretation(
    chart_data: Dict[str, Any],
    pan_type: str = 'bazi',
    rag_results: List[Dict] = None,
    client: AgnesClient = None,
) -> Dict[str, Any]:
    """AI 解读主入口（确定性计算 + AI 解读分离架构）。

    流程：
    1. 构建三段式提示词（含 RAG 上下文）
    2. 调用 AI API
    3. 解析为结构化三段式
    4. 强制校验古籍出处引用
    5. 附加免责声明

    Args:
        chart_data: 排盘数据（已计算，不含 AI 内容）
        pan_type: 术数类型（bazi / meihua / liuren / xuan_kong）
        rag_results: RAG 检索结果列表（可选）
        client: AgnesClient 实例（可选，默认新建）

    Returns:
        dict: {
            'success': bool,
            'interpretation': {
                'summary': str,   # 格局总评
                'analysis': str,  # 分项分析
                'advice': str,    # 建议与注意事项
                'citations': list[str],
                'citation_valid': bool,
            },
            'disclaimer': str,
            'elapsed_seconds': float,
            'from_cache': bool,
        }
    """
    t_start = time.time()

    # 构建 RAG 上下文
    rag_context = ''
    if rag_results:
        lines = ['【命理古籍参考】以下为相关古籍原文摘录，请在分析中引用并标注出处：']
        for item in rag_results[:5]:
            source = item.get('source', '古籍')
            score = item.get('score', 0)
            text = item.get('text', '')
            lines.append(f"——《{source}》（相关度≈{score:.2f}）——")
            lines.append(text)
        rag_context = '\n'.join(lines) + '\n\n'

    # 构建三段式提示词
    prompt = _build_three_part_prompt(chart_data, pan_type, rag_context)

    # 调用 AI（带缓存）
    from core.ai_cache import get_cached_result, save_to_cache
    cached = get_cached_result(pan_type, chart_data, question=None)
    if cached is not None:
        return {
            'success': True,
            'interpretation': cached,
            'disclaimer': DISCLAIMER,
            'elapsed_seconds': 0.0,
            'from_cache': True,
        }

    if client is None:
        client = AgnesClient()

    raw_response = client.chat_completion(prompt)
    elapsed = time.time() - t_start

    # 解析三段式
    parser = ThreePartInterpretation(rag_context=rag_context)
    parsed = parser.parse(raw_response)

    # 强制校验古籍出处
    citation_check = parser.validate_citations(parsed['citations'])
    parsed['citation_valid'] = citation_check['valid']
    if citation_check['warnings']:
        parsed['citation_warnings'] = citation_check['warnings']

    # 强制追加免责声明
    if not parsed.get('has_disclaimer'):
        parsed['advice'] += DISCLAIMER

    # 保存缓存
    save_to_cache(pan_type, chart_data, parsed, question=None)

    return {
        'success': True,
        'interpretation': parsed,
        'disclaimer': DISCLAIMER,
        'elapsed_seconds': round(elapsed, 2),
        'from_cache': False,
    }


# ---------------------------------------------------------------- 提示词构建

def _build_three_part_prompt(
    chart_data: Dict[str, Any],
    pan_type: str,
    rag_context: str,
) -> str:
    """构建三段式解读提示词。

    Args:
        chart_data: 排盘数据
        pan_type: 术数类型
        rag_context: RAG 古籍上下文

    Returns:
        str: 完整提示词
    """
    pan_name = {'bazi': '八字', 'meihua': '梅花易数', 'liuren': '大六壬',
                'xuan_kong': '玄空飞星'}.get(pan_type, pan_type)

    return f"""你是一位精通传统命理学的资深分析师。请根据以下{pan_name}排盘数据，
按照以下**三段式结构**生成详细解读：

## 第一段：格局总评
概括命局整体格局（身强/身弱、用神/忌神、格局高低），结合五行旺衰给出总体评价。
要求：用大白话讲清楚「这是什么命」，不超过200字。

## 第二段：分项分析
从事业财运、婚姻感情、健康状况、人际关系四个维度逐一分析。
每个维度按「盘面情况 → 吉凶趋势 → 原因分析」展开。
要求：每条结论必须有排盘依据，不得编造；引用古籍时注明出处（如《子平真诠》）。
每个维度不超过150字。

## 第三段：建议与注意事项
给出具体可行的生活建议（工作/投资/健康/社交），并标注哪些属于民俗说法。
涉及重大事项时提醒咨询专业人士。末尾必须附上免责声明。
要求：建议要具体可操作，避免「宜守成勿妄动」等空泛套话。

排盘数据：
{json.dumps(chart_data, ensure_ascii=False, indent=2)}

{rag_context}

输出要求：
1. 严格按上述三段结构输出，每段用明确标题区分
2. 禁止编造不存在的古籍依据
3. 明确区分「学理定论」与「民俗说法」
4. 末尾必须包含免责声明
"""


if __name__ == '__main__':
    # 快速自检
    sample_chart = {
        'year': '己卯', 'month': '丙子', 'day': '戊午', 'hour': '戊午',
        'rizhu': '戊', 'day_master': '戊土',
        'wuxing': {'土': 3, '火': 2, '水': 1, '金': 0, '木': 0},
    }
    print("=== 自检：ThreePartInterpretation ===")
    parser = ThreePartInterpretation()
    sample_text = """【格局总评】
戊土生于子月，水旺土囚，身弱需火生扶。

【分项分析】
事业财运：戊土身弱，宜从事火土相关行业。

【建议与注意事项】
建议多穿红色衣物，方位宜朝南。此为民俗说法。

免责声明：仅供文化研究参考，不构成决策依据。"""
    result = parser.parse(sample_text)
    print(f"summary长度: {len(result['summary'])}")
    print(f"analysis长度: {len(result['analysis'])}")
    print(f"advice长度: {len(result['advice'])}")
    print(f"citations: {result['citations']}")
    print(f"has_disclaimer: {result['has_disclaimer']}")
    check = parser.validate_citations(result['citations'])
    print(f"citation_valid: {check['valid']}")
    print(f"warnings: {check['warnings']}")
    print("自检完成。")
