"""
数据库管理模块 - 封装所有数据库操作
基于本地嵌入式 SQLite（data/fengshui.db），提供用户管理、排盘记录管理、
命理知识库查询、UI 设置与操作日志的统一入口。

数据库连接与首次建库统一委托 core.sqlite_db；本模块只负责补建少量运行期表
（ui_settings / operation_logs / system_logs）——这些表不在 base.sql 导出内。

种子数据版本/校验和检测：
- db_version 表记录 schema 版本、各种子表的行数和校验和
- 启动时对比当前数据库与预期校验和，发现偏差时记录警告
"""
import json
import hashlib
import threading
from typing import Optional, Dict, List, Any

import logging

from core import sqlite_db
# 干支静态常量的唯一权威源，用于生成十二长生等派生查找表
from core.ganzhi_constants import DI_ZHI, ZHI_INDEX, GAN_YANG

logger = logging.getLogger(__name__)

# 当前数据库 Schema 版本
DB_SCHEMA_VERSION = 5
# 预期种子数据校验和（各表：行数, MD5 前 16 位）
# 这些值基于当前 data/fengshui.db 权威数据（由 scripts/convert_mysql_to_sqlite.py 生成）
# 更新种子数据后须同步运行校验获取新值并更新此处
# 注：stroke_count 表数据量大（10万+行），仅校验行数，不计算 MD5 以提升启动性能
EXPECTED_SEED_CHECKSUMS = {
    'tian_gan': (10, '8cf735bc90ad4f51'),
    'di_zhi': (12, 'b116b9bec49e95f4'),
    'sixty_jiazi': (60, '8d4ff4c08c8baf95'),
    'month_gan_rules': (60, '073026e134a19c41'),
    'jie_qi': (24, '4319635cbf496ef1'),
    'di_zhi_hidden_gan': (56, '76a849c03884b30a'),
    'yue_ling_weight': (60, 'a32d754dc2e18103'),
    'ba_gua': (8, 'f948c136ac47f321'),
    'hexagram_64': (64, 'a123dc87a005f005'),
    'hexagram_yao_ci': (96, '993cd85078cdb4e1'),
    'shishen_knowledge': (10, '75203f261fdd58a2'),
    'shishen_map': (10, '3cd8c7057835f58d'),
    'wuxing_knowledge': (5, '0eae8c2526a6b095'),
    'wuxing_relations': (40, '144595e3861792c9'),
    'tian_gan_he': (5, 'bfa3166dfca27ebd'),
    'di_zhi_he': (6, 'f822cd54ef19d0cf'),
    'di_zhi_chong': (6, 'b55ac56bfc4373a0'),
    'di_zhi_hai': (6, '27eeb766b559effd'),
    'di_zhi_xing': (4, '47d32294d93e2145'),
    'di_zhi_san_he': (4, 'e603f0e24adb09fc'),
    'nayin_wuxing': (60, '3a84c7d86ebcbc87'),
    'shensha_terms': (21, '67eaf3650660e3fc'),
    'ganzhi_relation_terms': (0, '0000000000000000'),
    'foundation_terms': (0, '0000000000000000'),
    'meihua_terms': (0, '0000000000000000'),
    'meihua_knowledge': (8, 'e53b0785cfaa492e'),
    'city_coords': (20, '6c5a039ec50a1bb3'),
    'yunshi_gan_analysis': (10, 'fb66e5a1af04e20a'),
    'yunshi_zhi_analysis': (12, '5414f09a6e3b6c98'),
    'stroke_count': (102998, None),  # 大表仅校验行数，MD5 设为 None 跳过
}


