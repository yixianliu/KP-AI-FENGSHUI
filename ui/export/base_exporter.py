from abc import ABC, abstractmethod
import datetime

class BaseExporter(ABC):
    def __init__(self):
        self.data = None

    def export(self, data, file_path):
        self.data = data
        self.validate_data()
        self.perform_export(file_path)

    @abstractmethod
    def perform_export(self, file_path):
        pass

    def validate_data(self):
        if not self.data:
            raise ValueError("没有可导出的数据")

        required_keys = ['input', 'bazhi', 'wuxing', 'shishen']
        for key in required_keys:
            if key not in self.data:
                raise ValueError(f"数据缺少必要的字段: {key}")

    def get_basic_info(self):
        return {
            'name': self.data['input']['name'],
            'gender': self.data['input']['gender'],
            'calendar': '农历' if self.data['input']['is_lunar'] else '公历',
            'date': f"{self.data['input']['year']}-{self.data['input']['month']}-{self.data['input']['day']}",
            'hour': self.data['input']['hour'],
            'solar_date': self.data['bazhi']['solar_date'],
            'lunar_date': self.data['bazhi']['lunar_date']
        }

    def get_bazi_data(self):
        return {
            'year': self.data['bazhi']['year'],
            'month': self.data['bazhi']['month'],
            'day': self.data['bazhi']['day'],
            'hour': self.data['bazhi']['hour'],
            'rizhu': self.data['bazhi']['rizhu']
        }

    def get_wuxing_data(self):
        return self.data['wuxing']

    def get_shishen_data(self):
        return self.data['shishen']

    def format_wuxing_for_export(self):
        wuxing = self.get_wuxing_data()
        elements = ['木', '火', '土', '金', '水']
        result = []
        for element in elements:
            if element in wuxing:
                result.append({
                    'element': element,
                    'count': wuxing[element]['count'],
                    'percentage': wuxing[element]['percentage']
                })
        return result

    def format_shishen_for_export(self):
        shishen = self.get_shishen_data()
        return shishen['details']

    def get_export_timestamp(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
