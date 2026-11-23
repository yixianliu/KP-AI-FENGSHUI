import json
import logging
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)

# 板块类型 → RAG 知识库 category 映射
_RAG_CATEGORY_MAP = {
    'bazi': 'bazi',
    'meihua': 'meihua',
    'xuan_kong': 'xuan_kong',
}
# 最多从 RAG 检索几条知识作为参考
_RAG_TOP_K = 3

# 提示词指纹缓存：提示词模板在运行期不变，按板块计算一次即可
_PROMPT_FINGERPRINT_CACHE: dict = {}


def _prompt_fingerprint(pan_type: str) -> str:
    """计算指定板块提示词（人设 + 写作规范 + JSON schema）的版本指纹。

    提示词一改指纹即变，配合 `_cache_namespace` 让旧缓存自动失效，
    无需人工维护版本号或做数据库迁移。
    """
    if pan_type in _PROMPT_FINGERPRINT_CACHE:
        return _PROMPT_FINGERPRINT_CACHE[pan_type]
    import hashlib
    payload = (
        _MASTER_PERSONA
        + _WRITING_RULES
        + _SYSTEM_EXPERT.get(pan_type, '')
        + json.dumps(_JSON_SCHEMAS.get(pan_type, {}), ensure_ascii=False, sort_keys=True)
    )
    fp = hashlib.sha256(payload.encode('utf-8')).hexdigest()[:8]
    _PROMPT_FINGERPRINT_CACHE[pan_type] = fp
    return fp


def _cache_namespace(pan_type: str) -> str:
    """构造缓存版本命名空间：板块 + 当前模型 + 提示词指纹。

    换模型或改提示词后，同一份排盘数据会得到不同的缓存键，避免继续吃旧结论。
    读取模型失败时降级为空模型名（仍保留提示词指纹）。
    """
    model = ''
    try:
        from core.ai_config import get_config_manager
        profile = get_config_manager().get_active()
        if profile is not None:
            model = f'{getattr(profile, "model", "")}@{getattr(profile, "api_url", "")}'
    except Exception:
        pass
    return f'{pan_type}|model={model}|prompt={_prompt_fingerprint(pan_type)}'

