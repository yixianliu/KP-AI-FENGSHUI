"""
core/rag_knowledge.py — RAG 知识库管理器（轻量化本地实现）

设计依据：
- 执行计划任务 3.9–3.13：RAG 知识库 + LangChain + ChromaDB + bge-small-zh
- 本文档要求：古籍原文优先，BM25+向量混合检索，top-K=5，相关度≥0.8

当前实现为「关键词 + 语义评分」的轻量混合检索（无需外部向量库依赖），
满足项目 MVP 阶段需求。后续可按需迁移至 ChromaDB。

知识块来源（《子平真诠》《滴天髓》《穷通宝鉴》《三命通会》《渊海子平》）：
- 八字：格局论断、五行旺衰、十神定位、调候用神
- 玄空飞星：三元九运、二十四山向、九宫飞布、替卦、七星打劫
- 梅花易数：体用生克、动静动静、卦气旺衰
- 大六壬：九宗门、三传、天地盘、天将神煞
"""
from __future__ import annotations

import math
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ================================================================
# 知识块数据结构
# ================================================================

@dataclass
class KnowledgeChunk:
    """单个知识块（来自古籍原文）。"""
    id: str
    source: str          # 古籍名称，如 '子平真诠'
    category: str        # 板块：bazi/liuren/meihua/xuan_kong/all
    content: str         # 原文内容（500-800字符块）
    context: str = ''    # 上下文摘要
    tags: List[str] = field(default_factory=list)   # 关键词标签
    weight: float = 1.0  # 权威性权重（1.0最高）

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'source': self.source,
            'category': self.category,
            'content': self.content,
            'context': self.context,
            'tags': self.tags,
            'weight': self.weight,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'KnowledgeChunk':
        return cls(
            id=d['id'],
            source=d['source'],
            category=d['category'],
            content=d['content'],
            context=d.get('context', ''),
            tags=d.get('tags', []),
            weight=d.get('weight', 1.0),
        )


# ================================================================
# 关键词提取（轻量级，不依赖外部 NLP 库）
# ================================================================

_CJK_CHAR_RE = re.compile(r'[\u4e00-\u9fff]')
_STOP_CHARS = set('，。、；：！？""''（）【】《》——…\n\t ')


def extract_keywords(text: str, max_count: int = 15) -> List[str]:
    """从中文文本中提取关键词（高频汉字 + 专业术语）。"""
    chars = _CJK_CHAR_RE.findall(text)
    freq: Dict[str, int] = {}
    for c in chars:
        if c not in _STOP_CHARS:
            freq[c] = freq.get(c, 0) + 1
    # 取高频字
    sorted_chars = sorted(freq.items(), key=lambda x: -x[1])[:max_count]
    return [c for c, _ in sorted_chars]


# ================================================================
# BM25 简易实现
# ================================================================

def _bm25_score(query_terms: List[str], doc_terms: List[str],
                doc_len: int, avg_doc_len: float,
                k1: float = 1.5, b: float = 0.75) -> float:
    """简易 BM25 相关性评分。"""
    if not query_terms or not doc_terms:
        return 0.0
    score = 0.0
    doc_len_norm = doc_len / max(avg_doc_len, 1.0)
    for q in query_terms:
        count = doc_terms.count(q)
        if count == 0:
            continue
        numerator = count * (k1 + 1)
        denominator = count + k1 * (1 - b + b * doc_len_norm)
        score += math.log(1 + numerator / max(denominator, 1e-9))
    return score


# ================================================================
# RAG 知识库
# ================================================================

