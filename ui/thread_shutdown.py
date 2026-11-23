# -*- coding: utf-8 -*-
"""
ui/thread_shutdown.py — QThread 协作式收尾的统一入口

背景
----
后台 QThread 以 parent 挂在 GUI 对象树上时，父对象（主窗口 / 面板 / 对话框）
会先于线程退出而销毁。Qt 在析构仍在 run() 中的 QThread 时打印
``QThread: Destroyed while thread is still running``，随后进程在退出期崩溃。
旧实现只收尾了 AI 线程与 DB 线程，历史查询、导出、设置页连通测试三类线程
完全没有进入收尾名单。

机制（唯一实现，各处复用）
--------------------------
1. ``requestInterruption()``（若线程另有 ``cancel()/stop()`` 也一并调用）；
2. ``wait(timeout_ms)`` 有限等待；
3. 超时仍未结束的线程：``setParent(None)`` 从 Qt 父对象摘除，放入模块级
   ``_SURVIVORS`` 持有强引用，等 ``finished`` 后再 ``deleteLater()`` 并移出；
   这样窗口对象树销毁时不会连带销毁仍在运行的线程；
4. 全程**不调用** ``QThread.terminate()``；
5. 全程**不调用** ``processEvents()`` 企图派发 ``DeferredDelete``
   （实测无效，且显式 sendPostedEvents 会加剧退出期崩溃）。
"""
from __future__ import annotations

import logging
from typing import Iterable, List

from PySide6.QtCore import QThread

logger = logging.getLogger(__name__)

# 仍在运行、已从 Qt 父对象摘除的线程：必须持有 Python 强引用，
# 否则 Python 包装对象被 GC 时会直接析构底层 QThread 并触发同样的崩溃。
_SURVIVORS: List[QThread] = []


def _forget(thread: QThread) -> None:
    """线程结束后移出存活列表并安排销毁（幂等，容忍底层对象已释放）。"""
    try:
        if thread in _SURVIVORS:
            _SURVIVORS.remove(thread)
    except (RuntimeError, ValueError):
        pass
    try:
        thread.deleteLater()
    except RuntimeError:
        pass


def _request_stop(thread: QThread) -> None:
    """协作式停止：只置中断标志，不打断已进入的不可中断调用（如 SQLite 查询）。"""
    try:
        thread.requestInterruption()
    except RuntimeError:
        return
    # 兼容既有 worker 的 cancel()/stop() 约定（AI worker 用 cancel）
    fn = getattr(thread, 'cancel', None) or getattr(thread, 'stop', None)
    if callable(fn):
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - 取消失败不应阻断关窗
            logger.warning('[线程收尾] 调用取消入口失败：%s', e)


def detach_until_finished(thread: QThread) -> None:
    """把仍在运行的线程从 Qt 父对象摘除，并由本模块持有到 finished。"""
    try:
        thread.setParent(None)
    except RuntimeError:
        return
    if thread in _SURVIVORS:
        return
    _SURVIVORS.append(thread)
    try:
        thread.finished.connect(lambda t=thread: _forget(t))
    except RuntimeError:
        # 底层对象已销毁：无需持有
        try:
            _SURVIVORS.remove(thread)
        except ValueError:
            pass


def shutdown_threads(threads: Iterable, timeout_ms: int = 3000) -> List[QThread]:
    """对一批线程执行协作式收尾。

    Args:
        threads: 待收尾的 QThread（允许 None / 已销毁对象）。
        timeout_ms: 单个线程的最大等待毫秒数。

    Returns:
        list: 超时仍未结束、已被摘除并托管的线程；空列表表示全部已收尾。
    """
    still_running: List[QThread] = []
    for thread in threads:
        if thread is None:
            continue
        try:
            running = thread.isRunning()
        except RuntimeError:
            continue
        _request_stop(thread)
        if not running:
            continue
        if thread.wait(timeout_ms):
            continue
        detach_until_finished(thread)
        still_running.append(thread)
    if still_running:
        logger.warning(
            '[线程收尾] %d 个线程未在 %dms 内结束，已从父对象摘除并托管至 finished'
            '（不 terminate）', len(still_running), timeout_ms)
    return still_running


def _prune_finished() -> None:
    """兜底清理：finished 信号若因事件循环未回到主线程而延迟派发，这里主动移出。"""
    for thread in list(_SURVIVORS):
        try:
            if not thread.isRunning():
                _forget(thread)
        except RuntimeError:
            try:
                _SURVIVORS.remove(thread)
            except ValueError:
                pass


def survivor_count() -> int:
    """当前受托管（仍在运行且已摘除父对象）的线程数，供诊断 / 测试使用。"""
    _prune_finished()
    return len(_SURVIVORS)