"""
各分析类型要求模型返回的 JSON 字段（必须与下方 _parse_ai_response 的
required_fields 完全对应，否则解析端会补默认值导致界面字段缺失）
"""
_JSON_SCHEMAS = {
    'bazi': {
        'final_verdict': '整体格局与日主强弱的综合判断：必须结合日主强弱、五行旺衰、十神格局、大运走势、流年影响给出全面的总体定论。包括：格局定性（如从强格、从弱格、调候格等）、吉凶趋势分析、关键建议（趋吉避凶的具体措施）。内容必须详实、结合具体干支与十神、避免任何套话，不少于500字。',
        'key_points': '重点提示：必须提炼 5-7 条最关键、最值得命主注意的结论。每条必须包含：具体事件或时间点、吉凶性质、应对建议。例如：\"\n1. 2025年甲辰流年，冲动之年，需谨慎决策，避免投资失利；\n2. 丁巳大运（35-45岁），官星得地，事业有为，宜把握机遇；\n3. 婚姻宫逢桃花，异性缘佳，但需防范艳事；\"\n每条为独立段落，用于高亮标注。',
        'personality': '性格特征分析：必须结合日主、十神组合、五行偏枯、神煞影响，刻画具体性格优缺点。包括：核心性格特点、思维方式、情感表达、人际交往方式、优势所在、潜在不足、发展建议。内容必须具体、有深度、避免笼统描述，不少于300字。',
        'career': '事业与财运分析及建议：必须结合官杀/财星/印星与喜用神、十神格局、大运流年。包括：行业取向指导、适合职业类型、发展节奏分析、财富来源、投资方向、风险提示、具体行动建议。内容必须实用、具体、可操作，不少于400字。',
        'relationships': '感情与婚姻分析及建议：必须结合配偶星、桃花星、红鸾天喜、日支坐下、大运流年。包括：婚姻时机判断、婚姻质量分析、桃花运势、感情发展趋势、相处之道、婚姻经营建议、需规避的不利因素。内容必须细腻、具体、有参考价值，不少于350字。',
        'health': '健康分析及建议：必须结合五行偏枯、刑冲合化、神煞影响、六气运行。包括：弱脏腑系统、常见健康问题、季节性防护、生活调养建议、运动推荐、饮食调理、需警惕的危险信号（如出现持续不适应及时就医，命理内容仅作养生参考，非医疗诊断）。内容必须专业、实用、不少于300字。',
        'four_pillars_detail': '四柱天干地支的逐项解释：必须逐柱说明天干地支组合、纳音五行、十神含义、旺衰喜忌、所代表的亲属信息、体现的生活领域、吉凶细节。每柱不少于100字，总计不少于400字。',
        'annual_fortune': '近期流年提示：结合排盘数据中的流年（当年及未来一两年天干地支）与命局的生克关系，用大白话讲清近期生活节奏。包括：这一两年整体顺不顺、事业/财运/感情各方面大概什么状态、哪些月份或时段适合推进大事、哪些时段宜稳守。每条一个方面，像提醒朋友一样具体，不要空泛。4-6 条。',
        'study_exam': '学业与考试运：结合印星（代表学习、文书、贵人提携）、文昌等信息，分析读书考试、考证进修、技能学习方面的状态。包括：适合怎样的学习方式、考试发挥如何、进修深造是否有利。内容用学生和家长都看得懂的大白话，不少于200字；若排盘数据中无相关信息，说明「盘上此象不明显」并给通用勉励建议。',
        'folklore_tips': '民俗开运小建议：给出 3-5 条日常生活里图吉利的民俗做法（如适合的颜色、方位、作息、心态调整），每条都必须明确标注「民俗说法，图个吉利，不必迷信」，且不得承诺效果。',
        'scenario_advice': '针对用户提问场景（事业、婚姻、健康、财富、学习等）的逐项具体建议：必须根据用户具体问题，提供有针对性的分析和建议。包括：当前形势分析、有利时机、不利因素、具体行动步骤、预期效果、风险提示。内容必须紧扣主题、实用具体，不少于300字。',
        'historical_cases': '历史案例或统计参考：必须提供 2-3 个真实历史案例或统计数据，含概率/比例信息，佐证上述判断。每个案例需包括：基本情况、命理特征、事件经过、结果验证。内容必须真实可信、有说服力，不少于200字。',
        'probability_stats': '概率/置信度统计：必须用「维度名称：百分比数值%」格式逐条给出（如「事业财运：85%」「感情婚姻：75%」「健康状况：80%」「整体吉凶：80%」「财富运势：70%）），每条独立、直观对比各维度强弱，便于可视化展示。百分比为基于命理数据的相对估算，必须客观合理。',
        'disclaimer': '免责声明：必须说明命理分析仅供文化研究参考，不构成任何决策或医疗依据，建议用户在重要事务中咨询相关专业人士。',
    },
    'meihua': {
        'final_verdict': '总体断语：必须综合本卦/互卦/变卦、体用生克、动爻与应期、时令节气，给出全面的总体判断（格局定性、吉凶趋势、关键时机、核心建议）。内容详实、结合具体卦象、避免套话，不少于500字。',
        'key_points': '重点提示：必须提炼 5-7 条最关键、最值得问者注意的结论。每条必须包含：具体时间点或事件、吉凶性质、应对建议。例如：\"\n1. 动爻在上九，事情的变化多半由对方或外部引起，自己宜静观其变；\n2. 用卦生体卦（如金生水），眼下有外力相助，开口求人多半有回应；\n3. 变卦为艮，艮主山、主止，往后一段事态会慢慢稳下来，宜收心守成；\"\n每条为独立短句，用于高亮标注。',
        'analysis': '卦象分析：必须结合卦名、卦辞、上下卦与体用关系、纳音五行，给出整体吉凶与事态趋势的深度解析。包括：本卦意义、互卦作用、变卦趋势、动爻影响、体用关系。内容必须专业、深入、不少于300字。',
        'hexagram_interpretations': '每条爻辞的解释与吉凶：必须结合动爻与变卦，逐项说明各爻含义、得失吉凶、对所占之事的具体影响、建议措施。每爻不少于80字，总计不少于300字。',
        'timing': '应期（事情应验的时间）分析：结合动爻位置（初爻主近、上爻主远）、体用生克与卦气旺衰，用大白话推断事情大概什么时候见分晓——快则几天、慢则数月，给出时间窗口并说明依据；同时指出哪个时间段适合主动推进、哪个时间段宜等待。不少于200字。',
        'folklore_tips': '民俗开运小建议：给出 3-5 条问卦后日常图吉利的民俗做法（如适合的颜色、方位、心态调整），每条都必须明确标注「民俗说法，图个吉利，不必迷信」，且不得承诺效果。',
        'scenario_advice': '针对用户提问场景（事业、婚姻、健康等）的具体建议：必须结合本互变卦走势、体用生克、动爻与卦气旺衰，给出 3-5 条具体、可执行的行动指引。每条必须包括：应该做什么、避免什么、最佳时机、预期效果。内容必须独立成段，避免笼统套话。',
        'historical_cases': '历史案例或统计参考：必须提供 1-2 个历史案例（可引《梅花易数》中邵雍观梅占、牡丹占等经典占例的思路类比），含概率/比例信息，佐证卦象判断。内容必须真实可信、有参考价值，不少于150字。',
        'probability_stats': '针对所占之事的吉凶概率或置信度统计：必须给出相对比例，并说明判断依据。',
        'advice': '行动建议：必须结合体用生克、本互变卦走势与时令节气，给出 3-5 条具体、可执行的行动指引；每条必须以「【高】」「【中】」「【低】」开头标注优先级，接着明确写清「应该做什么」「避免什么」「最佳时机」「预期效果」，每条独立成段，避免笼统套话。',
        'disclaimer': '免责声明：必须说明卦象分析仅供参考、不构成决策依据，建议用户结合实际情况谨慎判断。',
    }
}