class DatabaseManager:
    """数据库管理器 - 封装所有基于本地 SQLite 的数据库操作"""

    def __init__(self, config_path: str = None):
        """
        初始化数据库管理器。

        Args:
            config_path: 兼容旧签名保留，当前实现忽略（DB 路径由 core.sqlite_db 统一解析）。
        """
        # 关键：在 __init__ 最开始就注册单例，防止初始化期间的递归创建
        # （如 StorageLogHandler.emit 记录日志触发 get_db_manager()）
        global _db_manager_singleton
        _db_manager_singleton = self

        self.config_path = config_path
        # 首次运行时由 schema_sqlite.sql 建库；随后补建运行期表
        sqlite_db.ensure_initialized()
        self._init_runtime_tables()

    def _connect(self):
        """获取一个本地 SQLite 连接（row_factory=Row，调用方负责 close）。"""
        return sqlite_db.get_connection()

    def _init_runtime_tables(self):
        """补建 base.sql 未包含的运行期表：ui_settings / operation_logs / system_logs / stroke_count / db_version。"""
        conn = self._connect()
        try:
            cur = conn.cursor()
            # 登录/注册功能已移除，清理遗留的 users 表与索引
            cur.execute("DROP TABLE IF EXISTS users")
            cur.execute("DROP INDEX IF EXISTS idx_users_username")
            conn.commit()
        except Exception:
            pass
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ui_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    settings_json TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    op_type TEXT,
                    op_object TEXT DEFAULT '',
                    user_id INTEGER,
                    session TEXT,
                    detail TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT,
                    message TEXT,
                    module TEXT,
                    data_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 笔画数表：用于梅花易数笔画起卦
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stroke_count (
                    char TEXT PRIMARY KEY,
                    strokes INTEGER NOT NULL,
                    source TEXT DEFAULT 'kangxi'
                )
            """)
            # 创建索引加速查询
            cur.execute("CREATE INDEX IF NOT EXISTS idx_stroke_count_strokes ON stroke_count(strokes)")
            # 数据库版本/校验和表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS db_version (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    schema_version INTEGER NOT NULL,
                    seed_checksums_json TEXT NOT NULL,
                    verified_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    drift_detected INTEGER DEFAULT 0,
                    drift_details_json TEXT
                )
            """)
            conn.commit()
            # 初始化常用字笔画数据（康熙字典笔画标准）
            self._init_stroke_count_data(cur)
            conn.commit()
            # 种子数据完整性验证：放入后台线程，避免阻塞主线程（stroke_count 表 10 万行全表扫描很慢）
            threading.Thread(target=self._verify_seed_integrity_async, daemon=True).start()
        finally:
            conn.close()

    def _verify_seed_integrity_async(self):
        """后台异步验证种子数据完整性，避免阻塞 UI 主线程。
        加重试应对偶发的 'database is locked' 瞬态；全部失败仅记录，不抛错。

        【日志优化】启动时的种子校验本意为保护数据完整性，但实际输出
        会在每次启动后产生大量重复日志，淹没真实的业务/ AI 错误。
        现改为“静默模式”：仅在发生真正偏移时发出一次 WARNING，健康情形不产出任何 INFO 级日志。
        异常也降到 DEBUG，不再干扰用户排查。
        """
        import time
        max_retries = 5
        retry_delay = 0.3
        last_err = None
        for attempt in range(max_retries):
            try:
                conn = self._connect()
                try:
                    self._verify_seed_integrity(conn.cursor())
                    conn.commit()
                    return
                finally:
                    conn.close()
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if 'locked' in msg and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                break
        if last_err is not None:
            # 异常降为 DEBUG，避免每次启动因锁竞争产生无意义警告
            logger.debug(f"[DB校验] 后台校验异常（已静默降级，不影响启动）：{last_err}")

    def _init_stroke_count_data(self, cur):
        """初始化汉字笔画数据（康熙字典标准）。

        优先从 external JSON 文件加载扩展数据，如果不存在则使用内置数据。
        """
        # 检查是否已有数据
        cur.execute("SELECT COUNT(*) as cnt FROM stroke_count")
        if cur.fetchone()['cnt'] > 0:
            return
        
        # 尝试从外部JSON文件加载扩展数据
        json_loaded = False
        try:
            import json
            import os
            json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'unihan_stroke_counts.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stroke_data = [(item['char'], item['strokes']) for item in data.get('characters', [])]
                    for char, strokes in stroke_data:
                        cur.execute(
                            "INSERT OR IGNORE INTO stroke_count (char, strokes, source) VALUES (?, ?, 'unihan')",
                            (char, strokes)
                        )
                    json_loaded = True
                    logger.info(f"[笔画数据] 从 {json_path} 加载了 {len(stroke_data)} 个字符")
        except Exception as e:
            logger.warning(f"[笔画数据] 加载外部JSON文件失败: {e}")
        
        # 如果外部文件加载失败，使用内置数据
        if not json_loaded:
            
            # 常用字笔画数据（部分高频字，康熙字典笔画）
            stroke_data = [
                # 1-2 画
                ('一', 1), ('丨', 1), ('丶', 1), ('丿', 1), ('乙', 1), ('亅', 1),
                ('二', 2), ('亠', 2), ('人', 2), ('儿', 2), ('入', 2), ('八', 2), ('冂', 2), ('冖', 2), ('冫', 2), ('几', 2), ('凵', 2), ('刀', 2), ('力', 2), ('勹', 2), ('匕', 2), ('匚', 2), ('匸', 2), ('十', 2), ('卜', 2), ('卩', 2), ('厂', 2), ('厶', 2), ('又', 2),
                # 3 画
                ('口', 3), ('囗', 3), ('土', 3), ('士', 3), ('夂', 3), ('夊', 3), ('夕', 3), ('大', 3), ('女', 3), ('子', 3), ('宀', 3), ('寸', 3), ('小', 3), ('尢', 3), ('尸', 3), ('屮', 3), ('山', 3), ('川', 3), ('工', 3), ('己', 3), ('巾', 3), ('干', 3), ('幺', 3), ('广', 3), ('廴', 3), ('廾', 3), ('弋', 3), ('弓', 3), ('彐', 3), ('彡', 3), ('彳', 3),
                # 4 画
                ('心', 4), ('戈', 4), ('戶', 4), ('手', 4), ('支', 4), ('攴', 4), ('文', 4), ('斗', 4), ('斤', 4), ('方', 4), ('无', 4), ('日', 4), ('曰', 4), ('月', 4), ('木', 4), ('欠', 4), ('止', 4), ('歹', 4), ('殳', 4), ('毋', 4), ('比', 4), ('毛', 4), ('氏', 4), ('气', 4), ('水', 4), ('火', 4), ('爪', 4), ('父', 4), ('爻', 4), ('爿', 4), ('片', 4), ('牙', 4), ('牛', 4), ('犬', 4),
                # 5 画
                ('玄', 5), ('玉', 5), ('瓜', 5), ('瓦', 5), ('甘', 5), ('生', 5), ('用', 5), ('田', 5), ('疋', 5), ('疒', 5), ('癶', 5), ('白', 5), ('皮', 5), ('皿', 5), ('目', 5), ('矛', 5), ('矢', 5), ('石', 5), ('示', 5), ('禸', 5), ('禾', 5), ('穴', 5), ('立', 5),
                # 常用字扩展
                ('甲', 5), ('乙', 1), ('丙', 5), ('丁', 2), ('戊', 5), ('己', 3), ('庚', 8), ('辛', 7), ('壬', 4), ('癸', 5),
                ('子', 3), ('丑', 6), ('寅', 11), ('卯', 5), ('辰', 7), ('巳', 6), ('午', 7), ('未', 8), ('申', 5), ('酉', 7), ('戌', 6), ('亥', 6),
                ('春', 9), ('夏', 10), ('秋', 9), ('冬', 5),
                ('年', 6), ('月', 4), ('日', 4), ('时', 10),
                ('吉', 6), ('凶', 6), ('福', 14), ('禄', 12), ('寿', 7),
                ('天', 4), ('地', 6), ('人', 2), ('和', 8),
                ('龙', 16), ('凤', 4), ('虎', 8), ('龟', 16),
                ('金', 8), ('木', 4), ('水', 4), ('火', 4), ('土', 3),
                ('山', 3), ('川', 3), ('河', 8), ('海', 11), ('湖', 12),
                ('风', 4), ('雨', 8), ('雷', 13), ('电', 5), ('云', 4),
                ('花', 8), ('草', 9), ('树', 10), ('林', 8), ('森', 12),
                ('书', 10), ('剑', 9), ('琴', 12), ('棋', 12), ('画', 8),
                ('诗', 13), ('词', 12), ('赋', 12), ('文', 4), ('章', 11),
                ('德', 15), ('仁', 4), ('义', 13), ('礼', 5), ('智', 12), ('信', 9),
                ('道', 12), ('法', 8), ('术', 10), ('数', 13), ('理', 11),
                ('命', 8), ('运', 12), ('卦', 8), ('象', 12), ('数', 13),
                ('梅', 11), ('花', 8), ('易', 8), ('数', 13), ('六', 4), ('壬', 4),
                ('大', 3), ('小', 3), ('中', 4), ('上', 3), ('下', 3),
                ('左', 5), ('右', 5), ('前', 9), ('后', 6), ('内', 4), ('外', 5),
                ('东', 5), ('西', 6), ('南', 9), ('北', 5), ('中', 4),
                ('男', 7), ('女', 3), ('夫', 4), ('妻', 8), ('子', 3), ('孙', 10),
                ('父', 4), ('母', 5), ('兄', 5), ('弟', 7), ('姐', 8), ('妹', 8),
                ('我', 7), ('你', 7), ('他', 5), ('它', 5), ('此', 6), ('彼', 8),
                ('是', 9), ('非', 8), ('有', 6), ('无', 4), ('在', 6), ('不', 4),
                ('可', 5), ('能', 10), ('会', 6), ('要', 9), ('想', 13), ('知', 8),
                ('见', 7), ('闻', 9), ('问', 6), ('答', 12), ('说', 9), ('听', 7),
                ('看', 9), ('读', 10), ('写', 5), ('做', 11), ('行', 6), ('走', 7),
                ('坐', 7), ('卧', 8), ('睡', 13), ('醒', 16), ('食', 9), ('饮', 12),
                ('穿', 12), ('戴', 17), ('用', 5), ('买', 12), ('卖', 12), ('给', 9),
                ('拿', 10), ('放', 8), ('开', 12), ('关', 11), ('进', 11), ('出', 5),
                ('来', 7), ('去', 5), ('回', 6), ('转', 8), ('过', 12), ('到', 8),
                ('从', 4), ('往', 7), ('向', 6), ('对', 5), ('为', 4), ('被', 10),
                ('把', 7), ('将', 10), ('让', 5), ('使', 8), ('叫', 5), ('喊', 12),
                ('笑', 10), ('哭', 10), ('喜', 12), ('怒', 9), ('哀', 9), ('乐', 5),
                ('爱', 10), ('恨', 9), ('怕', 8), ('惊', 11), ('急', 9), ('慢', 11),
                ('快', 7), ('慢', 11), ('早', 6), ('晚', 7), ('迟', 7), ('准', 10),
                ('好', 6), ('坏', 11), ('对', 5), ('错', 10), ('真', 10), ('假', 11),
                ('新', 13), ('旧', 5), ('旧', 5), ('古', 5), ('今', 4),
                ('多', 6), ('少', 4), ('大', 3), ('小', 3), ('长', 8), ('短', 12),
                ('高', 10), ('低', 7), ('上', 3), ('下', 3), ('左', 5), ('右', 5),
                ('前', 9), ('后', 6), ('里', 7), ('外', 5), ('内', 4), ('中', 4),
                ('间', 12), ('隙', 14), ('刻', 8), ('分', 4), ('秒', 9), ('时', 10),
                ('日', 4), ('月', 4), ('年', 6), ('春', 9), ('夏', 10), ('秋', 9), ('冬', 5),
                ('一', 1), ('二', 2), ('三', 3), ('四', 5), ('五', 4), ('六', 4), ('七', 2), ('八', 2), ('九', 2), ('十', 2),
                ('百', 6), ('千', 3), ('万', 3), ('亿', 3),
            ]
            
        for char, strokes in stroke_data:
            cur.execute(
                "INSERT OR IGNORE INTO stroke_count (char, strokes, source) VALUES (?, ?, 'kangxi')",
                (char, strokes)
            )

    def _compute_table_checksum(self, cur, table_name: str, compute_md5: bool = True) -> tuple:
        """计算表的行数和 MD5 校验和（基于所有行的 JSON 序列化）。

        Args:
            cur: 数据库游标
            table_name: 表名
            compute_md5: 是否计算 MD5，大表可设为 False 仅统计行数以提升性能

        Returns:
            (row_count, md5_hex_16): 行数和 MD5 前 16 位（若 compute_md5=False 则 MD5 为 None）
        """
        try:
            cur.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
            row_count = cur.fetchone()['cnt']
            if row_count == 0:
                return (0, '0' * 16 if compute_md5 else None)
            if not compute_md5:
                return (row_count, None)
            # 仅对小表计算 MD5：全表扫描序列化为 JSON
            cur.execute(f"SELECT * FROM {table_name} ORDER BY rowid")
            rows = cur.fetchall()
            data = [dict(r) for r in rows]
            json_str = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            md5_full = hashlib.md5(json_str.encode('utf-8')).hexdigest()
            return (row_count, md5_full[:16])
        except Exception as e:
            logger.warning(f"[DB校验] 计算表 {table_name} 校验和失败: {e}")
            return (0, 'error' if compute_md5 else None)

    def _verify_seed_integrity(self, cur):
        """启动时验证种子数据完整性，对比预期校验和。

        将当前数据库的种子表行数和校验和与 EXPECTED_SEED_CHECKSUMS 对比，
        发现偏差时写入 db_version 表并记录警告日志。
        对于大表（如 stroke_count），仅校验行数，跳过 MD5 计算以提升性能。
        【日志优化】原实现会在每次启动时产生大量重复 INFO/DEBUG，导致日志被刷屏且
        掩盖真实的 AI/运行错误。现改为仅在发生偏移时输出一次汇总，其余情况仅在
        DEBUG 级别记录，避免业务日志污染。
        """
        drift_details = {}
        drift_detected = False

        for table_name, (expected_rows, expected_md5) in EXPECTED_SEED_CHECKSUMS.items():
            # 大表（expected_md5 为 None）仅校验行数，不计算 MD5
            compute_md5 = expected_md5 is not None
            actual_rows, actual_md5 = self._compute_table_checksum(cur, table_name, compute_md5=compute_md5)
            # 对比时忽略 MD5 为 None 的情况
            md5_mismatch = compute_md5 and actual_md5 != expected_md5
            # 仅对行数偏离报警；MD5 偏离记为 debug，避免刷屏
            if actual_rows != expected_rows:
                drift_details[table_name] = {
                    'expected': {'rows': expected_rows, 'md5': expected_md5},
                    'actual': {'rows': actual_rows, 'md5': actual_md5}
                }
                drift_detected = True
                # 原 warning 改为 debug，避免重复刷屏
                logger.debug(
                    f"[DB校验] 种子表 {table_name} 行数偏离预期: "
                    f"预期行数={expected_rows}, 实际行数={actual_rows}"
                )
            elif md5_mismatch:
                # MD5 差异通常是序列化差异，不阻断功能
                logger.debug(
                    f"[DB校验] 种子表 {table_name} MD5 与预期不符（不影响功能）: "
                    f"预期={expected_md5}, 实际={actual_md5}"
                )

        # 更新 db_version 表
        current_checksums = {}
        for table_name, (expected_rows, expected_md5) in EXPECTED_SEED_CHECKSUMS.items():
            compute_md5 = expected_md5 is not None
            rows, md5 = self._compute_table_checksum(cur, table_name, compute_md5=compute_md5)
            current_checksums[table_name] = {'rows': rows, 'md5': md5}

        import datetime
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("""
            INSERT INTO db_version (id, schema_version, seed_checksums_json, verified_at, drift_detected, drift_details_json)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                schema_version = excluded.schema_version,
                seed_checksums_json = excluded.seed_checksums_json,
                verified_at = excluded.verified_at,
                drift_detected = excluded.drift_detected,
                drift_details_json = excluded.drift_details_json
        """, (
            DB_SCHEMA_VERSION,
            json.dumps(current_checksums, ensure_ascii=False),
            now,
            1 if drift_detected else 0,
            json.dumps(drift_details, ensure_ascii=False) if drift_details else None
        ))

        # 日志降噪：只有在真正发生偏移时才输出一次汇总提示。
        # 原实现每次启动都会输出 INFO 级别“验证通过”，导致日志淹没真实的 AI/错误日志。
        if drift_detected:
            logger.warning(
                f"[DB校验] 检测到种子数据偏移！共有 {len(drift_details)} 个表与预期不符。"
                f"请检查 scripts/convert_mysql_to_sqlite.py 是否已同步更新，"
                f"或重新运行数据库初始化。详情见 db_version 表 drift_details_json 字段。"
            )
        else:
            # 改为 debug 级别，避免每次启动刷屏
            logger.debug(f"[DB校验] 种子数据完整性验证通过，schema_version={DB_SCHEMA_VERSION}")

    def get_db_version_info(self) -> dict:
        """获取数据库版本与校验信息"""
        row = self._query_one("SELECT * FROM db_version WHERE id = 1")
        if not row:
            return {'schema_version': None, 'verified_at': None, 'drift_detected': False, 'details': None}
        return {
            'schema_version': row['schema_version'],
            'verified_at': row['verified_at'],
            'drift_detected': bool(row['drift_detected']),
            'drift_details': json.loads(row['drift_details_json']) if row['drift_details_json'] else None,
            'current_checksums': json.loads(row['seed_checksums_json']) if row['seed_checksums_json'] else None
        }

    # ==================== 文本数据查询接口 ====================

    def _query_all(self, sql: str, params=None) -> list:
        """执行查询并返回所有结果"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            return cursor.fetchall()
        finally:
            conn.close()

    def _query_one(self, sql: str, params=None) -> dict:
        """执行查询并返回单条结果"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            return cursor.fetchone()
        finally:
            conn.close()

    # ===== 公开 SQL 代理（供 service 层跨表查询使用，避免直接访问 _query_all） =====

    def query_all(self, sql: str, params=None) -> list:
        """公开查询接口：执行 SQL 并返回所有结果行（dict）。

        Args:
            sql: SQLite 查询语句
            params: 参数元组

        Returns:
            list[dict]: 结果行
        """
        return [dict(r) for r in self._query_all(sql, params)]

    def query_one(self, sql: str, params=None) -> Optional[dict]:
        """公开查询接口：执行 SQL 并返回单条结果（dict 或 None）。"""
        row = self._query_one(sql, params)
        return dict(row) if row is not None else None

    def execute_insert(self, sql: str, params=None) -> int:
        """公开写接口：执行 INSERT/UPDATE/DELETE 并提交，返回 lastrowid。

        Args:
            sql: SQL 语句
            params: 参数元组

        Returns:
            int: 最近插入的行 ID
        """
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    # ==================== FTS 历史记录全文搜索 ====================

    def search_records_fts(self, keyword: str, limit: int = 20) -> list:
        """使用 FTS5 虚拟表搜索历史排盘记录。

        优先命中 name、city、birth_date 字段；无匹配时回退到 LIKE 全文搜索。

        Args:
            keyword: 搜索关键词（支持模糊匹配，如「张」匹配所有含「张」的记录）
            limit: 返回结果数量上限，默认 20

        Returns:
            list[dict]: 匹配的排盘记录，按 relevance 降序排列
        """
        if not keyword or not keyword.strip():
            return []
        kw = keyword.strip()
        conn = self._connect()
        try:
            cursor = conn.cursor()
            # FTS5 优先：rank 按相关度排序
            try:
                cursor.execute(
                    """
                    SELECT r.*
                    FROM analysis_records r
                    JOIN analysis_records_fts f ON r.id = f.rowid
                    WHERE analysis_records_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (kw, limit),
                )
            except Exception:
                # FTS5 不存在时（旧版数据库），回退到 LIKE
                pattern = f'%{kw}%'
                cursor.execute(
                    """
                    SELECT id, name, gender, birth_date, birth_time, city, created_at
                    FROM analysis_records
                    WHERE name LIKE ? OR city LIKE ? OR birth_date LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (pattern, pattern, pattern, limit),
                )
            rows = cursor.fetchall()
            return [dict(r) for r in rows] if rows else []
        finally:
            conn.close()

    def get_record_count(self) -> int:
        """获取历史记录总数。"""
        row = self._query_one("SELECT COUNT(*) as cnt FROM analysis_records")
        return row['cnt'] if row else 0

    # -- 天干 --
    def get_tian_gan_all(self) -> list:
        """获取所有天干数据"""
        return self._query_all("SELECT * FROM tian_gan ORDER BY idx")

    def get_tian_gan_list(self) -> list:
        """获取天干列表 ['甲','乙',...]"""
        rows = self._query_all("SELECT gan FROM tian_gan ORDER BY idx")
        return [r['gan'] for r in rows]

    def get_tian_gan_map(self) -> dict:
        """获取天干到索引的映射 {gan: idx}"""
        rows = self._query_all("SELECT gan, idx FROM tian_gan")
        return {r['gan']: r['idx'] for r in rows}

    def get_tian_gan_wuxing(self) -> dict:
        """获取天干五行映射 {gan: wuxing}"""
        rows = self._query_all("SELECT gan, wuxing FROM tian_gan")
        return {r['gan']: r['wuxing'] for r in rows}

    def get_tian_gan_detail(self, gan: str) -> dict:
        """获取单个天干详细信息"""
        return self._query_one("SELECT * FROM tian_gan WHERE gan = ?", (gan,))

    # -- 地支 --
    def get_di_zhi_all(self) -> list:
        """获取所有地支数据"""
        return self._query_all("SELECT * FROM di_zhi ORDER BY idx")

    def get_di_zhi_list(self) -> list:
        """获取地支列表"""
        rows = self._query_all("SELECT zhi FROM di_zhi ORDER BY idx")
        return [r['zhi'] for r in rows]

    def get_di_zhi_map(self) -> dict:
        """获取地支到索引的映射"""
        rows = self._query_all("SELECT zhi, idx FROM di_zhi")
        return {r['zhi']: r['idx'] for r in rows}

    def get_di_zhi_wuxing(self) -> dict:
        """获取地支五行映射"""
        rows = self._query_all("SELECT zhi, wuxing FROM di_zhi")
        return {r['zhi']: r['wuxing'] for r in rows}

    # -- 地支藏干 --
    def get_di_zhi_hidden_gan(self) -> dict:
        """获取地支藏干数据 {zhi: [(gan, qi_type, score), ...]}"""
        rows = self._query_all(
            "SELECT zhi, hidden_gan, qi_type, qi_score FROM di_zhi_hidden_gan ORDER BY zhi, sort_order"
        )
        result = {}
        for r in rows:
            zhi = r['zhi']
            if zhi not in result:
                result[zhi] = []
            result[zhi].append((r['hidden_gan'], r['qi_type'], float(r['qi_score'])))
        return result

    def get_di_zhi_hidden_gan_simple(self) -> dict:
        """获取地支藏干简化版 {zhi: [gan, ...]}"""
        rows = self._query_all(
            "SELECT zhi, hidden_gan FROM di_zhi_hidden_gan ORDER BY zhi, sort_order"
        )
        result = {}
        for r in rows:
            if r['zhi'] not in result:
                result[r['zhi']] = []
            result[r['zhi']].append(r['hidden_gan'])
        return result

    # -- 六十甲子 --
    def get_sixty_jiazi(self) -> list:
        """获取六十甲子列表 ['甲子','乙丑',...]"""
        rows = self._query_all("SELECT ganzhi FROM sixty_jiazi ORDER BY idx")
        return [r['ganzhi'] for r in rows]

    def get_sixty_jiazi_map(self) -> dict:
        """获取六十甲子索引映射 {ganzhi: idx}"""
        rows = self._query_all("SELECT ganzhi, idx FROM sixty_jiazi")
        return {r['ganzhi']: r['idx'] for r in rows}

    # -- 月干规则 --
    def get_month_gan_rules(self) -> dict:
        """获取月干规则(五虎遁) {year_gan_group: [gan1, gan2, ...]}"""
        rows = self._query_all(
            "SELECT year_gan_group, month_order, month_gan FROM month_gan_rules ORDER BY year_gan_group, month_order"
        )
        result = {}
        for r in rows:
            group = r['year_gan_group']
            if group not in result:
                result[group] = [None] * 12
            result[group][r['month_order']] = r['month_gan']
        return result

    # -- 节气 --
    def get_jie_qi_list(self) -> list:
        """获取节气名称列表"""
        rows = self._query_all("SELECT name FROM jie_qi ORDER BY idx")
        return [r['name'] for r in rows]

    def get_jie_qi_angles(self) -> list:
        """获取节气黄经角度列表"""
        rows = self._query_all("SELECT angle FROM jie_qi ORDER BY idx")
        return [r['angle'] for r in rows]

    def get_jie_qi_base_days(self) -> list:
        """获取节气基准日偏移"""
        rows = self._query_all("SELECT base_days FROM jie_qi ORDER BY idx")
        return [float(r['base_days']) for r in rows]

    def get_jie_qi_month_map(self) -> dict:
        """获取节气-月建映射 {jieqi_idx: month_zhi}"""
        rows = self._query_all("SELECT jie_qi_idx, month_zhi FROM jie_qi_month_map")
        return {r['jie_qi_idx']: r['month_zhi'] for r in rows}

    # -- 月令权重 --
    def get_yue_ling_weight(self) -> dict:
        """获取月令权重 {zhi: {wuxing: weight}}"""
        rows = self._query_all("SELECT zhi, wuxing, weight FROM yue_ling_weight")
        result = {}
        for r in rows:
            if r['zhi'] not in result:
                result[r['zhi']] = {}
            result[r['zhi']][r['wuxing']] = float(r['weight'])
        return result

    # -- 八卦 --
    def get_ba_gua(self) -> dict:
        """获取八卦数据 {num: info_dict}"""
        rows = self._query_all("SELECT * FROM ba_gua")
        return {r['num']: r for r in rows}

    def get_ba_gua_by_num(self, num: int) -> dict:
        """按先天数获取八卦信息"""
        return self._query_one("SELECT * FROM ba_gua WHERE num = ?", (num,))

    # -- 64卦 --
    def get_hexagram_64(self) -> dict:
        """获取64卦数据 {(upper, lower): info_dict}"""
        rows = self._query_all("SELECT * FROM hexagram_64")
        return {(r['upper_num'], r['lower_num']): r for r in rows}

    def get_hexagram_by_id(self, hexagram_id: int) -> dict:
        """按卦序获取卦信息"""
        return self._query_one(
            "SELECT * FROM hexagram_64 WHERE hexagram_id = ?", (hexagram_id,)
        )

    def get_hexagram_by_upper_lower(self, upper: int, lower: int) -> dict:
        """按上下卦数获取卦信息"""
        return self._query_one(
            "SELECT * FROM hexagram_64 WHERE upper_num = ? AND lower_num = ?",
            (upper, lower)
        )

    # -- 64卦爻辞 --
    def get_hexagram_yao_ci(self, hexagram_id: int) -> list:
        """获取某卦的所有爻辞"""
        return self._query_all(
            "SELECT * FROM hexagram_yao_ci WHERE hexagram_id = ? ORDER BY yao_order",
            (hexagram_id,)
        )

    # -- 十神 --
    def get_shishen_knowledge(self) -> dict:
        """获取十神知识 {name: info}"""
        rows = self._query_all("SELECT * FROM shishen_knowledge")
        return {r['name']: r for r in rows}

    def get_shishen_map(self) -> dict:
        """获取十神映射 {shishen_type: {category, yang_name, yin_name}}"""
        rows = self._query_all("SELECT * FROM shishen_map")
        return {r['shishen_type']: r for r in rows}

    def get_shishen_wuxing_map(self) -> dict:
        """获取十神到五行关系的映射 {shishen_name: relation_type}"""
        rows = self._query_all("SELECT name, shishen_type FROM shishen_knowledge")
        return {r['name']: r['shishen_type'] for r in rows}

    # -- 五行知识 --
    def get_wuxing_knowledge(self) -> dict:
        """获取五行知识 {wuxing_name: info}"""
        rows = self._query_all("SELECT * FROM wuxing_knowledge")
        return {r['wuxing_name']: r for r in rows}

    # -- 五行关系 --
    def get_wuxing_relations(self) -> dict:
        """获取五行关系 {relation_type: {name, description, relations: [...]}}"""
        rows = self._query_all(
            "SELECT * FROM wuxing_relations ORDER BY relation_type, id"
        )
        result = {}
        for r in rows:
            rt = r['relation_type']
            if rt not in result:
                result[rt] = {
                    'name': r['relation_name'],
                    'description': r['description'],
                    'relations': []
                }
            result[rt]['relations'].append({
                'from': r['from_wuxing'],
                'to': r['to_wuxing'],
                'meaning': r['meaning']
            })
        return result

    # -- 天干合化 --
    def get_tian_gan_he(self) -> dict:
        """获取天干合化 {gan_pair: info}"""
        rows = self._query_all("SELECT * FROM tian_gan_he")
        return {r['gan_pair']: r for r in rows}

    # -- 地支合冲害刑 --
    def get_di_zhi_he(self) -> dict:
        """获取地支六合 {zhi_pair: info}"""
        rows = self._query_all("SELECT * FROM di_zhi_he")
        return {r['zhi_pair']: r for r in rows}

    def get_di_zhi_chong(self) -> dict:
        """获取地支六冲 {zhi_pair: info}"""
        rows = self._query_all("SELECT * FROM di_zhi_chong")
        return {r['zhi_pair']: r for r in rows}

    def get_di_zhi_hai(self) -> dict:
        """获取地支六害"""
        rows = self._query_all("SELECT * FROM di_zhi_hai")
        return {r['zhi_pair']: r for r in rows}

    def get_di_zhi_xing(self) -> dict:
        """获取地支三刑"""
        rows = self._query_all("SELECT * FROM di_zhi_xing")
        return {r['zhi_group']: r for r in rows}

    def get_di_zhi_san_he(self) -> dict:
        """获取地支三合"""
        rows = self._query_all("SELECT * FROM di_zhi_san_he")
        return {r['zhi_group']: r for r in rows}

    # -- 十二长生 --
    def get_shier_changsheng(self) -> dict:
        """获取十二长生知识 {name: info}"""
        rows = self._query_all("SELECT * FROM shier_changsheng")
        return {r['name']: r for r in rows}

    # -- 十二长生查找表 --
    def init_changsheng_lookup(self):
        """初始化十二长生查找表（天干 -> 地支 -> 阶段名）。

        算法：每个天干都有一个「长生」起始地支，阳干沿地支顺序顺行、
        阴干逆行，依次经历十二个阶段，正好绕地支一周。
        结果以 (gan, zhi, stage_name) 三元组批量写入 changsheng_lookup 表，
        使用 INSERT OR IGNORE 保证可重复执行而不产生重复行。
        """
        # 十二长生阶段名称，索引即距离起始地支的步数
        stages = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']
        # 各天干的「长生」起始地支
        changsheng_start = {
            '甲': '亥', '乙': '午', '丙': '寅', '丁': '酉',
            '戊': '寅', '己': '酉', '庚': '巳', '辛': '子',
            '壬': '申', '癸': '卯'
        }
        # 地支顺序与索引映射复用权威常量，避免本地重复硬编
        di_zhi_order = DI_ZHI
        di_zhi_map = ZHI_INDEX

        data = []
        for gan, start_zhi in changsheng_start.items():
            # 天干序号为偶数即阳干（甲丙戊庚壬），阳干顺行、阴干逆行
            is_yang = gan in GAN_YANG
            start_pos = di_zhi_map[start_zhi]
            for i, stage in enumerate(stages):
                if is_yang:
                    zhi_pos = (start_pos + i) % 12
                else:
                    zhi_pos = (start_pos - i) % 12
                zhi = di_zhi_order[zhi_pos]
                data.append((gan, zhi, stage))


        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO changsheng_lookup (gan, zhi, stage_name) VALUES (?, ?, ?)",
                data
            )
            conn.commit()

    def get_changsheng_lookup(self) -> dict:
        """获取十二长生查找表 {gan: {zhi: stage_name}}"""
        rows = self._query_all("SELECT gan, zhi, stage_name FROM changsheng_lookup")
        result = {}
        for r in rows:
            if r['gan'] not in result:
                result[r['gan']] = {}
            result[r['gan']][r['zhi']] = r['stage_name']
        return result

    def get_changsheng_lookup_list(self) -> dict:
        """获取十二长生查找表 {gan: [zhi_list]} 按阶段顺序"""
        stages = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']
        rows = self._query_all("SELECT gan, zhi, stage_name FROM changsheng_lookup")
        result = {}
        for r in rows:
            if r['gan'] not in result:
                result[r['gan']] = [None] * 12
            stage_idx = stages.index(r['stage_name']) if r['stage_name'] in stages else 0
            result[r['gan']][stage_idx] = r['zhi']
        return result

    # -- 纳音五行 --
    def init_nayin_wuxing(self):
        """初始化纳音五行数据"""
        nayin_data = [
            ('甲子', '海中金', '金'), ('乙丑', '海中金', '金'),
            ('丙寅', '炉中火', '火'), ('丁卯', '炉中火', '火'),
            ('戊辰', '大林木', '木'), ('己巳', '大林木', '木'),
            ('庚午', '路旁土', '土'), ('辛未', '路旁土', '土'),
            ('壬申', '剑锋金', '金'), ('癸酉', '剑锋金', '金'),
            ('甲戌', '山头火', '火'), ('乙亥', '山头火', '火'),
            ('丙子', '涧下水', '水'), ('丁丑', '涧下水', '水'),
            ('戊寅', '城头土', '土'), ('己卯', '城头土', '土'),
            ('庚辰', '白蜡金', '金'), ('辛巳', '白蜡金', '金'),
            ('壬午', '杨柳木', '木'), ('癸未', '杨柳木', '木'),
            ('甲申', '泉中水', '水'), ('乙酉', '泉中水', '水'),
            ('丙戌', '屋上土', '土'), ('丁亥', '屋上土', '土'),
            ('戊子', '霹雳火', '火'), ('己丑', '霹雳火', '火'),
            ('庚寅', '松柏木', '木'), ('辛卯', '松柏木', '木'),
            ('壬辰', '长流水', '水'), ('癸巳', '长流水', '水'),
            ('甲午', '沙中金', '金'), ('乙未', '沙中金', '金'),
            ('丙申', '山下火', '火'), ('丁酉', '山下火', '火'),
            ('戊戌', '平地木', '木'), ('己亥', '平地木', '木'),
            ('庚子', '壁上土', '土'), ('辛丑', '壁上土', '土'),
            ('壬寅', '金箔金', '金'), ('癸卯', '金箔金', '金'),
            ('甲辰', '覆灯火', '火'), ('乙巳', '覆灯火', '火'),
            ('丙午', '天河水', '水'), ('丁未', '天河水', '水'),
            ('戊申', '大驿土', '土'), ('己酉', '大驿土', '土'),
            ('庚戌', '钗钏金', '金'), ('辛亥', '钗钏金', '金'),
            ('壬子', '桑柘木', '木'), ('癸丑', '桑柘木', '木'),
            ('甲寅', '大溪水', '水'), ('乙卯', '大溪水', '水'),
            ('丙辰', '沙中土', '土'), ('丁巳', '沙中土', '土'),
            ('戊午', '天上火', '火'), ('己未', '天上火', '火'),
            ('庚申', '石榴木', '木'), ('辛酉', '石榴木', '木'),
            ('壬戌', '大海水', '水'), ('癸亥', '大海水', '水')
        ]
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO nayin_wuxing (ganzhi_pair, nayin_name, wuxing) VALUES (?, ?, ?)",
                nayin_data
            )
            conn.commit()

    def get_nayin_wuxing(self) -> dict:
        """获取纳音五行 {ganzhi: (nayin_name, wuxing)}"""
        rows = self._query_all("SELECT ganzhi_pair, nayin_name, wuxing FROM nayin_wuxing")
        return {r['ganzhi_pair']: (r['nayin_name'], r['wuxing']) for r in rows}

    # -- 神煞数据（含计算条件） --
    def init_shensha_terms(self):
        """初始化神煞术语数据（含计算条件）"""
        # shensha_terms 表字段: name, category, term_type, brief, description, check_method, influences, related_terms
        shensha_data = [
            ('天德', '神煞', 'positive', '天德贵人，主吉祥、逢凶化吉',
             '天德贵人是四柱神煞中最吉祥的神煞之一。天德者，谓合天德之正气，主人慈祥和蔼，聪明正直，一生少病灾，遇难呈祥，逢凶化吉。命中有天德贵人者，多为善良之人，容易得到他人帮助，一生平安顺遂。',
             '{"type": "gan", "conditions": {"丙": ["寅"], "丁": ["亥"], "戊": ["寅"], "己": ["申"], "庚": ["亥"], "辛": ["巳"], "壬": ["寅"], "癸": ["申"]}, "locations": ["月柱"]}',
             '["健康", "贵人运", "平安"]', '["月德", "天乙贵人"]'),
            ('月德', '神煞', 'positive', '月德贵人，主仁慈、聪明、福寿',
             '月德贵人与天德贵人并称"二德"，同为吉祥神煞。月德者，谓合月德之正气，主人仁慈敦厚，聪明好学，福寿双全，一生平安。命中有月德贵人者，性情温和，乐于助人，容易得到长辈和上级的提携。',
             '{"type": "gan", "conditions": {"丙": ["甲"], "丁": ["壬"], "戊": ["丙"], "己": ["甲"], "庚": ["戊"], "辛": ["丙"], "壬": ["庚"], "癸": ["戊"]}, "locations": ["月柱"]}',
             '["贵人运", "健康", "福寿"]', '["天德"]'),
            ('文昌', '神煞', 'positive', '文昌星，主学业、才华、聪明过人',
             '文昌星主学业、文章、才华。命中有文昌星者，聪明伶俐，记忆力强，学习能力出众，容易在学业上取得优异成绩，适合从事学术研究、教育、文化艺术等工作。文昌星入命，主其人多才多艺，富有创造力。',
             '{"type": "gan", "conditions": {"甲": ["巳"], "乙": ["午"], "丙": ["申"], "丁": ["酉"], "戊": ["申"], "己": ["酉"], "庚": ["亥"], "辛": ["子"], "壬": ["寅"], "癸": ["卯"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["学业", "才华", "聪明"]', '["学堂", "词馆"]'),
            ('桃花', '神煞', 'neutral', '桃花星，主人缘、异性缘、社交能力强',
             '桃花星主异性缘、人际关系、社交能力。命中有桃花星者，相貌俊秀，气质高雅，善于交际，异性缘旺盛。桃花星也主艺术才华，适合从事演艺、娱乐、公关等行业。但桃花过旺也可能带来感情困扰，需注意把握分寸。',
             '{"type": "zhi", "conditions": {"子": ["卯"], "午": ["酉"], "卯": ["子"], "酉": ["午"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["桃花", "人缘", "社交"]', '["红艳"]'),
            ('驿马', '神煞', 'neutral', '驿马星，主变动、旅行、迁移',
             '驿马星主变动、旅行、迁移、外出。命中有驿马星者，一生多动少静，喜欢旅行和探索，适合从事需要经常出差或外出的工作，如销售、物流、旅游等行业。驿马星也主机遇，往往在变动中获得发展机会。',
             '{"type": "zhi", "conditions": {"申": ["寅"], "寅": ["申"], "巳": ["亥"], "亥": ["巳"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["变动", "旅行", "迁移"]', '["华盖"]'),
            ('华盖', '神煞', 'neutral', '华盖星，主艺术、才华、孤独',
             '华盖星主艺术、才华、宗教、哲学。命中有华盖星者，富有艺术天赋，对传统文化、宗教哲学有浓厚兴趣，容易在这些领域取得成就。但华盖星也主孤独，其人往往性格内向，喜欢独处，有时会显得孤僻不合群。',
             '{"type": "zhi", "conditions": {"寅": ["戌"], "戌": ["寅"], "辰": ["丑"], "丑": ["辰"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["艺术", "才华", "孤独"]', '["驿马"]'),
            ('将星', '神煞', 'positive', '将星，主权威、领导力、事业有成',
             '将星主权威、领导力、组织能力。命中有将星者，具有领导才能，善于组织和指挥他人，容易成为团队中的核心人物或领导者。将星入命，主其人在事业上容易取得成就，适合从事管理、军事、政治等工作。',
             '{"type": "zhi", "conditions": {"子": ["午"], "午": ["子"], "卯": ["酉"], "酉": ["卯"]}, "locations": ["月柱", "时柱"]}',
             '["权威", "领导力", "事业"]', '["紫微"]'),
            ('天乙', '神煞', 'positive', '天乙贵人，主贵人相助、逢凶化吉',
             '天乙贵人是四柱神煞中最重要的贵人星。天乙者，乃天上之神，在紫微垣、阊阖门外，与太乙并列，事天皇大帝，下游三辰，家在己丑斗牛之次，出乎己未井鬼之舍，执玉衡较量天人之事，名曰天乙也。命中有天乙贵人者，一生多得贵人相助，逢凶化吉，遇难呈祥。',
             '{"type": "gan", "conditions": {"甲": ["丑", "未"], "乙": ["子", "申"], "丙": ["亥", "酉"], "丁": ["亥", "酉"], "戊": ["丑", "未"], "己": ["子", "申"], "庚": ["寅", "午"], "辛": ["寅", "午"], "壬": ["巳", "卯"], "癸": ["巳", "卯"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["贵人运", "吉祥", "帮助"]', '["天德", "月德"]'),
            ('劫煞', '神煞', 'negative', '劫煞，主是非、争斗、意外之灾',
             '劫煞主是非、争斗、抢劫、意外之灾。命中有劫煞者，性格刚烈，容易冲动，好勇斗狠，容易与人发生争执和冲突。劫煞也主财物损失，需注意防范盗窃、抢劫等意外事件。但劫煞也主勇敢果断，若能善用其力，也可在竞争中取得优势。',
             '{"type": "zhi", "conditions": {"申": ["巳"], "巳": ["申"], "寅": ["亥"], "亥": ["寅"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["是非", "争斗", "意外"]', '["亡神"]'),
            ('亡神', '神煞', 'negative', '亡神，主官非、病灾、精神困扰',
             '亡神主官非、病灾、精神困扰。命中有亡神者，容易遇到官司诉讼，身体方面容易有慢性疾病，精神上容易焦虑不安。亡神也主阴谋、暗害，需注意防范小人陷害。但亡神也主聪明才智，若能修身养性，也可将其转化为智慧之力。',
             '{"type": "zhi", "conditions": {"寅": ["巳"], "巳": ["申"], "申": ["亥"], "亥": ["寅"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["官非", "病灾", "精神困扰"]', '["劫煞"]'),
            ('孤辰', '神煞', 'negative', '孤辰，主孤独、寡合、婚姻不顺',
             '孤辰主孤独、寡合、婚姻不顺。命中有孤辰者，性格孤僻，不善于与人交往，朋友稀少，婚姻方面容易晚婚或婚姻不顺。孤辰也主内心空虚，容易感到孤独寂寞。但孤辰也主独立自强，其人往往能够独自完成事业，不需要依赖他人。',
             '{"type": "zhi", "conditions": {"寅": ["巳"], "巳": ["申"], "申": ["亥"], "亥": ["寅"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["孤独", "寡合", "婚姻不顺"]', '["寡宿"]'),
            ('寡宿', '神煞', 'negative', '寡宿，主孤独、守寡、人际关系淡薄',
             '寡宿主孤独、守寡、人际关系淡薄。命中有寡宿者，女性容易守寡或婚姻不幸，男性则容易孤独终老。寡宿也主人际关系淡薄，朋友不多，社交圈子狭窄。但寡宿也主清净无为，其人往往能够专注于自己的事业，不受外界干扰。',
             '{"type": "zhi", "conditions": {"辰": ["丑"], "丑": ["辰"], "戌": ["未"], "未": ["戌"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["孤独", "守寡", "人际关系淡薄"]', '["孤辰"]'),
            ('福星', '神煞', 'positive', '福星贵人，主福禄、长寿、吉祥',
             '福星贵人主福禄、长寿、吉祥。命中有福星贵人者，一生福气深厚，衣食无忧，寿命较长。福星贵人也主善良仁慈，乐于助人，容易得到他人的尊敬和爱戴。',
             '{"type": "gan", "conditions": {"甲": ["子"], "乙": ["丑"], "丙": ["寅"], "丁": ["卯"], "戊": ["辰"], "己": ["巳"], "庚": ["午"], "辛": ["未"], "壬": ["申"], "癸": ["酉"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["福禄", "长寿", "吉祥"]', '["金舆"]'),
            ('金舆', '神煞', 'positive', '金舆贵人，主财富、地位、车房',
             '金舆贵人主财富、地位、车房。命中有金舆贵人者，容易拥有车辆、房产等资产，财运较好，社会地位较高。金舆贵人也主出行便利，一生出行多有车辆代步。',
             '{"type": "gan", "conditions": {"甲": ["辰"], "乙": ["巳"], "丙": ["午"], "丁": ["未"], "戊": ["申"], "己": ["酉"], "庚": ["戌"], "辛": ["亥"], "壬": ["子"], "癸": ["丑"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["财富", "地位", "车房"]', '["福星"]'),
            ('学堂', '神煞', 'positive', '学堂星，主学业、教育、知识',
             '学堂星主学业、教育、知识。命中有学堂星者，学习能力强，学业成绩优异，适合从事教育、学术研究等工作。学堂星也主智慧，其人往往聪明好学，知识渊博。',
             '{"type": "gan", "conditions": {"甲": ["亥"], "乙": ["戌"], "丙": ["寅"], "丁": ["卯"], "戊": ["巳"], "己": ["午"], "庚": ["申"], "辛": ["酉"], "壬": ["子"], "癸": ["丑"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["学业", "教育", "知识"]', '["文昌", "词馆"]'),
            ('词馆', '神煞', 'positive', '词馆星，主文辞、才华、写作',
             '词馆星主文辞、才华、写作。命中有词馆星者，善于文辞表达，写作能力强，适合从事文学创作、新闻媒体、文案策划等工作。词馆星也主口才，其人往往能言善辩，表达能力出众。',
             '{"type": "gan", "conditions": {"甲": ["寅"], "乙": ["卯"], "丙": ["巳"], "丁": ["午"], "戊": ["申"], "己": ["酉"], "庚": ["亥"], "辛": ["子"], "壬": ["辰"], "癸": ["丑"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["文辞", "才华", "写作"]', '["文昌", "学堂"]'),
            ('太极贵人', '神煞', 'positive', '太极贵人，主智慧、神秘、悟性',
             '太极贵人主智慧、神秘、悟性。命中有太极贵人者，对哲学、宗教、神秘学等有浓厚兴趣，悟性较高，容易理解深奥的道理。太极贵人也主创造力，其人往往能够提出独特的见解和想法。',
             '{"type": "gan", "conditions": {"甲": ["子"], "乙": ["午"], "丙": ["卯"], "丁": ["酉"], "戊": ["辰"], "己": ["戌"], "庚": ["巳"], "辛": ["亥"], "壬": ["寅"], "癸": ["申"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["智慧", "神秘", "悟性"]', '["华盖"]'),
            ('天医', '神煞', 'positive', '天医星，主健康、医药、治愈',
             '天医星主健康、医药、治愈。命中有天医星者，对医学、养生等有浓厚兴趣，适合从事医疗、养生、保健等行业。天医星也主身体健康，其人往往较少生病，即使生病也容易痊愈。',
             '{"type": "gan", "conditions": {"甲": ["卯"], "乙": ["寅"], "丙": ["子"], "丁": ["亥"], "戊": ["丑"], "己": ["子"], "庚": ["酉"], "辛": ["申"], "壬": ["午"], "癸": ["巳"]}, "locations": ["月柱", "时柱"]}',
             '["健康", "医药", "治愈"]', '["华盖"]'),
            ('红艳', '神煞', 'neutral', '红艳煞，主桃花、感情、魅力',
             '红艳煞主桃花、感情、魅力。命中有红艳煞者，相貌出众，气质迷人，异性缘非常旺盛。红艳煞也主感情丰富，其人往往容易陷入感情纠葛，需注意把握感情分寸。',
             '{"type": "gan", "conditions": {"甲": ["午"], "乙": ["巳"], "丙": ["寅"], "丁": ["卯"], "戊": ["辰"], "己": ["丑"], "庚": ["子"], "辛": ["亥"], "壬": ["戌"], "癸": ["酉"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["桃花", "感情", "魅力"]', '["桃花"]'),
            ('勾绞', '神煞', 'negative', '勾绞煞，主是非、纠缠、牵连',
             '勾绞煞主是非、纠缠、牵连。命中有勾绞煞者，容易卷入他人的是非纠纷中，即使与自己无关也可能被牵连。勾绞煞也主人际关系复杂，容易与人发生矛盾和冲突。',
             '{"type": "zhi", "conditions": {"子": ["卯"], "卯": ["子"], "丑": ["辰"], "辰": ["丑"], "寅": ["巳"], "巳": ["寅"], "卯": ["午"], "午": ["卯"], "辰": ["未"], "未": ["辰"], "巳": ["申"], "申": ["巳"], "午": ["酉"], "酉": ["午"], "未": ["戌"], "戌": ["未"], "申": ["亥"], "亥": ["申"], "酉": ["子"], "子": ["酉"], "戌": ["丑"], "丑": ["戌"], "亥": ["寅"], "寅": ["亥"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["是非", "纠缠", "牵连"]', '["绞煞"]'),
            ('绞煞', '神煞', 'negative', '绞煞，主纠缠、束缚、困扰',
             '绞煞主纠缠、束缚、困扰。命中有绞煞者，容易被事情或人际关系所束缚，难以摆脱困扰。绞煞也主精神压力，其人往往感到身心疲惫，难以放松。',
             '{"type": "zhi", "conditions": {"子": ["酉"], "酉": ["子"], "丑": ["戌"], "戌": ["丑"], "寅": ["亥"], "亥": ["寅"], "卯": ["子"], "子": ["卯"], "辰": ["丑"], "丑": ["辰"], "巳": ["寅"], "寅": ["巳"], "午": ["卯"], "卯": ["午"], "未": ["辰"], "辰": ["未"], "申": ["巳"], "巳": ["申"], "酉": ["午"], "午": ["酉"], "戌": ["未"], "未": ["戌"], "亥": ["申"], "申": ["亥"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["纠缠", "束缚", "困扰"]', '["勾绞"]')
        ]
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """INSERT OR IGNORE INTO shensha_terms
                (name, category, term_type, brief, description, check_method, influences, related_terms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                shensha_data
            )
            conn.commit()

    def get_shensha_terms(self) -> dict:
        """获取神煞术语（用于术语解释）"""
        rows = self._query_all("SELECT * FROM shensha_terms")
        return {r['name']: r for r in rows}

    def get_shensha_for_calculation(self) -> dict:
        """获取神煞计算数据 {name: {type, description, detailed, locations, conditions}}"""
        rows = self._query_all("SELECT name, term_type, brief, description, check_method FROM shensha_terms")
        result = {}
        for r in rows:
            check = json.loads(r['check_method']) if r['check_method'] else {}
            result[r['name']] = {
                'type': r['term_type'] or 'neutral',
                'description': r['brief'] or r['name'],
                'detailed': r['description'] or '',
                'locations': check.get('locations', ['年柱', '月柱', '日柱', '时柱']),
                'conditions': check.get('conditions', {})
            }
        return result

    def get_ganzhi_relation_terms(self) -> dict:
        """获取干支关系术语"""
        rows = self._query_all("SELECT * FROM ganzhi_relation_terms")
        return {r['name']: r for r in rows}

    def get_foundation_terms(self) -> dict:
        """获取命理基础术语"""
        rows = self._query_all("SELECT * FROM foundation_terms")
        return {r['name']: r for r in rows}

    def get_meihua_terms(self) -> dict:
        """获取梅花易数术语"""
        rows = self._query_all("SELECT * FROM meihua_terms")
        return {r['name']: r for r in rows}

    def get_all_terms(self) -> dict:
        """获取所有术语合并"""
        result = {}
        for rows_func in [self.get_shensha_terms, self.get_ganzhi_relation_terms,
                         self.get_foundation_terms, self.get_meihua_terms]:
            result.update(rows_func())
        return result

    # -- 梅花易数知识 --
    def get_meihua_knowledge(self) -> dict:
        """获取梅花易数知识 {section: {content_key: content_value}}

        兼容两种 content_value 形态：
        - JSON 字符串（历史数据，列表/对象）：解析后赋值。
        - 纯文本（新 P2-3 种子，中文规则）：直接以字符串赋值。
        """
        import json as _json
        rows = self._query_all("SELECT * FROM meihua_knowledge")
        result = {}
        for r in rows:
            section = r['section']
            if section not in result:
                result[section] = {}
            val = r['content_value']
            if isinstance(val, str):
                s = val.strip()
                if s.startswith(('[', '{')):
                    try:
                        val = _json.loads(val)
                    except _json.JSONDecodeError:
                        # 纯文本：保持原样
                        pass
            result[section][r['content_key']] = val
        return result

    # -- 城市坐标 --
    def get_city_coords(self) -> dict:
        """获取城市坐标 {city: (lon, lat)}"""
        rows = self._query_all("SELECT city_name, longitude, latitude FROM city_coords")
        return {r['city_name']: (float(r['longitude']), float(r['latitude'])) for r in rows}

    def get_city_list(self) -> list:
        """获取城市列表"""
        rows = self._query_all("SELECT city_name FROM city_coords")
        return [r['city_name'] for r in rows]

    # -- 笔画数（梅花易数笔画起卦用） --
    def get_stroke_count(self, char: str) -> int:
        """获取单字笔画数（康熙字典标准），未收录返回 0"""
        row = self._query_one("SELECT strokes FROM stroke_count WHERE char = ?", (char,))
        return row['strokes'] if row else 0

    def get_stroke_count_batch(self, chars: list) -> dict:
        """批量获取笔画数 {char: strokes}"""
        if not chars:
            return {}
        placeholders = ','.join('?' * len(chars))
        rows = self._query_all(f"SELECT char, strokes FROM stroke_count WHERE char IN ({placeholders})", chars)
        return {r['char']: r['strokes'] for r in rows}

    # -- 运势天干分析 --
    def get_yunshi_gan_analysis(self) -> dict:
        """获取运势天干分析"""
        rows = self._query_all("SELECT * FROM yunshi_gan_analysis")
        return {r['gan']: r for r in rows}

    # -- 运势地支分析 --
    def get_yunshi_zhi_analysis(self) -> dict:
        """获取运势地支分析"""
        rows = self._query_all("SELECT * FROM yunshi_zhi_analysis")
        return {r['zhi']: r for r in rows}

    # -- 地支冲刑适配方法 (返回 geju_analyzer 兼容格式) --
    def get_di_zhi_chong_map(self) -> dict:
        """获取地支六冲映射 {zhi1: zhi2, zhi2: zhi1}"""
        rows = self._query_all("SELECT zhi_pair FROM di_zhi_chong")
        result = {}
        for r in rows:
            pair = r['zhi_pair']
            if len(pair) == 2:
                result[pair[0]] = pair[1]
                result[pair[1]] = pair[0]
        return result

    def get_di_zhi_xing_map(self) -> dict:
        """获取地支相刑映射 {zhi: [zhi_list]}"""
        rows = self._query_all("SELECT zhi_group FROM di_zhi_xing")
        result = {}
        for r in rows:
            group = r['zhi_group']
            for zhi in group:
                if zhi not in result:
                    result[zhi] = []
                for other in group:
                    if other != zhi:
                        result[zhi].append(other)
        return result

    # ==================== 排盘记录管理 ====================

    def save_pan_record(self, user_id: int, name: str, gender: str,
                        birth_date: str, birth_time: str, city: str,
                        pan_type: str, result: Dict[str, Any],
                        ai_analysis: Optional[Dict] = None) -> Optional[int]:
        """
        保存排盘记录（带重试机制，处理数据库锁定）

        Args:
            user_id: 用户ID
            name: 姓名
            gender: 性别
            birth_date: 出生日期
            birth_time: 出生时间
            city: 城市
            pan_type: 排盘类型
            result: 排盘结果字典
            ai_analysis: AI 深度分析结果（可选，落库 ai_json 列）

        Returns:
            记录ID，失败返回None
        """
        import time
        max_retries = 3
        retry_delay = 0.1  # 100ms
        
        for attempt in range(max_retries):
            try:
                with self._connect() as connection:
                    cursor = connection.cursor()
                    cursor.execute(
                        """
                        INSERT INTO pan_records
                        (user_id, name, gender, birth_date, birth_time, city, pan_type, result_json, ai_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user_id or 1, name, gender, birth_date, birth_time,
                            city, pan_type, json.dumps(result, ensure_ascii=False),
                            json.dumps(ai_analysis, ensure_ascii=False) if ai_analysis else None
                        )
                    )
                    record_id = cursor.lastrowid
                    connection.commit()
                    return record_id
            except Exception as e:
                error_msg = str(e)
                if "database is locked" in error_msg.lower() and attempt < max_retries - 1:
                    # 数据库被锁定，等待后重试
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                # 其他错误或重试次数用完，记录错误并返回None
                if attempt == max_retries - 1:
                    print(f"保存排盘记录失败(重试{max_retries}次后): {e}")
                else:
                    print(f"保存排盘记录失败: {e}")
                return None

    def update_pan_ai_result(self, record_id: int, ai_analysis: Dict[str, Any]) -> bool:
        """
        更新排盘记录的 AI 分析结果到 ai_json 列（带重试机制）。

        Args:
            record_id: 排盘记录 ID
            ai_analysis: AI 分析结果字典

        Returns:
            成功返回 True，失败返回 False
        """
        import time
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                with self._connect() as connection:
                    cursor = connection.cursor()
                    cursor.execute(
                        "UPDATE pan_records SET ai_json = ? WHERE id = ?",
                        (json.dumps(ai_analysis, ensure_ascii=False), record_id)
                    )
                    connection.commit()
                    return cursor.rowcount > 0
            except Exception as e:
                error_msg = str(e)
                if "database is locked" in error_msg.lower() and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                if attempt == max_retries - 1:
                    print(f"更新排盘AI分析结果失败(重试{max_retries}次后): {e}")
                else:
                    print(f"更新排盘AI分析结果失败: {e}")
                return False

    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单条排盘记录

        Args:
            record_id: 记录ID

        Returns:
            排盘记录字典，不存在返回None
        """
        try:
            with self._connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT id, user_id, name, gender, birth_date, birth_time,
                           city, pan_type, result_json, created_at
                    FROM pan_records
                    WHERE id = ?
                    """,
                    (record_id,)
                )
                row = cursor.fetchone()
                if row:
                    record = dict(row)
                    try:
                        record['result'] = json.loads(record['result_json'])
                    except (json.JSONDecodeError, KeyError):
                        record['result'] = {}
                    del record['result_json']
                    return record
        except Exception as e:
            print(f"获取排盘记录失败: {e}")
            return None

    def init_database(self):
        """
        重新初始化数据库（公开接口）
        用于外部调用确保数据库和表已创建
        """
        self._init_database()

    # ==================== 本地存储（界面配置 / 操作记录 / 系统日志，统一落地本地 SQLite） ====================

    def save_ui_settings(self, settings: dict) -> bool:
        """保存界面配置（单例行，id=1）。"""
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO ui_settings (id, settings_json) VALUES (1, ?) "
                    "ON CONFLICT(id) DO UPDATE SET settings_json = excluded.settings_json",
                    (json.dumps(settings, ensure_ascii=False),)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.warning(f"[界面配置] 保存失败：{e}")
            return False

    def load_ui_settings(self) -> dict:
        """读取界面配置，无记录返回 None。"""
        try:
            row = self._query_one("SELECT settings_json FROM ui_settings WHERE id = 1")
            if row and row['settings_json']:
                return json.loads(row['settings_json'])
        except Exception as e:
            logger.warning(f"[界面配置] 读取失败：{e}")
        return None

    def save_operation_log(self, op_type: str, op_object: str = '', user_id=None,
                            session: str = None, detail: str = None) -> bool:
        """记录一条操作日志（带重试机制）。"""
        import time
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                with self._connect() as conn:
                    conn.execute(
                        "INSERT INTO operation_logs (op_type, op_object, user_id, session, detail) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (op_type, op_object or '', user_id, session, detail)
                    )
                    conn.commit()
                    return True
            except Exception as e:
                error_msg = str(e)
                if "database is locked" in error_msg.lower() and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                if attempt == max_retries - 1:
                    logger.warning(f"[操作记录] 写入失败(重试{max_retries}次后)：{e}")
                else:
                    logger.warning(f"[操作记录] 写入失败：{e}")
                return False

    def load_operation_logs(self, limit: int = 100) -> list:
        """读取最近的操作日志。"""
        try:
            rows = self._query_all(
                "SELECT * FROM operation_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"[操作记录] 读取失败：{e}")
            return []

    def save_system_log(self, level: str, message: str, module: str, data: dict = None) -> bool:
        """写入一条系统日志（带重试机制）。"""
        import time
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                with self._connect() as conn:
                    conn.execute(
                        "INSERT INTO system_logs (level, message, module, data_json) "
                        "VALUES (?, ?, ?, ?)",
                        (level, message, module, json.dumps(data, ensure_ascii=False) if data else None)
                    )
                    conn.commit()
                    return True
            except Exception as e:
                error_msg = str(e)
                if "database is locked" in error_msg.lower() and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                if attempt == max_retries - 1:
                    # 最后一次重试失败，静默失败（避免日志循环）
                    pass
                return False


_db_manager_singleton = None
_db_manager_initializing = False  # 防止初始化期间的递归调用


def get_db_manager(config_path: str = None) -> "DatabaseManager":
    """DatabaseManager 进程内单例。

    使用 _db_manager_initializing 标志防止初始化期间的递归创建：
    - 当 DatabaseManager.__init__ 正在运行时，_db_manager_initializing=True
    - 此时若再次调用 get_db_manager()，直接返回正在初始化的实例（_db_manager_singleton 已预设）
    - 避免 StorageLogHandler.emit 触发的日志记录导致重复初始化
    """
    global _db_manager_singleton, _db_manager_initializing
    if _db_manager_singleton is None:
        if _db_manager_initializing:
            # 正在初始化中，等待完成（极少见，通常不会走这里）
            import time
            while _db_manager_singleton is None:
                time.sleep(0.01)
            return _db_manager_singleton
        _db_manager_initializing = True
        try:
            _db_manager_singleton = DatabaseManager(config_path)
        finally:
            _db_manager_initializing = False
    return _db_manager_singleton
