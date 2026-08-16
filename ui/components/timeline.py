"""
大运流年时间轴组件
====================
八字结果面板「大运流年」板块的视觉升级：把原先平铺的横向行列表重构为
竖向时间轴（主轴 + 节点圆点），并用五行生克关系给每个节点着色体现趋势，
起运作为关键节点高亮标注；流年改为 2 列紧凑网格。每行悬浮显示该步/该年的
天干地支五行与十神生克明细。

本组件与全局设计系统（ui/styles.py）保持一致：排盘类用青花蓝、强调用鎏金，
五行色取自 Colors.WOOD/FIRE/EARTH/METAL/WATER。
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QFrame)
from PySide6.QtCore import Qt

from ui.styles import Colors, Fonts, Spacing

# 天干/地支五行 → 主题色
WUXING_COLOR = {
    '木': Colors.WOOD, '火': Colors.FIRE, '土': Colors.EARTH,
    '金': Colors.METAL, '水': Colors.WATER,
}


def _relation_to_level(gan_rel, zhi_rel):
    """把天干/地支的五行生克关系归一为 (标签, 主色, 浅色glow)。

    优先级：克我 → 慎（需谨慎）；生我/比和 → 吉（帮扶）；其余 → 平。
    """
    combined = ' '.join([str(gan_rel or ''), str(zhi_rel or '')])
    if '克我' in combined:
        return ('慎', Colors.WARNING, Colors.WARNING_LIGHT)
    if '生我' in combined or '比和' in combined:
        return ('吉', Colors.SUCCESS, Colors.SUCCESS_LIGHT)
    return ('平', Colors.QINGHUA, Colors.QINGHUA_GLOW)


def _build_node_tooltip(detailed):
    """拼接悬浮明细：天干(五行) / 地支(五行) / 天干关系 / 地支关系。"""
    if not detailed or not isinstance(detailed, dict):
        return '（暂无五行生克明细）'
    parts = []
    gan, gan_wx = detailed.get('gan', ''), detailed.get('gan_wx', '')
    zhi, zhi_wx = detailed.get('zhi', ''), detailed.get('zhi_wx', '')
    if gan:
        parts.append(f'天干 {gan}（{gan_wx or "？"}）')
    if zhi:
        parts.append(f'地支 {zhi}（{zhi_wx or "？"}）')
    if detailed.get('gan_relation'):
        parts.append(f'天干关系：{detailed["gan_relation"]}')
    if detailed.get('zhi_relation'):
        parts.append(f'地支关系：{detailed["zhi_relation"]}')
    return '\n'.join(parts) if parts else '（暂无五行生克明细）'


def fortune_timeline_widget(dayun, liunian, color=Colors.LIUJIN):
    """大运竖向时间轴 + 流年网格，返回可直接 set_content 的 QWidget。

    Args:
        dayun:   排盘结果中的大运 dict（含 periods / direction / qiyun_text）。
        liunian: 排盘结果中的流年 dict（含 years）。
        color:   强调色（默认鎏金，与外层卡片一致）。

    Returns:
        QWidget。无数据则返回居中占位提示。
    """
    dayun = dayun or {}
    liunian = liunian or {}
    periods = dayun.get('periods') or []
    years_list = liunian.get('years') or []

    if not periods and not years_list:
        empty = QLabel('暂无大运流年数据')
        empty.setStyleSheet(
            f"color:{Colors.TEXT3}; font-size:{Fonts.SZ_BODY}; "
            f"font-family:{Fonts.BODY}; padding:8px;")
        empty.setAlignment(Qt.AlignCenter)
        return empty

    container = QWidget()
    container.setStyleSheet("background: transparent;")
    root = QVBoxLayout(container)
    root.setContentsMargins(4, 4, 4, 4)
    root.setSpacing(14)

    # ---------- 起运关键节点（顶部高亮） ----------
    qiyun_text = dayun.get('qiyun_text')
    direction = dayun.get('direction', '')
    if qiyun_text:
        qy = QWidget()
        qy_l = QHBoxLayout(qy)
        qy_l.setContentsMargins(0, 0, 0, 0)
        qy_l.setSpacing(10)

        dot = QLabel('◉')
        dot.setStyleSheet(
            f"color:{Colors.LIUJIN}; font-size:16px;")
        dot.setFixedSize(22, 22)
        dot.setAlignment(Qt.AlignCenter)
        qy_l.addWidget(dot)

        qy_text = QLabel(f'起运：{qiyun_text}')
        qy_text.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; "
            f"color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
        qy_l.addWidget(qy_text)
        if direction:
            d_lbl = QLabel(f'· 大运方向：{direction}')
            d_lbl.setStyleSheet(
                f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; "
                f"font-family:{Fonts.BODY};")
            qy_l.addWidget(d_lbl)
        qy_l.addStretch()
        root.addWidget(qy)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{Colors.DIVIDER};")
        root.addWidget(sep)

    # ---------- 大运时间轴 ----------
    if periods:
        title = QLabel('大运走势')
        title.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; "
            f"color:{Colors.QINGHUA}; font-family:{Fonts.BODY};")
        root.addWidget(title)

        for idx, period in enumerate(periods):
            root.addWidget(_build_dayun_row(period, color, idx == len(periods) - 1))

    # ---------- 流年网格 ----------
    if years_list:
        if periods:
            gap = QFrame()
            gap.setFixedHeight(1)
            gap.setStyleSheet(f"background:{Colors.TEXT3}; opacity:0.3; margin:6px 0;")
            root.addWidget(gap)

        flow_title = QLabel('流年运势（未来10年）')
        flow_title.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM}; "
            f"color:{Colors.LIUJIN}; font-family:{Fonts.BODY}; padding-top:4px;")
        root.addWidget(flow_title)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        for i, year_data in enumerate(years_list):
            grid.addWidget(_build_liunian_cell(year_data), i // 2, i % 2)
        root.addLayout(grid)

    return container


def _build_dayun_row(period, color, is_last):
    """单行大运：左节点列（圆点+主轴）+ 右内容卡。"""
    row = QWidget()
    row.setStyleSheet("background: transparent;")
    rl = QHBoxLayout(row)
    rl.setContentsMargins(0, 0, 0, 0)
    rl.setSpacing(12)

    # 左：节点列（圆点 + 主轴）
    node_col = QVBoxLayout()
    node_col.setContentsMargins(0, 0, 0, 0)
    node_col.setSpacing(0)

    detailed = period.get('detailed_analysis') or {}
    gan_wx = detailed.get('gan_wx', '')
    node_color = WUXING_COLOR.get(gan_wx, color)

    node = QLabel(str(period.get('period', '')))
    node.setStyleSheet(f"""
        background:{node_color}; color:white;
        font-size:11px; font-weight:{Fonts.W_BOLD};
        border-radius:11px; font-family:{Fonts.BODY};
    """)
    node.setFixedSize(22, 22)
    node.setAlignment(Qt.AlignCenter)
    node_col.addWidget(node)

    spine = QFrame()
    spine.setFixedWidth(2)
    spine.setStyleSheet(f"background:{Colors.DIVIDER}; border:none;")
    node_col.addWidget(spine, 1)  # stretch 撑满，连接下一节点
    rl.addLayout(node_col)

    # 右：内容卡
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background:{Colors.CARD}; border:1px solid {Colors.BORDER};
            border-radius:{Spacing.RADIUS_SM}; padding:10px 12px;
        }}
    """)
    cv = QVBoxLayout(card)
    cv.setContentsMargins(0, 0, 0, 0)
    cv.setSpacing(6)

    head = QHBoxLayout()
    head.setSpacing(8)

    ganzhi = QLabel(period.get('ganzhi', ''))
    ganzhi.setStyleSheet(f"""
        background:{Colors.QINGHUA}; color:white;
        font-size:{Fonts.SZ_BODY}; font-weight:{Fonts.W_MEDIUM};
        border-radius:{Spacing.RADIUS_SM}; padding:3px 12px;
        font-family:{Fonts.BODY}; min-width:60px;
    """)
    ganzhi.setAlignment(Qt.AlignCenter)
    head.addWidget(ganzhi)

    age = QLabel(f"{period.get('start_age','')}-{period.get('end_age','')}岁")
    age.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
    head.addWidget(age)

    years = QLabel(f"{period.get('start_year','')}-{period.get('end_year','')}年")
    years.setStyleSheet(f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT2}; font-family:{Fonts.BODY};")
    head.addWidget(years)

    # 趋势 badge
    label, badge_color, badge_glow = _relation_to_level(
        detailed.get('gan_relation'), detailed.get('zhi_relation'))
    icon = '✓' if label == '吉' else ('!' if label == '慎' else '～')
    badge = QLabel(f'{label} {icon}')
    badge.setStyleSheet(f"""
        background:{badge_glow}; color:{badge_color};
        font-size:{Fonts.SZ_MICRO}; font-weight:{Fonts.W_MEDIUM};
        border-radius:{Spacing.RADIUS_SM}; padding:2px 8px;
        font-family:{Fonts.BODY};
    """)
    head.addWidget(badge)
    head.addStretch()
    cv.addLayout(head)

    analysis = period.get('analysis', '')
    if analysis:
        a_lbl = QLabel(analysis)
        a_lbl.setWordWrap(True)
        a_lbl.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.TEXT}; "
            f"font-family:{Fonts.BODY}; line-height:1.5;")
        cv.addWidget(a_lbl)

    tooltip = _build_node_tooltip(detailed)
    if tooltip and tooltip != '（暂无五行生克明细）':
        card.setToolTip(tooltip)
    rl.addWidget(card, 1)
    return row


