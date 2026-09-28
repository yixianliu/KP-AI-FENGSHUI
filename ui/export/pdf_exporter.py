"""
PDF 导出器（reportlab）
将排盘结果排版为结构化 PDF 报告：命盘信息、命局类型、四柱八字、
五行分析、十神分析、大运流年（含起运）、运程总结（事业/财运/健康/感情）、
吉凶批注、AI 智能深度分析。
中文使用 reportlab 内置 CID 字体 STSong-Light。
"""
from typing import Dict, Any, List
import io
from ui.styles import Colors
from .base_exporter import (BaseExporter, has_chapter, extract_pillars,
                            extract_wuxing, PILLAR_FIELDS, PILLAR_LABELS)
from .ai_titles import AI_SECTION_TITLE

# AI 分析区章节标题（单一权威源：ui/export/ai_titles.py）
# 带下划线的别名：历史调用点（_build_ai 等）沿用 _AI_SECTION_TITLE，
# 此前该名未定义会导致带 AI 数据的报告整体导出失败，故在此显式绑定权威常量。
_AI_SECTION_TITLE = AI_SECTION_TITLE

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        ListFlowable, ListItem, HRFlowable, PageBreak,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    # reportlab 内置的 Helvetica/Times 等标准字体只覆盖 Latin-1 字符集，
    # 直接拿来渲染中文会输出成黑块或空白，因此必须显式注册一款中文字体。
    # 这里选用 CID 字体 STSong-Light：它由 reportlab 自带映射、无需外挂
    # ttf 文件，也就不依赖用户机器上装了什么字体，打包分发最稳妥。
    _FONT = 'STSong-Light'
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(_FONT))
    except Exception:
        # 极少数精简安装缺少 CID 字体资源，退回 Helvetica 保证仍能出 PDF
        # （中文会丢失，但不至于整个导出功能不可用）
        _FONT = 'Helvetica'
    _REPORTLAB_OK = True
except Exception:
    # reportlab 未安装时不让 import 失败拖垮整个 app 启动，
    # 改为置标志位，等真正实例化 PdfExporter 时再报错提示安装
    _REPORTLAB_OK = False


# 命理主题色（PDF 打印专用调色板）
#
# 【已归位 Colors.PDF_* 令牌组】此前此色板是裸 hex 硬编码、被记为「已知审计
# 豁免」（理由：8 色中仅 3 个与既有令牌重合，其余无 UI 对应，提级会让 Colors
# 表膨胀）。现已提级为 styles.py 的 PDF_* 令牌组——单一真相源收敛到 Colors，
# 与 UI 深色主题、export_dialog 纸质主题（PAPER_*）并列，语义互不干扰。
#
# 服务对象是导出成品（PDF / 打印），色值比屏幕版更「实」以保证打印对比度
# （PDF_LIUJIN #B88A30 vs 屏幕 GOLD #c9a227；PDF_TEXT #333333 vs TEXT #F5F1E8）。
# 命名注意：PDF_QINGHUA 是真正的青（#4A7A90），而 Colors.QINGHUA 已收敛为
# 古金别名（= BRAND），二者语义不同，故 PDF_ 前缀独立命名。
try:
    _C_ZHUSHA = colors.HexColor(Colors.PDF_ZHUSHA)   # 朱砂，标题强调
    _C_QINGHUA = colors.HexColor(Colors.PDF_QINGHUA)  # 青华，次级强调
    _C_LIUJIN = colors.HexColor(Colors.PDF_LIUJIN)    # 流金，装饰线
    _C_BG = colors.HexColor(Colors.PDF_BG)            # 页面底色
    _C_CARD = colors.HexColor(Colors.PDF_CARD)        # 卡片 / 表格底
    _C_TEXT = colors.HexColor(Colors.PDF_TEXT)        # 正文墨色
    _C_LINE = colors.HexColor(Colors.PDF_LINE)        # 表格线 / 分隔线
    _C_MUTED = colors.HexColor(Colors.PDF_MUTED)      # 次要文字
except NameError:
    # reportlab 未安装时占位，实例化 PdfExporter 时会抛 RuntimeError
    _C_ZHUSHA = _C_QINGHUA = _C_LIUJIN = _C_BG = _C_CARD = _C_TEXT = _C_LINE = _C_MUTED = None

# AI 字段 -> 中文标题
_AI_SECTIONS = [
    # 与 core.analysis_storage._JSON_SCHEMAS 对齐（三种类型的并集，仅保留列表型字段；
    # final_verdict / disclaimer 为段落型，由各自面板/导出分支单独处理）。
    ('personality', '性格特质'),
    ('career', '事业财运'),
    ('relationships', '婚姻感情'),
    ('health', '健康注意'),
    ('four_pillars_detail', '四柱详细解读'),
    ('analysis', '卦象/课体分析'),
    ('hexagram_interpretations', '卦爻解释'),
    ('timing', '应期时机'),
    ('scenario_advice', '场景化建议'),
    ('advice', '行动建议'),
    ('historical_cases', '历史案例'),
    ('probability_stats', '概率统计'),
]


