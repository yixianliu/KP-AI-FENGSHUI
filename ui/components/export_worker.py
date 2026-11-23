"""
导出工作线程：把 PDF / Excel / CSV 导出移出 GUI 线程。

设计要点：
1. 导出先写到目标目录下的临时文件，成功后 os.replace 原子替换目标文件，
   失败则删除临时文件——避免留下半截文件，也避免失败时破坏同名旧文件。
2. 成功 / 失败都通过信号回主线程，失败携带异常摘要（而非只打印日志）。
3. 与 bazi_calculation_worker.py 保持一致的 QThread + 自定义信号写法。
"""
import os
import tempfile

from PySide6.QtCore import QThread, Signal


class ExportWorker(QThread):
    """后台执行单个导出任务的工作线程。"""

    # 成功：目标文件路径（已落盘）
    finished = Signal(str)
    # 失败：目标文件路径 + 错误类型（export_error / exception）+ 异常摘要
    failed = Signal(str, str, str)
    # 进度：阶段文案（复用面板状态标签，不引入新控件）
    progress = Signal(str)

    def __init__(self, exporter, data: dict, file_path: str,
                 format_label: str = '文件'):
        """初始化导出线程。

        Args:
            exporter: 已实例化的导出器（CsvExporter / ExcelExporter /
                PdfExporter），实例化放在主线程，依赖缺失可在点击时立即提示
            data: 已按章节过滤的导出数据字典
            file_path: 用户选择的最终目标文件路径（可含中文）
            format_label: 格式显示名（如 CSV / Excel / PDF），用于进度文案
        """
        super().__init__()
        self._exporter = exporter
        self._data = data
        self._file_path = file_path
        self._format_label = format_label or '文件'
        self.last_error = ''

    def run(self):
        """执行导出：写临时文件 -> 成功则原子替换 -> 清理临时文件 -> 发信号。"""
        # 协作式取消：尚未开工时直接退出；已开始的导出允许跑完（写临时文件 +
        # 原子替换是短事务，中途放弃反而会留下不完整状态）。
        if self.isInterruptionRequested():
            return
        tmp_path = None
        try:
            self.progress.emit(f'正在生成{self._format_label}文件…')
            tmp_path = self._make_temp_path(self._file_path)
            ok = self._exporter.export(self._data, tmp_path)
            if not ok:
                # 导出器内部已吞异常并返回 False，这里取它记录的最后一条错误摘要
                summary = (getattr(self._exporter, 'last_error', '')
                           or '导出过程中发生错误')
                self.last_error = summary
                raise ExportFailure(summary)

            os.replace(tmp_path, self._file_path)
            tmp_path = None
            self.finished.emit(self._file_path)
        except ExportFailure as e:
            self._safe_remove(tmp_path)
            self.failed.emit(self._file_path, 'export_error', str(e))
        except Exception as e:
            self._safe_remove(tmp_path)
            summary = f'{type(e).__name__}: {e}'
            self.last_error = summary
            self.failed.emit(self._file_path, 'exception', summary)

    @staticmethod
    def _make_temp_path(file_path: str) -> str:
        """在目标文件同目录创建临时文件，保证 os.replace 为同盘原子替换。

        Args:
            file_path: 目标文件路径（可含中文目录 / 文件名）

        Returns:
            str，临时文件绝对路径（沿用原扩展名，兼容按后缀判断的导出器）
        """
        directory = os.path.dirname(os.path.abspath(file_path)) or os.getcwd()
        suffix = os.path.splitext(file_path)[1] or '.tmp'
        # mkstemp 会在目录不可写时抛出，交由 run 的异常分支回传 UI
        fd, tmp = tempfile.mkstemp(prefix='.kp_export_', suffix=suffix,
                                   dir=directory)
        os.close(fd)
        return tmp

    @staticmethod
    def _safe_remove(path: str) -> None:
        """删除临时文件；清理失败不再向上抛，避免掩盖真正的导出错误。"""
        if not path:
            return
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


class ExportFailure(Exception):
    """导出器返回 False 时用于走统一失败分支的内部异常。"""