def _build_liunian_cell(year_data):
    """流年单个网格单元：年份 + 干支 + 悬浮明细。"""
    cell = QFrame()
    cell.setStyleSheet(f"""
        QFrame {{
            background:{Colors.CARD}; border:1px solid {Colors.BORDER};
            border-radius:{Spacing.RADIUS_SM}; padding:6px 8px;
        }}
        QFrame:hover {{ border:1px solid {Colors.LIUJIN_LIGHT}; }}
    """)
    cl = QHBoxLayout(cell)
    cl.setContentsMargins(0, 0, 0, 0)
    cl.setSpacing(8)

    year = QLabel(str(year_data.get('year', '')))
    year.setStyleSheet(f"""
        background:{Colors.LIUJIN}; color:white;
        font-size:{Fonts.SZ_SMALL}; font-weight:{Fonts.W_MEDIUM};
        border-radius:{Spacing.RADIUS_SM}; padding:2px 8px;
        font-family:{Fonts.BODY}; min-width:42px;
    """)
    year.setAlignment(Qt.AlignCenter)
    cl.addWidget(year)

    ganzhi = QLabel(year_data.get('ganzhi', ''))
    ganzhi.setStyleSheet(f"""
        background:{Colors.QINGHUA}; color:white;
        font-size:{Fonts.SZ_SMALL}; font-weight:{Fonts.W_MEDIUM};
        border-radius:{Spacing.RADIUS_SM}; padding:2px 8px;
        font-family:{Fonts.BODY}; min-width:48px;
    """)
    ganzhi.setAlignment(Qt.AlignCenter)
    cl.addWidget(ganzhi)
    cl.addStretch()

    detailed = year_data.get('detailed_analysis') or {}
    tip = _build_node_tooltip(detailed)
    if year_data.get('analysis'):
        tip += f'\n\n{year_data["analysis"]}'
    if tip and tip != '（暂无五行生克明细）':
        cell.setToolTip(tip)
    return cell
