"""
AI 分析结果统一渲染器 v2.2
========================
职责：把各面板的「龙虎山大师兄」AI 解读渲染成统一视觉语言，
消灭八字/梅花/六壬三面板之间的字段映射、命名、高亮缺失等漂移。

v2.2 视觉交互与排版升级：
- 顶部 hero 标题区（鎏金渐变 + 大图标 + 时间戳 + 副标题）
- 章节目录导航条（胶囊按钮组，点击锚点跳转）
- 整体结论升级为 hero 卡片（更高视觉权重）
- 章节卡片新增序号徽章 + 渐变色条
- 列表项改为带编号的 rich_list_block
- 免责声明升级为合规化的多级声明卡片

约定
----
- 入口：render_analysis(pan_type, payload, target_layout)
- pan_type: 'bazi' | 'meihua' | 'liuren'
- target_layout: 结果面板的 QVBoxLayout（各面板自己的内容容器）
- payload: AI 返回的 dict，字段以 core.analysis_storage._JSON_SCHEMAS 为准
- 颜色约定：排盘类=青花蓝(Colors.QINGHUA)，AI 解读类=鎏金(Colors.LIUJIN)
- 概率统计固定走 Colors.SUCCESS（绿色语义）
- 文案常量统一由本模块维护，面板不再硬编码同义标题。
"""

from typing import List, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ui.styles import Colors, Fonts, Spacing
from ui.components.collapsible_card import (
    CollapsibleCard,
    ai_section_header,
    ai_section_nav,
    ai_section_card_header,
    highlight_label,
    probability_stats_widget,
    conclusion_block,
    suggestion_block,
    risk_aware_label,
    hero_conclusion_block,
    rich_list_block,
    disclaimer_card,
)


# ---------------------------------------------------------------------------
# AI 分析区文案常量（单一权威源）
# ---------------------------------------------------------------------------
AI_SECTION_TITLE = '龙虎山大师兄算命详批'
KEY_POINTS_LABEL = '【关键信息】'
FINAL_VERDICT_TITLE = '总体判断'
DISCLAIMER_TITLE = '免责声明'


# ---------------------------------------------------------------------------
# 兜底分支使用：未知英文 key → 中文友好标题映射
# 防止 AI 返回未在 sections 中登记的字段时，UI 上直接显示英文 key 名。
# ---------------------------------------------------------------------------
_FALLBACK_KEY_TITLES = {
    'final_verdict': '总体断语',
    'key_points': '重点提示',
    'summary': '综合摘要',
    'overview': '整体概述',
    'analysis': '整体分析',
    'interpretation': '解读',
    'interpretation_detail': '解读详情',
    'advice': '行动建议',
    'suggestions': '建议',
    'scenario_advice': '场景化建议',
    'timing': '应期时机',
    'personality': '性格特质',
    'career': '事业财运',
    'relationships': '婚姻感情',
    'health': '健康注意',
    'hexagram_interpretations': '卦爻解释',
    'historical_cases': '历史案例',
    'probability_stats': '概率统计',
    'disclaimer': '免责声明',
    'four_pillars_detail': '四柱详细解读',
    'analysis_basis': '推断依据',
    'verification_points': '应验要点',
    'caveats': '注意事项',
    # v2.3 扩充维度
    'annual_fortune': '近期流年提示',
    'study_exam': '学业考试运',
    'folklore_tips': '民俗开运建议',
    'tianjiang_detail': '天将神煞详解',
    'scene_readings': '分类占断',
}


def _fallback_title(key: str) -> str:
    """根据英文 key 获取中文友好标题，未登记的 key 保留原 key。"""
    if not key:
        return '补充信息'
    if key in _FALLBACK_KEY_TITLES:
        return _FALLBACK_KEY_TITLES[key]
    # 处理 snake_case：转中文友好短语
    readable = key.replace('_', ' ').strip()
    return readable if readable else '补充信息'


def _truncate_text(s: str, max_len: int = 3000) -> str:
    """极长文本截断，防止 UI 卡顿。"""
    if not isinstance(s, str):
        s = str(s)
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[:max_len].rstrip() + '…（内容过长已截断）'


