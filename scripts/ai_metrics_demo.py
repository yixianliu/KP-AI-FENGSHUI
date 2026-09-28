# -*- coding: utf-8 -*-
"""
scripts/ai_metrics_demo.py
AI 缓存命中率与熔断历史曲线演示脚本
"""
import sys
sys.path.insert(0, '.')
import random
from datetime import datetime, timedelta
from ui.components.ai_metrics_chart import AIMetricsChart
from PySide6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    chart = AIMetricsChart()
    chart.show()
    # 生成演示数据
    now = datetime.now()
    cache_data = []
    circuit_data = []
    for i in range(48):
        t = now - timedelta(hours=47 - i)
        rate = 65 + random.uniform(-10, 25)
        cache_data.append((t, max(0, min(100, rate))))
        count = random.choices([0, 1, 2, 3], weights=[80, 12, 5, 3])[0]
        circuit_data.append((t, count))
    chart.update_charts(cache_data, circuit_data)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
