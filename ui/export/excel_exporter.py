"""
Excel 导出器
支持按"可选章节"导出：基本信息 / 命局类型 / 四柱八字 / 五行分析 /
十神分析 / 大运流年（含起运）/ 运程总结（事业/财运/健康/感情）/
吉凶批注 / AI 智能分析。调用方已用 filter_export_data
过滤 data，本导出器再按数据键是否存在逐项渲染。
"""
from typing import Dict, Any
from .base_exporter import BaseExporter, has_chapter

# 惰性导入：未安装 openpyxl 时仅置为 None，不影响本模块导入与 app 启动；
# 只有在真正实例化 / 调用 Excel 导出时才提示安装。
try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
except ImportError:
    openpyxl = None
    Font = Alignment = PatternFill = Border = Side = None

# AI 字段 -> 中文标题（与 PDF 导出保持一致）
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


class ExcelExporter(BaseExporter):
    """Excel 导出器"""

    def __init__(self):
        if openpyxl is None:
            raise RuntimeError(
                "缺少依赖 openpyxl，无法导出 Excel，请先安装：pip install openpyxl"
            )
        self.styles = {
            'title': Font(name='微软雅黑', size=14, bold=True, color='FF333333'),
            'header': Font(name='微软雅黑', size=12, bold=True, color='FF5D4037'),
            'content': Font(name='微软雅黑', size=11, color='FF333333'),
            'center': Alignment(horizontal='center', vertical='center'),
            'left': Alignment(horizontal='left', vertical='center'),
            'border': Border(
                left=Side(style='thin', color='FFD4AF37'),
                right=Side(style='thin', color='FFD4AF37'),
                top=Side(style='thin', color='FFD4AF37'),
                bottom=Side(style='thin', color='FFD4AF37')
            ),
            'fill_gold': PatternFill(start_color='FFD4AF37', end_color='FFD4AF37', fill_type='solid'),
            'fill_light': PatternFill(start_color='FFFFF8E7', end_color='FFFFF8E7', fill_type='solid')
        }

    def export(self, data: Dict[str, Any], file_path: str) -> bool:
        if openpyxl is None:
            raise RuntimeError(
                "缺少依赖 openpyxl，无法导出 Excel，请先安装：pip install openpyxl"
            )
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = '八字排盘结果'

            row = 1
            ws.merge_cells(f'A{row}:B{row}')
            title_cell = ws.cell(row=row, column=1, value='八字排盘分析结果')
            title_cell.font = self.styles['title']
            title_cell.alignment = self.styles['center']
            row += 2

            # 基本信息
            if has_chapter(data, 'basic_info'):
                row = self._add_section(ws, row, '基本信息', data.get('basic_info', {})) + 2

            # 命局类型（含用神喜忌）
            if has_chapter(data, 'bazi_types'):
                row = self._add_bazi_types_section(ws, row, data.get('bazi_types', {})) + 2

            # 四柱八字
            if has_chapter(data, 'bazi'):
                row = self._add_section(ws, row, '四柱八字', data.get('bazi', {})) + 2

            # 五行分析
            if has_chapter(data, 'wuxing'):
                row = self._add_wuxing_section(ws, row, '五行分析', data.get('wuxing', {})) + 2

            # 十神分析
            if has_chapter(data, 'shishen'):
                row = self._add_shishen_section(ws, row, '十神分析', data.get('shishen', {})) + 2

            # 大运流年
            if has_chapter(data, 'yunshi'):
                row = self._add_yunshi_section(ws, row, data) + 2

            # 运程总结（事业 / 财运 / 健康 / 感情）
            if has_chapter(data, 'yuncheng'):
                row = self._add_yuncheng_section(ws, row, data.get('yuncheng', {})) + 2

            # 神煞
            mingli = data.get('mingli', {}) or {}
            shensha = mingli.get('shensha', [])
            if shensha:
                self._add_shensha_section(ws, row, '神煞', shensha)
                row += len(shensha) + 3

            # 吉凶批注
            analysis = data.get('analysis', []) or []
            if analysis:
                self._add_analysis_section(ws, row, '吉凶批注', analysis)
                row += len(analysis) + 3

            # AI 智能分析
            if has_chapter(data, 'ai_analysis'):
                self._add_ai_section(ws, row, data.get('ai_analysis', {}))

            ws.column_dimensions['A'].width = 22
            ws.column_dimensions['B'].width = 60

            wb.save(file_path)
            return True
        except Exception as e:
            print(f"Excel 导出失败: {e}")
            return False

    def _add_section(self, ws, start_row, title, data: dict) -> int:
        """添加键值区块，返回下一空行行号"""
        ws.merge_cells(f'A{start_row}:B{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value=title)
        title_cell.font = self.styles['header']
        title_cell.alignment = self.styles['center']
        title_cell.fill = self.styles['fill_gold']
        title_cell.border = self.styles['border']

        row = start_row + 1
        for key, value in data.items():
            self._cell(ws, row, 1, str(key), align='left')
            self._cell(ws, row, 2, str(value), align='left')
            row += 1
        return row

    def _add_bazi_types_section(self, ws, start_row, bt: dict) -> int:
        ws.merge_cells(f'A{start_row}:B{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value='命局类型')
        title_cell.font = self.styles['header']
        title_cell.alignment = self.styles['center']
        title_cell.fill = self.styles['fill_gold']
        title_cell.border = self.styles['border']

        row = start_row + 1
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
        if ys.get('yongshen'):
            rows.append(('用神', f"{ys.get('yongshen')}（{ys.get('yongshen_name')}）"))
            if ys.get('xishen_names'):
                rows.append(('喜神', '、'.join(ys.get('xishen_names'))))
            if ys.get('jishen_names'):
                rows.append(('忌神', '、'.join(ys.get('jishen_names'))))

        for k, v in rows:
            self._cell(ws, row, 1, str(k), align='left')
            self._cell(ws, row, 2, str(v), align='left')
            row += 1
        if row == start_row + 1:  # 无内容
            row += 1
        return row

    def _add_wuxing_section(self, ws, start_row, title, wuxing_data: dict) -> int:
        return self._add_section(ws, start_row, title, wuxing_data)

    def _add_shishen_section(self, ws, start_row, title, shishen_data: dict) -> int:
        return self._add_section(ws, start_row, title, shishen_data)

    def _add_yunshi_section(self, ws, start_row, data: dict) -> int:
        ws.merge_cells(f'A{start_row}:B{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value='大运流年')
        title_cell.font = self.styles['header']
        title_cell.alignment = self.styles['center']
        title_cell.fill = self.styles['fill_gold']
        title_cell.border = self.styles['border']

        row = start_row + 1
        dayun = data.get('dayun', {}) or {}
        liunian = data.get('liunian', {}) or {}
        periods = dayun.get('periods', []) if isinstance(dayun, dict) else []
        years = liunian.get('years', []) if isinstance(liunian, dict) else []

        if periods:
            self._cell(ws, row, 1, '大运', align='left')
            self._cell(ws, row, 2, str(dayun.get('direction', '')), align='left')
            row += 1
            qiyun = dayun.get('qiyun_text')
            if qiyun:
                self._cell(ws, row, 1, '起运', align='left')
                self._cell(ws, row, 2, str(qiyun), align='left')
                row += 1
            for p in periods:
                label = (f"第{p.get('period')}运 {p.get('ganzhi')} "
                         f"（{p.get('start_age')}-{p.get('end_age')}岁，"
                         f"{p.get('start_year')}-{p.get('end_year')}年）")
                self._cell(ws, row, 1, label, align='left')
                self._cell(ws, row, 2, str(p.get('analysis', '')), align='left')
                row += 1
        if years:
            self._cell(ws, row, 1, '流年', align='left')
            self._cell(ws, row, 2, '', align='left')
            row += 1
            for y in years:
                label = f"{y.get('year')}年 {y.get('ganzhi')}"
                self._cell(ws, row, 1, label, align='left')
                self._cell(ws, row, 2, str(y.get('analysis', '')), align='left')
                row += 1
        if row == start_row + 1:
            row += 1
        return row

    def _add_yuncheng_section(self, ws, start_row, yc: dict) -> int:
        ws.merge_cells(f'A{start_row}:B{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value='运程总结')
        title_cell.font = self.styles['header']
        title_cell.alignment = self.styles['center']
        title_cell.fill = self.styles['fill_gold']
        title_cell.border = self.styles['border']

        row = start_row + 1
        overview = yc.get('overview')
        if overview:
            self._cell(ws, row, 1, '综合', align='left')
            self._cell(ws, row, 2, str(overview), align='left')
            row += 1
        for key, label in (('career', '事业'), ('wealth', '财运'),
                           ('health', '健康'), ('love', '感情')):
            text = yc.get(key)
            if text:
                self._cell(ws, row, 1, label, align='left')
                self._cell(ws, row, 2, str(text), align='left')
                row += 1
        tags = yc.get('tags') or []
        if tags:
            self._cell(ws, row, 1, '标签', align='left')
            self._cell(ws, row, 2, '、'.join(str(t) for t in tags), align='left')
            row += 1
        if row == start_row + 1:
            row += 1
        return row

    def _add_shensha_section(self, ws, start_row, title, shensha_list):
        ws.merge_cells(f'A{start_row}:B{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value=title)
        title_cell.font = self.styles['header']
        title_cell.alignment = self.styles['center']
        title_cell.fill = self.styles['fill_gold']
        title_cell.border = self.styles['border']

        row = start_row + 1
        for ss in shensha_list:
            self._cell(ws, row, 1, str(ss.get('name', '')), align='left')
            self._cell(ws, row, 2, str(ss.get('description', '')), align='left')
            row += 1

    def _add_analysis_section(self, ws, start_row, title, analysis_list):
        ws.merge_cells(f'A{start_row}:B{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value=title)
        title_cell.font = self.styles['header']
        title_cell.alignment = self.styles['center']
        title_cell.fill = self.styles['fill_gold']
        title_cell.border = self.styles['border']

        row = start_row + 1
        for an in analysis_list:
            type_color = 'FFC45545' if an.get('type') == '凶' else 'FF4CAF50' if an.get('type') == '吉' else 'FFFFA726'
            self._cell(ws, row, 1, str(an.get('type', '')), fill=type_color, align='center')
            self._cell(ws, row, 2, str(an.get('text', '')), align='left')
            row += 1

    def _add_ai_section(self, ws, start_row, ai: dict):
        ws.merge_cells(f'A{start_row}:B{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value='AI 智能深度分析')
        title_cell.font = self.styles['header']
        title_cell.alignment = self.styles['center']
        title_cell.fill = self.styles['fill_gold']
        title_cell.border = self.styles['border']

        row = start_row + 1
        for key, title in _AI_SECTIONS:
            items = ai.get(key, []) or []
            if not items:
                continue
            self._cell(ws, row, 1, title, align='left')
            self._cell(ws, row, 2, '', align='left')
            row += 1
            for it in items:
                self._cell(ws, row, 1, '•', align='center')
                self._cell(ws, row, 2, str(it), align='left')
                row += 1

    def _cell(self, ws, r, c, value, align='left', fill=None):
        cell = ws.cell(row=r, column=c, value=value)
        cell.font = self.styles['content']
        cell.alignment = self.styles[align]
        cell.border = self.styles['border']
        if fill:
            cell.fill = PatternFill(start_color=fill, end_color=fill, fill_type='solid')

    def get_file_extension(self) -> str:
        return '.xlsx'
