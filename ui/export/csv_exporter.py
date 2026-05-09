from ui.export.base_exporter import BaseExporter
import csv

class CsvExporter(BaseExporter):
    def perform_export(self, file_path):
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            writer.writerow(['八字排盘导出报告'])
            writer.writerow(['导出时间', self.get_export_timestamp()])
            writer.writerow([])

            writer.writerow(['基本信息'])
            basic_info = self.get_basic_info()
            for key, value in basic_info.items():
                writer.writerow([key, value])
            writer.writerow([])

            writer.writerow(['四柱八字'])
            bazi_data = self.get_bazi_data()
            pillars = ['年柱', '月柱', '日柱', '时柱']
            pillar_keys = ['year', 'month', 'day', 'hour']
            for pillar, key in zip(pillars, pillar_keys):
                writer.writerow([pillar, bazi_data[key]])
            writer.writerow(['日主', bazi_data['rizhu']])
            writer.writerow([])

            writer.writerow(['五行分布'])
            writer.writerow(['五行', '数量', '百分比'])
            wuxing_data = self.format_wuxing_for_export()
            for item in wuxing_data:
                writer.writerow([
                    item['element'],
                    f"{item['count']:.1f}",
                    f"{item['percentage']}%"
                ])
            writer.writerow([])

            writer.writerow(['十神分析'])
            shishen_data = self.format_shishen_for_export()
            writer.writerow(['柱位', '天干', '十神', '地支', '藏干十神'])
            for detail in shishen_data:
                writer.writerow([
                    detail['pillar'],
                    detail['gan'],
                    detail['gan_shishen'],
                    detail['zhi'],
                    ' '.join(detail['zhi_shishens'])
                ])
            writer.writerow([])

            writer.writerow(['命局分析'])
            shishen = self.get_shishen_data()
            writer.writerow(['日主', shishen['rizhu'], shishen['rizhu_wuxing']])
            writer.writerow(['十神统计'])
            for name, count in shishen['summary'].items():
                writer.writerow([name, f'{count}个'])
