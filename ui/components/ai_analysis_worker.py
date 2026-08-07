"""
AI分析Worker线程模块
实现在后台线程中执行AI分析，避免UI阻塞（同步执行，结果经信号回传 UI）
"""
from PySide6.QtCore import QThread, Signal, QObject

# NOTE: sys.path 已在 main.py 入口统一注入，此处不再重复 inject

from core.analysis_pipeline import AnalysisPipeline


class AiAnalysisWorker(QThread):
    """
    AI分析工作线程
    在后台线程中执行AI分析，通过信号与UI线程通信
    """

    progress_updated = Signal(str, str)
    analysis_finished = Signal(dict)
    analysis_failed = Signal(str, str)

    def __init__(self, analysis_type: str, input_data: dict, chart_data: dict = None, task_id: str = None):
        """
        初始化分析工作线程

        Args:
            analysis_type: 分析类型 ('bazi' 或 'meihua')
            input_data: 输入数据
            chart_data: 排盘/卦象数据
            task_id: 任务ID（用于日志关联，可选）
        """
        super().__init__()
        self.analysis_type = analysis_type
        self.input_data = input_data
        self.chart_data = chart_data or {}
        self.task_id = task_id
        self._is_running = True

    def run(self):
        """执行分析任务"""
        try:
            self.progress_updated.emit('validating', '正在验证输入数据...')

            self.progress_updated.emit('initializing', '正在初始化龙虎山大师兄分析引擎...')
            pipeline = AnalysisPipeline()

            if self.analysis_type == 'bazi':
                self.progress_updated.emit('analyzing', '龙虎山大师兄正在深入分析八字命理...')
                result = pipeline.run_bazi_analysis(self.input_data, self.chart_data, self.task_id)
            elif self.analysis_type == 'meihua':
                self.progress_updated.emit('analyzing', '龙虎山大师兄正在解读卦象玄机...')
                result = pipeline.run_meihua_analysis(self.input_data, self.chart_data, self.task_id)
            elif self.analysis_type == 'liuren':
                self.progress_updated.emit('analyzing', '龙虎山大师兄正在解读六壬玄机...')
                result = pipeline.run_liuren_analysis(self.input_data, self.chart_data, self.task_id)
            elif self.analysis_type == 'comprehensive':
                self.progress_updated.emit('analyzing', '龙虎山大师兄正在统筹三方结论，生成综合建议...')
                # chart_data 此处承载 {'parts': 三方分析, 'meta': 补充信息}
                parts = (self.chart_data or {}).get('parts', {})
                meta = (self.chart_data or {}).get('meta', {})
                result = pipeline.run_comprehensive_analysis(parts, meta, self.task_id)
            else:
                self.analysis_failed.emit('unknown_type', f'不支持的分析类型: {self.analysis_type}')
                return

            if result.get('success'):
                self.progress_updated.emit('completed', '分析完成！')
                self.analysis_finished.emit(result)
            else:
                error_type = result.get('error_type', 'unknown')
                error_msg = result.get('error_message', '未知错误')
                self.analysis_failed.emit(error_type, error_msg)

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.analysis_failed.emit('exception', f'{str(e)}\n{error_detail}')

    def stop(self):
        """停止分析任务"""
        self._is_running = False


class AiAnalysisManager(QObject):
    """
    AI分析管理器
    管理分析工作线程的创建、执行和结果处理
    """

    def __init__(self, parent=None):
        """
        初始化分析管理器。

        生命周期约定：同一时刻只持有一个工作线程 self._worker。新任务启动前会先
        等待上一个线程自然结束（见 start_analysis），且线程对象必须由本管理器长期
        持有——若不保留 Python 引用，QThread 会在函数返回后被回收，触发
        "QThread: Destroyed while thread is still running" 崩溃。

        Args:
            parent: Qt 父对象（通常为主窗口），用于随父对象一并析构。
        """
        super().__init__(parent)
        self._worker = None      # 当前（或最近一次）的工作线程，兼作保活引用
        self._result_cache = {}  # 预留的结果缓存，便于后续按 task_id 复用分析结果

    def start_analysis(self, analysis_type: str, input_data: dict, chart_data: dict = None, task_id: str = None) -> AiAnalysisWorker:
        """
        启动AI分析

        Args:
            analysis_type: 分析类型
            input_data: 输入数据
            chart_data: 排盘数据
            task_id: 任务ID（用于日志关联，可选）

        Returns:
            Worker线程对象
        """
        if self._worker and self._worker.isRunning():
            self._worker.wait()

        self._worker = AiAnalysisWorker(analysis_type, input_data, chart_data, task_id)
        self._worker.start()
        return self._worker

    def is_running(self) -> bool:
        """检查是否有分析任务正在运行"""
        return self._worker is not None and self._worker.isRunning()

    def stop_current(self):
        """停止当前分析任务"""
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
