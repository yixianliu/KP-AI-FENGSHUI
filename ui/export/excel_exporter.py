from ui.export.base_exporter import BaseExporter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

class ExcelExporter(BaseExporter):
    def perform_export(self, file_path):
        wb = Workbook()

        self.create_basic_sheet(wb)
        self.create_bazi_sheet(wb)
        self.create_wuxing_sheet(wb)
        self.create_shishen_sheet(wb)
        self.create_summary_sheet(wb)

        wb.remove(wb.active)

        wb.save(file_path)

    def create_basic_sheet(self, wb):
        ws = wb.create_sheet('基本信息')

        header_fill = PatternFill(start_color='5D4037', end_color='5D4037', fill_type='solid')
        header_font = Font(name='SimHei', size=12, bold=True, color='FFFFFF')
        cell_font = Font(name='Microsoft YaHei', size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        ws['A1'] = '八字排盘导出报告'
        ws['A1'].font = Font(name='SimHei', size=16, bold=True, color='D4AF37')
        ws.merge_cells('A1:B1')

        ws['A2'] = '导出时间'
        ws['B2'] = self.get_export_timestamp()

        ws['A4'] = '基本信息'
        ws['A4'].font = header_font
        ws['A4'].fill = header_fill
        ws.merge_cells('A4:B4')

        basic_info = self.get_basic_info()
        labels = ['姓名', '性别', '历法', '日期', '时辰', '公历日期', '农历日期']
        keys = ['name', 'gender', 'calendar', 'date', 'hour', 'solar_date', 'lunar_date']

        for i, (label, key) in enumerate(zip(labels, keys), start=5):
            ws.cell(row=i, column=1, value=label).font = cell_font
            ws.cell(row=i, column=1).border = border
            ws.cell(row=i, column=2, value=basic_info.get(key, '')).font = cell_font
            ws.cell(row=i, column=2).border = border

        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25

    def create_bazi_sheet(self, wb):
        ws = wb.create_sheet('四柱八字')

        header_fill = PatternFill(start_color='5D4037', end_color='5D4037', fill_type='solid')
        header_font = Font(name='SimHei', size=12, bold=True, color='FFFFFF')
        cell_font = Font(name='Microsoft YaHei', size=11)
        title_font = Font(name='SimHei', size=14, bold=True, color='5D4037')
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        ws['A1'] = '四柱八字'
        ws['A1'].font = title_font
        ws.merge_cells('A1:D1')

        bazi_data = self.get_bazi_data()
        pillars = ['年柱', '月柱', '日柱', '时柱']
        pillar_keys = ['year', 'month', 'day', 'hour']

        ws.append([''] + pillars)
        for col in range(1, 5):
            cell = ws.cell(row=2, column=col+1)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = border

        ws.append(['干支'] + [bazi_data[key] for key in pillar_keys])
        for col in range(1, 5):
            cell = ws.cell(row=3, column=col+1)
            cell.font = Font(name='SimHei', size=18, bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.border = border

        ws['A4'] = '日主'
        ws['B4'] = bazi_data['rizhu']
        ws['A4'].font = cell_font
        ws['B4'].font = Font(name='SimHei', size=14, bold=True)
        ws['B4'].alignment = Alignment(horizontal='center')

        for col in range(1, 5):
            ws.column_dimensions[get_column_letter(col+1)].width = 12

    def create_wuxing_sheet(self, wb):
        ws = wb.create_sheet('五行分布')

        header_fill = PatternFill(start_color='5D4037', end_color='5D4037', fill_type='solid')
        header_font = Font(name='SimHei', size=12, bold=True, color='FFFFFF')
        title_font = Font(name='SimHei', size=14, bold=True, color='5D4037')
        cell_font = Font(name='Microsoft YaHei', size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        colors = {
            '木': '228B22',
            '火': 'DC143C',
            '土': 'D2691E',
            '金': '708090',
            '水': '1E90FF'
        }

        ws['A1'] = '五行分布'
        ws['A1'].font = title_font
        ws.merge_cells('A1:D1')

        ws.append(['', '木', '火', '土', '金', '水'])
        for col in range(1, 6):
            cell = ws.cell(row=2, column=col+1)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = border

        wuxing_data = self.format_wuxing_for_export()
        ws.append(['数量'] + [f"{item['count']:.1f}" for item in wuxing_data])
        for col in range(1, 6):
            cell = ws.cell(row=3, column=col+1)
            cell.font = cell_font
            cell.alignment = Alignment(horizontal='center')
            cell.border = border

        ws.append(['百分比'] + [f"{item['percentage']}%" for item in wuxing_data])
        for col in range(1, 6):
            cell = ws.cell(row=4, column=col+1)
            cell.font = cell_font
            cell.alignment = Alignment(horizontal='center')
            cell.border = border

        for col in range(1, 6):
            ws.column_dimensions[get_column_letter(col+1)].width = 12

    def create_shishen_sheet(self, wb):
        ws = wb.create_sheet('十神分析')

        header_fill = PatternFill(start_color='5D4037', end_color='5D4037', fill_type='solid')
        header_font = Font(name='SimHei', size=12, bold=True, color='FFFFFF')
        title_font = Font(name='SimHei', size=14, bold=True, color='5D4037')
        cell_font = Font(name='Microsoft YaHei', size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        ws['A1'] = '十神分析'
        ws['A1'].font = title_font
        ws.merge_cells('A1:E1')

        headers = ['柱位', '天干', '十神', '地支', '藏干十神']
        ws.append([''] + headers)
        for col in range(1, 6):
            cell = ws.cell(row=2, column=col+1)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = border

        shishen_data = self.format_shishen_for_export()
        for row_idx, detail in enumerate(shishen_data, start=3):
            ws.append([
                '',
                detail['pillar'],
                detail['gan'],
                detail['gan_shishen'],
                detail['zhi'],
                ' '.join(detail['zhi_shishens'])
            ])
            for col in range(1, 6):
                cell = ws.cell(row=row_idx, column=col+1)
                cell.font = cell_font
                cell.alignment = Alignment(horizontal='center')
                cell.border = border

        ws['A7'] = '日主'
        ws['B7'] = self.data['shishen']['rizhu']
        ws['C7'] = self.data['shishen']['rizhu_wuxing']
        ws['A7'].font = cell_font
        ws['B7'].font = Font(name='SimHei', size=12, bold=True)
        ws['C7'].font = cell_font

        for col in range(1, 6):
            ws.column_dimensions[get_column_letter(col+1)].width = 14

    def create_summary_sheet(self, wb):
        ws = wb.create_sheet('命局总结')

        header_fill = PatternFill(start_color='5D4037', end_color='5D4037', fill_type='solid')
        header_font = Font(name='SimHei', size=12, bold=True, color='FFFFFF')
        title_font = Font(name='SimHei', size=14, bold=True, color='5D4037')
        cell_font = Font(name='Microsoft YaHei', size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        ws['A1'] = '命局总结'
        ws['A1'].font = title_font
        ws.merge_cells('A1:B1')

        shishen = self.get_shishen_data()

        ws['A3'] = '十神统计'
        ws['A3'].font = header_font
        ws['A3'].fill = header_fill
        ws.merge_cells('A3:B3')

        row = 4
        for name, count in shishen['summary'].items():
            ws.cell(row=row, column=1, value=name).font = cell_font
            ws.cell(row=row, column=1).border = border
            ws.cell(row=row, column=2, value=f'{count}个').font = cell_font
            ws.cell(row=row, column=2).border = border
            row += 1

        ws['A' + str(row+1)] = '五行分析'
        ws['A' + str(row+1)].font = header_font
        ws['A' + str(row+1)].fill = header_fill
        ws.merge_cells(f'A{row+1}:B{row+1}')

        row += 2
        wuxing = self.get_wuxing_data()
        elements = ['木', '火', '土', '金', '水']
        for element in elements:
            if element in wuxing:
                ws.cell(row=row, column=1, value=element).font = cell_font
                ws.cell(row=row, column=1).border = border
                ws.cell(row=row, column=2, value=f"{wuxing[element]['count']:.1f} ({wuxing[element]['percentage']}%)").font = cell_font
                ws.cell(row=row, column=2).border = border
                row += 1

        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 20
