# -*- coding: utf-8 -*-
"""
tests/test_debug_keys.py — 双模式密钥管理测试

覆盖：
  1. 调试密钥源 core.debug_keys 环境变量 / 模块常量两种注入方式
  2. AIConfigManager.get_active() 在源码运行（非冻结）且无 GUI 配置时，
     自动注入调试密钥（内存态、不落盘）；冻结（EXE）时忽略
  3. GUI 配置优先于调试密钥
  4. purge_ai_secrets.clear_debug_keys 能把真实密钥清空为 ""

前后置逻辑统一复用 tests/_support.py 的 NoDebugKeyTestCase，
避免每个测试类各写一遍 setUp / tearDown。
"""
import os
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _support import NoDebugKeyTestCase, ENV_KEY
from core.ai_config import AIConfigManager, make_default_profile


class TestDebugKeySource(NoDebugKeyTestCase):
    """core.debug_keys 取值逻辑：环境变量优先于模块常量。"""

    def test_empty_when_nothing_set(self):
        """两个来源都为空时应返回 None，表示无调试密钥可用。"""
        from core.debug_keys import get_debug_keys
        self.assertIsNone(get_debug_keys())

    def test_env_var_wins(self):
        """环境变量与模块常量同时存在时，环境变量优先。"""
        from core.debug_keys import get_debug_keys
        os.environ[ENV_KEY] = 'sk-env-abcdefghij0123456789'
        self.debug_key_guard._module.DEBUG_AGNES_API_KEY = 'sk-const-abcdefghij012345'
        data = get_debug_keys()
        self.assertIsNotNone(data)
        self.assertEqual(data['api_key'], 'sk-env-abcdefghij0123456789')
        self.assertEqual(data['model'], 'agnes-2.5-flash')
        self.assertIn('api.agnes-ai.cn', data['api_url'])

    def test_module_const_works(self):
        """没有环境变量时，回退读取模块常量。"""
        from core.debug_keys import get_debug_keys
        self.debug_key_guard._module.DEBUG_AGNES_API_KEY = 'sk-const-abcdefghij012345'
        data = get_debug_keys()
        self.assertEqual(data['api_key'], 'sk-const-abcdefghij012345')


class TestDebugFallback(NoDebugKeyTestCase):
    """AIConfigManager 调试兜底：仅在源码运行且无 GUI 配置时生效。"""

    def setUp(self):
        """屏蔽调试密钥后重置单例，保证每个用例从干净状态开始。"""
        super().setUp()
        AIConfigManager.reset_instance()
        self.addCleanup(AIConfigManager.reset_instance)

    def _mgr(self) -> AIConfigManager:
        """创建一个指向临时目录的管理器实例（磁盘上无既有配置）。"""
        tmp = Path(tempfile.mkdtemp()) / 'ai_config.json'
        return AIConfigManager(tmp)

    def test_no_fallback_when_empty(self):
        """无调试密钥时不应凭空产生配置档。"""
        mgr = self._mgr()
        self.assertIsNone(mgr.get_active())

    def test_fallback_from_env_in_debug(self):
        """环境变量提供密钥时，源码运行应自动注入且不落盘明文。"""
        os.environ[ENV_KEY] = 'sk-debugenv-abcdefghij0123456789'
        mgr = self._mgr()
        prof = mgr.get_active()
        self.assertIsNotNone(prof)
        self.assertEqual(prof.api_key, 'sk-debugenv-abcdefghij0123456789')
        self.assertEqual(prof.model, 'agnes-2.5-flash')
        self.assertIn('Bearer', prof.auth_header())
        # 调试兜底为内存态，不应落盘为明文
        self.assertNotIn('sk-debugenv', (mgr.path()).read_text(encoding='utf-8')
                         if mgr.path().exists() else '')

    def test_fallback_from_module_const(self):
        """模块常量提供密钥时同样能触发兜底注入。"""
        self.debug_key_guard._module.DEBUG_AGNES_API_KEY = 'sk-debugconst-abcdefghij012345'
        mgr = self._mgr()
        prof = mgr.get_active()
        self.assertIsNotNone(prof)
        self.assertEqual(prof.api_key, 'sk-debugconst-abcdefghij012345')

    def test_frozen_mode_ignores_debug(self):
        """冻结（打包为 EXE）状态下必须完全忽略调试密钥。"""
        os.environ[ENV_KEY] = 'sk-debugenv-abcdefghij0123456789'
        mgr = self._mgr()
        saved = getattr(sys, 'frozen', None)
        sys.frozen = True
        try:
            self.assertIsNone(mgr.get_active())
        finally:
            if saved is None:
                del sys.frozen
            else:
                sys.frozen = saved

    def test_gui_profile_takes_precedence(self):
        """用户在 GUI 配置过密钥后，调试密钥应被忽略。"""
        os.environ[ENV_KEY] = 'sk-debugenv-abcdefghij0123456789'
        mgr = self._mgr()
        p = make_default_profile()
        p.api_url = 'https://api.agnes-ai.cn/v1/chat/completions'
        p.model = 'agnes-2.5-flash'
        p.api_key = 'sk-gui-user-key-abcdefghij012345'
        mgr.upsert_profile(p, make_active=True)
        prof = mgr.get_active()
        self.assertEqual(prof.api_key, 'sk-gui-user-key-abcdefghij012345')


class TestPurgeDebugKeys(unittest.TestCase):
    """purge_ai_secrets 清空调试密钥的正则行为。"""

    def test_regex_clears_real_key(self):
        """含真实密钥时应被替换为空串，且不残留原文片段。"""
        from scripts.purge_ai_secrets import _DEBUG_KEY_RE
        sample = (
            'DEBUG_AGNES_API_KEY = "sk-real-abcdefghij0123456789"\n'
            'DEBUG_AGNES_API_URL = "https://api.agnes-ai.cn/v1/chat/completions"\n'
        )
        new, n = _DEBUG_KEY_RE.subn(lambda m: 'DEBUG_AGNES_API_KEY = ""', sample)
        self.assertEqual(n, 1)
        self.assertIn('DEBUG_AGNES_API_KEY = ""', new)
        self.assertNotIn('sk-real', new)

    def test_regex_noop_when_empty(self):
        """已是空串时不应产生任何替换（保持幂等）。"""
        from scripts.purge_ai_secrets import _DEBUG_KEY_RE
        sample = 'DEBUG_AGNES_API_KEY = ""\n'
        new, n = _DEBUG_KEY_RE.subn(lambda m: 'DEBUG_AGNES_API_KEY = ""', sample)
        self.assertEqual(n, 0)
        self.assertEqual(new, sample)


if __name__ == '__main__':
    unittest.main(verbosity=2)
