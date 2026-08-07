# -*- coding: utf-8 -*-
"""
tests/test_ai_config.py — AI 配置中央管理器测试

覆盖三类不变量：
  1. 配置读写正确（多档位、切换、删除、字段校验）
  2. 热更新可靠（版本自增、订阅回调、外部改动感知）
  3. 统一调用（客户端按当前生效配置构建，配置变更后自动重建）

注意：
  凡是断言「初始未配置」的测试类，都必须继承 :class:`NoDebugKeyTestCase`，
  否则 core.debug_keys 的调试兜底密钥会让管理器变成「已配置」状态。
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _support import NoDebugKeyTestCase
from core.ai_config import (AIConfigManager, AIProfile, PROVIDER_PRESETS,
                            make_default_profile, encrypt_key, decrypt_key,
                            OFFICIAL_AGNES_ENDPOINT, OFFICIAL_AGNES_MODEL)


def _usable_profile(name='测试配置', model='test-model', key='sk-test-1234567890abcdef'):
    """构造一个字段完整、可通过 validate() 的配置档，供各用例复用。

    Args:
        name: 配置档显示名。
        model: 模型名。
        key: API 密钥（使用 example.invalid 域名，确保不会真实联网）。

    Returns:
        AIProfile: 已填好必填字段的配置档实例。
    """
    p = make_default_profile()
    p.name = name
    p.api_url = 'https://example.invalid/v1/chat/completions'
    p.model = model
    p.api_key = key
    return p


class TestAIProfile(unittest.TestCase):
    """配置档数据模型：字段校验、鉴权头拼装、脱敏与克隆。"""

    def test_validate_rejects_incomplete(self):
        """必填字段（端点/模型/密钥）缺任意一项都应校验失败。"""
        p = AIProfile()
        self.assertIsNotNone(p.validate())          # 端点为空
        p.api_url = 'https://example.invalid/v1'
        self.assertIsNotNone(p.validate())          # 模型为空
        p.model = 'm'
        self.assertIsNotNone(p.validate())          # 密钥为空
        p.api_key = 'sk-x'
        self.assertIsNone(p.validate())

    def test_validate_rejects_bad_scheme(self):
        """端点必须是 http/https，其他协议应被拒绝。"""
        p = _usable_profile()
        p.api_url = 'ftp://example.invalid/v1'
        self.assertIn('http', p.validate())

    def test_validate_ranges(self):
        """超时与温度必须落在合理区间内。"""
        p = _usable_profile()
        p.timeout = 99999
        self.assertIn('超时', p.validate())
        p.timeout = 120
        p.temperature = 5.0
        self.assertIn('温度', p.validate())

    def test_official_provider_is_single_and_requires_key(self):
        """当前仅保留官方「龙虎山大师兄 AI」一个模型，且强制要求密钥。"""
        self.assertEqual(list(PROVIDER_PRESETS.keys()), ['agnes'])
        self.assertTrue(PROVIDER_PRESETS['agnes'].needs_key)
        p = make_default_profile()
        self.assertEqual(p.api_url, OFFICIAL_AGNES_ENDPOINT)
        self.assertEqual(p.model, OFFICIAL_AGNES_MODEL)
        self.assertIsNotNone(p.validate(), '未填密钥时不应通过校验')
        p.api_key = 'sk-test-1234567890abcdef'
        self.assertIsNone(p.validate())

    def test_auth_header_schemes(self):
        """Bearer 方案自动补前缀且不重复；raw 方案原样透传。"""
        p = _usable_profile(key='sk-abc')
        self.assertEqual(p.auth_header(), 'Bearer sk-abc')
        p.api_key = 'Bearer sk-abc'
        self.assertEqual(p.auth_header(), 'Bearer sk-abc', '不应重复添加前缀')
        p.auth_scheme = 'raw'
        p.api_key = 'custom-token'
        self.assertEqual(p.auth_header(), 'custom-token')

    def test_masked_key_hides_body(self):
        """脱敏展示只保留首尾，中间必须打码。"""
        p = _usable_profile(key='sk-abcdefghijklmnopqrst')
        masked = p.masked_key()
        self.assertNotIn('efghijklmnop', masked)
        self.assertIn('*', masked)

    def test_summary_has_no_plaintext_key(self):
        """summary() 用于 UI/日志展示，绝不能带出明文密钥。"""
        p = _usable_profile(key='sk-secretsecretsecret')
        self.assertNotIn('secretsecret', json.dumps(p.summary(), ensure_ascii=False))

    def test_clone_gets_new_id(self):
        """克隆出的副本应有独立 id，但沿用原密钥。"""
        p = _usable_profile()
        c = p.clone('副本')
        self.assertNotEqual(p.id, c.id)
        self.assertEqual(c.name, '副本')
        self.assertEqual(c.api_key, p.api_key)


class TestKeyObfuscation(unittest.TestCase):
    """密钥落盘混淆：加解密往返、密文不含明文、空值透传。"""

    def test_roundtrip(self):
        """加密后再解密应还原为原始密钥。"""
        secret = 'sk-roundtrip-0123456789'
        self.assertEqual(decrypt_key(encrypt_key(secret)), secret)

    def test_ciphertext_hides_plaintext(self):
        """密文中不得出现原文，也不得残留 sk- 特征串。"""
        secret = 'sk-hidden-0123456789abcdef'
        enc = encrypt_key(secret)
        self.assertNotIn(secret, enc)
        self.assertNotIn('sk-', enc)

    def test_empty_key_passthrough(self):
        """空字符串直接透传，不做加解密。"""
        self.assertEqual(encrypt_key(''), '')
        self.assertEqual(decrypt_key(''), '')

    def test_plaintext_import_tolerated(self):
        """用户手工写入的明文（外部导入场景）应能被读取。"""
        self.assertEqual(decrypt_key('sk-manual-import'), 'sk-manual-import')


class TestConfigManager(NoDebugKeyTestCase):
    """配置管理器读写与多档位管理。

    继承 NoDebugKeyTestCase 以屏蔽调试兜底密钥，
    保证 test_starts_unconfigured 等用例的「未配置」前提成立。
    """

    def setUp(self):
        """每个用例都用独立临时目录，避免相互污染。"""
        super().setUp()
        self.path = Path(tempfile.mkdtemp()) / 'ai_config.json'
        self.m = AIConfigManager(self.path)

    def test_starts_unconfigured(self):
        """全新管理器应处于未配置状态。"""
        self.assertFalse(self.m.is_configured())
        self.assertIsNone(self.m.get_active())
        self.assertIn('尚未配置', self.m.status_text())

    def test_upsert_and_activate(self):
        """写入并激活配置档后，状态应变为已就绪。"""
        p = _usable_profile()
        self.assertTrue(self.m.upsert_profile(p, make_active=True))
        self.assertTrue(self.m.is_configured())
        self.assertEqual(self.m.get_active().id, p.id)
        self.assertIn('已就绪', self.m.status_text())

    def test_persistence_across_instances(self):
        """配置写盘后，新建管理器实例应能读回同样内容（含密钥）。"""
        p = _usable_profile(model='persisted-model')
        self.m.upsert_profile(p, make_active=True)
        again = AIConfigManager(self.path)
        self.assertEqual(again.get_active().model, 'persisted-model')
        self.assertEqual(again.get_active().api_key, p.api_key)

    def test_multi_profile_switch(self):
        """支持保存多档配置并在其间切换生效档。"""
        a = _usable_profile('甲', 'model-a')
        b = _usable_profile('乙', 'model-b')
        self.m.upsert_profile(a, make_active=True)
        self.m.upsert_profile(b)
        self.assertEqual(len(self.m.list_profiles()), 2)
        self.assertEqual(self.m.get_active().model, 'model-a')
        self.assertTrue(self.m.set_active(b.id))
        self.assertEqual(self.m.get_active().model, 'model-b')

    def test_delete_reassigns_active(self):
        """删除当前生效档后应自动改选剩余档，而非留空。"""
        a = _usable_profile('甲', 'model-a')
        b = _usable_profile('乙', 'model-b')
        self.m.upsert_profile(a, make_active=True)
        self.m.upsert_profile(b)
        self.assertTrue(self.m.delete_profile(a.id))
        self.assertEqual(self.m.get_active().id, b.id, '删除生效档后应自动改选其他档')

    def test_delete_missing_returns_false(self):
        """删除不存在的档位应返回 False 而不是抛异常。"""
        self.assertFalse(self.m.delete_profile('not-exist'))

    def test_replace_all_is_single_write(self):
        """整体替换应合并为一次写盘，版本号只自增一次。"""
        a = _usable_profile('甲', 'model-a')
        b = _usable_profile('乙', 'model-b')
        v0 = self.m.version
        self.assertTrue(self.m.replace_all([a, b], b.id))
        self.assertEqual(self.m.version, v0 + 1, '整体替换应只自增一次版本')
        self.assertEqual(len(self.m.list_profiles()), 2)
        self.assertEqual(self.m.get_active().id, b.id)

    def test_clear_all(self):
        """清空后应回到未配置状态。"""
        self.m.upsert_profile(_usable_profile(), make_active=True)
        self.assertTrue(self.m.clear_all())
        self.assertFalse(self.m.is_configured())

    def test_corrupt_file_degrades_gracefully(self):
        """配置文件损坏时应降级为未配置，而不是让程序崩溃。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text('{ this is not json', encoding='utf-8')
        m = AIConfigManager(self.path)
        self.assertFalse(m.is_configured(), '配置损坏应降级为未配置而非崩溃')

    def test_unknown_fields_ignored(self):
        """旧版本/未来版本写入的多余字段不应导致解析失败。"""
        payload = {
            'schema': 1,
            'active': 'x1',
            'profiles': [{
                'id': 'x1', 'name': 'n', 'provider': 'custom',
                'api_url': 'https://example.invalid/v1', 'model': 'm',
                'api_key_enc': encrypt_key('sk-abc'),
                'future_field': 'whatever',
            }],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload), encoding='utf-8')
        m = AIConfigManager(self.path)
        self.assertEqual(m.get_active().model, 'm')
        self.assertEqual(m.get_active().api_key, 'sk-abc')

    def test_legacy_dict_contract(self):
        """兼容层字典必须包含旧调用方依赖的全部键。"""
        p = _usable_profile()
        self.m.upsert_profile(p, make_active=True)
        d = self.m.as_legacy_dict()
        for key in ('api_url', 'api_key', 'model', 'timeout',
                    'max_retries', 'retry_delay'):
            self.assertIn(key, d)
        self.assertTrue(d['api_key'].startswith('Bearer '))

    def test_legacy_dict_safe_when_unconfigured(self):
        """未配置时兼容层应返回空串，而不是 None 或抛异常。"""
        d = self.m.as_legacy_dict()
        self.assertEqual(d['api_url'], '')
        self.assertEqual(d['api_key'], '')