# ---------------------------------------------------------------------------
# 「文化研究算法」人设与写作规范（八字 / 梅花共用）
# 目标：让 AI 输出既有传统命理依据，又通俗易懂、贴近生活、守住合规红线
# ---------------------------------------------------------------------------
_MASTER_PERSONA = (
    "你是「文化研究算法」，一位在龙虎山修习传统术数多年的师傅，"
    "精通子平八字、梅花易数。你为人随和实在，批断像茶馆里跟街坊聊天，"
    "不端架子、不掉书袋；既守古法规矩，又懂现代人的生活难处。"
)

# 各板块共用的写作红线与风格要求
_WRITING_RULES = """写作要求（务必逐条遵守）：
1. 说人话：专业术语（如「十神」「用神」「体用」「空亡」等）第一次出现时，必须用括号或大白话顺带解释，让完全没接触过命理的人也能看懂。
2. 贴生活：每条结论都要落到真实生活场景——求职上班、跳槽创业、生意求财、恋爱婚姻、考试学习、家人健康、同事朋友相处，给出像老朋友支招一样具体的建议；不要写「宜守成、勿妄动」这类放之四海皆准的空泛套话。
3. 有依据：所有判断必须严格基于给定的排盘数据（四柱干支、五行十神 / 本互变卦、体用动爻），数据里没有的信息不得编造；引用古籍说法时注明出处（如《子平真诠》《滴天髓》《梅花易数》），盘上信息不明显处要明说「这一点盘上看不分明」，禁止无据妄断。
4. 三段式：每个分析字段内部尽量按「是什么（盘面情况，白话讲清）→ 怎么看（吉凶趋势与原因）→ 怎么办（生活里具体怎么应对）」展开。
5. 守分寸：不得承诺具体结果（禁说「必发财」「一定离婚」「准能考上」），不得恐吓（禁说「大难临头」「在劫难逃」）；概率高低用「可能性偏大 / 偏小」这类措辞；凡涉及健康、法律、投资等重大事项，必须提醒用户去咨询医生、律师、理财顾问等专业人士。
6. 分民俗：开运颜色、吉祥方位、吉利数字等内容属于民俗文化，涉及到时要明确标注「这是民俗说法，图个吉利」，不得说成必然有效。
7. disclaimer 字段必须表达「仅供传统文化研究参考，不构成任何决策依据」的意思。"""

# 各板块人设后缀（术数方向不同）
_SYSTEM_EXPERT = {
    'bazi': (
        "你尤其精通子平八字：年柱以立春为界、月柱五虎遁、时柱五鼠遁，"
        "论命以日主为核心，看五行旺衰、十神格局、调候用神、大运流年。"
    ),
    'meihua': (
        "你尤其精通梅花易数：以不动之卦为体、动爻之卦为用，看体用生克定吉凶，"
        "参本卦（事之始）、互卦（事之中）、变卦（事之终）与动爻爻辞断事。"
    ),
}


