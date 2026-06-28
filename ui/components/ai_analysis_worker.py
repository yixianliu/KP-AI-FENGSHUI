"""
AI分析Worker线程模块
实现在后台线程中执行AI分析，避免UI阻塞
支持Redis轮询机制读取分析结果
"""
import sys
import time
from pathlib import Path
from PySide6.QtCore import QThread, Signal, QObject

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.analysis_pipeline import AnalysisPipeline
from core.redis_manager import get_redis_manager, RedisConnectionError, RedisOperationError


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
            task_id: 任务ID，用于Redis数据关联
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

            self.progress_updated.emit('initializing', '正在初始化AI分析引擎...')
            pipeline = AnalysisPipeline()

            if self.analysis_type == 'bazi':
                self.progress_updated.emit('analyzing', 'AI正在深入分析八字命理...')
                result = pipeline.run_bazi_analysis(self.input_data, self.chart_data, self.task_id)
            elif self.analysis_type == 'meihua':
                self.progress_updated.emit('analyzing', 'AI正在解读卦象玄机...')
                result = pipeline.run_meihua_analysis(self.input_data, self.chart_data, self.task_id)
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

    def _poll_redis_result(self, max_retries: int = 30, interval: float = 1.0) -> dict:
        """
        从Redis轮询分析结果

        Args:
            max_retries: 最大重试次数
            interval: 轮询间隔（秒）

        Returns:
            分析结果字典，如果超时或失败返回空字典
        """
        if not self.task_id:
            return {}

        try:
            redis_manager = get_redis_manager()
            if not redis_manager:
                return {}

            for i in range(max_retries):
                if not self._is_running:
                    break

                result = redis_manager.get_task_result(self.analysis_type, self.task_id)
                if result:
                    return result

                status = redis_manager.get_task_status(self.analysis_type, self.task_id)
                if status == 'failed':
                    result = redis_manager.get_task_result(self.analysis_type, self.task_id)
                    return result or {'success': False, 'error_type': 'analysis_failed', 'error_message': '分析失败'}

                time.sleep(interval)
                self.progress_updated.emit('polling', f'等待分析结果 ({i + 1}/{max_retries})')

            return {'success': False, 'error_type': 'timeout', 'error_message': '分析超时'}

        except (RedisConnectionError, RedisOperationError) as e:
            return {'success': False, 'error_type': 'redis_error', 'error_message': f'Redis连接错误: {e}'}
        except Exception as e:
            return {'success': False, 'error_type': 'polling_error', 'error_message': f'轮询错误: {e}'}


class AiAnalysisManager(QObject):
    """
    AI分析管理器
    管理分析工作线程的创建、执行和结果处理
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._result_cache = {}

    def start_analysis(self, analysis_type: str, input_data: dict, chart_data: dict = None, task_id: str = None) -> AiAnalysisWorker:
        """
        启动AI分析

        Args:
            analysis_type: 分析类型
            input_data: 输入数据
            chart_data: 排盘数据
            task_id: 任务ID，用于Redis数据关联

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