class TestHotReload(unittest.TestCase):
    """热更新：版本号自增、订阅回调、外部文件改动感知。"""

    def setUp(self):
        """每个用例独立临时配置文件。"""
        self.path = Path(tempfile.mkdtemp()) / 'ai_config.json'
        self.m = AIConfigManager(self.path)

    def test_version_increments_on_write(self):
        """任何一次写入都应让版本号 +1，供下游判断是否需重建客户端。"""
        v0 = self.m.version
        self.m.upsert_profile(_usable_profile(), make_active=True)
        self.assertEqual(self.m.version, v0 + 1)

    def test_subscribers_notified(self):
        """订阅者应在每次配置变更后收到最新版本号。"""
        seen = []
        self.m.subscribe(lambda v: seen.append(v))
        self.m.upsert_profile(_usable_profile(), make_active=True)
        self.assertEqual(len(seen), 1)
        self.m.upsert_profile(_usable_profile('第二个'), make_active=True)
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[-1], self.m.version)

    def test_unsubscribe_stops_notifications(self):
        """subscribe 返回的注销函数应能真正停止通知。"""
        seen = []
        off = self.m.subscribe(lambda v: seen.append(v))
        self.m.upsert_profile(_usable_profile(), make_active=True)
        off()
        self.m.upsert_profile(_usable_profile('之后'), make_active=True)
        self.assertEqual(len(seen), 1, '取消订阅后不应再收到通知')

    def test_faulty_subscriber_does_not_break_save(self):
        """单个订阅者抛异常不得影响写盘与其他订阅者。"""
        def boom(_v):
            """故意抛异常的订阅者，用于验证隔离性。"""
            raise RuntimeError('订阅者炸了')
        ok = []
        self.m.subscribe(boom)
        self.m.subscribe(lambda v: ok.append(v))
        self.assertTrue(self.m.upsert_profile(_usable_profile(), make_active=True))
        self.assertEqual(len(ok), 1, '一个订阅者异常不应影响其他订阅者')

    def test_external_file_change_detected(self):
        """其他进程改了配置文件，应能被自动感知并重载。"""
        import core.ai_config as ac
        self.m.upsert_profile(_usable_profile(model='before'), make_active=True)
        self.assertEqual(self.m.get_active().model, 'before')

        # 绕过节流，模拟外部写入
        original = ac._MTIME_CHECK_INTERVAL
        ac._MTIME_CHECK_INTERVAL = 0.0
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            data['profiles'][0]['model'] = 'after'
            self.path.write_text(json.dumps(data), encoding='utf-8')
            # 触发一次版本读取即应重载
            _ = self.m.version
            self.assertEqual(self.m.get_active().model, 'after')
        finally:
            ac._MTIME_CHECK_INTERVAL = original