def _smart_fix_json(content: str) -> Optional[dict]:
    """对可能被截断的 JSON 做智能修复，返回解析后的 dict 或 None。

    策略（优先级从高到低）：
    1. 直接 parse_json_response（完整 JSON）
    2. 提取平衡 JSON 子串（AI 在 JSON 外夹杂解释文字）
    3. 补全截断 JSON：找到最后一个完整键值对，关闭所有未闭合的括号/字符串/数组
    4. 仍失败返回 None，由调用方降级到 fallback
    """
    from api.agnes_client import AgnesClient
    # 1) 标准解析
    parsed = AgnesClient.parse_json_response(content)
    if parsed is not None:
        return parsed

    # 2) 提取平衡子串
    from api.agnes_client import _try_extract_balanced_json
    balanced = _try_extract_balanced_json(content)
    if balanced is not None:
        try:
            return json.loads(balanced)
        except json.JSONDecodeError:
            pass

    # 3) 截断补全：找到 content 中最后一个 "key": "value" 或 "key": [...] 的完整结构
    #    思路：从末尾往前找最后一个完整的 "key": 配对，然后关闭所有未闭合结构
    text = content.strip()
    if not text.startswith('{'):
        return None

    # 统计未闭合的括号/引号
    depth = 0
    in_string = False
    escape = False

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                # 完整 JSON 对象结束，但外层 parse 失败了——尝试去掉尾部垃圾
                if i + 1 <= len(text):
                    try:
                        return json.loads(text[:i + 1])
                    except json.JSONDecodeError:
                        pass
                return None

    # 未闭合，尝试补全：截断到最后一个完整的 "key": "value" 或 "key": [...]
    # 从末尾删除未完成的字符串/数组/对象
    fixed = text.rstrip()
    # 去掉末尾的逗号、未闭合的引号
    fixed = re.sub(r',\s*$', '', fixed)

    # 检测末尾是否处于“未闭合字符串”内部（AI 常在长字段值中间被截断，
    # 例如 final_verdict 的整段白话还未写完就断了）。此时最后一个 '"' 是
    # 该字符串的“开引号”，其后直到末尾都是残缺值，必须整体丢弃，否则补全
    # 括号后 json.loads 仍会因畸形字符串失败。
    # 用转义感知的扫描统计引号，判断最后一个 '"' 是否成对。
    in_str = False
    escaped = False
    last_open_quote = -1
    for i, ch in enumerate(fixed):
        if in_str:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
                last_open_quote = i
    if in_str and last_open_quote > 0:
        # 找到该未闭合字符串值对应的 "key": " 前缀，一并丢弃（保证剩余部分仍是合法 JSON 前缀）
        key_close = fixed.rfind('"', 0, last_open_quote)
        if key_close > 0:
            # key 闭引号之前是 key 开引号；截断到 key 开引号之前，
            # 彻底丢弃这个未写完的键值对（保留前一个完整键值对的结尾）。
            key_open = fixed.rfind('"', 0, key_close)
            fixed = fixed[:key_open] if key_open > 0 else '{'
        else:
            fixed = fixed[:last_open_quote]
        # 去掉可能的残留逗号
        fixed = re.sub(r',\s*$', '', fixed)
    else:
        # 传统处理：末尾是未闭合引号（截断恰好落在字符串收尾处）
        if fixed.endswith('"') and fixed.count('"') % 2 == 1:
            last_quote = fixed.rfind('"')
            fixed = fixed[:last_quote]

    # 补齐闭合括号
    open_braces = fixed.count('{') - fixed.count('}')
    open_brackets = fixed.count('[') - fixed.count(']')
    if open_braces > 0 or open_brackets > 0:
        # 关闭数组和对象
        suffix = ']' * open_brackets + '}' * open_braces
        fixed = fixed + suffix
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    return None


def _system_prompt(pan_type: str) -> str:
    """组装指定板块的 system 提示词（大师兄人设 + 术数专长 + 写作规范）。"""
    expert = _SYSTEM_EXPERT.get(pan_type, '')
    return f"{_MASTER_PERSONA}{expert}\n\n{_WRITING_RULES}"


def _user_prompt(pan_type: str, chart_data: dict) -> str:
    """组装 user 提示词：排盘数据 + JSON schema + 输出与风格要求 + RAG古籍参考。"""
    from .rag_knowledge import get_knowledge_base
    schema = _JSON_SCHEMAS.get(pan_type, {})
    pan_name = {'bazi': '八字', 'meihua': '梅花易数'}.get(pan_type, pan_type)

    # RAG 检索：从排盘关键特征提取查询词，获取古籍参考
    rag_context = ''
    try:
        kb = get_knowledge_base()
        category = _RAG_CATEGORY_MAP.get(pan_type, 'all')
        # 提取排盘关键字段作为查询
        query_parts = []
        if 'day_master' in str(chart_data):
            query_parts.append('日干')
        if 'wuxing' in str(chart_data):
            query_parts.append('五行旺衰')
        if 'shishen' in str(chart_data):
            query_parts.append('十神格局')
        if 'sui_xiang' in str(chart_data):
            query_parts.append('玄空飞星 山星向星')
        if 'hexagram' in str(chart_data):
            query_parts.append('体用生克')
        query = ' '.join(query_parts) if query_parts else pan_type
        results = kb.search(query, category=category, top_k=_RAG_TOP_K)
        if results:
            rag_lines = ['【命理古籍参考】以下为相关古籍原文摘录，请在分析中引用并标注出处：']
            for chunk, score in results:
                rag_lines.append(f"——《{chunk.source}》（相关度≈{score:.2f}）——")
                rag_lines.append(chunk.content)
            rag_context = '\n'.join(rag_lines) + '\n\n'
    except Exception as e:
        logger.warning(f"[RAG] 检索失败，跳过古籍参考: {e}")

    return f"""请根据以下{pan_name}排盘数据，为问命者做一份详细批断。
{rag_context}
{pan_name}排盘数据：
{json.dumps(chart_data, ensure_ascii=False, indent=2)}

请严格按照以下 JSON 字段要求生成分析结果（字段名保持英文，内容用中文）：
{json.dumps(schema, ensure_ascii=False, indent=2)}

输出要求：
1. 只返回一个有效的 JSON 对象，不要 markdown 代码块标记、不要任何额外解释文字。
2. 每个字段内容必须符合上面的描述与字数要求；probability_stats 为字符串数组，每条形如「事业财运：82%」。
3. 所有判断必须来自排盘数据本身，排盘里没有的信息不得编造，杜绝千篇一律的套话。
4. 语言风格按大师兄的规矩来：大白话、贴生活、术语随文解释、吉凶留余地、重大事项提示咨询专业人士。
5. 引用古籍原文时必须注明出处（如《子平真诠》《滴天髓》等），禁止编造不存在的典籍依据。"""


