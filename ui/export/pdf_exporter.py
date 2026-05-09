from ui.export.base_exporter import BaseExporter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER

class PdfExporter(BaseExporter):
    def perform_export(self, file_path):
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#5D4037'),
            alignment=TA_CENTER,
            spaceAfter=20
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#5D4037'),
            spaceBefore=15,
            spaceAfter=10
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#333333'),
            spaceAfter=5
        )

        elements = []

        elements.append(Paragraph('八字排盘', title_style))
        elements.append(Paragraph('命盘分析报告', styles['Heading2']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"导出时间: {self.get_export_timestamp()}", body_style))
        elements.append(Spacer(1, 20))

        basic_info = self.get_basic_info()
        elements.append(Paragraph('基本信息', heading_style))

        basic_data = [
            ['姓名', basic_info['name']],
            ['性别', basic_info['gender']],
            ['历法', basic_info['calendar']],
            ['日期', basic_info['date']],
            ['时辰', f"{basic_info['hour']}时"],
            ['公历日期', basic_info['solar_date']],
            ['农历日期', basic_info['lunar_date']]
        ]

        basic_table = Table(basic_data, colWidths=[80, 150])
        basic_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'STSong-Light-Medium'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#5D4037')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#D4AF37')),
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#F5E6D3')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(basic_table)
        elements.append(Spacer(1, 20))

        elements.append(Paragraph('四柱八字', heading_style))
        bazi_data = self.get_bazi_data()
        pillars = ['年柱', '月柱', '日柱', '时柱']
        pillar_keys = ['year', 'month', 'day', 'hour']

        bazi_data_row = [bazi_data[key] for key in pillar_keys]
        bazi_table_data = [pillars, bazi_data_row]

        bazi_table = Table(bazi_table_data, colWidths=[120]*4)
        bazi_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'STSong-Light-Medium'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, 1), 18),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#8B7355')),
            ('TEXTCOLOR', (0, 1), (-1, 1), HexColor('#5D4037')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#D4AF37')),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#F5E6D3')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(bazi_table)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(f"日主: {bazi_data['rizhu']}", body_style))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph('五行分布', heading_style))
        wuxing_data = self.format_wuxing_for_export()

        wuxing_header = ['木', '火', '土', '金', '水']
        wuxing_count = [f"{item['count']:.1f}" for item in wuxing_data]
        wuxing_pct = [f"{item['percentage']}%" for item in wuxing_data]

        wuxing_table = Table([wuxing_header, wuxing_count, wuxing_pct], colWidths=[60]*5)
        wuxing_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'STSong-Light-Medium'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#228B22')),
            ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#DC143C')),
            ('TEXTCOLOR', (2, 0), (2, -1), HexColor('#D2691E')),
            ('TEXTCOLOR', (3, 0), (3, -1), HexColor('#708090')),
            ('TEXTCOLOR', (4, 0), (4, -1), HexColor('#1E90FF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#D4AF37')),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#FFF8E7')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(wuxing_table)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(f"五行分析: {self.get_wuxing_data()['summary']}", body_style))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph('十神分析', heading_style))
        shishen_details = self.format_shishen_for_export()

        shishen_header = ['柱位', '天干', '十神', '地支', '藏干十神']
        shishen_rows = [shishen_header]
        for detail in shishen_details:
            shishen_rows.append([
                detail['pillar'],
                detail['gan'],
                detail['gan_shishen'],
                detail['zhi'],
                ' '.join(detail['zhi_shishens'])
            ])

        shishen_table = Table(shishen_rows, colWidths=[50, 50, 60, 50, 100])
        shishen_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'STSong-Light-Medium'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#D4AF37')),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#5D4037')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#FFF8E7')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(shishen_table)
        elements.append(Spacer(1, 10))

        shishen = self.get_shishen_data()
        summary_parts = [f"日主: {shishen['rizhu']} ({shishen['rizhu_wuxing']})"]
        for name, count in shishen['summary'].items():
            summary_parts.append(f"{name}: {count}个")
        elements.append(Paragraph(' | '.join(summary_parts), body_style))

        elements.append(PageBreak())

        elements.append(Paragraph('命局分析', heading_style))
        elements.append(Spacer(1, 10))

        rizhu = bazi_data['rizhu']
        summary = []

        if self.get_wuxing_data()['summary']:
            summary.append(self.get_wuxing_data()['summary'])

        shishen_list = list(shishen['summary'].keys())
        if '正官' in shishen_list or '七杀' in shishen_list:
            summary.append('官杀混杂' if ('正官' in shishen_list and '七杀' in shishen_list) else '官杀得位')

        if '正印' in shishen_list or '偏印' in shishen_list:
            summary.append('印星护身')

        if not summary:
            summary.append('格局平和')

        geju_text = f"日主为{rizhu}，{'；'.join(summary)}"
        elements.append(Paragraph(geju_text, body_style))
        elements.append(Spacer(1, 30))

        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#999999'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph('— 八字排盘系统 —', footer_style))

        doc.build(elements)