class TestClientIntegration(NoDebugKeyTestCase):
    """客户端统一走中央配置，且随配置热重建。

    同样继承 NoDebugKeyTestCase：
    test_client_raises_when_unconfigured 依赖「确实没有任何可用密钥」。
    """

    def setUp(self):
        """重置全局单例并指向临时配置文件，避免跨用例串扰。"""
        super().setUp()
        from core.ai_config import AIConfigManager as M
        self.path = Path(tempfile.mkdtemp()) / 'ai_config.json'
        M.reset_instance()
        self.m = M.instance()
        self.m.set_path(self.path)
        import api.agnes_client as ac
        ac.invalidate_client()

    def tearDown(self):
        """清理客户端缓存与配置单例，恢复干净的全局状态。"""
        from core.ai_config import AIConfigManager as M
        import api.agnes_client as ac
        ac.invalidate_client()
        M.reset_instance()
        super().tearDown()

    def test_client_raises_when_unconfigured(self):
        """未配置密钥时构建客户端应抛出可识别的专用异常。"""
        from api.agnes_client import AgnesClient, AgnesNotConfiguredError, AgnesClientError
        with self.assertRaises(AgnesNotConfiguredError):
            AgnesClient()
        # 仍属 AgnesClientError 子类，上层既有降级逻辑不受影响
        self.assertTrue(issubclass(AgnesNotConfiguredError, AgnesClientError))

    def test_client_reads_active_profile(self):
        """客户端各项参数应取自当前生效配置档。"""
        from api.agnes_client import AgnesClient
        p = _usable_profile(model='wired-model')
        p.timeout = 66
        self.m.upsert_profile(p, make_active=True)
        c = AgnesClient()
        self.assertEqual(c.model, 'wired-model')
        self.assertEqual(c.timeout, 66)
        self.assertTrue(c.api_key.startswith('Bearer '))

    def test_singleton_rebuilds_after_config_change(self):
        """配置版本变化后，全局单例应按新配置重建。"""
        from api.agnes_client import get_agnes_client
        self.m.upsert_profile(_usable_profile(model='first'), make_active=True)
        c1 = get_agnes_client()
        self.assertEqual(c1.model, 'first')

        self.m.upsert_profile(_usable_profile('第二档', 'second'), make_active=True)
        c2 = get_agnes_client()
        self.assertEqual(c2.model, 'second', '配置变更后客户端应自动按新配置重建')
        self.assertIsNot(c1, c2)

    def test_singleton_stable_without_change(self):
        """配置未变时应复用同一客户端实例，避免重复建连。"""
        from api.agnes_client import get_agnes_client
        self.m.upsert_profile(_usable_profile(), make_active=True)
        self.assertIs(get_agnes_client(), get_agnes_client(), '配置未变时应复用单例')

    def test_explicit_profile_overrides_active(self):
        """GUI「保存前测试连接」用：直接传入草稿配置。"""
        from api.agnes_client import AgnesClient
        self.m.upsert_profile(_usable_profile(model='saved'), make_active=True)
        draft = _usable_profile('草稿', 'draft-model')
        c = AgnesClient(profile=draft)
        self.assertEqual(c.model, 'draft-model')

    def test_load_ai_config_delegates_to_manager(self):
        """兼容函数 load_ai_config 应转发到中央管理器。"""
        from api.agnes_client import load_ai_config
        self.m.upsert_profile(_usable_profile(model='delegated'), make_active=True)
        self.assertEqual(load_ai_config()['model'], 'delegated')

    def test_local_settings_shim_roundtrip(self):
        """core.local_settings 兼容层读写应落到中央配置档上。"""
        from core.local_settings import load_tunables, save_tunables
        self.m.upsert_profile(_usable_profile(), make_active=True)
        self.assertTrue(save_tunables({'timeout': 77, 'max_retries': 4, 'retry_delay': 9}))
        got = load_tunables()
        self.assertEqual(got['timeout'], 77)
        self.assertEqual(got['max_retries'], 4)
        self.assertEqual(self.m.get_active().timeout, 77,
                         '兼容层应把参数写进中央配置档')


if __name__ == '__main__':
    unittest.main(verbosity=2)
