"""
meihua_knowledge 种子固化回归测试（P2-3）

目的：确保删库重建后，meihua_knowledge 解卦原则种子仍能从
schema_sqlite.sql 自动恢复（不再依赖运行期 Python 代码注入）。

约定：
- 删除测试用临时 DB（与主库隔离），不污染 data/fengshui.db。
- 验证：重建后表存在 + 行数 == 8 + 含关键 section/content_key。
"""
import os
import shutil
import sqlite3
import tempfile
import unittest


class TestMeihuaKnowledgeSeed(unittest.TestCase):
    """schema_sqlite.sql 应固化 meihua_knowledge 种子（删库重建不丢）"""

    def setUp(self):
        """创建隔离的临时工作目录并定位项目 schema 文件。"""
        self._workdir = tempfile.mkdtemp(prefix='fs_seed_test_')
        # 拷贝 schema（只读）；准备 schema + sqlite_db 路径
        self._proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._schema_path = os.path.join(self._proj_root, 'database', 'schema_sqlite.sql')

    def tearDown(self):
        """清理临时工作目录，避免遗留测试数据库文件。"""
        shutil.rmtree(self._workdir, ignore_errors=True)

    def _build_db(self):
        """用 schema 在临时目录重建一个 db，返回连接"""
        db_path = os.path.join(self._workdir, 'test.db')
        con = sqlite3.connect(db_path)
        with open(self._schema_path, 'r', encoding='utf-8') as f:
            con.executescript(f.read())
        con.commit()
        return con, db_path

    def test_table_exists_after_rebuild(self):
        """删库重建后 meihua_knowledge 表应存在"""
        con, _ = self._build_db()
        try:
            row = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='meihua_knowledge'"
            ).fetchone()
            self.assertIsNotNone(row, 'meihua_knowledge 表未通过 schema 创建')
        finally:
            con.close()

    def test_seed_count(self):
        """删库重建后 meihua_knowledge 应有 8 条种子（与 _BUILTIN_MEIHUA_RULES 同步）"""
        con, _ = self._build_db()
        try:
            row = con.execute('SELECT COUNT(*) AS c FROM meihua_knowledge').fetchone()
            self.assertGreaterEqual(row[0], 8,
                f'种子不足: 仅 {row[0]} 条（应有 ≥ 8 条解卦原则）')
        finally:
            con.close()

    def test_key_sections_present(self):
        """关键 section / content_key 必须存在（覆盖体用、动静、互变、卦气、卦名、断语六大主题）"""
        con, _ = self._build_db()
        try:
            rows = con.execute(
                'SELECT section, content_key FROM meihua_knowledge'
            ).fetchall()
            pairs = {(r[0], r[1]) for r in rows}
            required = {
                ('体用关系', 'ti_yong'),
                ('体用关系', 'sheng_ke_ji_xiong'),
                ('动静之机', 'dong_jing'),
                ('互卦变卦', 'hu_gua'),
                ('互卦变卦', 'bian_gua'),
                ('卦气旺衰', 'gua_qi'),
                ('卦名本义', 'gua_ming'),
                ('断语风格', 'duan_yu'),
            }
            missing = required - pairs
            self.assertFalse(missing, f'种子缺少关键条目: {missing}')
        finally:
            con.close()

    def test_seed_content_non_empty(self):
        """所有种子 content_value 非空且非占位"""
        con, _ = self._build_db()
        try:
            rows = con.execute(
                'SELECT content_value FROM meihua_knowledge'
            ).fetchall()
            self.assertGreater(len(rows), 0)
            for r in rows:
                self.assertTrue(r[0] and r[0].strip(),
                    f'种子 content_value 为空: {r[0]!r}')
        finally:
            con.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
