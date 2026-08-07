"""
AI 调用缓存测试（P2-4）

覆盖：
- 输入哈希的稳定性（顺序/类型变化不影响）
- 同盘 + 同问题命中缓存；同盘 + 不同问题不命中
- 写入缓存（自动 UPSERT）+ hit_count 原子累加
- 缓存统计（total_entries / total_hits / by_type）
- LRU 清理接口
- 与 analysis_pipeline.run_* 集成：第一次走 API，第二次命中缓存
"""
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path


class TestAiCacheCore(unittest.TestCase):
    """ai_cache 模块的核心功能（键生成、读写、统计）"""

    def setUp(self):
        """隔离数据库到临时目录并据 schema_sqlite.sql 重建，避免污染主库。"""
        # 用临时目录隔离 DB，避免污染主库
        self._tmpdir = tempfile.mkdtemp(prefix='fs_aicache_test_')
        # 替换 get_connection 使其指向临时库
        from core import sqlite_db
        self._orig_db_path = sqlite_db._DB_PATH
        self._orig_initialized = sqlite_db._INITIALIZED
        sqlite_db._DB_PATH = os.path.join(self._tmpdir, 'test.db')
        sqlite_db._INITIALIZED = False
        # 重建临时库（用 schema_sqlite.sql）
        schema_path = Path(__file__).resolve().parent.parent / 'database' / 'schema_sqlite.sql'
        con = sqlite3.connect(sqlite_db._DB_PATH)
        with open(schema_path, 'r', encoding='utf-8') as f:
            con.executescript(f.read())
        con.commit()
        con.close()

    def tearDown(self):
        """恢复主库路径并删除临时目录，回收测试遗留文件。"""
        from core import sqlite_db
        sqlite_db._DB_PATH = self._orig_db_path
        sqlite_db._INITIALIZED = self._orig_initialized
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_compute_input_hash_stable(self):
        """同输入（字段顺序不同）应得相同 hash"""
        from core.ai_cache import compute_input_hash
        a = {'year': 2000, 'month': 1, 'day': 1, 'hour': 12, 'gender': '男', 'name': '张三'}
        b = {'gender': '男', 'name': '张三', 'hour': 12, 'day': 1, 'month': 1, 'year': 2000}
        self.assertEqual(compute_input_hash('bazi', a),
                         compute_input_hash('bazi', b))

    def test_compute_input_hash_different_fields(self):
        """改 year 即 hash 不同"""
        from core.ai_cache import compute_input_hash
        a = {'year': 2000, 'month': 1, 'day': 1, 'hour': 12}
        b = {'year': 2001, 'month': 1, 'day': 1, 'hour': 12}
        self.assertNotEqual(compute_input_hash('bazi', a),
                            compute_input_hash('bazi', b))

    def test_compute_question_hash(self):
        """问题哈希稳定（去空白）"""
        from core.ai_cache import compute_question_hash
        self.assertEqual(compute_question_hash('今天事业如何'),
                         compute_question_hash('  今天事业如何  '))
        self.assertNotEqual(compute_question_hash('事业'),
                            compute_question_hash('财运'))

    def test_save_and_get(self):
        """写入后能读回；hit_count 累加"""
        from core.ai_cache import save_to_cache, get_cached_result
        input_data = {'year': 2000, 'month': 1, 'day': 1, 'hour': 12}
        ai_result = {'personality': ['坚韧'], 'final_verdict': '事业有成'}

        # 首次写入
        ok = save_to_cache('bazi', input_data, None, ai_result)
        self.assertTrue(ok)

        # 首次查询：命中
        cached = get_cached_result('bazi', input_data, None)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['personality'], ['坚韧'])
        self.assertEqual(cached['_cache_hit_count'], 1)

        # 二次查询：hit_count=2
        cached2 = get_cached_result('bazi', input_data, None)
        self.assertEqual(cached2['_cache_hit_count'], 2)

    def test_miss_on_different_question(self):
        """同 pan_type 但 question 不同 → 不命中"""
        from core.ai_cache import save_to_cache, get_cached_result
        input_data = {'year': 2000, 'month': 1, 'day': 1, 'hour': 12}
        save_to_cache('meihua', input_data, '问事业', {'answer': 'A'})
        save_to_cache('meihua', input_data, '问财运', {'answer': 'B'})

        self.assertIsNotNone(get_cached_result('meihua', input_data, '问事业'))
        self.assertIsNotNone(get_cached_result('meihua', input_data, '问财运'))
        self.assertIsNone(get_cached_result('meihua', input_data, '问健康'))

    def test_upsert_no_duplicate(self):
        """UPSERT：同键二次 save_to_cache 不会产生多行（hit_count 不被覆盖）"""
        from core.ai_cache import save_to_cache, get_cached_result
        input_data = {'year': 2000, 'month': 1, 'day': 1, 'hour': 12}
        save_to_cache('bazi', input_data, None, {'v': 1})
        save_to_cache('bazi', input_data, None, {'v': 2})

        # 应只有一行
        from core.ai_cache import get_cache_stats
        stats = get_cache_stats()
        self.assertEqual(stats['total_entries'], 1)

        # 命中仍能读出（应是最新的值）
        cached = get_cached_result('bazi', input_data, None)
        self.assertEqual(cached['v'], 2)

    def test_stats(self):
        """统计：total_entries / total_hits / by_type"""
        from core.ai_cache import save_to_cache, get_cached_result, get_cache_stats
        # 写 2 条八字（不同 year）+ 1 条梅花（用完整字段集确保 hash 不同）
        bazi_2000 = {'year': 2000, 'month': 1, 'day': 1, 'hour': 12}
        bazi_2001 = {'year': 2001, 'month': 1, 'day': 1, 'hour': 12}
        meihua_2000 = {'method': 'time', 'year': 2000, 'month': 1, 'day': 1, 'hour': 12}
        save_to_cache('bazi', bazi_2000, None, {'a': 1})
        save_to_cache('bazi', bazi_2001, None, {'a': 2})
        save_to_cache('meihua', meihua_2000, 'q', {'m': 1})
        # 各命中 1 次
        get_cached_result('bazi', bazi_2000, None)
        get_cached_result('meihua', meihua_2000, 'q')

        stats = get_cache_stats()
        self.assertEqual(stats['total_entries'], 3)
        self.assertEqual(stats['total_hits'], 2)
        types = {r['pan_type']: r['c'] for r in stats['by_type']}
        self.assertEqual(types.get('bazi'), 2)
        self.assertEqual(types.get('meihua'), 1)

    def test_clear_old(self):
        """清理 hit_count < N 的缓存条目"""
        from core.ai_cache import (save_to_cache, get_cached_result,
                                   clear_old, get_cache_stats)
        bazi_2000 = {'year': 2000, 'month': 1, 'day': 1, 'hour': 12}
        bazi_2001 = {'year': 2001, 'month': 1, 'day': 1, 'hour': 12}
        save_to_cache('bazi', bazi_2000, None, {'a': 1})
        save_to_cache('bazi', bazi_2001, None, {'b': 2})
        # 命中 bazi_2000 两次（hit_count=2），bazi_2001 0 次
        get_cached_result('bazi', bazi_2000, None)
        get_cached_result('bazi', bazi_2000, None)

        deleted = clear_old(min_hit_count_to_keep=2)
        self.assertEqual(deleted, 1)
        stats = get_cache_stats()
        self.assertEqual(stats['total_entries'], 1)

    def test_clear_all(self):
        """清空全部缓存"""
        from core.ai_cache import (save_to_cache, clear_all, get_cache_stats)
        save_to_cache('bazi', {'y': 2000}, None, {'a': 1})
        save_to_cache('meihua', {'y': 2000}, None, {'b': 2})
        deleted = clear_all()
        self.assertEqual(deleted, 2)
        stats = get_cache_stats()
        self.assertEqual(stats['total_entries'], 0)


