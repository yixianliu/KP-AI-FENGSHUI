"""
ui/components/pan_task_worker.py — 排盘/起卦落库等轻量后台任务线程

用途：把「不该占用 GUI 线程」的工作（落库写盘、可能加锁 30s 的 SQLite 写入）
搬到后台执行，供八字与梅花两个板块共用同一份实现，避免每块面板各复制一套。

约定：
    - 只执行传入的 ``task(worker)`` 可调用对象，不关心业务细节；
    - 成功发 ``succeeded``（携带任意 payload），失败发 ``failed``（错误类型 + 文案）；
    - 线程基类自带的 ``finished`` 信号保持原样（未重定义），因此主窗口的
      ``_register_worker`` / 统一收尾逻辑可以直接复用；
    - 取消走 ``requestInterruption()``，绝不使用 ``QThread.terminate()``。
"""
from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class PanTaskWorker(QThread):
    """轻量后台任务线程：跑一个可调用对象，结束后回传结果或错误。"""

    #: 任务成功：payload 为任务返回值（任意可序列化对象均可）
    succeeded = Signal(object)
    #: 任务失败：(错误类型, 可读文案)
    failed = Signal(str, str)
    #: 进度：(阶段, 提示文案)
    progress = Signal(str, str)

    def __init__(self, task: Callable[['PanTaskWorker'], Any], label: str = '',
                 parent=None):
        """
        Args:
            task: 在后台线程执行的可调用对象，入参为 worker 自身（可用其 emit 进度）。
            label: 任务名称，仅用于日志定位。
            parent: Qt 父对象（通常传 None，由主窗口自行持有引用）。
        """
        super().__init__(parent)
        self._task = task
        self._label = label or 'pan_task'

    def cancel(self):
        """请求取消：只置中断标志，由 run() 在安全点检查。"""
        self.requestInterruption()

    def run(self):
        """执行任务；异常一律转为 failed 信号，绝不让线程静默退出。"""
        try:
            payload = self._task(self)
            if self.isInterruptionRequested():
                logger.info('[%s] 已取消，丢弃本次结果', self._label)
                return
            self.succeeded.emit(payload)
        except ValueError as e:
            # 输入类错误单独标记，便于 GUI 用「输入错误」措辞提示
            self.failed.emit('validation_error', str(e))
        except Exception as e:  # noqa: BLE001 - 后台线程必须兜住所有异常
            traceback.print_exc()
            self.failed.emit('calculation_error', str(e))
