"""
可折叠卡片（共享组件）
========================
三套右侧结果面板（八字 / 梅花易数 / 大六壬）统一复用此组件，保证
视觉一致：左侧强调色条 + 图标 + 标题 + 内容区。

配色约定（视觉层次）：
  - 排盘类卡片：青色条 (Colors.QINGHUA)
  - AI 解读类卡片：鎏金色条 (Colors.LIUJIN)
强调色由调用方通过 accent_color 传入，便于语义化区分。

注：自 v5.1 起，右侧显示板块取消内容折叠功能，所有卡片默认展开并不可折叠，
避免用户错以为内容「消失」；标题栏仅作视觉分组，不再响应点击折叠。
"""
import re

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
                               QProgressBar)
from PySide6.QtCore import Qt
from ui.styles import Colors, Fonts, Spacing


class CollapsibleCard(QFrame):
    """结果显示卡片 - 始终展开（无折叠）。

    原折叠交互已移除：标题栏仅作视觉分组，点击不再收起内容，
    保证排盘信息 / AI 解读内容始终可见。
    """

    def __init__(self, title: str, icon: str = '', parent=None,
                 accent_color=None, collapsed: bool = False):
        """
        构建卡片骨架：标题栏（强调色条 + 图标 + 标题）与内容容器。

        Args:
            title:        卡片标题文字。
            icon:         标题左侧图标字符（emoji 或卦符），空串表示不显示。
            parent:       Qt 父控件。
            accent_color: 左侧强调色条颜色；None 时取青色 Colors.QINGHUA。
                          约定排盘类卡片用青色、AI 解读类卡片用鎏金 Colors.LIUJIN。
            collapsed:    已废弃参数，保留仅为兼容旧调用，卡片始终展开。
        """
        super().__init__(parent)
        # 始终展开，忽略 collapsed 参数（折叠功能已移除）
        self._collapsed = False
        self._accent_color = accent_color or Colors.QINGHUA
        self._content_widget = None

        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.RADIUS};
            }}
            QFrame:hover {{
                border-color: {self._accent_color};
            }}
        """)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # 标题栏（纯展示，不再可点击折叠）
        self._header = QFrame()
        self._header.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
                border-radius: {Spacing.RADIUS};
            }}
        """)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(10)

        # 强调色条（视觉层次标识：排盘=青 / AI=金）
        self._accent_bar = QFrame()
        self._accent_bar.setFixedSize(4, 20)
        self._accent_bar.setStyleSheet(f"background: {self._accent_color}; border-radius: 2px;")

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 16px; color: {self._accent_color};")
        icon_label.setFixedWidth(24)

        # 标题（五号字阶梯：SECTION 级）
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_MEDIUM};
            color: {Colors.TEXT};
            font-family: {Fonts.BODY};
        """)

        header_layout.addWidget(self._accent_bar)
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self._main_layout.addWidget(self._header)

        # 内容容器（始终展开）
        self._content_container = QWidget()
        self._content_container.setStyleSheet("background: transparent; border: none;")
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(16, 0, 16, 14)
        self._content_layout.setSpacing(0)
        self._main_layout.addWidget(self._content_container)

    def set_content(self, widget: QWidget):
        """设置卡片内容（首次/更新均安全）。"""
        if self._content_widget:
            self._content_layout.removeWidget(self._content_widget)
            self._content_widget.deleteLater()
        self._content_widget = widget
        # 内容顶部加一条分割线，强化标题与内容的层次
        if self._content_layout.count() == 0:
            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet(f"background-color: {Colors.DIVIDER}; margin-bottom: 12px;")
            self._content_layout.addWidget(div)
        self._content_layout.addWidget(widget)

    def is_collapsed(self) -> bool:
        """兼容旧调用：卡片始终展开，固定返回 False。"""
        return False


def ai_section_header(title: str = '龙虎山大师兄分析预测', icon: str = '🧙') -> QWidget:
    """金色渐变分隔条 + 鎏金色标题，用于在各面板中分隔『大师兄解读区』，与八字面板视觉一致。

    返回可直接 addWidget 的 QWidget（自身无外边距，由父布局控制间距）。
    """
    container = QWidget()
    v = QVBoxLayout(container)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)

    # 金色渐变分隔线（中亮两端透明）
    divider = QFrame()
    divider.setFixedHeight(2)
    divider.setStyleSheet(
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 transparent, stop:0.5 {Colors.LIUJIN}, stop:1 transparent); "
        f"border: none; margin: 18px 0 10px 0;"
    )
    v.addWidget(divider)

    h = QHBoxLayout()
    h.setContentsMargins(0, 0, 0, 4)
    h.setSpacing(8)
    icon_label = QLabel(icon)
    icon_label.setStyleSheet(f"font-size: 18px; color: {Colors.LIUJIN};")
    title_label = QLabel(title)
    title_label.setStyleSheet(
        f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
        f"color: {Colors.LIUJIN}; font-family: {Fonts.TITLE};"
    )
    h.addWidget(icon_label)
    h.addWidget(title_label)
    h.addStretch()
    v.addLayout(h)
    return container


def highlight_label(text: str, color: str = Colors.LIUJIN) -> QWidget:
    """生成一条「重要内容」高亮提示块：左侧色条 + 鎏金/强调色图标 + 文案。

    用于 KP 模型智能深度分析中标注关键结论、重点提示或风险提示，
    与排盘卡片视觉一致，强化信息层级。

    Args:
        text:  要强调的文案（支持换行）。
        color: 强调色（默认鎏金 Colors.LIUJIN）。

    Returns:
        可直接 addWidget 到卡片内容容器的 QWidget。
    """
    container = QFrame()
    container.setStyleSheet(f"""
        QFrame {{
            background: {Colors.LIUJIN_GLOW};
            border-left: 4px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    hl = QHBoxLayout(container)
    hl.setContentsMargins(12, 10, 12, 10)
    hl.setSpacing(10)

    star = QLabel('⭐')
    star.setStyleSheet(f"font-size: 15px; color: {color};")
    star.setFixedSize(22, 22)
    star.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

    txt = QLabel(text)
    txt.setWordWrap(True)
    txt.setStyleSheet(
        f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
        f"font-family: {Fonts.BODY}; line-height: 1.6;"
    )
    hl.addWidget(star)
    hl.addWidget(txt, 1)
    return container


def probability_stats_widget(stats: object, color: str = Colors.LIUJIN) -> QWidget:
    """把「概率统计」渲染为可读卡片：每个条目 = 含义标签 + 数值（百分比/分值）+ 进度条 + 解读。

    设计目标：解决原先只丢几个数字、用户完全看不懂的问题。
    - 若 AI 返回「带百分号/分数的字符串列表」，自动拆出「标签 + 数值」，并用进度条直观展示占比；
    - 若返回纯描述性列表（无数字），则退化为带说明文字的列表，并补一句来源提示；
    - 始终附「数据说明」：明确这些数值是模型基于命理数据的相对概率/置信度估算，非统计采样结果。

    Args:
        stats: AI 返回的 probability_stats，可能是字符串列表或字符串。
        color: 强调色（默认鎏金）。

    Returns:
        可直接 set_content / addWidget 的 QWidget。
    """
    container = QWidget()
    v = QVBoxLayout(container)
    v.setContentsMargins(4, 4, 4, 4)
    v.setSpacing(12)

    items = []
    if isinstance(stats, (list, tuple)):
        items = [str(x).strip() for x in stats if x and str(x).strip()]
    elif isinstance(stats, str):
        items = [stats] if stats.strip() else []

    # 解析「标签 + 数值」：优先匹配末尾的「标签：数值%」或「标签 数值%」结构，
    # 支持 "事业财运：82%" / "感情婚姻:65%" / "事业 85分" / "整体 0.75" 等
    _num_pat = re.compile(r'[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|％|分|/100)?\s*$')
    parsed = []  # (label, percent_or_none, raw)
    for it in items:
        m = _num_pat.search(it)
        if m:
            num = float(m.group(1))
            unit = m.group(2)
            if unit in ('%', '％'):
                pct = num
            elif unit == '分':
                pct = num * 10 if num <= 10 else (num / 100 if num <= 100 else num)
            elif num <= 1.5:          # 形如 0.75 → 视为比例
                pct = num * 100
            else:                     # 形如 85 / 92 → 视为百分制
                pct = num
            pct = max(0.0, min(100.0, pct))
            # 标签 = 去掉末尾数字部分后的前缀文字
            label = _num_pat.sub('', it).strip(' :：·-')
            if not label:
                label = it
            parsed.append((label, pct, it))
        else:
            # 无数字：纯描述条目
            parsed.append((it, None, it))

    # 动态提取维度名，用于「如何理解这些数据」说明块
    dimension_labels = [label for (label, pct, raw) in parsed if label]
    if dimension_labels:
        v.insertWidget(0, _build_explanation_box(dimension_labels, color))

    if parsed:
        for label, pct, raw in parsed:
            row = QWidget()
            rv = QVBoxLayout(row)
            rv.setContentsMargins(0, 0, 0, 0)
            rv.setSpacing(5)

            head = QHBoxLayout()
            head.setSpacing(8)
            name_lbl = QLabel(label)
            name_lbl.setStyleSheet(
                f"font-size: {Fonts.SZ_BODY}; font-weight: {Fonts.W_MEDIUM}; "
                f"color: {Colors.TEXT}; font-family: {Fonts.BODY};")
            head.addWidget(name_lbl)
            head.addStretch()
            if pct is not None:
                val_lbl = QLabel(f'{pct:.0f}%')
                val_lbl.setStyleSheet(
                    f"font-size: {Fonts.SZ_BODY}; font-weight: {Fonts.W_BOLD}; "
                    f"color: {color}; font-family: {Fonts.BODY};")
                head.addWidget(val_lbl)
            rv.addLayout(head)

            if pct is not None:
                bar = QProgressBar()
                bar.setRange(0, 100)
                bar.setValue(int(round(pct)))
                bar.setTextVisible(False)
                bar.setFixedHeight(8)
                bar.setStyleSheet(f"""
                    QProgressBar {{
                        background: {Colors.BORDER}; border-radius: 4px;
                        border: none; text-align: center;
                    }}
                    QProgressBar::chunk {{
                        background: {color}; border-radius: 4px;
                    }}
                """)
                rv.addWidget(bar)
            else:
                # 纯描述：作为说明文字展示，避免空荡
                desc = QLabel(raw)
                desc.setWordWrap(True)
                desc.setStyleSheet(
                    f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT2}; "
                    f"font-family: {Fonts.BODY}; line-height: 1.6;")
                rv.addWidget(desc)

            if pct is not None:
                tip = (f"{label}：基于命理数据的相对概率 / 置信度估算"
                       f"（{pct:.0f}%），用于对比该维度强弱趋势，非统计采样结果。")
            else:
                tip = (f"{label}：基于命理数据的相对概率 / 置信度估算，"
                       f"用于对比该维度强弱趋势，非统计采样结果。")
            row.setToolTip(tip)
            v.addWidget(row)
    else:
        empty = QLabel('本次分析未给出概率统计。')
        empty.setStyleSheet(
            f"color: {Colors.TEXT3}; font-size: {Fonts.SZ_BODY}; "
            f"font-family: {Fonts.BODY};")
        empty.setAlignment(Qt.AlignCenter)
        v.addWidget(empty)

    return container


# ---------------------------------------------------------------------------
# 强调色 → 浅色底（部分主题色无 *_GLOW，用 *_LIGHT 顶替）
# ---------------------------------------------------------------------------
_GLOW_MAP = {
    Colors.LIUJIN: Colors.LIUJIN_GLOW,
    Colors.QINGHUA: Colors.QINGHUA_GLOW,
    Colors.ZHUSHA: Colors.ZHUSHA_GLOW,
    Colors.SUCCESS: Colors.SUCCESS_LIGHT,
    Colors.WARNING: Colors.WARNING_LIGHT,
    Colors.DANGER: Colors.DANGER_LIGHT,
    Colors.INFO: Colors.INFO_LIGHT,
}


def _glow(color):
    """返回强调色对应的浅色底，用于色块背景。"""
    return _GLOW_MAP.get(color, Colors.LIUJIN_GLOW)


def _build_explanation_box(dimension_labels, color=Colors.LIUJIN) -> QWidget:
    """概率统计的「如何理解这些数据？」说明块：含义 / 计算维度 / 实际用途。

    说明块置于进度条上方，帮助用户理解百分比所指，而非孤立数字。
    """
    box = QFrame()
    box.setStyleSheet(f"""
        QFrame {{
            background: {_glow(color)};
            border-left: 4px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    bl = QVBoxLayout(box)
    bl.setContentsMargins(12, 10, 12, 10)
    bl.setSpacing(6)

    head = QLabel('📊 如何理解这些数据？')
    head.setStyleSheet(
        f"font-size: {Fonts.SZ_SMALL}; font-weight: {Fonts.W_MEDIUM}; "
        f"color: {color}; font-family: {Fonts.BODY};")
    bl.addWidget(head)

    dims = '、'.join(dimension_labels) if dimension_labels else '各维度'
    lines = [
        f'含义：以上为龙虎山大师兄基于命理数据的相对概率 / 置信度估算，反映各维度趋势强弱。',
        f'计算维度：{dims}（由 AI 按命局自动给出）。',
        '实际用途：用于直观对比自身各维度强弱、辅助趋势判断；非统计采样结果，仅供参考。',
    ]
    for ln in lines:
        t = QLabel(ln)
        t.setWordWrap(True)
        t.setStyleSheet(
            f"font-size: {Fonts.SZ_SMALL}; color: {Colors.TEXT2}; "
            f"font-family: {Fonts.BODY}; line-height: 1.6;")
        bl.addWidget(t)
    return box


def conclusion_block(text: str, color=Colors.LIUJIN) -> QWidget:
    """整体结论高亮块：粗金边 + 强调色底 + 「🎯 整体结论」标题 + 正文。

    用于龙虎山大师兄分析预测区中最核心的 final_verdict，视觉层级高于普通卡片。
    """
    box = QFrame()
    box.setStyleSheet(f"""
        QFrame {{
            background: {_glow(color)};
            border-left: 6px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    bl = QVBoxLayout(box)
    bl.setContentsMargins(14, 12, 14, 12)
    bl.setSpacing(8)

    head = QLabel('🎯 整体结论')
    head.setStyleSheet(
        f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
        f"color: {color}; font-family: {Fonts.TITLE};")
    bl.addWidget(head)

    body = QLabel(text)
    body.setWordWrap(True)
    body.setStyleSheet(
        f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
        f"font-family: {Fonts.BODY}; line-height: 1.8;")
    bl.addWidget(body)
    return box


def suggestion_block(items, color=Colors.SUCCESS) -> QWidget:
    """核心建议高亮块：绿边 + 浅绿底 + 「💡 核心建议」标题 + 逐条列表。

    用于龙虎山大师兄的 scenario_advice，从普通列表卡片中提升为独立强调块。
    """
    box = QFrame()
    box.setStyleSheet(f"""
        QFrame {{
            background: {_glow(color)};
            border-left: 6px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    bl = QVBoxLayout(box)
    bl.setContentsMargins(14, 12, 14, 12)
    bl.setSpacing(8)

    head = QLabel('💡 核心建议')
    head.setStyleSheet(
        f"font-size: {Fonts.SZ_SECTION}; font-weight: {Fonts.W_BOLD}; "
        f"color: {color}; font-family: {Fonts.TITLE};")
    bl.addWidget(head)

    if isinstance(items, str):
        items = [items]
    for item in items or []:
        if not item or not str(item).strip():
            continue
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)
        dot = QLabel('•')
        dot.setStyleSheet(
            f"color: {color}; font-size: {Fonts.SZ_BODY}; "
            f"font-weight: {Fonts.W_BOLD}; font-family: {Fonts.BODY};")
        dot.setFixedWidth(14)
        dot.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        txt = QLabel(str(item).strip())
        txt.setWordWrap(True)
        txt.setStyleSheet(
            f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
            f"font-family: {Fonts.BODY}; line-height: 1.7;")
        rl.addWidget(dot)
        rl.addWidget(txt, 1)
        bl.addWidget(row)
    return box


# 风险关键词：命中即视为风险提示行
_RISK_KEYWORDS = ('忌', '避', '凶', '慎', '危', '不宜', '切忌', '规避', '少', '减', '防', '勿', '禁')


def risk_aware_label(text: str, color=Colors.LIUJIN) -> QWidget:
    """重点提示块（升级版 highlight_label）：自带头「【重点提示】」标题；

    将文本按换行切分，含风险关键词的行渲染为红字 + ⚠ 前缀 + 左侧红色细条子块，
    其余行正常显示。无风险词时退化为与普通高亮块一致。
    """
    container = QFrame()
    container.setStyleSheet(f"""
        QFrame {{
            background: {Colors.LIUJIN_GLOW};
            border-left: 4px solid {color};
            border-radius: {Spacing.RADIUS_SM};
        }}
    """)
    cl = QVBoxLayout(container)
    cl.setContentsMargins(12, 10, 12, 10)
    cl.setSpacing(8)

    title = QLabel('⭐ 【重点提示】')
    title.setStyleSheet(
        f"font-size: {Fonts.SZ_BODY}; font-weight: {Fonts.W_MEDIUM}; "
        f"color: {color}; font-family: {Fonts.BODY};")
    cl.addWidget(title)

    if isinstance(text, (list, tuple)):
        lines = [str(x) for x in text if x and str(x).strip()]
    else:
        lines = [ln for ln in str(text).split('\n') if ln.strip()]

    for ln in lines:
        ln = ln.strip()
        if any(kw in ln for kw in _RISK_KEYWORDS):
            sub = QFrame()
            sub.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.DANGER_LIGHT};
                    border-left: 3px solid {Colors.DANGER};
                    border-radius: {Spacing.RADIUS_SM};
                }}
            """)
            sl = QHBoxLayout(sub)
            sl.setContentsMargins(8, 6, 8, 6)
            sl.setSpacing(6)
            warn = QLabel('⚠')
            warn.setStyleSheet(f"font-size: {Fonts.SZ_SMALL}; color: {Colors.DANGER};")
            warn.setFixedWidth(16)
            warn.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            rt = QLabel(ln)
            rt.setWordWrap(True)
            rt.setStyleSheet(
                f"font-size: {Fonts.SZ_BODY}; color: {Colors.DANGER}; "
                f"font-family: {Fonts.BODY}; line-height: 1.6;")
            sl.addWidget(warn)
            sl.addWidget(rt, 1)
            cl.addWidget(sub)
        else:
            t = QLabel(ln)
            t.setWordWrap(True)
            t.setStyleSheet(
                f"font-size: {Fonts.SZ_BODY}; color: {Colors.TEXT}; "
                f"font-family: {Fonts.BODY}; line-height: 1.6;")
            cl.addWidget(t)
    return container