class TestAiCachePipelineIntegration(unittest.TestCase):
    """与 analysis_pipeline.run_* 的集成（无需 API，模拟缓存命中场景）"""

    def setUp(self):
        """隔离数据库并据 schema_sqlite.sql 重建，供流水线集成用例使用。"""
        # 隔离 DB
        self._tmpdir = tempfile.mkdtemp(prefix='fs_aicache_pipe_')
        from core import sqlite_db
        self._orig_db_path = sqlite_db._DB_PATH
        self._orig_initialized = sqlite_db._INITIALIZED
        sqlite_db._DB_PATH = os.path.join(self._tmpdir, 'test.db')
        sqlite_db._INITIALIZED = False
        schema_path = Path(__file__).resolve().parent.parent / 'database' / 'schema_sqlite.sql'
        con = sqlite3.connect(sqlite_db._DB_PATH)
        with open(schema_path, 'r', encoding='utf-8') as f:
            con.executescript(f.read())
        con.commit()
        con.close()

    def tearDown(self):
        """恢复主库路径并删除临时目录，回收测试遗留文件。"""
        from core import sqlite_db
        sqlite_db._DB_PATH = self._orig_db_path
        sqlite_db._INITIALIZED = self._orig_initialized
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_bazi_cache_hit_returns_same_shape(self):
        """预填缓存 → 调用 run_bazi_analysis 应直接返回缓存（from_cache=True, token_usage=0）"""
        from core.ai_cache import save_to_cache
        from core.analysis_pipeline import AnalysisPipeline
        from core.knowledge_base import KnowledgeBase

        # 预填缓存（绕开真实 API 调用）
        input_data = {'name': '测试', 'gender': '男', 'year': 2000,
                      'month': 1, 'day': 1, 'hour': 12, 'minute': 0,
                      'longitude': 120.0, 'is_lunar': False}
        ai_result = {'personality': ['示例性格']}
        save_to_cache('bazi', input_data, None, ai_result)

        # 调用 run_bazi_analysis：缓存命中，不走 API
        pipeline = AnalysisPipeline()
        result = pipeline.run_bazi_analysis(input_data, chart_data=None)
        self.assertTrue(result['success'])
        self.assertTrue(result['from_cache'])
        self.assertEqual(result['token_usage'], 0)
        self.assertEqual(result['ai_analysis']['personality'], ['示例性格'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