def _as_text(value):
    """将 None / 字符串 / 列表 / dict 归一化为纯文本，避免 UI 逐字渲染。"""
    if value is None:
        return ''
    if isinstance(value, (list, tuple)):
        parts = [_as_text(x) for x in value if x is not None]
        parts = [p for p in parts if p.strip()]
        return '\n'.join(parts)
    if isinstance(value, dict):
        # dict 转为可读文本，避免 JSON 原样显示
        lines = []
        for k, v in value.items():
            if v is None:
                continue
            v_text = _as_text(v)
            if not v_text.strip():
                continue
            # 递归展开，避免嵌套 dict/list 显示为 repr
            lines.append(f"{k}: {v_text}")
        return '\n'.join(lines)
    return str(value).strip()


def _as_list(value):
    """将 None / 字符串 / 列表 / dict 归一化为字符串列表。"""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        out = []
        for x in value:
            if x is None:
                continue
            txt = _as_text(x)
            if txt.strip():
                out.append(txt)
        return out
    if isinstance(value, dict):
        # dict 转为 “key: value” 列表，避免 JSON 原样显示
        items = []
        for k, v in value.items():
            if v is None:
                continue
            v_text = _as_text(v)
            if not v_text.strip():
                continue
            items.append(f"{k}: {v_text}")
        return items
    text = str(value).strip()
    return [text] if text else []


def _color_for_pan(pan_type: str) -> str:
    """返回面板默认强调色：梅花用青花蓝，其余用鎏金。"""
    return Colors.QINGHUA if pan_type == 'meihua' else Colors.LIUJIN


def _build_empty_widget(message: str) -> QWidget:
    """构建空状态提示控件。"""
    label = QLabel(message)
    label.setStyleSheet(
        f"color:{Colors.TEXT3}; font-size:{Fonts.SZ_BODY}; "
        f"font-family:{Fonts.BODY}; padding:24px;"
    )
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    return label


def _wrap_card(card: CollapsibleCard, anchor_id: str, title: str, icon: str,
               color: str, index: int, content: QWidget) -> None:
    """统一的章节卡片容器：替换默认头部为 ai_section_card_header。

    Args:
        card:  CollapsibleCard 实例
        anchor_id: 锚点 ID（用于导航跳转）
        title / icon / color / index: 标题、图标、强调色、序号
        content: 已构造好的卡片内容
    """
    # 隐藏卡片默认头部（保留内容区）
    if hasattr(card, '_header') and card._header:
        card._header.setVisible(False)
    # 重新插入自定义标题头部
    header_widget = ai_section_card_header(
        index=index,
        title=title,
        icon=icon,
        color=color,
        anchor_id=anchor_id,
    )
    # 通过 main_layout 在最前面插入自定义标题
    card._main_layout.insertWidget(0, header_widget)
    # 设置实际内容
    card.set_content(content)


def _anchor_id_for(key: str) -> str:
    """生成稳定的 Qt objectName 作为锚点 ID（字母数字下划线）。"""
    return f'ai_anchor_{key}'


