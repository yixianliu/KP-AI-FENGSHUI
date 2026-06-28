"""
地点数据库 - 适配新UI的简化接口
数据从数据库 city_coords 表加载
"""

from core.database_manager import DatabaseManager


def _get_db():
    return DatabaseManager()


class LocationDB:
    """地点数据库"""

    def __init__(self):
        # 从数据库加载城市坐标数据
        db = _get_db()
        self.cities = db.get_city_coords()

    def get_coords(self, city_name):
        """获取城市坐标"""
        return self.cities.get(city_name, (120.0, 30.0))

    def get_all_cities(self):
        """获取所有城市列表"""
        return list(self.cities.keys())

    def search_city(self, keyword):
        """搜索城市"""
        results = []
        for city in self.cities:
            if keyword in city:
                results.append(city)
        return results