class AnalysisStorage:
    """确保分析缓存表就绪的存储类"""
    def __init__(self):
        # 确保AI缓存表存在
        from ..ai_cache import ensure_cache_table
        ensure_cache_table()


def _check_bazi_cache(input_data: dict) -> Optional[dict]:
    """检查八字分析缓存，如果存在则返回缓存结果。
    
    Args:
        input_data: 输入数据（年月日时等）
        
    Returns:
        如果存在缓存则返回缓存结果字典，否则返回None
    """
    from ..ai_cache import get_cached_result
    question = None
    return get_cached_result('bazi', input_data, question,
                             namespace=_cache_namespace('bazi'))


def _calculate_bazi_chart_data(input_data: dict) -> dict:
    """从输入数据计算八字排盘数据。
    
    Args:
        input_data: 输入数据（年月日时等）
        
    Returns:
        计算得到的八字排盘数据字典
        
    Raises:
        Exception: 如果计算过程中发生任何错误
    """
    from core.bazi.bazi_calculator import BaziCalculator
    calculator = BaziCalculator()
    return calculator.calculate(
        year=input_data.get('year'),
        month=input_data.get('month'),
        day=input_data.get('day'),
        hour=input_data.get('hour'),
        minute=input_data.get('minute', 0),
        longitude=input_data.get('longitude', 120.0),
        is_lunar=input_data.get('is_lunar', False)
    )


def _check_bazi_ai_config() -> Optional[dict]:
    """检查AI配置，如果未配置则返回降级分析结果。
    
    Returns:
        如果AI未配置则返回降级分析结果字典，否则返回None
    """
    try:
        from core.ai_config import get_config_manager
        if get_config_manager().get_active() is None:
            logger.warning("AI未配置，八字分析降级为本地规则兜底")
            from .analysis_fallback import generate_fallback_analysis
            # 注意：这里需要chart_data参数，但我们无法获取到
            # 这个函数只能在有chart_data的情况下被调用
            return {'needs_fallback': True}
    except Exception:
        pass
    return None


def _invoke_bazi_ai_analysis(chart_data: dict) -> dict:
    """调用AI进行八字分析并处理响应。
    
    Args:
        chart_data: 八字排盘数据
        
    Returns:
        包含AI分析结果的字典
        
    Raises:
        Exception: 如果AI调用过程中发生任何错误
    """
    from api.agnes_client import get_agnes_client
    agnes_client = get_agnes_client()

    # 构建提示词（大师兄人设 + 排盘数据 + JSON schema）
    prompt = _user_prompt('bazi', chart_data)

    # 调用AI
    response = agnes_client.chat_completion([
        {"role": "system", "content": _system_prompt('bazi')},
        {"role": "user", "content": prompt}
    ])

    # 解析AI返回的JSON内容
    content = response.get('content', '')
    ai_analysis = agnes_client.parse_json_response(content)

    # 如果解析失败，尝试提取JSON部分
    if ai_analysis is None:
        # 尝试从内容中提取JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                ai_analysis = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                ai_analysis = None

    # 如果仍然失败，改用本地命理规则引擎生成白话兜底分析（而非占位符）
    fallback_used = False
    if ai_analysis is None:
        # 二次尝试：使用 _smart_fix_json 修复可能的截断 JSON
        try:
            fixed = _smart_fix_json(content)
            if fixed is not None:
                ai_analysis = fixed
        except Exception:
            pass
        if ai_analysis is None:
            logger.warning(f"AI分析返回非JSON内容: {content[:200]}...，改用本地规则兜底")
            from .analysis_fallback import generate_fallback_analysis
            ai_analysis = generate_fallback_analysis('bazi', chart_data or {})
            fallback_used = True

    # 获取token使用量
    token_usage = response.get('usage', {})

    return {
        'success': True,
        'from_cache': False,
        'token_usage': token_usage,
        'ai_analysis': ai_analysis,
        'from_fallback': fallback_used,
    }


