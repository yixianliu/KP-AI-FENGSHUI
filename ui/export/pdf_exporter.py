"""
PDF 导出器（reportlab）
将排盘结果排版为结构化 PDF 报告：命盘信息、命局类型、四柱八字、
五行分析、十神分析、大运流年（含起运）、运程总结（事业/财运/健康/感情）、
吉凶批注、AI 智能深度分析。
中文使用 reportlab 内置 CID 字体 STSong-Light。
"""
from typing import Dict, Any, List
from .base_exporter import BaseExporter

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        ListFlowable, ListItem, HRFlowable,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    _FONT = 'STSong-Light'
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(_FONT))
    except Exception:
        _FONT = 'Helvetica'
    _REPORTLAB_OK = True
except Exception:
    _REPORTLAB_OK = False


# 命理主题色（与界面一致）
_C_ZHUSHA = colors.HexColor('#C45545')   # 朱砂
_C_QINGHUA = colors.HexColor('#4A7A90')  # 青华
_C_LIUJIN = colors.HexColor('#B88A30')    # 流金
_C_BG = colors.HexColor('#F7F4EE')
_C_CARD = colors.HexColor('#FFFFFF')
_C_TEXT = colors.HexColor('#333333')
_C_LINE = colors.HexColor('#D9CDB8')
_C_MUTED = colors.HexColor('#8A7F6B')

# AI 字段 -> 中文标题
_AI_SECTIONS = [
    ('personality', '性格特质'),
    ('career', '事业财运'),
    ('marriage', '婚姻感情'),
    ('health', '健康注意'),
    ('pattern_analysis', '格局分析'),
    ('wuxing_balance', '五行平衡分析'),
    ('shishen_analysis', '十神分析'),
    ('improvement_plan', '改善方案'),
    ('suggestions', '综合建议'),
]


def _esc(text: Any) -> str:
    """转义 reportlab Paragraph 的 XML 特殊字符"""
    s = '' if text is None else str(text)
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _to_str(v: Any) -> str:
    if v is None:
        return '-'
    if isinstance(v, (list, tuple)):
        return '、'.join(str(x) for x in v if x) if v else '-'
    return str(v)


