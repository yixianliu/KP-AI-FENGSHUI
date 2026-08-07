# -*- coding: utf-8 -*-
"""
tests/_support.py — 测试公共支撑模块

存在意义：
    `core.debug_keys` 提供「源码调试时自动注入本地密钥」的兜底能力。
    该兜底会让 AIConfigManager 在没有 GUI 配置时也返回一个可用配置档，
    从而破坏那些断言「初始为未配置状态」的用例。

    多个测试文件都需要同一套「临时屏蔽调试密钥」的前后置逻辑，
    集中在本模块，避免各测试文件重复实现 setUp / tearDown。
"""
import os
import sys
import unittest

# 保证测试可直接 import 项目根下的 core / api / scripts 包
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 调试密钥的环境变量名，与 core.debug_keys._ENV_KEY 保持一致
ENV_KEY = 'KP_AGNES_API_KEY'


class DebugKeyGuard:
    """临时屏蔽调试兜底密钥的守卫对象。

    调用 :meth:`activate` 后，环境变量与模块常量两个密钥来源都会被清空；
    调用 :meth:`restore` 精确还原到激活前的状态（包括「原本就不存在」这一情形）。

    典型用法::

        guard = DebugKeyGuard()
        guard.activate()
        try:
            ...  # 此段代码内 get_debug_keys() 必定返回 None
        finally:
            guard.restore()
    """

    def __init__(self):
        """初始化守卫的内部状态（保存位与模块引用均置空）。"""
        # 激活前的环境变量值；None 表示激活前该变量不存在
        self._saved_env = None
        # 激活前的模块常量值
        self._saved_const = ''
        # core.debug_keys 模块引用，restore 时用于写回常量
        self._module = None
        # 防止重复 activate 导致保存值被覆盖
        self._active = False

    def activate(self):
        """清空两个调试密钥来源，并记录原值以便还原。"""
        if self._active:
            return
        import core.debug_keys as debug_keys

        self._module = debug_keys
        self._saved_env = os.environ.pop(ENV_KEY, None)
        self._saved_const = debug_keys.DEBUG_AGNES_API_KEY
        debug_keys.DEBUG_AGNES_API_KEY = ''
        self._active = True

    def restore(self):
        """还原激活前的环境变量与模块常量。"""
        if not self._active:
            return
        self._module.DEBUG_AGNES_API_KEY = self._saved_const
        if self._saved_env is not None:
            os.environ[ENV_KEY] = self._saved_env
        else:
            os.environ.pop(ENV_KEY, None)
        self._active = False

    # 支持 with 语句，便于在单个用例内局部屏蔽
    def __enter__(self):
        """进入 with 上下文时激活屏蔽；返回守卫自身。"""
        self.activate()
        return self

    def __exit__(self, exc_type, exc, tb):
        """退出 with 上下文时还原调试密钥来源；异常不在此吞掉。"""
        self.restore()
        return False


class NoDebugKeyTestCase(unittest.TestCase):
    """测试基类：整个用例执行期间保证「不存在调试兜底密钥」。

    子类如需自定义 setUp，务必先调用 ``super().setUp()``；
    还原动作通过 ``addCleanup`` 注册，即使用例抛异常也会执行。
    """

    def setUp(self):
        """每个用例前临时屏蔽调试兜底密钥，并注册 addCleanup 保证还原。"""
        super().setUp()
        guard = DebugKeyGuard()
        guard.activate()
        self.addCleanup(guard.restore)
        self.debug_key_guard = guard