def _handle_bazi_ai_exception(e: Exception, chart_data: dict) -> dict:
    """处理八字AI调用异常，生成降级分析结果。
    
    Args:
        e: 发生的异常
        chart_data: 八字排盘数据
        
    Returns:
        包含降级分析结果的字典
    """
    # AI调用失败，使用本地命理规则生成有意义的分析结果
    # 区分不同错误类型，给出准确的日志和降级行为
    try:
        from api.agnes_client import AgnesResponseError, AgnesTimeoutError, AgnesRequestError, AgnesQuotaError
        if isinstance(e, AgnesQuotaError):
            logger.error(f"AI分析[bazi] 配额用尽（{e}），已降级为本地兜底")
        elif isinstance(e, AgnesTimeoutError):
            logger.error(f"AI分析[bazi] 请求超时（{e}），已降级为本地兜底")
        elif isinstance(e, AgnesResponseError):
            logger.error(f"AI分析[bazi] 响应异常（{e}），已降级为本地兜底")
        elif isinstance(e, AgnesRequestError):
            logger.error(f"AI分析[bazi] 请求失败（{e}），已降级为本地兜底")
        else:
            logger.error(f"AI分析[bazi] 调用失败（{e}），已降级为本地兜底",
                         exc_info=True)
    except ImportError:
        logger.error(f"AI分析[bazi] 调用失败（{e}），已降级为本地兜底",
                     exc_info=True)
    from .analysis_fallback import generate_fallback_analysis
    dummy_analysis = generate_fallback_analysis('bazi', chart_data or {})

    return {
        'success': True,
        'from_cache': False,
        'token_usage': 0,
        'ai_analysis': dummy_analysis,
        'ai_error': str(e),
    }


def run_bazi_analysis(input_data: dict, chart_data: dict = None, task_id: str = None,
                      force_refresh: bool = False):
    """
    执行八字AI分析
    :param input_data: 输入数据（年月日时等）
    :param chart_data: 预计算的八字排盘数据，如果为None则从input_data计算
    :param task_id: 任务ID（用于日志，当前未使用）
    :param force_refresh: True 时跳过缓存读取强制重新分析（成功结果仍写缓存）
    :return: 分析结果字典
    """
    t_start = time.time()
    # 确保缓存表就绪
    AnalysisStorage()
    from ..ai_cache import save_to_cache

    # 使用input_data和固定的question=None作为缓存键
    # 注意：实际应用中，question可能来自用户输入，但在此上下文中我们假设为None
    question = None

    namespace = _cache_namespace('bazi')

    # 1. 检查缓存（force_refresh=True 时跳过，供「重新分析」入口使用）
    cached_result = None if force_refresh else _check_bazi_cache(input_data)
    if cached_result is not None:
        return {
            'success': True,
            'from_cache': True,
            'token_usage': 0,
            'ai_analysis': cached_result,
            'elapsed_seconds': round(time.time() - t_start, 2),
        }

    # 2. 计算排盘数据（如果需要）
    if chart_data is None:
        try:
            chart_data = _calculate_bazi_chart_data(input_data)
        except Exception as e:
            error_result = {
                'success': False,
                'error_type': 'calculation_error',
                'error_message': f'计算八字排盘失败: {e}',
                'ai_analysis': {},
                'elapsed_seconds': round(time.time() - t_start, 2),
            }
            # 错误结果不缓存
            return error_result

    # 3. 检查AI配置
    ai_config_result = _check_bazi_ai_config()
    if ai_config_result is not None and ai_config_result.get('needs_fallback'):
        from .analysis_fallback import generate_fallback_analysis
        dummy_analysis = generate_fallback_analysis('bazi', chart_data or {})
        # 未配置 AI 属于降级结果，不入缓存（否则配置好模型后仍会吃到这份兜底）
        elapsed = round(time.time() - t_start, 2)
        return {
            'success': True,
            'from_cache': False,
            'token_usage': 0,
            'ai_analysis': dummy_analysis,
            'ai_error': 'AI模型未配置，已使用本地规则兜底',
            'elapsed_seconds': elapsed,
        }

    # 4. 调用AI分析
    try:
        ai_result = _invoke_bazi_ai_analysis(chart_data)
        
        # 5. 保存到缓存并返回结果（仅缓存真正的 AI 结果，JSON 解析失败后的兜底不缓存）
        if not ai_result.get('from_fallback'):
            save_to_cache('bazi', input_data, question, ai_result['ai_analysis'],
                          namespace=namespace)
        elapsed = round(time.time() - t_start, 2)
        ai_result['elapsed_seconds'] = elapsed
        return ai_result
        
    except Exception as e:
        # 6. 处理异常（异常降级结果不写缓存，避免一次网络抖动把兜底永久固化）
        error_result = _handle_bazi_ai_exception(e, chart_data)
        elapsed = round(time.time() - t_start, 2)
        error_result['elapsed_seconds'] = elapsed
        return error_result


