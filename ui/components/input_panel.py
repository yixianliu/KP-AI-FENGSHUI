"""
左侧输入面板 - 极简轻量国风
垂直表单 · 圆角控件 · 朱砂红主按钮 · 白底灰框副按钮
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QPushButton, QFrame, QButtonGroup,
                             QDateEdit, QTextEdit, QScrollArea, QSpinBox,
                             QStackedWidget, QDoubleSpinBox, QSizePolicy)
from PySide6.QtCore import QDate, QEvent, Qt, Signal
from ui.styles import Stylesheets, Colors, Fonts, Spacing
from ui.components.collapsible_card import CollapsibleCard
import logging

logger = logging.getLogger(__name__)

# 城市坐标表的唯一来源在 service/location_resolver.py：
# 面板下拉与排盘主路径解析共用同一份数据，避免两处维护导致坐标漂移。
from service.location_resolver import CITY_COORDS

# 经纬度有效范围（与 Service / core 层校验口径一致）
LON_MIN, LON_MAX = -180.0, 180.0
LAT_MIN, LAT_MAX = -90.0, 90.0

HOUR_NAMES = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时',
              '午时', '未时', '申时', '酉时', '戌时', '亥时']
HOUR_RANGES = [(23,1),(1,3),(3,5),(5,7),(7,9),(9,11),(11,13),(13,15),(15,17),(17,19),(19,21),(21,23)]

# 农历月份显示名（1~12 月，正月在前）与日期显示名（初一~三十）
LUNAR_MONTH_NAMES = ['正月', '二月', '三月', '四月', '五月', '六月',
                     '七月', '八月', '九月', '十月', '冬月', '腊月']
LUNAR_DAY_NAMES = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八',
                   '初九', '初十', '十一', '十二', '十三', '十四', '十五', '十六',
                   '十七', '十八', '十九', '二十', '廿一', '廿二', '廿三', '廿四',
                   '廿五', '廿六', '廿七', '廿八', '廿九', '三十']

#: 标签列视觉下限：标签列过窄会显得松散，故实测值小于 48 时仍取 48
LABEL_MIN_WIDTH = Spacing.S8
#: 实测最宽文案后的安全余量，吸收字体渲染舍入与 DPI 取整
LABEL_SAFETY_MARGIN = Spacing.S1


def form_label_style(color=None):
    """返回表单标签的 QSS 样式（单一来源，供标签与其字体度量使用）。"""
    return f"""
        font-size: {Fonts.SZ_SMALL};
        color: {color or Colors.TEXT2};
        font-family: {Fonts.BODY};
    """


def label_width_for(texts, metrics):
    """按当前字体实测标签文案集合的宽度，返回列宽。

    Args:
        texts: 该面板全部标签文案（显式传入，不遍历控件猜测）。
        metrics: 当前字体的 QFontMetrics（须由已应用 QSS 的标签提供）。

    Returns:
        int: max(最宽文案 + 安全余量, 48px 视觉下限)。
    """
    need = max(metrics.horizontalAdvance(t) for t in texts)
    return max(need + LABEL_SAFETY_MARGIN, LABEL_MIN_WIDTH)


def refresh_form_labels(labels):
    """字体变化后按新字体重新计算并应用标签列宽。"""
    for lb in labels:
        lb.refresh_width()


class FormLabel(QLabel):
    """表单左侧定宽标签：宽度随实测字体自适应，不再使用固定魔法值。

    宽度取「该面板全部标签文案的最宽实测值 + 安全余量」，字体被替换
    （QSS 改字号、系统字体变化、DPI 缩放）时会在 changeEvent 中重算并
    setFixedWidth，避免 100% 缩放下测试通过、用户机器上却截断。
    """

    def __init__(self, text, texts, color=None, parent=None):
        """
        Args:
            text: 本行标签文字。
            texts: 所在面板全部标签文案集合，用于取最宽值统一列宽。
            color: 文字颜色；None 使用次级灰 TEXT2。
            parent: Qt 父控件。
        """
        super().__init__(text, parent)
        self._texts = tuple(texts)
        self.setStyleSheet(form_label_style(color))
        # 先应用 QSS 字体再度量，避免用默认字体算出偏窄的初始宽度
        self.ensurePolished()
        self.refresh_width()

    def refresh_width(self):
        """按当前字体度量重算列宽并应用。"""
        self.setFixedWidth(label_width_for(self._texts, self.fontMetrics()))

    def changeEvent(self, event):
        """字体或样式变化时重算列宽（覆盖换字体 / DPI / 主题字号变更）。"""
        super().changeEvent(event)
        if event.type() in (QEvent.FontChange, QEvent.StyleChange):
            self.refresh_width()


def form_label(text, color=None, texts=None):
    """生成表单左侧自适应定宽说明标签（八字 / 梅花 / 玄空三块面板共用）。

    Args:
        text: 标签文字。
        color: 文字颜色；None 时使用次级灰 TEXT2。
        texts: 所在面板全部标签文案；缺省按单条文案计算。

    Returns:
        FormLabel: 宽度由实测字体决定的标签，保证各行输入控件左边缘严格对齐。
    """
    return FormLabel(text, texts or (text,), color)


def build_action_bar(submit_btn, reset_btn):
    """构建吸底操作条：1px 上分隔线 + 主按钮（伸展）/ 次按钮（最小宽 96）。

    三块输入面板共用同一实现，保证按钮尺寸、内边距与分隔线一致。
    调用方只需把它 addWidget 到面板最外层 QVBoxLayout 末尾，
    即可让操作按钮脱离滚动容器，在任何窗口高度下恒定可见。

    Args:
        submit_btn: 主操作按钮（由主窗口连接业务槽）。
        reset_btn: 重置按钮。

    Returns:
        QFrame: 已装好按钮与布局的吸底操作条。
    """
    bar = QFrame()
    bar.setObjectName('input_action_bar')
    bar.setStyleSheet(
        f"QFrame#input_action_bar {{"
        f" background-color: {Colors.BG};"
        f" border: none;"
        f" border-top: 1px solid {Colors.DIVIDER};"
        f" }}")
    row = QHBoxLayout(bar)
    row.setContentsMargins(Spacing.S6, Spacing.S2, Spacing.S6, Spacing.S2)
    row.setSpacing(Spacing.S3)
    reset_btn.setMinimumWidth(Spacing.S8 * 2)
    row.addWidget(submit_btn, 1)
    row.addWidget(reset_btn)
    return bar


#: 农历年信息缓存：{农历年: {'leap': 闰月月份(0=无闰月), 'days': {(月, 是否闰月): 天数}}}
#: 闰月有无与每月 29/30 天均由 lunarcalendar 真实历表校验得出，按年缓存避免重复构造。
_LUNAR_YEAR_INFO_CACHE = {}


def lunar_year_info(year):
    """查询某个农历年的闰月月份与各月实际天数（带缓存）。

    Args:
        year: 农历年（1900~2100）。

    Returns:
        dict: ``{'leap': 闰月月份(1~12，0 表示该年无闰月),
                'days': {(month, is_leap): 29 或 30}}``。
        缺少 lunarcalendar 依赖时降级为一律 30 天且无闰月，只影响可选范围，不影响换算。
    """
    year = int(year)
    cached = _LUNAR_YEAR_INFO_CACHE.get(year)
    if cached is not None:
        return cached

    leap = 0
    days = {}
    try:
        from lunarcalendar import Lunar
    except ImportError:  # pragma: no cover - 正常环境必有该依赖
        info = {'leap': 0,
                'days': {(m, False): 30 for m in range(1, 13)}}
        _LUNAR_YEAR_INFO_CACHE[year] = info
        return info

    def _exists(month, day, is_leap):
        """该农历日期是否真实存在（lunarcalendar 构造时即严格校验）。"""
        try:
            Lunar(year, month, day, is_leap)
        except Exception:
            return False
        return True

    # 先确定闰月：全年至多一个闰月
    for m in range(1, 13):
        if _exists(m, 1, True):
            leap = m
            break
    for m in range(1, 13):
        days[(m, False)] = 30 if _exists(m, 30, False) else 29
    if leap:
        days[(leap, True)] = 30 if _exists(leap, 30, True) else 29

    info = {'leap': leap, 'days': days}
    _LUNAR_YEAR_INFO_CACHE[year] = info
    return info


class LunarDatePicker(QWidget):
    """农历「年 / 农历月 / 农历日」三组选择器（支持闰月，公历模式不使用）。

    交互约定：
      - 月份列表按「正月、二月…腊月」排列，仅在该年真实存在闰月时插入「闰X月」，
        且紧随同号平月之后；非闰月年份不出现任何「闰」项。
      - 切换年份后若原先选中的闰月不存在，自动回落到同号平月，并在下方提示，
        绝不静默改成别的月份。
      - 日期下拉只给出该农历月真实天数（29 或 30），越界（如 31 日）不可选。
    """

    #: 用户修改了年/月/日（用于上游刷新展示与校验）
    changed = Signal()

    def __init__(self, parent=None):
        """
        Args:
            parent: Qt 父控件。
        """
        super().__init__(parent)
        today = QDate.currentDate()
        self._year = today.year()
        self._month = 1
        self._leap = False
        self._day = 1
        self._syncing = False   # 程序回写期间置位，阻断信号递归
        self._build()
        # 默认值取「今天」对应的农历日期，保证切到农历时不是空白/陈旧值
        self.set_from_solar_date(today.year(), today.month(), today.day())

    def _build(self):
        """构建三组选择器 + 回落提示标签，并接线信号。

        年 / 月 / 日原为同一横排，三控件最小宽合计约 328px，在 1000×700
        的窄左栏（视口约 338px，扣除卡片内边距后每行可用约 244px）必然
        横向溢出。改为「年一行、月+日一行」两行堆叠，控件尺寸不变。
        """
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(Spacing.S1)

        year_row = QHBoxLayout()
        year_row.setSpacing(Spacing.S2)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 2100)
        self.year_spin.setSuffix(' 年')
        self.year_spin.setValue(self._year)
        # 104px：扣除 QSS 左右内边距与 12px 上下按钮后，仍能完整显示「2026 年」
        self.year_spin.setFixedWidth(Spacing.S8 * 2 + Spacing.S2)
        self.year_spin.setStyleSheet(Stylesheets.INPUT)

        self.month_combo = QComboBox()
        self.month_combo.setStyleSheet(Stylesheets.COMBO)
        # 88px 下限：QSS 左右内边距 + 箭头共占 42px，88px 仍可完整显示最长的
        # 「闰七月」(实测 39px)。不设下限时 QComboBox 的默认最小尺寸按其最长项
        # 计算为 102px，两个并列会把整行最小宽撑到 212px，使 900px 窗口下的
        # 视口（约 308px）仅剩 2px 余量；压到 88px 后最小行宽 184px，余量 30px。
        self.month_combo.setMinimumWidth(Spacing.S8 + Spacing.S7 + Spacing.S2)  # 88
        self.day_combo = QComboBox()
        self.day_combo.setStyleSheet(Stylesheets.COMBO)
        self.day_combo.setMinimumWidth(Spacing.S8 + Spacing.S7 + Spacing.S2)    # 88

        year_row.addWidget(self.year_spin)
        year_row.addStretch()
        outer.addLayout(year_row)

        # 月 / 日各自伸展，平分整行宽度（窄栏下仍能完整显示「闰七月」「三十」）
        md_row = QHBoxLayout()
        md_row.setSpacing(Spacing.S2)
        md_row.addWidget(self.month_combo, 1)
        md_row.addWidget(self.day_combo, 1)
        outer.addLayout(md_row)

        self.hint = QLabel('')
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet(
            f"font-size: {Fonts.SZ_MICRO}; color: {Colors.SEMANTIC_WARNING};"
            f" font-family: {Fonts.BODY};")
        self.hint.hide()
        outer.addWidget(self.hint)

        self._rebuild_months(self._month, self._leap)
        self._rebuild_days(self._day)

        self.year_spin.valueChanged.connect(self._on_year_changed)
        self.month_combo.currentIndexChanged.connect(self._on_month_changed)
        self.day_combo.currentIndexChanged.connect(self._on_day_changed)

    # ------------------------------------------------------------------ 内部
    def _build_month_items(self):
        """按该年真实闰月生成 (月, 是否闰月) 列表，闰月紧随同号平月。"""
        info = lunar_year_info(self.year_spin.value())
        items = []
        for m in range(1, 13):
            items.append((m, False))
            if info['leap'] == m:
                items.append((m, True))
        return items

    def _rebuild_months(self, prefer_month, prefer_leap):
        """重建月份下拉，并尽量保持原选中项。

        Args:
            prefer_month: 期望保持的农历月（1~12）。
            prefer_leap: 期望保持的是否为闰月。

        Returns:
            bool: True 表示期望的闰月在该年不存在、已回落到同号平月（需提示）。
        """
        self._year = self.year_spin.value()
        self.month_combo.blockSignals(True)
        self.month_combo.clear()
        for m, leap in self._build_month_items():
            text = ('闰' if leap else '') + LUNAR_MONTH_NAMES[m - 1]
            self.month_combo.addItem(text, (m, leap))

        target = -1
        for i in range(self.month_combo.count()):
            if self.month_combo.itemData(i) == (prefer_month, prefer_leap):
                target = i
                break
        fell_back = target < 0
        if fell_back:
            for i in range(self.month_combo.count()):
                if self.month_combo.itemData(i) == (prefer_month, False):
                    target = i
                    break
        if target < 0:
            target = 0
        self.month_combo.setCurrentIndex(target)
        self.month_combo.blockSignals(False)
        self._month, self._leap = self.month_combo.itemData(target)
        return fell_back

    def _month_days(self):
        """当前农历年月的实际天数（29 或 30）。

        P2-12：原实现 ``days.get(key, 30)`` 在历表缺项时默认 30，会让 29 天月份的
        「三十日」被放行并一路传到换算层。现改为缺项时按 29 处理并留痕——宁可少给
        一天，也不能凭空造出不存在的日期。
        """
        info = lunar_year_info(self._year)
        days = info['days'].get((self._month, self._leap))
        if days not in (29, 30):
            logger.warning(
                '[农历] 历表缺少 %s 年 %s月%s 的天数，按 29 天处理（不得放行三十日）',
                self._year, self._month, '（闰）' if self._leap else '')
            days = 29
        return days

    def _rebuild_days(self, prefer_day):
        """按当前农历月天数重建日期下拉，超出上限的值自动钳制到当月最后一天。"""
        days = self._month_days()
        self._day = max(1, min(int(prefer_day), days))
        self.day_combo.blockSignals(True)
        self.day_combo.clear()
        for d in range(1, days + 1):
            self.day_combo.addItem(LUNAR_DAY_NAMES[d - 1], d)
        self.day_combo.setCurrentIndex(self._day - 1)
        self.day_combo.blockSignals(False)

    # ------------------------------------------------------------------ 槽
    def _on_year_changed(self, value):
        """年份变更：重建月份（闰月随年份增减），必要时回落并提示。"""
        if self._syncing:
            return
        old_month, old_leap, old_day = self._month, self._leap, self._day
        fell_back = self._rebuild_months(old_month, old_leap)
        self._rebuild_days(old_day)
        if fell_back:
            self.hint.setText(
                f'{value} 年没有闰{LUNAR_MONTH_NAMES[old_month - 1]}，'
                f'已回落到{LUNAR_MONTH_NAMES[self._month - 1]}')
            self.hint.show()
        else:
            self.hint.hide()
        self.changed.emit()

    def _on_month_changed(self, *_):
        """月份变更：按该月天数重建日期下拉。"""
        if self._syncing:
            return
        data = self.month_combo.currentData()
        if data:
            self._month, self._leap = data
        self._rebuild_days(self._day)
        self.hint.hide()
        self.changed.emit()

    def _on_day_changed(self, *_):
        """日期变更：仅更新内部状态并通知上游。"""
        if self._syncing:
            return
        idx = self.day_combo.currentIndex()
        if idx >= 0:
            self._day = self.day_combo.itemData(idx) or (idx + 1)
        self.changed.emit()

    # ------------------------------------------------------------------ 公共
    def set_lunar(self, year, month, day, is_leap=False):
        """程序化设置农历日期（越界日期按当月上限钳制，闰月不存在则回落平月）。"""
        self._syncing = True
        self.year_spin.setValue(max(1900, min(2100, int(year))))
        want_month, want_leap = int(month), bool(is_leap)
        fell_back = self._rebuild_months(want_month, want_leap)
        self._rebuild_days(int(day))
        self._syncing = False
        if fell_back:
            self.hint.setText(
                f'{self._year} 年没有闰{LUNAR_MONTH_NAMES[want_month - 1]}，'
                f'已回落到{LUNAR_MONTH_NAMES[self._month - 1]}')
            self.hint.show()
        else:
            self.hint.hide()
        self.changed.emit()

    def set_from_solar_date(self, year, month, day):
        """以公历日期初始化本控件（自动换算为含闰月标志的农历日期）。"""
        try:
            from datetime import date

            from lunarcalendar import Lunar
            lunar = Lunar.from_date(date(int(year), int(month), int(day)))
            self.set_lunar(lunar.year, lunar.month, lunar.day, bool(lunar.isleap))
        except Exception:
            # 依赖缺失或公历日期非法：仅按数字保守初始化（换算环节仍会严格校验）
            self.set_lunar(year, month, day, False)

    def lunar_date(self):
        """返回当前选择：``(农历年, 农历月, 农历日, 是否闰月)``。"""
        return (self._year, self._month, self._day, self._leap)

    def is_leap(self):
        """当前选择是否为闰月。"""
        return self._leap


def hour_to_index(hour: int) -> int:
    """T3.2 由小时数换算时辰索引（0=子时 … 11=亥时）。

    时辰以 2 小时为一格且子时跨日（23:00~01:00），故先把 23 点折算到 -1
    再看落在哪一格：((h + 1) // 2) % 12 即覆盖全部 24 小时且天然处理跨日。

    Args:
        hour: 小时数（0~23）

    Returns:
        int: 时辰索引
    """
    return ((int(hour) + 1) // 2) % 12

PAN_TYPES = [
    ('bazi','八字四柱'),('ziwei','紫微斗数'),('qimen','奇门遁甲'),
    ('liuyao','六爻纳甲'),('yangzhai','阳宅风水'),('yinning','阴宅风水'),
]


class InputPanel(QWidget):
    """八字排盘输入面板（主窗口左栏）。

    负责收集姓名、历法、日期、时辰、出生地、性别、流派、备注等排盘要素，
    由 get_data() 打包成 dict 交给 core 层排盘；面板自身不做任何命理计算。

    与主窗口的交互约定：
      - submit_btn / reset_btn 由主窗口连接到「排盘」「重置」槽函数；
      - 输入不合法时 submit_btn 自动置灰，见 _validate()。
    """

    #: 本面板全部标签文案：显式清单决定标签列宽（不遍历控件猜测）
    LABEL_TEXTS = ('姓名', '历法', '日期', '时辰', '性别', '类型', '出生地',
                   '城市', '经度', '纬度', '流派', '原始出生时间', '当前时辰',
                   '经度基准')

    def __init__(self, parent=None):
        """
        Args:
            parent: Qt 父控件。
        """
        super().__init__(parent)
        self._form_labels = []           # 已创建的标签，字体变化时统一重算宽度
        self.selected_hour = 6           # 时辰索引，默认 6 = 午时（11:00~13:00）
        self.selected_pan_type = 'bazi'  # 本标签页固定为八字四柱，保留字段供下游读取
        self._lunar_initialized = False  # 农历控件是否已按当前日期初始化过
        self._syncing_coords = False     # 程序回写经纬度期间置位，避免与城市联动互触
        self._coords_touched = False     # 用户是否显式指定过经纬度（城市选择/手改=True，程序回填=False）
        self._build()

    def _build(self):
        """构建表单界面并接线信号。

        结构：外层垂直布局 = QScrollArea（标题 -> 分割线 -> 4 张卡片）+ 吸底操作条。
        窗口拉窄/变矮时表单内容滚动，操作按钮始终固定可见。
        末尾创建的 lng_edit / lat_edit / day_night_switch / true_solar_switch 是历史遗留
        的兼容字段，仍有下游代码按属性名读取，因此保留对象但设为不可见。
        """
        self.setStyleSheet(f"background-color: {Colors.BG};")

        scroll = QScrollArea()
        scroll.setStyleSheet(Stylesheets.SCROLL)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.BG};")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(Spacing.S6, Spacing.S5, Spacing.S6, Spacing.S5)
        lay.setSpacing(Spacing.S4)

        # 标题
        hdr = QHBoxLayout()
        hdr.setSpacing(Spacing.S2)
        icon = QLabel('☯')
        icon.setStyleSheet(f"font-size: 13px; color: {Colors.LIUJIN};")
        title = QLabel('风水排盘参数')
        title.setStyleSheet(f"""
            font-size: {Fonts.SZ_SECTION};
            font-weight: {Fonts.W_BOLD};
            color: {Colors.TEXT};
            font-family: {Fonts.TITLE};
        """)
        hdr.addWidget(icon)
        hdr.addWidget(title)
        hdr.addStretch()
        lay.addLayout(hdr)

        # 青蓝分割线
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.QINGHUA_LIGHT};")
        lay.addWidget(div)

        # ===== 基本信息分组（姓名 / 历法 / 日期 / 时辰时间 / 性别 / 类型） =====
        basic_card = CollapsibleCard('基本信息', '☯', accent_color=Colors.QINGHUA, collapsed=False)
        basic_body = QWidget()
        basic_body.setStyleSheet("background: transparent;")
        basic_lay = QVBoxLayout(basic_body)
        basic_lay.setContentsMargins(Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM)
        basic_lay.setSpacing(Spacing.S3)

        # 姓名
        col, row = self._field('姓名')
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(Stylesheets.INPUT)
        self.name_edit.setPlaceholderText('请输入姓名')
        row.addWidget(self.name_edit, 1)
        basic_lay.addLayout(col)

        # 历法
        col, row = self._field('历法')
        self.solar_btn = QPushButton('公历')
        self.solar_btn.setStyleSheet(Stylesheets.BTN_SWITCH)
        self.solar_btn.setCheckable(True)
        self.solar_btn.setChecked(True)
        self.solar_btn.setCursor(Qt.PointingHandCursor)
        self.lunar_btn = QPushButton('农历')
        self.lunar_btn.setStyleSheet(Stylesheets.BTN_SWITCH)
        self.lunar_btn.setCheckable(True)
        self.lunar_btn.setCursor(Qt.PointingHandCursor)
        row.addWidget(self.solar_btn)
        row.addWidget(self.lunar_btn)
        row.addStretch()
        basic_lay.addLayout(col)

        # 日期：公历日历 / 农历「年·月·日」双页切换（农历页含闰月与日期上限约束）
        # 标签已由 _field 统一放在上方，两个内页不再各自重复一个「日期」标签
        col, row = self._field('日期')
        self.date_stack = QStackedWidget()
        self.date_stack.setStyleSheet('background: transparent;')

        solar_page = QWidget()
        solar_page.setStyleSheet('background: transparent;')
        solar_row = QHBoxLayout(solar_page)
        solar_row.setContentsMargins(0, 0, 0, 0)
        solar_row.setSpacing(Spacing.S2)
        self.date_edit = QDateEdit()
        self.date_edit.setStyleSheet(Stylesheets.DATE)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        solar_row.addWidget(self.date_edit, 1)
        self.date_stack.addWidget(solar_page)

        lunar_page = QWidget()
        lunar_page.setStyleSheet('background: transparent;')
        lunar_row = QHBoxLayout(lunar_page)
        lunar_row.setContentsMargins(0, 0, 0, 0)
        lunar_row.setSpacing(Spacing.S2)
        self.lunar_picker = LunarDatePicker()
        lunar_row.addWidget(self.lunar_picker, 1)
        self.date_stack.addWidget(lunar_page)

        row.addWidget(self.date_stack, 1)
        basic_lay.addLayout(col)

        # T3.2 时辰 / 时间：时辰下拉（快速选）+ 时分双输入（精确调）+ 实时时辰映射
        col, row = self._field('时辰')
        self.hour_combo = QComboBox()
        self.hour_combo.setStyleSheet(Stylesheets.COMBO)
        # 旧文案「午时 (11:00~13:00)」默认最小宽 286px、实测文本 208px，
        # 会独自撑破窄栏；现改为紧凑文案 + 按内容长度收缩，
        # 实际宽度仍由 stretch=1 撑满整行。
        self.hour_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.hour_combo.setMinimumContentsLength(2)
        self.hour_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for i, n in enumerate(HOUR_NAMES):
            # 项文案取紧凑写法「午时 11~13点」：带括号的完整写法实测 208px，
            # 在 900px 窗口（左栏视口约 308px，行内可用 172px）会被裁掉尾部。
            # 起止整点信息不丢失，完整写法仍由下方 time_label 展示。
            self.hour_combo.addItem(
                f'{n} {HOUR_RANGES[i][0]:02d}~{HOUR_RANGES[i][1]:02d}点', i)
        self.hour_combo.setCurrentIndex(6)
        row.addWidget(self.hour_combo, 1)
        basic_lay.addLayout(col)

        # 时 / 分 双 SpinBox：替代原单文本 time_edit，杜绝手填非法格式
        col, row = self._field('时分')
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(12)
        self.hour_spin.setSuffix(' 时')
        # 84px：QSS 左右内边距 + 12px 上下按钮后仍能完整显示「12 时 / 59 分」
        self.hour_spin.setFixedWidth(Spacing.S8 * 2 - Spacing.S3)
        self.hour_spin.setStyleSheet(Stylesheets.INPUT)
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(0)
        self.minute_spin.setSuffix(' 分')
        # 与小时微调框同宽，保证「时 / 分」两列视觉等宽
        self.minute_spin.setFixedWidth(Spacing.S8 * 2 - Spacing.S3)
        self.minute_spin.setStyleSheet(Stylesheets.INPUT)
        row.addWidget(self.hour_spin)
        row.addWidget(self.minute_spin)
        row.addStretch()
        basic_lay.addLayout(col)

        # 实时时辰映射标签：随时分变化显示「午时 (11:00~13:00)」。
        # 独立成行并允许自动换行，避免与上方下拉/双微调争夺横向空间导致截断。
        self.time_label = QLabel()
        self.time_label.setStyleSheet(
            f"font-size:{Fonts.SZ_SMALL}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};"
        )
        self.time_label.setWordWrap(True)
        tl_row = QHBoxLayout()
        tl_row.setContentsMargins(0, 0, 0, 0)
        tl_row.setSpacing(Spacing.S2)
        # 标签已纵向堆叠，本行无需占位标签，独占整行宽度
        tl_row.addWidget(self.time_label, 1)
        basic_lay.addLayout(tl_row)

        # 性别
        col, row = self._field('性别')
        self.gender_grp = QButtonGroup(self)
        self.male_btn = QPushButton('♂ 男')
        self.male_btn.setStyleSheet(Stylesheets.BTN_SWITCH)
        self.male_btn.setCheckable(True)
        self.male_btn.setChecked(True)
        self.male_btn.setCursor(Qt.PointingHandCursor)
        self.female_btn = QPushButton('♀ 女')
        self.female_btn.setStyleSheet(Stylesheets.BTN_SWITCH)
        self.female_btn.setCheckable(True)
        self.female_btn.setCursor(Qt.PointingHandCursor)
        self.gender_grp.addButton(self.male_btn, 0)
        self.gender_grp.addButton(self.female_btn, 1)
        row.addWidget(self.male_btn)
        row.addWidget(self.female_btn)
        row.addStretch()
        basic_lay.addLayout(col)

        # 类型徽章（八字标签类型固定，避免误导）
        col, row = self._field('类型')
        type_badge = QLabel('八字四柱')
        type_badge.setCursor(Qt.PointingHandCursor)
        type_badge.setToolTip(
            '本程序当前支持的排盘类型：八字四柱、梅花易数。\n'
            '当前位于「八字排盘」标签，类型固定为八字四柱。'
        )
        type_badge.setStyleSheet(f"""
            background: {Colors.QINGHUA_GLOW};
            color: {Colors.QINGHUA};
            border: 1px solid {Colors.QINGHUA_LIGHT};
            border-radius: {Spacing.RADIUS_SM};
            font-size: 12px;
            font-weight: {Fonts.W_MEDIUM};
            font-family: {Fonts.BODY};
            padding: 5px 16px;
        """)
        row.addWidget(type_badge)
        row.addStretch()
        basic_lay.addLayout(col)

        basic_card.set_content(basic_body)
        lay.addWidget(basic_card)

        # ===== 地点与偏好分组（出生地 / 流派） =====
        pref_card = CollapsibleCard('地点与偏好', '◎', accent_color=Colors.QINGHUA, collapsed=False)
        pref_body = QWidget()
        pref_body.setStyleSheet("background: transparent;")
        pref_lay = QVBoxLayout(pref_body)
        pref_lay.setContentsMargins(Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM)
        pref_lay.setSpacing(Spacing.S3)

        # 出生地（手动文本，仅作记录与备注；经纬度以下方输入为准）
        col, row = self._field('出生地')
        self.location_edit = QLineEdit()
        self.location_edit.setStyleSheet(Stylesheets.INPUT)
        self.location_edit.setPlaceholderText('如：北京市朝阳区 / 纽约 / 洛杉矶（仅作记录，经纬度请填下方）')
        row.addWidget(self.location_edit, 1)
        pref_lay.addLayout(col)

        # 城市快捷选择：选中后自动写入经度/纬度；手改经纬度则回到「自定义」
        col, row = self._field('城市')
        self.city_combo = QComboBox()
        self.city_combo.setStyleSheet(Stylesheets.COMBO)
        # 最长项「乌鲁木齐（87.62°E, 43.79°N）」默认最小宽 377px，会撑破窄栏；
        # 按内容长度收缩后，实际宽度仍由 stretch=1 撑满整行。
        self.city_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.city_combo.setMinimumContentsLength(2)
        self.city_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.city_combo.addItem('自定义', None)
        # 项文本只放城市名：带括号坐标的完整写法最长实测 299px，在 900~1200px
        # 窗口的左栏（行内可用 172~272px）必然被裁切。坐标不丢，放到该项的
        # ToolTipRole，下拉悬停与选中后的控件 tooltip 都能看到完整经纬度。
        for city_name, city_lon, city_lat in CITY_COORDS:
            idx = self.city_combo.count()
            self.city_combo.addItem(city_name, (city_lon, city_lat))
            self.city_combo.setItemData(
                idx, f'经度 {city_lon:.2f}°E，纬度 {city_lat:.2f}°N',
                Qt.ItemDataRole.ToolTipRole)
        self.city_combo.setToolTip('自定义：使用下方填写的经纬度')
        row.addWidget(self.city_combo, 1)
        pref_lay.addLayout(col)

        # 经度：参与真太阳时校正（经度差 1° ≈ 4 分钟时差）
        col, row = self._field('经度')
        self.lng_spin = QDoubleSpinBox()
        self.lng_spin.setRange(LON_MIN, LON_MAX)
        self.lng_spin.setDecimals(2)
        self.lng_spin.setSingleStep(0.1)
        self.lng_spin.setValue(120.00)
        self.lng_spin.setSuffix(' °')
        self.lng_spin.setStyleSheet(Stylesheets.INPUT)
        row.addWidget(self.lng_spin, 1)
        pref_lay.addLayout(col)

        # 纬度：真太阳时只依赖经度，纬度仅随记录保存，供历史回填
        col, row = self._field('纬度')
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(LAT_MIN, LAT_MAX)
        self.lat_spin.setDecimals(2)
        self.lat_spin.setSingleStep(0.1)
        self.lat_spin.setValue(30.00)
        self.lat_spin.setSuffix(' °')
        self.lat_spin.setStyleSheet(Stylesheets.INPUT)
        row.addWidget(self.lat_spin, 1)
        pref_lay.addLayout(col)

        # 流派
        col, row = self._field('流派')
        self.school_combo = QComboBox()
        self.school_combo.setStyleSheet(Stylesheets.COMBO)
        self.school_combo.addItems(['子平真诠', '滴天髓', '三命通会'])
        row.addWidget(self.school_combo, 1)
        pref_lay.addLayout(col)

        pref_card.set_content(pref_body)
        lay.addWidget(pref_card)

        # ===== 时间校准分组（6.1.3：默认折叠，展示出生时间与经度说明） =====
        # 输入面板不做任何命理计算（零功能变更），真太阳时由排盘引擎内部依据
        # 经度与节气校正；此处仅展示原始输入时间、经度基准与校正说明。
        self._ts_time_label = QLabel()
        self._ts_time_label.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; color:{Colors.TEXT}; font-family:{Fonts.BODY};")
        self._ts_hour_label = QLabel()
        self._ts_hour_label.setStyleSheet(
            f"font-size:{Fonts.SZ_BODY}; color:{Colors.LIUJIN}; font-family:{Fonts.BODY};")
        self._ts_note = QLabel(
            '真太阳时由排盘引擎依据「经度」校正：经度差 1° 约 4 分钟，'
            '西部城市与东八区标准经度 120°E 的差异可达 2 小时以上。'
            '请在「地点与偏好」中选择城市或直接填写经纬度；纬度仅随记录保存。')
        self._ts_note.setStyleSheet(
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
        self._ts_note.setWordWrap(True)

        ts_card = CollapsibleCard('时间校准', '◷', accent_color=Colors.YU, collapsed=True)
        ts_body = QWidget()
        ts_body.setStyleSheet("background: transparent;")
        ts_lay = QVBoxLayout(ts_body)
        ts_lay.setContentsMargins(Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM)
        ts_lay.setSpacing(Spacing.S2)
        ts_lay.addWidget(self._label('原始出生时间'))
        ts_lay.addWidget(self._ts_time_label)
        ts_lay.addWidget(self._label('当前时辰'))
        ts_lay.addWidget(self._ts_hour_label)
        ts_lay.addWidget(self._label('经度基准'))
        self._ts_lng_label = QLabel()
        self._ts_lng_label.setStyleSheet(
            f"font-size:{Fonts.SZ_MICRO}; color:{Colors.TEXT3}; font-family:{Fonts.BODY};")
        self._ts_lng_label.setWordWrap(True)
        ts_lay.addWidget(self._ts_lng_label)
        ts_lay.addWidget(self._ts_note)
        ts_card.set_content(ts_body)
        lay.addWidget(ts_card)
        self._refresh_true_solar()
        # 保留历史遗留兼容字段（仍有下游按属性名读取），但由新卡片驱动展示
        self.true_solar_switch = ts_card

        # ===== 备注分组 =====
        notes_card = CollapsibleCard('备注', '✎', accent_color=Colors.TEXT3, collapsed=False)
        notes_body = QWidget()
        notes_body.setStyleSheet("background: transparent;")
        notes_lay = QVBoxLayout(notes_body)
        notes_lay.setSpacing(Spacing.S2)  # 显式设值：避免继承 Qt 默认 6（非 8-4 体系）
        notes_lay.setContentsMargins(Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM, Spacing.S_PAD_SM)
        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(Stylesheets.TEXT_EDIT)
        self.notes_edit.setPlaceholderText('可选补充…')
        self.notes_edit.setFixedHeight(60)
        notes_lay.addWidget(self.notes_edit)
        notes_card.set_content(notes_body)
        lay.addWidget(notes_card)

        lay.addStretch()

        # 滚动容器只承载表单内容；操作按钮移到外层吸底条，
        # 保证「开始排盘」在任意窗口高度下首屏即可见（无需滚动到底部）。
        scroll.setWidget(content)

        self.submit_btn = QPushButton('开始排盘')
        self.submit_btn.setStyleSheet(Stylesheets.BTN_PRIMARY)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setEnabled(False)
        self.reset_btn = QPushButton('重置')
        self.reset_btn.setStyleSheet(Stylesheets.BTN_SECONDARY)
        self.reset_btn.setCursor(Qt.PointingHandCursor)

        outer = QVBoxLayout(self)
        outer.setSpacing(Spacing.S0)  # 操作条紧贴滚动区，1px 上分隔线即面板分界
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll, 1)
        outer.addWidget(build_action_bar(self.submit_btn, self.reset_btn))

        # 隐藏兼容字段
        self.lng_edit = QLineEdit(); self.lng_edit.setVisible(False)
        self.lat_edit = QLineEdit(); self.lat_edit.setVisible(False)
        self.day_night_switch = QFrame(); self.day_night_switch.setVisible(False)
        # 备注：true_solar_switch 已在「时间校准」卡片构建处指向真实折叠卡，
        # 此处不再用隐藏 QFrame 覆盖，保留属性名供下游读取。

        # 信号
        self.hour_combo.currentIndexChanged.connect(self._on_hour)
        # T3.2 时分 SpinBox 变更 → 反推时辰并回写下拉框（信号屏蔽防循环触发）
        self.hour_spin.valueChanged.connect(self._on_time_spin)
        self.minute_spin.valueChanged.connect(self._on_time_spin)
        self.date_edit.dateChanged.connect(self._refresh_true_solar)
        self.lunar_picker.changed.connect(self._refresh_true_solar)
        self.solar_btn.clicked.connect(self._refresh_true_solar)
        self.lunar_btn.clicked.connect(self._refresh_true_solar)
        # 城市快捷选择 / 经纬度手改：两条路径互相同步
        self.city_combo.currentIndexChanged.connect(self._on_city_selected)
        self.lng_spin.valueChanged.connect(self._on_coord_edited)
        self.lat_spin.valueChanged.connect(self._on_coord_edited)
        self._sync_time_label()
        self._refresh_true_solar()
        self.name_edit.textChanged.connect(self._validate)
        self.solar_btn.clicked.connect(lambda: self._cal(True))
        self.lunar_btn.clicked.connect(lambda: self._cal(False))
        self.male_btn.clicked.connect(lambda: self._gen(True))
        self.female_btn.clicked.connect(lambda: self._gen(False))
        self._validate()

    def _label(self, text):
        """生成表单左侧的定宽说明标签，使各行输入框左边缘严格对齐。

        Args:
            text: 标签文字。

        Returns:
            FormLabel: 宽度由本面板文案集合实测字体宽度决定的次级灰标签。
        """
        lb = form_label(text, Colors.TEXT2, self.LABEL_TEXTS)
        self._form_labels.append(lb)
        return lb

    def _field(self, text):
        """构建「标签在上、控件在下」的字段容器。

        原布局为标签与控件同行，标签列实测 76px 会与控件争宽：在
        1000×700 下左栏视口仅约 338px，同行排布使内容最小宽达 646px，
        出现 308px 横向滚动。改为纵向堆叠后，每行只受视口宽度约束，
        标签列宽（FormLabel 自适应）不再参与横向宽度计算。

        Args:
            text: 标签文案。

        Returns:
            tuple[QVBoxLayout, QHBoxLayout]: 外层垂直布局（已放入标签）
            与下方控件行布局（调用方往里 addWidget）。
        """
        col = QVBoxLayout()
        col.setSpacing(Spacing.S1)   # 4px：标签与控件贴紧，避免纵向过度膨胀
        col.addWidget(self._label(text))
        row = QHBoxLayout()
        row.setSpacing(Spacing.S2)
        col.addLayout(row)
        return col, row

    def changeEvent(self, event):
        """字体变化时按新字体重算所有标签列宽（换字体/DPI 后不裁切）。"""
        super().changeEvent(event)
        if event.type() == QEvent.FontChange:
            refresh_form_labels(self._form_labels)

    def _on_hour(self, i):
        """时辰下拉框变更槽（由 hour_combo.currentIndexChanged 触发）。

        选定时辰后把时间输入框同步为该时辰的起始整点，省去用户手填；用户仍可
        自行改写分钟。改写后立即重新校验，及时更新提交按钮的可用状态。

        Args:
            i: 时辰索引，0=子时 … 11=亥时，与 HOUR_NAMES / HOUR_RANGES 对应。
        """
        self.selected_hour = i
        s, _ = HOUR_RANGES[i]
        # 同步时 SpinBox 为该时辰起始整点（如子时 23 点）；分保持不变
        self.hour_spin.blockSignals(True)
        self.hour_spin.setValue(s)
        self.hour_spin.blockSignals(False)
        self._sync_time_label()
        self._validate()

    def _on_time_spin(self, *_):
        """T3.2 时分 SpinBox 变更槽：反推时辰并同步下拉框与映射标签。

        用户直接调时分时，时辰下拉框需跟着走，否则两处显示会互相矛盾；
        回写前屏蔽 combo 信号，避免与 _on_hour 形成互相触发的死循环。
        """
        idx = hour_to_index(self.hour_spin.value())
        self.selected_hour = idx
        if self.hour_combo.currentIndex() != idx:
            self.hour_combo.blockSignals(True)
            self.hour_combo.setCurrentIndex(idx)
            self.hour_combo.blockSignals(False)
        self._sync_time_label()
        self._validate()

    def _sync_time_label(self):
        """T3.2 刷新实时时辰映射标签（如「午时 (11:00~13:00)」）。"""
        idx = self.selected_hour
        s, e = HOUR_RANGES[idx]
        self.time_label.setText(
            f'{HOUR_NAMES[idx]} ({s:02d}:00~{e:02d}:00)')
        self._refresh_true_solar()

    def _refresh_true_solar(self):
        """6.1.3 刷新「时间校准」折叠卡显示的原始出生时间与时辰。"""
        if not hasattr(self, '_ts_time_label'):
            return
        if self.solar_btn.isChecked():
            cal = '公历'
            d = self.date_edit.date().toString('yyyy-MM-dd')
        else:
            ly, lm, ld, leap = self.lunar_picker.lunar_date()
            cal = '农历'
            d = (f'{ly}年{"闰" if leap else ""}'
                 f'{LUNAR_MONTH_NAMES[lm - 1]}{LUNAR_DAY_NAMES[ld - 1]}')
        hh = self.hour_spin.value()
        mm = self.minute_spin.value()
        self._ts_time_label.setText(f'{cal} {d} {hh:02d}:{mm:02d}')
        idx = self.selected_hour
        s, e = HOUR_RANGES[idx]
        self._ts_hour_label.setText(f'{HOUR_NAMES[idx]}（{s:02d}:00~{e:02d}:00）')
        # 经度基准：展示当前实际使用的经度，避免用户误以为恒为 120°E
        if hasattr(self, '_ts_lng_label'):
            city = self.city_combo.currentText() if self.city_combo.currentIndex() > 0 else '自定义'
            self._ts_lng_label.setText(
                f'{city}：经度 {self.lng_spin.value():.2f}°（参与真太阳时校正），'
                f'纬度 {self.lat_spin.value():.2f}°（仅随记录保存）')

    # ------------------------------------------------------------------ 经纬度联动
    def _on_city_selected(self, index):
        """城市下拉变更槽：把内置坐标写入经度/纬度输入框。

        Args:
            index: 下拉索引；0 为「自定义」，此时不改变已有经纬度。
        """
        data = self.city_combo.itemData(index)
        if not data:
            self._refresh_city_tooltip()
            return
        lon, lat = data
        self._syncing_coords = True
        self.lng_spin.setValue(lon)
        self.lat_spin.setValue(lat)
        self._syncing_coords = False
        self._coords_touched = True      # 用户主动选城市 = 显式坐标，下方地理编码不得覆盖
        self._refresh_city_tooltip()
        # 出生地文本框留空时，顺手填上城市名，便于历史记录识别
        if not self.location_edit.text().strip():
            self.location_edit.setText(self.city_combo.itemText(index))
        self._refresh_true_solar()

    def _refresh_city_tooltip(self):
        """按当前选中项刷新城市下拉的 tooltip（项文本只有城市名，坐标放这里）。

        选中「自定义」或程序回填且未匹配到内置城市时，提示使用下方经纬度。
        """
        tip = self.city_combo.itemData(
            self.city_combo.currentIndex(), Qt.ItemDataRole.ToolTipRole)
        self.city_combo.setToolTip(
            str(tip) if tip else '自定义：使用下方填写的经纬度')

    def _on_coord_edited(self, *_):
        """经度/纬度手改槽：脱离城市绑定，回到「自定义」。"""
        if self._syncing_coords:
            return
        self._coords_touched = True      # 手动改经纬度 = 显式坐标，必须优先于出生地文本解析
        if self.city_combo.currentIndex() != 0:
            self.city_combo.blockSignals(True)
            self.city_combo.setCurrentIndex(0)
            self.city_combo.blockSignals(False)
            self._refresh_city_tooltip()
        self._refresh_true_solar()

    def get_coordinates(self):
        """读取并校验经纬度，返回 (经度, 纬度)。

        Raises:
            ValueError: 超出 -180~180 / -90~90（防御性校验，SpinBox 正常不会越界）
        """
        lon, lat = self.lng_spin.value(), self.lat_spin.value()
        if not (LON_MIN <= lon <= LON_MAX):
            raise ValueError(f'经度 {lon}° 超出有效范围 {LON_MIN:g}~{LON_MAX:g}°')
        if not (LAT_MIN <= lat <= LAT_MAX):
            raise ValueError(f'纬度 {lat}° 超出有效范围 {LAT_MIN:g}~{LAT_MAX:g}°')
        return lon, lat

    def set_coordinates(self, longitude, latitude):
        """程序化写入经纬度（历史记录回填用）。

        Args:
            longitude: 经度；None 表示旧记录无该字段，保留面板当前值
            latitude: 纬度；None 同上

        Raises:
            ValueError: 数值非法或超范围（绝不静默回落默认 120/30）
        """
        if longitude is None or latitude is None:
            return
        try:
            lon, lat = float(longitude), float(latitude)
        except (TypeError, ValueError):
            raise ValueError(f'经纬度必须为数值，收到 {longitude!r} / {latitude!r}')
        if not (LON_MIN <= lon <= LON_MAX):
            raise ValueError(f'经度 {lon}° 超出有效范围 {LON_MIN:g}~{LON_MAX:g}°')
        if not (LAT_MIN <= lat <= LAT_MAX):
            raise ValueError(f'纬度 {lat}° 超出有效范围 {LAT_MIN:g}~{LAT_MAX:g}°')
        self._syncing_coords = True
        self.lng_spin.setValue(lon)
        self.lat_spin.setValue(lat)
        self._syncing_coords = False
        # 程序回填（历史记录载入）不算用户显式设定：来源标为 auto，
        # 这样旧记录（不带 coords_source）与回填后的面板保持同一语义
        self._coords_touched = False
        # 与内置城市表按 2 位小数精度近似匹配时回显城市名，否则保持「自定义」
        matched = 0
        for i in range(1, self.city_combo.count()):
            data = self.city_combo.itemData(i)
            if data and abs(data[0] - lon) < 0.005 and abs(data[1] - lat) < 0.005:
                matched = i
                break
        self.city_combo.blockSignals(True)
        self.city_combo.setCurrentIndex(matched)
        self.city_combo.blockSignals(False)
        self._refresh_city_tooltip()
        self._refresh_true_solar()

    def _cal(self, s):
        """历法切换槽（由 solar_btn / lunar_btn 的 clicked 触发）。

        这两个按钮没有加入 QButtonGroup，故须在此手动维持互斥。
        切换同时切换日期页：公历=日历控件，农历=年/月/日选择器；首次进入农历时
        以当前公历日期（含闰月）作为初值，之后保留用户已选的农历日期。

        Args:
            s: True 表示选择公历，False 表示农历。
        """
        self.solar_btn.setChecked(s); self.lunar_btn.setChecked(not s)
        if s:
            self.date_stack.setCurrentIndex(0)
        else:
            if not self._lunar_initialized:
                d = self.date_edit.date()
                self.lunar_picker.set_from_solar_date(d.year(), d.month(), d.day())
                self._lunar_initialized = True
            self.date_stack.setCurrentIndex(1)
        self._refresh_true_solar()
        self._validate()

    def _gen(self, m):
        """性别切换槽（由 male_btn / female_btn 的 clicked 触发）。

        虽然两按钮已加入 gender_grp 按钮组（默认互斥），这里仍显式设置一次，
        以便代码主动调用时（非用户点击）也能保证两个按钮不会同时高亮。

        Args:
            m: True 表示男，False 表示女。
        """
        self.male_btn.setChecked(m); self.female_btn.setChecked(not m)

    def _validate(self):
        """实时校验输入，决定「开始排盘」按钮是否可点。

        触发时机：姓名输入变化、时辰下拉或时分 SpinBox 变化时。
        通过条件：姓名非空（时分由 SpinBox 限定了 0-23 / 0-59，恒为合法值）。
        """
        name = self.name_edit.text().strip()
        self.submit_btn.setEnabled(bool(name))

    def _time_tuple(self):
        """T3.2 读取时分 SpinBox 并做范围兜底，返回 (时, 分)。

        返回:
            tuple[int, int]: 合法时分的二元组
        抛出:
            ValueError: 越界时抛出（SpinBox 正常情况下不会触发，属防御性校验）
        """
        hh, mm = self.hour_spin.value(), self.minute_spin.value()
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError(f"时间范围错误: {hh:02d}:{mm:02d}")
        return hh, mm

    @staticmethod
    def _check_lunar_date(year, month, day, is_leap):
        """校验农历日期真实存在；不存在直接抛 ValueError（禁止带非法日期排盘）。

        Args:
            year: 农历年。
            month: 农历月。
            day: 农历日。
            is_leap: 是否闰月。

        Raises:
            ValueError: 该农历日期（含闰月）不存在。
        """
        from core.lunar_converter import convert_lunar_to_solar
        convert_lunar_to_solar(year, month, day, is_leap)

    def get_data(self):
        """获取输入数据。若时间/日期非法则抛出 ValueError。

        农历模式下年月日取自农历选择器，并随身携带 is_leap（闰月）标志，
        交由 Service / core 层做真实换算；公历模式完全沿用原日历控件。
        """
        hh, mm = self._time_tuple()

        is_lunar = self.lunar_btn.isChecked()
        is_leap = False
        if is_lunar:
            year, month, day, is_leap = self.lunar_picker.lunar_date()
            self._check_lunar_date(year, month, day, is_leap)
        else:
            d = self.date_edit.date()
            year, month, day = d.year(), d.month(), d.day()
        if year < 1900 or year > 2100:
            raise ValueError(f"年份范围错误: {year}（需 1900~2100）")

        # 经纬度取自面板输入（经度参与真太阳时校正，纬度仅随记录保存）
        longitude, latitude = self.get_coordinates()

        return {
            'name': self.name_edit.text().strip(),
            'gender': '男' if self.male_btn.isChecked() else '女',
            'is_lunar': is_lunar,
            'is_leap': is_leap,
            'year': year, 'month': month, 'day': day,
            'hour': hh, 'minute': mm, 'hour_index': self.selected_hour,
            'is_early_zi': False,
            'location': self.location_edit.text().strip(),
            'latitude': latitude, 'longitude': longitude,
            # 坐标来源：explicit=用户显式设定（不可被地点文本地理编码覆盖），
            # auto=沿用默认/程序回填（允许按出生地文本解析经纬度）
            'coords_source': 'explicit' if self._coords_touched else 'auto',
            'solar_time_mode': '自动', 'age_type': '虚岁', 'leap_rule': '归前',
            'pan_type': self.selected_pan_type, 'notes': self.notes_edit.toPlainText(),
        }

    def clear(self):
        """重置表单为初始状态（由主窗口「重置」按钮触发）。

        日期回到今天、时辰回到午时、性别归男、历法归公历，并把「开始排盘」按钮
        重新置灰——姓名已清空，此刻本就不满足提交条件。
        注意：出生地、经纬度（含城市快捷选择）与流派刻意不在重置范围内，
        属于用户偏好，连续排盘时无需重填。
        """
        self.name_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.male_btn.setChecked(True); self.female_btn.setChecked(False)
        self.solar_btn.setChecked(True); self.lunar_btn.setChecked(False)
        self.date_stack.setCurrentIndex(0)
        self._lunar_initialized = False
        today = QDate.currentDate()
        self.lunar_picker.set_from_solar_date(today.year(), today.month(), today.day())
        self.hour_combo.setCurrentIndex(6)
        self.hour_spin.setValue(12); self.minute_spin.setValue(0)
        self._sync_time_label()
        self.notes_edit.clear(); self.submit_btn.setEnabled(False)