def _esc(text: Any) -> str:
    """转义 reportlab Paragraph 的 XML 特殊字符"""
    s = '' if text is None else str(text)
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _to_str(v: Any) -> str:
    """把任意排盘字段值转换为适合排入 PDF 表格/段落的字符串。

    与 CSV 导出器同名函数的区别：PDF 是给人看的正式报告，空单元格会让
    表格看起来像渲染出错，因此空值统一显示为占位符横杠而非空串。

    Args:
        v: 任意排盘字段值，可为 None、list/tuple 或标量

    Returns:
        str，None 或空列表返回占位横杠；list/tuple 用顿号连接（过滤空元素）；
        其余类型直接 str() 转换
    """
    if v is None:
        return '-'
    if isinstance(v, (list, tuple)):
        # 过滤空元素避免出现连续顿号；整体为空列表时同样退回占位符
        return '、'.join(str(x) for x in v if x) if v else '-'
    return str(v)


def _app_version() -> str:
    """T6.4 取应用版本号用于封面，导入失败时回落到常量。"""
    try:
        from core.app_version import get_version_label
        return get_version_label()
    except Exception:
        return 'v5.0.6'


# reportlab 缺席时退回 object，保证模块级 class 定义不会因 NameError 拖垮
# 「import pdf_exporter」本身（真正导出时由 PdfExporter.__init__ 抛 RuntimeError）。
_TocBase = SimpleDocTemplate if _REPORTLAB_OK else object