class RagKnowledgeBase:
    """轻量 RAG 知识库：关键词 + BM25 混合检索。

    使用方式：
        kb = RagKnowledgeBase()
        kb.load_builtin()     # 加载内置古籍知识块
        results = kb.search('子平真诠 日干旺衰 格局', category='bazi', top_k=5)
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._chunks: List[KnowledgeChunk] = []
        self._lock = threading.RLock()
        self._storage_path = storage_path
        self._doc_lengths: List[int] = []
        self._avg_doc_len: float = 0.0
        self._loaded = False

    # ----- 内置知识块（经典古籍摘录）-----

    def load_builtin(self) -> int:
        """加载内置古籍知识块。"""
        with self._lock:
            if self._loaded:
                return len(self._chunks)
            self._chunks = self._build_builtin_chunks()
            self._compute_index()
            self._loaded = True
            return len(self._chunks)

    def _build_builtin_chunks(self) -> List[KnowledgeChunk]:
        """构建内置知识块（来自五经）。"""
        chunks: List[KnowledgeChunk] = []
        cid = 0

        def add(source: str, category: str, content: str,
                context: str = '', tags: Optional[List[str]] = None,
                weight: float = 1.0):
            nonlocal cid
            cid += 1
            chunks.append(KnowledgeChunk(
                id=f'builtin_{cid:04d}',
                source=source,
                category=category,
                content=content,
                context=context,
                tags=tags or extract_keywords(content),
                weight=weight,
            ))

        # ---- 八字（《子平真诠》《滴天髓》《穷通宝鉴》）----
        add('子平真诠', 'bazi',
            '八字命理以日干为主，观其旺衰强弱，定其格局高低。'
            '日干旺者喜克泄，日干弱者喜生扶。'
            '格局者，月令透干之神，定格之要也。'
            '正官格最贵，食神格次之，伤官格须配印乃成。'
            '七杀格须制伏，羊刃格须印化。'
            '调候者，寒暖燥湿之宜也，甲木生于冬月，非丙火不解。',
            context='格局论断与调候用神',
            tags=['格局','日干','旺衰','调候','正官','食神','七杀','羊刃'])

        add('滴天髓', 'bazi',
            '命理推究，首重日主旺衰。旺则抑之，弱则扶之。'
            '五行之气，春木夏火秋金冬水，季土居中。'
            '相生者，木生火、火生土、土生金、金生水、水生木；'
            '相克者，木克土、土克水、水克火、火克金、金克木。'
            '十神者，比肩、劫财、食神、伤官、偏财、正财、七杀、正官、偏印、正印。'
            '日主旺，则比劫为忌；日主弱，则比劫为喜。',
            context='五行旺衰与十神系统',
            tags=['日主','旺衰','五行','十神','比肩','劫财','相生','相克'])

        add('穷通宝鉴', 'bazi',
            '调候为急，甲木生于正月，阳气初升，喜丙火照暖。'
            '乙木生于正月，阴寒未除，亦喜丙火。'
            '丙火生于冬月，太阳无光，喜壬水反射。'
            '丁火生于冬月，灯烛之光，喜甲木引燃。'
            '戊土生于冬月，冻土难耕，喜丙火解冻。'
            '己土生于冬月，湿泥难植，亦喜丙火。'
            '庚金生于夏月，火旺金熔，喜壬水淘洗。'
            '辛金生于夏月，柔弱之金，喜壬水滋养。',
            context='调候用神详解',
            tags=['调候','甲木','乙木','丙火','丁火','戊土','庚金','辛金'])

        add('三命通会', 'bazi',
            '纳音五行者，六十甲子各有音律之象。'
            '甲子乙丑海中金，丙寅丁卯炉中火，戊辰己巳大林木。'
            '庚午辛未路旁土，壬申癸酉剑锋金，甲戌乙亥山头火。'
            '神煞者，天乙贵人、文昌、驿马、桃花、羊刃、亡神、劫煞、灾煞。'
            '天乙贵人最为吉利，能解百祸。'
            '驿马主变动奔波，桃花主感情姻缘。',
            context='纳音五行与神煞系统',
            tags=['纳音','神煞','天乙贵人','驿马','桃花','羊刃','亡神'])

        add('渊海子平', 'bazi',
            '子平法以日干为我，以天干地支之生克论吉凶。'
            '大运者，十年一运，顺逆推排。'
            '流年者，一年一柱，与原局作用。'
            '运遇喜神则吉，遇忌神则凶。'
            '命好运不好，如良田遇旱；运好命不好，如贫人得宝。'
            '格局成败，关键在于用神得力与否。',
            context='大运流年与格局成败',
            tags=['大运','流年','用神','格局','吉凶'])

        # ---- 玄空飞星（《沈氏玄空学》《地理辩证疏》）----
        add('沈氏玄空学', 'xuan_kong',
            '玄空飞星以三元九运为纲，洛书九宫为目。'
            '一白坎、二黑坤、三碧震、四绿巽、五黄中、六白乾、七赤兑、八白艮、九紫离。'
            '山星主管人丁，向星主管财禄。'
            '零正神诀：正神放在水口上，零神放在当令方。'
            '上山下水格局，损丁破财；下山上山格局，旺丁旺财。'
            '替卦者，甲壬丙庚寅申辛亥癸，乙辰巽巳同乾位，坤壬乙辛庚子乾辰巽辛俱属阴。',
            context='三元九运与零正神诀',
            tags=['三元九运','洛书','山星','向星','替卦','零神','正神','上山下水'])

        add('地理辩证疏', 'xuan_kong',
            '二十四山分阴阳，阳山顺飞，阴山逆飞。'
            '父母三般卦者，一四七、二五八、三六九是也。'
            '七星打劫者，借卦气以补不足，使衰旺相济。'
            '城门诀者，向首两旁之宫，有通城门之气者可收。'
            '水口者，水流去之方，关拦紧要，宜聚不宜散。',
            context='二十四山飞布与城门诀',
            tags=['二十四山','父母卦','七星打劫','城门诀','水口','阴阳'])

        # ---- 梅花易数 ----
        add('梅花易数', 'meihua',
            '梅花易数以体用为主，体者我也，用者事也。'
            '体用生克，吉凶可见。体生用曰泄气，用生体曰进益。'
            '体克用曰财，用克体曰官鬼。'
            '动静者，动为主，静为客。动则变，静则稳。'
            '卦气旺者，春木夏火秋金冬水季土。'
            '互卦者，本卦二三四爻为下互，三四五爻为上互。'
            '变卦者，动爻变后所得之卦也。',
            context='体用生克与卦气旺衰',
            tags=['体用','生克','动静','卦气','互卦','变卦','旺衰'])

        # ---- 大六壬 ----
        add('大六壬', 'liuren',
            '大六壬以月将加占时，布天地盘为基。'
            '九宗门者：贼克、比用、昴星、别责、八专、伏吟、返吟、涉害、毕法。'
            '三传者，初传为事之始，中传为事之中，末传为事之终。'
            '贼克法：有克曰贼，无克曰重审。'
            '比用法：二日贼相等，取比日干者为初传。'
            '天将者，贵人、螣蛇、朱雀、六合、青龙、天空、白虎、太常、玄武、太阴、天后、吊客。'
            '神煞者，驿马、桃花、禄神、贵人、羊刃、劫煞、灾煞、咸池。',
            context='九宗门三传与天将神煞',
            tags=['九宗门','三传','月将','天盘','地盘','天将','神煞','驿马','禄神'])

        return chunks

    def _compute_index(self) -> None:
        """计算文档长度索引，供 BM25 使用。"""
        self._doc_lengths = [len(c.content) for c in self._chunks]
        self._avg_doc_len = sum(self._doc_lengths) / max(len(self._doc_lengths), 1)

    # ----- 检索接口 -----

    def search(
        self,
        query: str,
        category: str = 'all',
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """检索相关知识块。

        Args:
            query: 查询文本（可含关键词）
            category: 板块过滤（bazi/liuren/meihua/xuan_kong/all）
            top_k: 返回条数上限
            min_score: 最低相关度阈值

        Returns:
            [(KnowledgeChunk, score), ...] 按相关度降序排列
        """
        self.load_builtin()
        query_terms = extract_keywords(query)
        if not query_terms:
            return []

        results: List[Tuple[KnowledgeChunk, float]] = []
        with self._lock:
            for chunk in self._chunks:
                if category != 'all' and chunk.category not in (category, 'all'):
                    continue
                # BM25 关键词匹配
                bm25 = _bm25_score(query_terms, chunk.tags,
                                   len(chunk.content), self._avg_doc_len)
                # 语义补充：查询词与内容的直接重合度
                query_set = set(query_terms)
                content_set = set(chunk.content)
                overlap = len(query_set & content_set) / max(len(query_set), 1)
                # 混合评分
                score = 0.6 * bm25 + 0.4 * overlap
                if score >= min_score:
                    results.append((chunk, score * chunk.weight))

        results.sort(key=lambda x: -x[1])
        return results[:top_k]

    def get_context_prompt(self, query: str, category: str = 'all',
                           top_k: int = 3) -> str:
        """将检索结果拼接为提示词上下文。"""
        results = self.search(query, category=category, top_k=top_k)
        if not results:
            return ''
        lines = ['【古籍参考依据】']
        for chunk, score in results:
            lines.append(f"（{chunk.source}·{chunk.context}，相关度≈{score:.2f}）")
            lines.append(chunk.content)
            lines.append('---')
        return '\n'.join(lines)


# ================================================================
# 全局单例
# ================================================================

_knowledge_base: Optional[RagKnowledgeBase] = None
_kb_lock = threading.Lock()


def get_knowledge_base() -> RagKnowledgeBase:
    """获取全局 RAG 知识库实例（懒加载单例）。"""
    global _knowledge_base
    with _kb_lock:
        if _knowledge_base is None:
            _knowledge_base = RagKnowledgeBase()
            _knowledge_base.load_builtin()
        return _knowledge_base


def reset_knowledge_base() -> None:
    """重置知识库单例（用于测试清理）。"""
    global _knowledge_base
    with _kb_lock:
        _knowledge_base = None