class PdfExporter(BaseExporter):
    """PDF 报告导出器"""

    def __init__(self):
        if not _REPORTLAB_OK:
            raise RuntimeError('未安装 reportlab，无法导出 PDF（请 pip install reportlab）')
        self.styles = self._build_styles()

    def _build_styles(self):
        ss = getSampleStyleSheet()
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
        return '.pdf'

    def export(self, data: Dict[str, Any], file_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(
                file_path, pagesize=A4,
                leftMargin=18 * mm, rightMargin=18 * mm,
                topMargin=16 * mm, bottomMargin=16 * mm,
                title='八字排盘分析报告',
                author='KP-龙虎山大师兄',
            )
            story = []
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
            doc.build(story)
            return True
        except Exception as e:
            print(f"PDF 导出失败: {e}")
            return False

    # ----------------- 章节构造 -----------------
    def _build_title(self, story, data):
        s = self.styles
        story.append(Paragraph('八字排盘分析报告', s['title']))
        bi = data.get('basic_info', {}) or {}
        sub = bi.get('name') and f"姓名：{bi.get('name')}" or ''
        if bi.get('solar_date'):
            sub = (sub + '　' if sub else '') + f"公历：{bi.get('solar_date')}"
        if sub:
            story.append(Paragraph(_esc(sub), s['subtitle']))
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width='100%', thickness=1, color=_C_LIUJIN,
                               spaceBefore=2, spaceAfter=8))

    def _section_title(self, story, text):
        story.append(Paragraph(_esc(text), self.styles['h2']))

    def _kv_table(self, story, pairs: List[tuple]):
        """渲染 键值对 表格（两列）"""
        rows = [[Paragraph(_esc(k), self.styles['cell_head']),
                 Paragraph(_esc(_to_str(v)), self.styles['cell'])]
                for k, v in pairs if k]
        if not rows:
            return
        t = Table(rows, colWidths=[40 * mm, 119 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), _C_QINGHUA),
            ('GRID', (0, 0), (-1, -1), 0.5, _C_LINE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (1, 0), (1, -1), [_C_CARD, _C_BG]),
        ]))
        story.append(t)

    def _build_basic(self, story, data):
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
        bt = data.get('bazi_types', {}) or {}
        if not bt:
            return
        self._section_title(story, '二、命局类型')
        rows = []
        if bt.get('strength'):
            rows.append(('日主强弱', bt.get('strength')))
        if bt.get('geju_type'):
            name = bt.get('geju_name', '')
            val = bt.get('geju_type') + (f"（{name}）" if name else '')
            rows.append(('格局类型', val))
            if bt.get('geju_desc'):
                rows.append(('格局说明', bt.get('geju_desc')))
        if bt.get('wuxing_summary'):
            rows.append(('五行旺衰', bt.get('wuxing_summary')))
        ys = bt.get('yongshen') or {}
        if ys.get('yongshen_name'):
            rows.append(('用神', f"{ys.get('yongshen')}（{ys.get('yongshen_name')}）"))
            if ys.get('xishen_names'):
                rows.append(('喜神', '、'.join(ys.get('xishen_names'))))
            if ys.get('jishen_names'):
                rows.append(('忌神', '、'.join(ys.get('jishen_names'))))
        self._kv_table(story, rows)

    def _build_pillars(self, story, data):
        bz = data.get('bazi', {}) or {}
        if not bz:
            return
        self._section_title(story, '三、四柱八字')
        rows = [
            ('年柱', bz.get('year_pillar')),
            ('月柱', bz.get('month_pillar')),
            ('日柱', bz.get('day_pillar')),
            ('时柱', bz.get('hour_pillar')),
        ]
        self._kv_table(story, rows)

    def _build_wuxing(self, story, data):
        wx = data.get('wuxing', {}) or {}
        if not wx:
            return
        self._section_title(story, '四、五行分析')
        order = ['木', '火', '土', '金', '水']
        header = [Paragraph('五行', self.styles['cell_head']),
                  Paragraph('分数', self.styles['cell_head'])]
        data_rows = []
        for n in order:
            if n in wx:
                data_rows.append([Paragraph(_esc(n), self.styles['cell']),
                                  Paragraph(_esc(wx.get(n)), self.styles['cell'])])
        if not data_rows:
            return
        t = Table([header] + data_rows, colWidths=[40 * mm, 119 * mm])
        t.setStyle(TableStyle([
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
        ss = data.get('shishen', {}) or {}
        if not ss:
            return
        items = [(k, v) for k, v in ss.items() if v]
        if not items:
            return
        self._section_title(story, '五、十神分析')
        rows = [[Paragraph(_esc(k), self.styles['cell_head']),
                 Paragraph(_esc(v), self.styles['cell_head'])]
                for k, v in items]
        t = Table(rows, colWidths=[40 * mm, 119 * mm])
        t.setStyle(TableStyle([
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
        dayun = data.get('dayun', {}) or {}
        liunian = data.get('liunian', {}) or {}
        periods = dayun.get('periods', []) if isinstance(dayun, dict) else []
        years = liunian.get('years', []) if isinstance(liunian, dict) else []
        if not periods and not years:
            return
        self._section_title(story, '六、大运流年')
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
        yc = data.get('yuncheng', {}) or {}
        if not yc:
            return
        self._section_title(story, '七、运程总结')
        # 综合综述（置顶高亮）
        overview = yc.get('overview')
        if overview:
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
        an = data.get('analysis', []) or []
        if not an:
            return
        self._section_title(story, '八、吉凶批注')
        items = []
        for a in an:
            t = a.get('type', '')
            label = f"[{t}] " if t else ''
            items.append(ListItem(Paragraph(_esc(label + _to_str(a.get('text'))),
                                      self.styles['bullet'])))
        story.append(ListFlowable(items, bulletType='bullet', start='•', leftIndent=12))

    def _build_ai(self, story, data):
        ai = data.get('ai_analysis', {}) or {}
        if not ai:
            return
        self._section_title(story, '九、龙虎山大师兄智能深度分析')
        any_content = False
        for key, title in _AI_SECTIONS:
            items = ai.get(key, []) or []
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
            if mh_ai.get('final_verdict'):
                story.append(Paragraph('<b>结论：</b>' + _esc(_to_str(mh_ai.get('final_verdict'))),
                                       self.styles['body']))

    def _build_liuren(self, story, data):
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
            if lr_ai.get('final_verdict'):
                story.append(Paragraph('<b>结论：</b>' + _esc(_to_str(lr_ai.get('final_verdict'))),
                                       self.styles['body']))

    def _build_zonghe(self, story, data):
        z = data.get('zonghe', {}) or {}
        if not z:
            return
        self._section_title(story, '十、综合建议（龙虎山大师兄融合）')
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