class _TocDocTemplate(_TocBase):
    """T6.4 带页码采集能力的文档模板。

    覆写 afterFlowable：每当一个带 _toc_anchor 属性的 Flowable 被绘制后，
    记录「锚点 -> 所在页码」。目录页的真实页码依赖此采集结果，因此报告
    采用两遍构建（第一遍干跑采集页码，第二遍带目录正式输出）。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.toc_pages = {}

    def afterFlowable(self, flowable):
        anchor = getattr(flowable, '_toc_anchor', None)
        if anchor:
            self.toc_pages[anchor] = self.page


class PdfExporter(BaseExporter):
    """PDF 报告导出器"""

    def __init__(self):
        """初始化 PDF 导出器，预先构建整份报告复用的段落样式表。

        样式表在构造期一次性建好并挂到实例上，避免每个章节渲染时
        重复创建 ParagraphStyle 对象。

        Raises:
            RuntimeError: 未安装 reportlab 依赖时抛出，提示安装命令
        """
        if not _REPORTLAB_OK:
            raise RuntimeError('未安装 reportlab，无法导出 PDF（请 pip install reportlab）')
        self.styles = self._build_styles()

    def _build_styles(self):
        """构建全套中文段落样式，供各 _build_* 章节方法取用。

        所有样式都必须显式指定 fontName=_FONT：reportlab 的
        getSampleStyleSheet() 返回的是 Helvetica 系列样式，直接继承会导致
        中文无法显示，所以每个派生样式都要把字体覆盖回已注册的中文字体。
        配色沿用界面的命理主题色，保证导出件与软件观感一致。

        Returns:
            dict，样式名到 ParagraphStyle 的映射，含 title（报告主标题）、
            subtitle（副标题）、h2（章节标题）、body（正文）、cell（表格正文格）、
            cell_head（表格深色表头格，用白字）、bullet（列表项）、note（弱化小字）
        """
        ss = getSampleStyleSheet()
        # 正文类样式共用的字体与文字色，用 ** 展开以免逐条重复书写
        base = dict(fontName=_FONT, textColor=_C_TEXT)
        return {
            'title': ParagraphStyle('cn_title', parent=ss['Title'], fontName=_FONT,
                                     fontSize=20, textColor=_C_ZHUSHA, leading=26, spaceAfter=4),
            'subtitle': ParagraphStyle('cn_sub', parent=ss['Normal'], fontName=_FONT,
                                       fontSize=11, textColor=_C_MUTED, leading=16, spaceAfter=2),
            'h2': ParagraphStyle('cn_h2', parent=ss['Heading2'], fontName=_FONT,
                                  fontSize=14, textColor=_C_QINGHUA, leading=20,
                                  spaceBefore=12, spaceAfter=6),
            'body': ParagraphStyle('cn_body', parent=ss['Normal'], **base, fontSize=11, leading=16),
            'cell': ParagraphStyle('cn_cell', parent=ss['Normal'], **base, fontSize=10, leading=14),
            'cell_head': ParagraphStyle('cn_cell_head', parent=ss['Normal'], fontName=_FONT,
                                       fontSize=10, textColor=colors.white, leading=14),
            'bullet': ParagraphStyle('cn_bullet', parent=ss['Normal'], **base, fontSize=10, leading=15),
            'note': ParagraphStyle('cn_note', parent=ss['Normal'], fontName=_FONT,
                                  fontSize=9, textColor=_C_MUTED, leading=13),
        }

    def get_file_extension(self) -> str:
        """返回本导出器对应的文件扩展名。

        实现 BaseExporter.get_file_extension 契约，供上层拼接默认文件名
        和文件对话框过滤器使用。

        Returns:
            str，固定为 '.pdf'
        """
        return '.pdf'

    def export(self, data: Dict[str, Any], file_path: str) -> bool:
        """把排盘结果排版成结构化 PDF 报告并落盘。

        实现 BaseExporter.export 契约。流程为：建 A4 文档模板 -> 依次调用
        各 _build_* 方法往 story 流式列表里追加 Flowable -> 交给 reportlab
        统一分页渲染。各章节方法内部自行判断数据是否存在，缺数据的章节
        直接跳过，因此这里无条件按固定顺序调用即可。

        Args:
            data: 排盘结果字典，可能包含 basic_info / bazi_types / bazi /
                wuxing / shishen / dayun / liunian / yuncheng / analysis /
                ai_analysis / meihua_data / meihua_ai / liuren_data /
                liuren_ai / zonghe 等键
            file_path: 目标 PDF 文件路径

        Returns:
            bool，渲染并保存成功返回 True；任何异常（路径不可写、字体缺失、
            内容排版失败等）被捕获后打印错误并返回 False，不向上抛出
        """
        try:
            # T6.4 两遍构建：reportlab 在 build 前无法预知章节落在第几页，
            # 所以先用 BytesIO 干跑一遍采集各章节锚点页码，再带目录正式输出。
            # 两遍的 story 结构必须保持一致（封面 1 页 + 目录 1 页），
            # 否则第二遍的页码会整体偏移。
            self._toc_entries = []
            buf = io.BytesIO()
            doc1 = _TocDocTemplate(
                buf, pagesize=A4,
                leftMargin=18 * mm, rightMargin=18 * mm,
                topMargin=16 * mm, bottomMargin=16 * mm,
                title='八字排盘分析报告', author='龙虎山大师兄',
            )
            doc1.build(self._build_story(data, with_toc=False))
            pages = doc1.toc_pages

            self._toc_entries = []
            doc2 = _TocDocTemplate(
                file_path, pagesize=A4,
                leftMargin=18 * mm, rightMargin=18 * mm,
                topMargin=16 * mm, bottomMargin=16 * mm,
                title='八字排盘分析报告', author='龙虎山大师兄',
            )
            doc2.build(self._build_story(data, with_toc=True, pages=pages))
            return True
        except Exception as e:
            # 导出属于用户主动触发的非关键路径，失败时不应让界面崩溃，
            # 统一吞掉异常并以返回值告知调用方
            print(f"PDF 导出失败: {e}")
            return False

    def _build_story(self, data: Dict[str, Any], with_toc: bool,
                     pages: Dict[str, int] = None) -> List[Any]:
        """T6.4 构建完整 story：封面页 + 目录页（可选） + 正文章节。

        Args:
            data: 排盘结果字典
            with_toc: True 时插入带真实页码的目录页；False 时插入一个等高的
                空页占位，保证两遍构建的正文章节起始页码一致
            pages: 第一遍采集到的「锚点 -> 页码」映射，仅 with_toc=True 时用到
        """
        story = []
        self._build_cover(story, data)
        story.append(PageBreak())
        if with_toc:
            self._build_toc(story, pages or {})
        story.append(PageBreak())

        # 正文：各章节方法内部自行判空，缺数据的章节直接跳过
        self._build_title(story, data)
        self._build_basic(story, data)
        self._build_types(story, data)
        self._build_pillars(story, data)
        self._build_wuxing(story, data)
        self._build_shishen(story, data)
        self._build_yunshi(story, data)
        self._build_yuncheng(story, data)
        self._build_analysis(story, data)
        self._build_ai(story, data)
        self._build_meihua(story, data)
        self._build_liuren(story, data)
        self._build_zonghe(story, data)
        return story

    def _build_cover(self, story, data):
        """T6.4 渲染封面页：品牌标识、报告名、版本、核心参数与免责提示。"""
        s = self.styles
        bi = data.get('basic_info', {}) or {}
        bz = extract_pillars(data)

        story.append(Spacer(1, 26 * mm))
        # 品牌标识（太极符号在多数 PDF 字体下可正常显示）
        brand = Paragraph('☯', ParagraphStyle(
            'cover_brand', parent=s['title'], fontSize=44, alignment=1,
            textColor=_C_ZHUSHA, leading=52))
        story.append(brand)
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph('风水排盘专业工具', ParagraphStyle(
            'cover_brand_name', parent=s['title'], fontSize=18, alignment=1,
            textColor=_C_QINGHUA, leading=24)))
        story.append(Paragraph(f'KP-AI-FENGSHUI {_esc(_app_version())}', ParagraphStyle(
            'cover_ver', parent=s['subtitle'], alignment=1, fontSize=10)))
        story.append(Spacer(1, 10 * mm))
        story.append(HRFlowable(width='60%', thickness=1.2, color=_C_LIUJIN,
                                spaceBefore=2, spaceAfter=10, hAlign='CENTER'))
        story.append(Paragraph('八字排盘分析报告', ParagraphStyle(
            'cover_title', parent=s['title'], fontSize=24, alignment=1,
            textColor=_C_TEXT, leading=32)))
        story.append(Spacer(1, 16 * mm))

        # 核心参数（缺项自动跳过，避免封面出现一排横杠）
        pairs = []
        if bi.get('name'):
            pairs.append(('姓名', bi.get('name')))
        if bi.get('gender'):
            pairs.append(('性别', bi.get('gender')))
        if bi.get('solar_date'):
            pairs.append(('公历', bi.get('solar_date')))
        if bi.get('lunar_date'):
            pairs.append(('农历', bi.get('lunar_date')))
        # 八字四柱：拼成一行「年 月 日 时」
        pillars = [bz.get(k) for k in ('year_pillar', 'month_pillar',
                                       'day_pillar', 'hour_pillar')]
        if any(pillars):
            pairs.append(('八字', '　'.join(_to_str(p) if p else '—' for p in pillars)))

        if pairs:
            rows = [[Paragraph(_esc(k), s['cell_head']),
                     Paragraph(_esc(_to_str(v)), s['cell'])] for k, v in pairs]
            t = Table(rows, colWidths=[32 * mm, 100 * mm], hAlign='CENTER')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), _C_QINGHUA),
                ('GRID', (0, 0), (-1, -1), 0.5, _C_LINE),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t)

        story.append(Spacer(1, 18 * mm))
        from datetime import datetime
        story.append(Paragraph(
            f'报告生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}',
            ParagraphStyle('cover_time', parent=s['note'], alignment=1)))
        story.append(Paragraph(
            '本解读仅供文化研究参考，不构成任何决策依据',
            ParagraphStyle('cover_disc', parent=s['note'], alignment=1,
                           textColor=_C_ZHUSHA)))

    def _build_toc(self, story, pages: Dict[str, int]):
        """T6.4 渲染目录页：章节名 + 页码（页码来自第一遍干跑采集）。"""
        s = self.styles
        story.append(Paragraph('目　录', ParagraphStyle(
            'toc_head', parent=s['title'], fontSize=18, alignment=1,
            textColor=_C_QINGHUA, leading=26)))
        story.append(Spacer(1, 6 * mm))
        if not self._toc_entries:
            story.append(Paragraph('（无章节）', s['note']))
            return
        rows = []
        for title, anchor in self._toc_entries:
            rows.append([
                Paragraph(_esc(title), s['cell']),
                Paragraph(str(pages.get(anchor, '-')),
                          ParagraphStyle('toc_page', parent=s['cell'], alignment=2)),
            ])
        t = Table(rows, colWidths=[140 * mm, 19 * mm], hAlign='LEFT')
        t.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -2), 0.4, _C_LINE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    # ----------------- 章节构造 -----------------
    def _build_title(self, story, data):
        """渲染报告首部：主标题、姓名/公历副标题和一条金色分隔线。

        位于导出流程最前端，由 export 第一个调用。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，仅读取 basic_info 下的 name / solar_date
        """
        s = self.styles
        story.append(Paragraph('八字排盘分析报告', s['title']))
        bi = data.get('basic_info', {}) or {}
        # 姓名与公历日期都是可选项，用短路表达式拼出副标题；
        # 两项都缺时 sub 为空串，下面就不输出副标题行
        sub = bi.get('name') and f"姓名：{bi.get('name')}" or ''
        if bi.get('solar_date'):
            sub = (sub + '　' if sub else '') + f"公历：{bi.get('solar_date')}"
        if sub:
            story.append(Paragraph(_esc(sub), s['subtitle']))
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width='100%', thickness=1, color=_C_LIUJIN,
                               spaceBefore=2, spaceAfter=8))

    def _section_title(self, story, text):
        """向 story 追加一个二级章节标题（如「一、基本信息」）。

        T6.4：标题附带 HTML 锚点并登记进 self._toc_entries，
        供目录页回填真实页码（页码由 _TocDocTemplate.afterFlowable 采集）。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            text: 章节标题文本，内部会做 XML 转义
        """
        if not hasattr(self, '_toc_entries') or self._toc_entries is None:
            self._toc_entries = []
        anchor = f'toc_sec_{len(self._toc_entries)}'
        self._toc_entries.append((text, anchor))
        # <a name="..."/> 是 reportlab 支持的锚点标记；_toc_anchor 属性
        # 会被 _TocDocTemplate.afterFlowable 读取以记录页码
        para = Paragraph(f'<a name="{anchor}"/>' + _esc(text), self.styles['h2'])
        para._toc_anchor = anchor
        story.append(para)

    def _kv_table(self, story, pairs: List[tuple]):
        """渲染 键值对 表格（两列）"""
        rows = [[Paragraph(_esc(k), self.styles['cell_head']),
                 Paragraph(_esc(_to_str(v)), self.styles['cell'])]
                for k, v in pairs if k]
        if not rows:
            return
        # 固定列宽而非自适应：全篇多个章节都用这套宽度，视觉上左侧标签列能对齐；
        # 数值列留足空间容纳长段批注，超出部分由 Paragraph 自动换行
        t = Table(rows, colWidths=[40 * mm, 119 * mm])
        t.setStyle(TableStyle([
            # 第一列整列铺青华底色作为标签列，配合 cell_head 的白字
            ('BACKGROUND', (0, 0), (0, -1), _C_QINGHUA),
            ('GRID', (0, 0), (-1, -1), 0.5, _C_LINE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            # 仅对数值列做斑马纹，长表格逐行阅读时不易串行
            ('ROWBACKGROUNDS', (1, 0), (1, -1), [_C_CARD, _C_BG]),
        ]))
        story.append(t)

    def _build_basic(self, story, data):
        """渲染「一、基本信息」章节：排盘类型、公历/农历、时辰、地点、性别。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，仅读取 basic_info 子字典

        Returns:
            None；basic_info 缺失或为空时直接返回，不输出标题
        """
        bi = data.get('basic_info', {}) or {}
        if not bi:
            return
        self._section_title(story, '一、基本信息')
        self._kv_table(story, [
            ('排盘类型', bi.get('pan_type')),
            ('公历日期', bi.get('solar_date')),
            ('农历日期', bi.get('lunar_date')),
            ('出生时辰', bi.get('hour')),
            ('出生地点', bi.get('location')),
            ('性别', bi.get('gender')),
        ])

    def _build_types(self, story, data):
        """渲染「二、命局类型」章节：日主强弱、格局、五行旺衰与用神喜忌。

        本章节字段全部可选（不同排盘深度算出的项不一样），因此先把有值的
        项收集进 rows 再一次性出表，避免出现整行空白。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，仅读取 bazi_types 子字典

        Returns:
            None；bazi_types 缺失或为空时直接返回，不输出标题
        """
        bt = data.get('bazi_types', {}) or {}
        if not bt:
            return
        self._section_title(story, '二、命局类型')
        rows = []
        if bt.get('strength'):
            rows.append(('日主强弱', bt.get('strength')))
        if bt.get('geju_type'):
            # 格局别名（如「正官格」的通俗称呼）只在存在时才加括号后缀
            name = bt.get('geju_name', '')
            val = bt.get('geju_type') + (f"（{name}）" if name else '')
            rows.append(('格局类型', val))
            # 格局说明依附于格局类型，父项没有时不单独出现
            if bt.get('geju_desc'):
                rows.append(('格局说明', bt.get('geju_desc')))
        if bt.get('wuxing_summary'):
            rows.append(('五行旺衰', bt.get('wuxing_summary')))
        ys = bt.get('yongshen') or {}
        # 喜神/忌神是用神推导的衍生结果，用神未定则整组都不展示
        if ys.get('yongshen_name'):
            rows.append(('用神', f"{ys.get('yongshen')}（{ys.get('yongshen_name')}）"))
            if ys.get('xishen_names'):
                rows.append(('喜神', '、'.join(ys.get('xishen_names'))))
            if ys.get('jishen_names'):
                rows.append(('忌神', '、'.join(ys.get('jishen_names'))))
        self._kv_table(story, rows)

    def _build_pillars(self, story, data):
        """渲染「三、四柱八字」章节：年月日时四柱干支。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，仅读取 bazi 子字典的四个 *_pillar 键

        Returns:
            None；bazi 缺失或为空时直接返回，不输出标题
        """
        # 兼容两种上游结构：旧结构集中在 data['bazi']，Service 路径摊平在
        # 顶层，统一由 extract_pillars 兜底（详见 base_exporter）。
        bz = extract_pillars(data)
        if not bz:
            return
        self._section_title(story, '三、四柱八字')
        rows = [
            (PILLAR_LABELS.get(k, k), bz.get(k))
            for k in PILLAR_FIELDS
        ]
        self._kv_table(story, rows)

    def _build_wuxing(self, story, data):
        """渲染「四、五行分析」章节：木火土金水各自的得分表。

        与其他章节的键值表不同，这里是带表头的真表格，因此不复用 _kv_table
        而是就地构造 Table。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，仅读取 wuxing 子字典（五行名 -> 分数）

        Returns:
            None；wuxing 缺失、为空或五行项全不存在时直接返回
        """
        # 兼容两种上游结构：旧结构为 data['wuxing']（五行 -> 分值），Service
        # 路径为 wuxing_detail（五行 -> {percentage, score}），统一由
        # extract_wuxing 兜底；percentage 已是百分数语义，这里补上 % 号。
        wx = extract_wuxing(data)
        if wx:
            wx = {n: (f"{v}%" if isinstance(v, (int, float)) else v)
                  for n, v in wx.items()}
        if not wx:
            return
        self._section_title(story, '四、五行分析')
        # 固定按相生顺序输出，而不是跟随 dict 的插入顺序，保证每份报告排列一致
        order = ['木', '火', '土', '金', '水']
        header = [Paragraph('五行', self.styles['cell_head']),
                  Paragraph('分数', self.styles['cell_head'])]
        data_rows = []
        for n in order:
            if n in wx:
                data_rows.append([Paragraph(_esc(n), self.styles['cell']),
                                  Paragraph(_esc(wx.get(n)), self.styles['cell'])])
        # 标题已经输出，但若五行数据一项都没命中则不再补一张空表
        if not data_rows:
            return
        t = Table([header] + data_rows, colWidths=[40 * mm, 119 * mm])
        t.setStyle(TableStyle([
            # 这里是横向表头（首行整行着色），区别于 _kv_table 的纵向标签列
            ('BACKGROUND', (0, 0), (-1, 0), _C_QINGHUA),
            ('GRID', (0, 0), (-1, -1), 0.5, _C_LINE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [_C_CARD, _C_BG]),
        ]))
        story.append(t)

    def _build_shishen(self, story, data):
        """渲染「五、十神分析」章节：各十神的分值表。

        十神项目数量随命局变化，得分为 0/空的十神不列出，避免表格被无效行撑长。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，仅读取 shishen 子字典（十神名 -> 分数）

        Returns:
            None；shishen 缺失、为空或过滤后无有效项时直接返回
        """
        ss = data.get('shishen', {}) or {}
        if not ss:
            return
        # 先过滤再判空，确保「有 shishen 键但全是零值」时也不输出章节标题
        items = [(k, v) for k, v in ss.items() if v]
        if not items:
            return
        self._section_title(story, '五、十神分析')
        rows = [[Paragraph(_esc(k), self.styles['cell_head']),
                 Paragraph(_esc(v), self.styles['cell_head'])]
                for k, v in items]
        t = Table(rows, colWidths=[40 * mm, 119 * mm])
        t.setStyle(TableStyle([
            # 十神表用朱砂色标签列，与前面青华色的基础信息表做视觉区分
            ('BACKGROUND', (0, 0), (0, -1), _C_ZHUSHA),
            ('GRID', (0, 0), (-1, -1), 0.5, _C_LINE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (1, 0), (1, -1), [_C_CARD, _C_BG]),
        ]))
        story.append(t)

    def _build_yunshi(self, story, data):
        """渲染「六、大运流年」章节：起运说明、各步大运与逐年流年批注。

        这是一个虚拟章节，数据来自 dayun 和 liunian 两个并列的键，
        两者有其一即可成章。内容以项目符号列表呈现而非表格，因为每条
        批注是长文本，表格换行后可读性差。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，读取 dayun.periods / dayun.direction /
                dayun.qiyun_text 与 liunian.years

        Returns:
            None；大运与流年皆为空时直接返回
        """
        dayun = data.get('dayun', {}) or {}
        liunian = data.get('liunian', {}) or {}
        # 上游偶尔会传入非 dict 的旧结构，先做 isinstance 兜底再取子键
        periods = dayun.get('periods', []) if isinstance(dayun, dict) else []
        years = liunian.get('years', []) if isinstance(liunian, dict) else []
        if not periods and not years:
            return
        self._section_title(story, '六、大运流年')
        # 起运信息是解读大运的前提，用弱化小字置于列表之前
        qiyun = dayun.get('qiyun_text')
        if qiyun:
            story.append(Paragraph('起运：' + _esc(qiyun), self.styles['note']))
            story.append(Spacer(1, 2 * mm))
        if periods:
            story.append(Paragraph('大运（' + _esc(dayun.get('direction', '')) + '）', self.styles['body']))
            items = []
            for p in periods:
                title = f"第{p.get('period')}运 {p.get('ganzhi')}（{p.get('start_age')}-{p.get('end_age')}岁，{p.get('start_year')}-{p.get('end_year')}年）"
                items.append(ListItem(Paragraph(_esc(title + '：' + _to_str(p.get('analysis'))), self.styles['bullet'])))
            story.append(ListFlowable(items, bulletType='bullet', start='•', leftIndent=12))
            story.append(Spacer(1, 4 * mm))
        if years:
            story.append(Paragraph('流年', self.styles['body']))
            items = []
            for y in years:
                title = f"{y.get('year')}年 {y.get('ganzhi')}"
                items.append(ListItem(Paragraph(_esc(title + '：' + _to_str(y.get('analysis'))), self.styles['bullet'])))
            story.append(ListFlowable(items, bulletType='bullet', start='•', leftIndent=12))

    def _build_yuncheng(self, story, data):
        """渲染「七、运程总结」章节：综述 + 事业/财运/健康/感情四维 + 标签。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，读取 yuncheng 下的 overview / career /
                wealth / health / love / tags

        Returns:
            None；yuncheng 缺失或为空时直接返回，不输出标题
        """
        yc = data.get('yuncheng', {}) or {}
        if not yc:
            return
        self._section_title(story, '七、运程总结')
        # 综合综述（置顶高亮）
        overview = yc.get('overview')
        if overview:
            # <b> 是 reportlab Paragraph 支持的行内标记，属于版式的一部分，
            # 所以只对来自数据的正文做 _esc 转义，标签本身保持原样
            story.append(Paragraph('<b>综合：</b>' + _esc(overview), self.styles['body']))
            story.append(Spacer(1, 3 * mm))
        blocks = [
            ('事业', yc.get('career')),
            ('财运', yc.get('wealth')),
            ('健康', yc.get('health')),
            ('感情', yc.get('love')),
        ]
        for title, text in blocks:
            if not text:
                continue
            story.append(Paragraph(f'<b>{_esc(title)}：</b>' + _esc(text), self.styles['bullet']))
            story.append(Spacer(1, 2 * mm))
        tags = yc.get('tags') or []
        if tags:
            story.append(Paragraph('标签：' + _esc('、'.join(str(t) for t in tags)), self.styles['note']))
    def _build_analysis(self, story, data):
        """渲染「八、吉凶批注」章节：逐条列出吉凶判语。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，读取 analysis 列表，元素形如
                {'type': '吉'/'凶', 'text': '批注正文'}

        Returns:
            None；analysis 缺失或为空列表时直接返回，不输出标题
        """
        an = data.get('analysis', []) or []
        if not an:
            return
        self._section_title(story, '八、吉凶批注')
        items = []
        for a in an:
            t = a.get('type', '')
            # 吉凶类型作为方括号前缀内联在文本里；部分批注没有类型，此时不加前缀
            label = f"[{t}] " if t else ''
            items.append(ListItem(Paragraph(_esc(label + _to_str(a.get('text'))),
                                      self.styles['bullet'])))
        story.append(ListFlowable(items, bulletType='bullet', start='•', leftIndent=12))

    def _build_ai(self, story, data):
        """渲染「九、龙虎山大师兄分析预测」章节：AI 生成的各维度解读。

        按 _AI_SECTIONS 固定顺序遍历，使报告章节次序不受 AI 返回字段顺序影响。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，读取 ai_analysis 子字典，每个键对应一个
                字符串列表（如 personality / career / suggestions 等）

        Returns:
            None；ai_analysis 缺失或为空时直接返回，不输出标题
        """
        ai = data.get('ai_analysis', {}) or {}
        if not ai:
            return
        self._section_title(story, _AI_SECTION_TITLE)
        # AI 有时会返回结构完整但各项均为空数组的结果，
        # 用该标志位在末尾补一句提示，避免读者以为是导出出错
        any_content = False
        for key, title in _AI_SECTIONS:
            items = ai.get(key, []) or []
            # 防御：个别字段可能为字符串（如旧缓存数据），统一包成单元素列表，
            # 避免逐字符写入 bullet。
            if isinstance(items, str):
                items = [items] if items.strip() else []
            elif not isinstance(items, (list, tuple)):
                items = [items] if items else []
            if not items:
                continue
            any_content = True
            story.append(Paragraph(_esc(title), self.styles['body']))
            flow = [ListItem(Paragraph(_esc(_to_str(x)), self.styles['bullet'])) for x in items]
            story.append(ListFlowable(flow, bulletType='bullet', start='•', leftIndent=12))
            story.append(Spacer(1, 3 * mm))
        if not any_content:
            story.append(Paragraph('（龙虎山大师兄未返回有效条目）', self.styles['note']))

    def _build_meihua(self, story, data):
        """渲染梅花易数卦象章节：卦象要素表 + AI 卦理解读。

        梅花的排盘数据（meihua_data）与 AI 解读（meihua_ai）是两个独立的键，
        用户可能只算了卦没跑 AI，也可能反过来，因此两者分别判空、任一有值即成章。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，读取 meihua_data（本卦/变卦/互卦/体用等）
                与 meihua_ai（各维度解读列表及 final_verdict 结论）

        Returns:
            None；两个键都为空时直接返回，不输出标题
        """
        mh = data.get('meihua_data', {}) or {}
        mh_ai = data.get('meihua_ai') or {}
        if not mh and not mh_ai:
            return
        self._section_title(story, '九、梅花易数卦象')
        if mh:
            pairs = [
                ('起卦方法', mh.get('method')),
                ('本卦', mh.get('base_hex')),
                ('变卦', mh.get('changed_hex')),
                ('互卦', mh.get('hu_hex')),
                ('体卦', mh.get('ti_gong')),
                ('用卦', mh.get('yong_gong')),
                ('体卦五行', mh.get('ti_zhi')),
                ('用卦五行', mh.get('yong_zhi')),
                ('互卦五行', mh.get('hu_gong')),
                ('变卦五行', mh.get('bian_gong')),
                ('体用关系', mh.get('hex_relation')),
            ]
            self._kv_table(story, pairs)
        if mh_ai:
            story.append(Spacer(1, 4 * mm))
            story.append(Paragraph('<b>龙虎山大师兄梅花解读：</b>', self.styles['body']))
            for key, title in _AI_SECTIONS:
                items = mh_ai.get(key, []) or []
                if not items:
                    continue
                story.append(Paragraph(_esc(title), self.styles['body']))
                flow = [ListItem(Paragraph(_esc(_to_str(x)), self.styles['bullet'])) for x in items]
                story.append(ListFlowable(flow, bulletType='bullet', start='•', leftIndent=12))
                story.append(Spacer(1, 2 * mm))
            # final_verdict 是梅花特有的总断语，独立于 _AI_SECTIONS 各分项，放在最后压轴
            if mh_ai.get('final_verdict'):
                story.append(Paragraph('<b>结论：</b>' + _esc(_to_str(mh_ai.get('final_verdict'))),
                                       self.styles['body']))

    def _build_liuren(self, story, data):
        """渲染大六壬起课章节：四课三传等课体要素表 + AI 课理解读。

        结构与 _build_meihua 完全对称：排盘数据 liuren_data 与 AI 解读
        liuren_ai 是两个独立的键，任一有值即成章。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，读取 liuren_data（四课/三传/月将/天将/神煞等）
                与 liuren_ai（各维度解读列表及 final_verdict 结论）

        Returns:
            None；两个键都为空时直接返回，不输出标题
        """
        lr = data.get('liuren_data', {}) or {}
        lr_ai = data.get('liuren_ai') or {}
        if not lr and not lr_ai:
            return
        self._section_title(story, '十、大六壬起课')
        if lr:
            pairs = [
                ('公历日期', lr.get('pan_date')),
                ('四课', lr.get('si_ke')),
                ('三传', lr.get('san_chuan')),
                ('三传门法', lr.get('gate')),
                ('月将', lr.get('yue_jiang')),
                ('天将', lr.get('tian_jiang')),
                ('神煞', lr.get('shen_sha')),
            ]
            self._kv_table(story, pairs)
        if lr_ai:
            story.append(Spacer(1, 4 * mm))
            story.append(Paragraph('<b>龙虎山大师兄六壬解读：</b>', self.styles['body']))
            for key, title in _AI_SECTIONS:
                items = lr_ai.get(key, []) or []
                if not items:
                    continue
                story.append(Paragraph(_esc(title), self.styles['body']))
                flow = [ListItem(Paragraph(_esc(_to_str(x)), self.styles['bullet'])) for x in items]
                story.append(ListFlowable(flow, bulletType='bullet', start='•', leftIndent=12))
                story.append(Spacer(1, 2 * mm))
            # final_verdict 是六壬特有的总断语，独立于 _AI_SECTIONS 各分项，放在最后压轴
            if lr_ai.get('final_verdict'):
                story.append(Paragraph('<b>结论：</b>' + _esc(_to_str(lr_ai.get('final_verdict'))),
                                       self.styles['body']))

    def _build_zonghe(self, story, data):
        """渲染综合建议章节：AI 融合八字/梅花/六壬三方结论后的统一判断。

        位于导出流程最末尾，是全报告的收口章节，附免责说明。

        Args:
            story: reportlab 的 Flowable 列表，本方法就地追加元素
            data: 排盘结果字典，读取 zonghe 下的 tri_method_overview /
                consistency_check / synthesis / unified_plan / key_timing
                （均为字符串列表）以及 disclaimer

        Returns:
            None；zonghe 缺失或为空时直接返回，不输出标题
        """
        z = data.get('zonghe', {}) or {}
        if not z:
            return
        self._section_title(story, '十、综合建议（大师兄融合）')
        # 顺序即「先摆三方结论 -> 再校验矛盾 -> 后给定论和方案」的推理链条，不可随意调换
        sections = [
            ('tri_method_overview', '三方概览'),
            ('consistency_check', '矛盾与印证'),
            ('synthesis', '综合定论'),
            ('unified_plan', '统一趋吉避凶方案'),
            ('key_timing', '关键时机与禁忌'),
        ]
        for key, title in sections:
            items = z.get(key) or []
            if not items:
                continue
            story.append(Paragraph(_esc(title), self.styles['body']))
            flow = [ListItem(Paragraph(_esc(_to_str(x)), self.styles['bullet'])) for x in items]
            story.append(ListFlowable(flow, bulletType='bullet', start='•', leftIndent=12))
            story.append(Spacer(1, 3 * mm))
        disc = z.get('disclaimer')
        if disc:
            story.append(Paragraph('<b>免责说明：</b>' + _esc(disc), self.styles['note']))