def run_meihua_analysis(input_data: dict, chart_data: dict = None, task_id: str = None,
                        force_refresh: bool = False):
    """
    执行梅花AI分析
    :param input_data: 输入数据
    :param chart_data: 预计算的梅花排盘数据，如果为None则尝试从input_data计算
    :param task_id: 任务ID（用于日志，当前未使用）
    :param force_refresh: True 时跳过缓存读取强制重新分析（成功结果仍写缓存）
    :return: 分析结果字典
    """
    t_start = time.time()
    # 确保缓存表就绪
    AnalysisStorage()
    from ..ai_cache import get_cached_result, save_to_cache

    # 使用input_data和固定的question=None作为缓存键
    question = None
    namespace = _cache_namespace('meihua')
    cached = None if force_refresh else get_cached_result(
        'meihua', input_data, question, namespace=namespace)
    if cached is not None:
        return {
            'success': True,
            'from_cache': True,
            'token_usage': 0,
            'ai_analysis': cached,
            'elapsed_seconds': round(time.time() - t_start, 2),
        }

    # 未命中缓存，需要计算
    # 如果未提供chart_data（None 或空 dict），从 input_data 自动计算排盘数据
    if not chart_data:
        try:
            from core.divination.meihua import MeiHuaCalculator
            from core.divination.hexagram_analyzer import HexagramAnalyzer
            calc = MeiHuaCalculator()
            analyzer = HexagramAnalyzer()
            method = input_data.get('method', 'time')
            q = input_data.get('question', '')
            hr = None
            if method == 'time':
                hr = calc.time_divination(
                    input_data.get('year'), input_data.get('month'),
                    input_data.get('day'), input_data.get('hour'), q)
            elif method == 'number':
                numbers = input_data.get('numbers') or [input_data.get('num1'), input_data.get('num2')]
                hr = calc.number_divination(numbers, q)
            elif method == 'direction':
                hr = calc.direction_divination(input_data.get('direction', ''), q,
                                               input_data.get('hour'))
            elif method == 'text':
                hr = calc.text_divination(input_data.get('text', ''), q)
            elif method == 'copper_coin':
                hr = calc.copper_coin_divination(input_data.get('six_lines', []), q)
            elif method == 'stroke':
                hr = calc.stroke_divination(input_data.get('char', ''), q,
                                            input_data.get('stroke_count'))
            if hr:
                all_hex = calc.generate_all_hexagrams(hr)
                analysis = analyzer.analyze_divination(hr, all_hex)
                base_raw = analysis.get('base', {})
                hu_raw = analysis.get('hu', {})
                bian_raw = analysis.get('bian', {})
                def _enrich(raw):
                    if not raw:
                        return {}
                    e = raw.copy()
                    un, ln = raw.get('upper_num'), raw.get('lower_num')
                    bg = analyzer.bagua
                    e['symbol'] = (bg.get(un, {}).get('symbol', '') +
                                   bg.get(ln, {}).get('symbol', ''))
                    e['explanation'] = raw.get('description', '')
                    e['upper_gua'] = bg.get(un, {}).get('name', '')
                    e['lower_gua'] = bg.get(ln, {}).get('name', '')
                    return e
                chart_data = {
                    'base': _enrich(base_raw),
                    'hu': _enrich(hu_raw),
                    'bian': _enrich(bian_raw),
                    'overall_judgment': analysis.get('overall_judgment', '平'),
                }
                # 动爻信息
                cy = base_raw.get('changing_yao', 0)
                yao_ci = base_raw.get('yao_ci', [])
                for idx, yao in enumerate(yao_ci, start=1):
                    if idx == cy:
                        chart_data['base']['changing_yao'] = idx
                        chart_data['base']['changing_yao_name'] = yao.get('yao', '')
                        chart_data['base']['changing_yao_text'] = yao.get('text', '')
                        chart_data['base']['changing_yao_meaning'] = yao.get('meaning', '')
                        break
                logger.info(f"[AI][meihua] chart_data 为空，已从 input_data 自动计算排盘（method={method}）")
            else:
                raise ValueError("起卦返回空结果")
        except Exception as e:
            logger.error(f"[AI][meihua] 自动排盘失败: {e}", exc_info=True)
            error_result = {
                'success': False,
                'error_type': 'calculation_error',
                'error_message': f'梅花排盘自动计算失败: {e}',
                'ai_analysis': {},
                'elapsed_seconds': round(time.time() - t_start, 2),
            }
            return error_result

    # 检查 AI 是否已配置，未配置则直接降级为本地兜底分析
    try:
        from core.ai_config import get_config_manager
        if get_config_manager().get_active() is None:
            logger.warning("AI未配置，梅花分析降级为本地规则兜底")
            from .analysis_fallback import generate_fallback_analysis
            dummy_analysis = generate_fallback_analysis('meihua', chart_data or {})
            # 未配置 AI 的降级结果不入缓存，避免配好模型后仍吃到兜底
            elapsed = round(time.time() - t_start, 2)
            return {
                'success': True,
                'from_cache': False,
                'token_usage': 0,
                'ai_analysis': dummy_analysis,
                'ai_error': 'AI模型未配置，已使用本地规则兜底',
                'elapsed_seconds': elapsed,
            }
    except Exception:
        pass

    # 生成AI分析结果
    try:
        from api.agnes_client import get_agnes_client
        agnes_client = get_agnes_client()

        # 构建提示词（大师兄人设 + 起卦数据 + JSON schema）
        prompt = _user_prompt('meihua', chart_data)

        # 调用AI
        response = agnes_client.chat_completion([
            {"role": "system", "content": _system_prompt('meihua')},
            {"role": "user", "content": prompt}
        ])

        # 解析AI返回的JSON内容
        content = response.get('content', '')
        ai_analysis = agnes_client.parse_json_response(content)

        # 如果解析失败，尝试智能补全（处理 max_tokens 截断等场景）
        if ai_analysis is None:
            logger.debug("标准JSON解析失败，尝试智能补全...")
            try:
                ai_analysis = _smart_fix_json(content)
            except Exception:
                ai_analysis = None

        # 如果仍然失败，使用本地命理规则生成有意义的分析结果（而非无意义占位符）
        fallback_used = False
        if ai_analysis is None:
            logger.warning("AI分析返回非JSON内容（已尝试补全仍失败），将使用本地规则生成分析")
            from .analysis_fallback import generate_fallback_analysis
            ai_analysis = generate_fallback_analysis('meihua', chart_data)
            fallback_used = True

        # 获取token使用量
        token_usage = response.get('usage', {})

        # 保存到缓存（只缓存真正的 AI 结果，解析失败后的兜底不缓存）
        if not fallback_used:
            save_to_cache('meihua', input_data, question, ai_analysis,
                          namespace=namespace)

        elapsed = round(time.time() - t_start, 2)
        return {
            'success': True,
            'from_cache': False,
            'token_usage': token_usage,
            'ai_analysis': ai_analysis,
            'elapsed_seconds': elapsed,
        }
    except Exception as e:
        # AI调用失败，使用本地命理规则生成有意义的分析结果
        # 区分不同错误类型，给出准确的日志和降级行为
        try:
            from api.agnes_client import AgnesResponseError, AgnesTimeoutError, AgnesRequestError, AgnesQuotaError
            if isinstance(e, AgnesQuotaError):
                logger.error(f"AI分析[meihua] 配额用尽（{e}），已降级为本地兜底")
            elif isinstance(e, AgnesTimeoutError):
                logger.error(f"AI分析[meihua] 请求超时（{e}），已降级为本地兜底")
            elif isinstance(e, AgnesResponseError):
                logger.error(f"AI分析[meihua] 响应异常（{e}），已降级为本地兜底")
            elif isinstance(e, AgnesRequestError):
                logger.error(f"AI分析[meihua] 请求失败（{e}），已降级为本地兜底")
            else:
                logger.error(f"AI分析[meihua] 调用失败（{e}），已降级为本地兜底",
                             exc_info=True)
        except ImportError:
            logger.error(f"AI分析[meihua] 调用失败（{e}），已降级为本地兜底",
                         exc_info=True)
        from .analysis_fallback import generate_fallback_analysis
        dummy_analysis = generate_fallback_analysis('meihua', chart_data or {})

        # 异常降级结果不入缓存：一次超时/限流不应把兜底结论永久固化
        elapsed = round(time.time() - t_start, 2)
        return {
            'success': True,
            'from_cache': False,
            'token_usage': 0,
            'ai_analysis': dummy_analysis,
            'ai_error': str(e),
            'elapsed_seconds': elapsed,
        }