def render_analysis(pan_type: str, payload: dict, target_layout: QVBoxLayout) -> None:
    """统一渲染 AI 分析结果到目标布局。

    Args:
        pan_type: 面板类型标识，用于语义化配色。
        payload: AI 返回的结构化解读 dict。
        target_layout: 三面板各自的内容布局（bazi.clay / meihua.content_layout /
                       liuren.content_layout），从该布局外部 append 卡片。
    """
    if not payload or not isinstance(payload, dict):
        target_layout.addWidget(_build_empty_widget(
            '龙虎山大师兄未起得有效卦象，请点击「重新测算」再试'
        ))
        return

    default_color = _color_for_pan(pan_type)
    container = QWidget()
    container.setObjectName('ai_analysis_container')
    container.setStyleSheet('background: transparent;')
    root = QVBoxLayout(container)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(14)

    # ---------- 1) hero 标题区 ----------
    root.addWidget(ai_section_header(AI_SECTION_TITLE))

    has_content = False
    nav_items: List[Tuple[str, str, str]] = []

    # ---------- 2) 重点提示（高亮块，置顶） ----------
    key_points = payload.get('key_points')
    if isinstance(key_points, (list, tuple)):
        kp_text = '\n'.join(str(x) for x in key_points if x and str(x).strip())
    elif isinstance(key_points, str):
        kp_text = key_points
    else:
        kp_text = ''
    kp_text = _truncate_text(kp_text, max_len=2000)
    if kp_text.strip():
        root.addWidget(highlight_label(f'{KEY_POINTS_LABEL}\n' + kp_text.strip(), Colors.LIUJIN))
        has_content = True

    # ---------- 3) 各面板字段映射（带锚点 ID） ----------
    sections = []
    if pan_type == 'bazi':
        sections = [
            # 注：key_points（重点提示）已在顶部高亮块统一渲染，此处不再重复出卡
            ('final_verdict', '总体判断', '🎯', Colors.LIUJIN, 'conclusion_hero'),
            ('personality', '性格特质', '🧠', Colors.QINGHUA, 'list'),
            ('career', '事业财运', '💼', Colors.LIUJIN, 'list'),
            ('relationships', '婚姻感情', '💕', Colors.ZHUSHA, 'list'),
            ('health', '健康注意', '💪', Colors.SUCCESS, 'list'),
            ('four_pillars_detail', '四柱详细解读', '🕰', Colors.LIUJIN, 'list'),
            ('annual_fortune', '近期流年提示', '📅', Colors.ZHUSHA, 'list'),
            ('study_exam', '学业考试运', '🎓', Colors.QINGHUA, 'conclusion'),
            ('historical_cases', '历史案例', '📚', Colors.ZHUSHA, 'list'),
            ('folklore_tips', '民俗开运建议', '🍀', Colors.SUCCESS, 'advice'),
            ('scenario_advice', '核心建议', '💡', Colors.SUCCESS, 'advice'),
            ('probability_stats', '概率统计', '📊', Colors.SUCCESS, 'probability'),
            ('disclaimer', DISCLAIMER_TITLE, '⚠', Colors.TEXT3, 'disclaimer'),
        ]
    elif pan_type == 'meihua':
        sections = [
            ('final_verdict', '总体判断', '🎯', Colors.LIUJIN, 'conclusion_hero'),
            ('analysis', '卦象分析', '☯', Colors.QINGHUA, 'conclusion'),
            ('hexagram_interpretations', '卦爻解释', '📖', Colors.LIUJIN, 'list'),
            ('timing', '应期时机', '⏳', Colors.SUCCESS, 'conclusion'),
            ('advice', '行动建议', '💡', Colors.LIUJIN, 'advice'),
            ('scenario_advice', '场景化建议', '🎯', Colors.ZHUSHA, 'conclusion'),
            ('folklore_tips', '民俗开运建议', '🍀', Colors.SUCCESS, 'advice'),
            ('historical_cases', '历史案例', '📚', Colors.QINGHUA, 'list'),
            ('probability_stats', '概率统计', '📊', Colors.SUCCESS, 'probability'),
            ('disclaimer', DISCLAIMER_TITLE, '⚠', Colors.ZHUSHA, 'disclaimer'),
        ]
    elif pan_type == 'liuren':
        sections = [
            ('final_verdict', '总体判断', '🎯', Colors.LIUJIN, 'conclusion_hero'),
            ('analysis', '课体分析', '☯', Colors.LIUJIN, 'conclusion'),
            ('tianjiang_detail', '天将神煞详解', '🎭', Colors.QINGHUA, 'list'),
            ('scene_readings', '分类占断', '🧭', Colors.LIUJIN, 'conclusion'),
            ('scenario_advice', '综合建议', '✨', Colors.ZHUSHA, 'conclusion'),
            ('timing', '应期时机', '⏳', Colors.SUCCESS, 'conclusion'),
            ('folklore_tips', '民俗开运建议', '🍀', Colors.SUCCESS, 'advice'),
            ('historical_cases', '历史案例', '📚', Colors.QINGHUA, 'list'),
            ('probability_stats', '概率统计', '📊', Colors.LIUJIN, 'probability'),
            ('disclaimer', DISCLAIMER_TITLE, '⚠', Colors.TEXT3, 'disclaimer'),
        ]

    rendered_keys = set()

    # 预扫描：确定有效的章节（用于序号 & 目录）
    valid_sections = []
    for key, title, icon, color, mode in sections:
        raw = payload.get(key)
        if raw is None:
            continue
        if mode == 'probability':
            if not _as_list(raw):
                continue
        elif mode in ('list', 'advice'):
            if not _as_list(raw):
                continue
        elif mode in ('conclusion', 'conclusion_hero'):
            if not _as_text(raw):
                continue
        elif mode == 'disclaimer':
            # disclaimer 始终渲染（即便 AI 返回空，也显示默认声明）
            pass
        else:
            if not _as_text(raw):
                continue
        valid_sections.append((key, title, icon, color, mode))

    # ---------- 4) 目录导航条（仅在章节 ≥3 时显示，避免小报告拥挤） ----------
    if len(valid_sections) >= 3:
        nav_items = [
            (_anchor_id_for(key), title, icon)
            for key, title, icon, _color, _mode in valid_sections
        ]
        nav_widget = ai_section_nav(nav_items, active_color=default_color)
        root.addWidget(nav_widget)

    # ---------- 5) 章节渲染 ----------
    for idx, (key, title, icon, color, mode) in enumerate(valid_sections, 1):
        if key in rendered_keys:
            continue
        raw = payload.get(key)
        anchor = _anchor_id_for(key)

        if mode == 'probability':
            items = _as_list(raw)
            card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
            card.set_content(probability_stats_widget(items, color))
            root.addWidget(card)
            # 标记锚点
            card.setObjectName(anchor)
            has_content = True
            rendered_keys.add(key)
            continue

        if mode == 'advice':
            items = _as_list(raw)
            if not items:
                continue
            # 核心建议：使用 suggestion_block（带情感徽章 + 关键词高亮）
            root.addWidget(suggestion_block(items, Colors.SUCCESS))
            has_content = True
            rendered_keys.add(key)
            continue

        if mode == 'disclaimer':
            # 使用升级版免责声明卡片
            text = _as_text(raw) if raw is not None else ''
            root.addWidget(disclaimer_card(text))
            has_content = True
            rendered_keys.add(key)
            continue

        if mode == 'conclusion_hero':
            # 整体结论 - hero 高视觉权重块
            text = _as_text(raw)
            hero_block = hero_conclusion_block(text, default_color)
            hero_block.setObjectName(anchor)
            root.addWidget(hero_block)
            has_content = True
            rendered_keys.add(key)
            continue

        text = _as_text(raw)
        if not text:
            continue

        if mode == 'conclusion':
            card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
            card.set_content(conclusion_block(text, color))
        elif mode == 'list':
            items = _as_list(raw)
            # 列表渲染：使用 rich_list_block 替代扁平列表，更精致
            list_block = rich_list_block(
                items=items,
                color=color,
                title=title,
                icon=icon,
            )
            list_block.setObjectName(anchor)
            root.addWidget(list_block)
            has_content = True
            rendered_keys.add(key)
            continue
        else:
            card = CollapsibleCard(title, icon, accent_color=color, collapsed=False)
            card.set_content(risk_aware_label(text, color=Colors.LIUJIN, show_sentiment=False))

        card.setObjectName(anchor)
        root.addWidget(card)
        has_content = True
        rendered_keys.add(key)

    # ---------- 6) 兜底：未在 sections 中消费的扩展字段 ----------
    for key, val in payload.items():
        if key in rendered_keys:
            continue
        text = _as_text(val)
        # 极端值护栏：空值/过短/过长
        if not text or len(text.strip()) < 3:
            continue
        text = _truncate_text(text, max_len=4000)
        items = _as_list(val)
        # 限制列表长度，防止 UI 爆炸
        if items:
            # 对每个条目做截断
            items = [_truncate_text(it, max_len=500) for it in items][:200]
        # 兜底标题统一走中文映射，避免显示英文 key 名
        title_cn = _fallback_title(key)
        if items and len(items) > 1:
            list_block = rich_list_block(items=items, color=default_color, title=title_cn, icon='📝')
            list_block.setObjectName(_anchor_id_for(key))
            root.addWidget(list_block)
        else:
            card = CollapsibleCard(title_cn, '📝', accent_color=default_color, collapsed=False)
            card.set_content(risk_aware_label(text, color=Colors.LIUJIN, show_sentiment=False))
            card.setObjectName(_anchor_id_for(key))
            root.addWidget(card)
        has_content = True

    if not has_content:
        root.addWidget(_build_empty_widget(
            '龙虎山大师兄未起得有效条目，请点击「重新测算」再试'
        ))

    # 挂载到目标布局，并在外部完成滚动
    target_layout.addWidget(container)
