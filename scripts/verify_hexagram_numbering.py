# -*- coding: utf-8 -*-
"""64 卦编号数据层修正 + 玄空死代码删除 的定向验证脚本。

覆盖四组断言（全部可证伪）：
  1. 64 条 hexagram_64 记录的「卦名 ↔ 上下卦先天数」与脚本内独立基准逐条一致；
  2. 迁移幂等：连续执行两次，hexagram_64 状态完全一致，第二次返回 0 行修正；
  3. 迁移只改 hexagram_64：其余表在迁移前后的行数与内容摘要不变；
  4. 消费者视角：HexagramAnalyzer / KnowledgeBase 按先天数查表返回正确卦名；
  5. 玄空：删除 MOUNTAIN_TO_STAR 前后 calculate() 输出逐项一致。

基准在脚本内单独声明，不使用被测实现（数据库 / DatabaseManager / hexagram_analyzer）
推导期望值，避免「用被测实现算期望值」的自证循环。

用法：
    .\\venv\\Scripts\\python.exe scripts\\verify_hexagram_numbering.py
退出码 0 表示全部通过。
"""
import hashlib
import json
import os
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ==================== 独立基准（先天八卦数） ====================
# 乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
# 逐条按卦名（上卦+下卦）手工声明，与数据库/业务代码完全独立。
BASELINE = [
    (1,  '乾为天',   1, 1), (2,  '天风姤',   1, 5), (3,  '天山遁',   1, 7),
    (4,  '天地否',   1, 8), (5,  '风地观',   5, 8), (6,  '山地剥',   7, 8),
    (7,  '火地晋',   3, 8), (8,  '火天大有', 3, 1), (9,  '坎为水',   6, 6),
    (10, '水泽节',   6, 2), (11, '水雷屯',   6, 4), (12, '水火既济', 6, 3),
    (13, '泽火革',   2, 3), (14, '雷火丰',   4, 3), (15, '地火明夷', 8, 3),
    (16, '地水师',   8, 6), (17, '艮为山',   7, 7), (18, '山火贲',   7, 3),
    (19, '山天大畜', 7, 1), (20, '山泽损',   7, 2), (21, '火泽睽',   3, 2),
    (22, '天泽履',   1, 2), (23, '风泽中孚', 5, 2), (24, '风山渐',   5, 7),
    (25, '震为雷',   4, 4), (26, '雷地豫',   4, 8), (27, '雷水解',   4, 6),
    (28, '雷风恒',   4, 5), (29, '地风升',   8, 5), (30, '水风井',   6, 5),
    (31, '泽风大过', 2, 5), (32, '泽雷随',   2, 4), (33, '巽为风',   5, 5),
    (34, '风天小畜', 5, 1), (35, '风火家人', 5, 3), (36, '风雷益',   5, 4),
    (37, '天雷无妄', 1, 4), (38, '火雷噬嗑', 3, 4), (39, '山雷颐',   7, 4),
    (40, '山风蛊',   7, 5), (41, '离为火',   3, 3), (42, '火山旅',   3, 7),
    (43, '火风鼎',   3, 5), (44, '火水未济', 3, 6), (45, '山水蒙',   7, 6),
    (46, '风水涣',   5, 6), (47, '天水讼',   1, 6), (48, '天火同人', 1, 3),
    (49, '坤为地',   8, 8), (50, '地雷复',   8, 4), (51, '地泽临',   8, 2),
    (52, '地天泰',   8, 1), (53, '雷天大壮', 4, 1), (54, '泽天夬',   2, 1),
    (55, '水天需',   6, 1), (56, '水地比',   6, 8), (57, '兑为泽',   2, 2),
    (58, '泽水困',   2, 6), (59, '泽地萃',   2, 8), (60, '泽山咸',   2, 7),
    (61, '水山蹇',   6, 7), (62, '地山谦',   8, 7), (63, '雷山小过', 4, 7),
    (64, '雷泽归妹', 4, 2),
]

PASS_COUNT = 0
FAILS = []


def check(cond, msg):
    """记录一条断言结果。"""
    global PASS_COUNT
    if cond:
        PASS_COUNT += 1
    else:
        FAILS.append(msg)
        print('  FAIL:', msg)


def open_db(path):
    """以只读/读写方式打开指定 SQLite 库，row_factory 返回 dict 兼容行。"""
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    return con


def dump_hexagram_64(con):
    """导出 hexagram_64 全表内容（按 hexagram_id 排序）作为状态快照。"""
    cur = con.execute(
        "SELECT hexagram_id, name, upper_num, lower_num, gua_ci, judgment, description "
        "FROM hexagram_64 ORDER BY hexagram_id")
    return [tuple(r) for r in cur.fetchall()]


def table_digest(con):
    """对库内每张表计算 (行数, 内容摘要)，用于证明「只改 hexagram_64」。"""
    names = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name").fetchall()]
    out = {}
    for name in names:
        cols = [c[1] for c in con.execute('PRAGMA table_info("%s")' % name).fetchall()]
        rows = con.execute('SELECT * FROM "%s" ORDER BY rowid' % name).fetchall()
        payload = json.dumps([[list(map(str, r)) for r in rows]], ensure_ascii=False,
                             sort_keys=True, separators=(',', ':'))
        out[name] = (len(rows), hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16])
    return out


def assert_baseline(rows, label, strict=True):
    """逐条比对 64 条记录与独立基准。

    strict=False 用于「迁移前」状态：此时偏差本身就是待修复的缺陷，
    只统计不一致条数，不计入失败断言。
    """
    print('[%s] 逐条比对卦名 ↔ 上下卦（基准 %d 条）' % (label, len(BASELINE)))
    by_id = {r[0]: r for r in rows}
    ok = 0
    for hid, name, up, low in BASELINE:
        r = by_id.get(hid)
        if r is None:
            if strict:
                check(False, '%s 缺少 hexagram_id=%d %s' % (label, hid, name))
            continue
        row_name, row_up, row_low = r[1], r[2], r[3]
        passed = (row_name == name and row_up == up and row_low == low)
        if passed:
            ok += 1
        elif strict:
            check(False, '%s id=%d 期望 %s(%d,%d) 实际 %s(%d,%d)'
                  % (label, hid, name, up, low, row_name, row_up, row_low))
    if strict:
        check(len(by_id) == 64, '%s 行数为 %d，期望 64' % (label, len(by_id)))
        pairs = {(r[2], r[3]) for r in rows}
        check(len(pairs) == 64, '%s 上下卦组合去重后 %d 个，期望 64（应为双射）' % (label, len(pairs)))
    print('  %d/64 条一致' % ok)
    return ok


def migration_shim():
    """构造仅带静态推导方法的轻量实例，避免触发 DatabaseManager 单例初始化。"""
    from core.database_manager import DatabaseManager
    shim = type('MigrationShim', (), {
        '_expected_hexagram_nums': staticmethod(DatabaseManager._expected_hexagram_nums),
    })()
    return DatabaseManager, shim


def main():
    db_path = os.path.join(ROOT, 'data', 'fengshui.db')
    if not os.path.exists(db_path):
        print('FAIL: 数据库不存在', db_path)
        return 1

    # ---------- 1. 独立基准比对（迁移前状态） ----------
    con = open_db(db_path)
    before_rows = dump_hexagram_64(con)
    before_tables = table_digest(con)
    con.close()
    fixed_before = assert_baseline(before_rows, '迁移前', strict=False)
    print('  迁移前偏差 %d 条（待迁移修正）' % (64 - fixed_before))

    # ---------- 2. 第一次迁移：走产品启动路径 ----------
    from core.database_manager import DatabaseManager
    DatabaseManager()
    con = open_db(db_path)
    after1_rows = dump_hexagram_64(con)
    after1_tables = table_digest(con)
    con.close()
    print('[幂等] 第一次执行（产品初始化路径）后：%d/64 条与基准一致'
          % assert_baseline(after1_rows, '迁移后'))

    # ---------- 3. 第二次迁移：直接调用迁移方法，必须 0 行修正 ----------
    DatabaseManager, shim = migration_shim()
    con = open_db(db_path)
    ret2 = DatabaseManager._migrate_hexagram_64_numbering(shim, con)
    after2_rows = dump_hexagram_64(con)
    after2_tables = table_digest(con)
    con.close()
    print('[幂等] 第二次执行返回修正行数 = %d（应为 0）' % ret2)
    check(ret2 == 0, '第二次迁移仍修正了 %d 行，非幂等' % ret2)
    check(after1_rows == after2_rows, '两次执行后 hexagram_64 状态不一致')
    # db_version 为既有运行期元数据表，每次启动都会被后台校验线程重写（与本次迁移无关）
    runtime_tables = {'db_version'}
    diff_tables = [t for t in after1_tables
                   if t not in runtime_tables and after2_tables.get(t) != after1_tables[t]]
    check(not diff_tables, '两次执行后除 db_version 外仍有表变化：%s' % diff_tables)
    print('  两次执行后除 db_version 外变化表：%s' % (diff_tables or '无'))
    if fixed_before == 64:
        check(before_rows == after1_rows, '首次执行前已修正，但首次执行后状态发生变化')
    print('  hexagram_64 状态一致：%s（sha256=%s）' % (
        after1_rows == after2_rows,
        hashlib.sha256(json.dumps([[str(x) for x in r] for r in after1_rows],
                                  ensure_ascii=False).encode()).hexdigest()[:16]))

    # ---------- 4. 只改 hexagram_64 的证明 ----------
    changed = [t for t in before_tables
               if after1_tables.get(t) != before_tables[t]]
    print('[范围] 迁移前后内容发生变化的表：%s' % (changed or '无'))
    unexpected = [t for t in changed if t not in ('hexagram_64', 'db_version')]
    check(not unexpected, '迁移改动了不允许的表：%s' % unexpected)
    check(all(before_tables.get(t) == after1_tables.get(t)
              for t in before_tables if t != 'hexagram_64'),
          '除 hexagram_64 外存在表内容变化')

    # ---------- 5. 全新库（修正后的 schema）自检 ----------
    schema = os.path.join(ROOT, 'database', 'schema_sqlite.sql')
    tmp_dir = tempfile.mkdtemp(prefix='kp_hex_verify_')
    tmp_db = os.path.join(tmp_dir, 'fresh.db')
    con = sqlite3.connect(tmp_db)
    con.executescript(open(schema, encoding='utf-8').read())
    con.commit()
    con.close()
    con = open_db(tmp_db)
    fresh_rows = dump_hexagram_64(con)
    ok_fresh = assert_baseline(fresh_rows, '新建库(schema)')
    ret_fresh = DatabaseManager._migrate_hexagram_64_numbering(shim, con)
    check(ret_fresh == 0, '新建库仍需迁移 %d 行，说明建库脚本未修正' % ret_fresh)
    con.close()
    print('[新建库] 与基准一致 %d/64，迁移返回 %d' % (ok_fresh, ret_fresh))

    # ---------- 5b. 旧编号库模拟：迁移必须修正 28 行且幂等 ----------
    # 旧编号 = 先天数上把 2/6 互换，故对全表做 2↔6 互换即可复现历史库形态
    legacy_db = os.path.join(tmp_dir, 'legacy.db')
    con = sqlite3.connect(legacy_db)
    con.executescript(open(schema, encoding='utf-8').read())
    con.execute("UPDATE hexagram_64 SET upper_num = CASE upper_num "
                "WHEN 2 THEN 6 WHEN 6 THEN 2 ELSE upper_num END, "
                "lower_num = CASE lower_num "
                "WHEN 2 THEN 6 WHEN 6 THEN 2 ELSE lower_num END")
    con.commit()
    con.close()
    con = open_db(legacy_db)
    legacy_rows = dump_hexagram_64(con)
    ok_legacy = assert_baseline(legacy_rows, '旧编号库(模拟)', strict=False)
    check(ok_legacy == 36, '旧编号库应只有 36/64 条一致，实际 %d' % ok_legacy)
    ret_legacy = DatabaseManager._migrate_hexagram_64_numbering(shim, con)
    check(ret_legacy == 28, '旧编号库应修正 28 行，实际 %d' % ret_legacy)
    ok_fixed = assert_baseline(dump_hexagram_64(con), '旧编号库迁移后')
    ret_again = DatabaseManager._migrate_hexagram_64_numbering(shim, con)
    check(ret_again == 0, '旧编号库第二次迁移仍修正 %d 行' % ret_again)
    con.close()
    print('[旧编号模拟] 迁移前 %d/64 -> 修正 %d 行 -> 迁移后 %d/64 -> 再跑 %d 行'
          % (ok_legacy, ret_legacy, ok_fixed, ret_again))

    # ---------- 5c. 不可判定数据必须整体跳过 ----------
    bad_db = os.path.join(tmp_dir, 'bad.db')
    con = sqlite3.connect(bad_db)
    con.executescript(open(schema, encoding='utf-8').read())
    con.execute("UPDATE hexagram_64 SET upper_num = 9 WHERE hexagram_id = 1")
    con.commit()
    con.close()
    con = open_db(bad_db)
    ret_bad = DatabaseManager._migrate_hexagram_64_numbering(shim, con)
    check(ret_bad == 0, '异常数据下迁移应整体跳过，实际修正 %d 行' % ret_bad)
    con.close()
    print('[异常数据] 迁移返回 %d 行（应为 0，不做猜测性修正）' % ret_bad)
    for f in (tmp_db, legacy_db, bad_db, tmp_db + '-wal', legacy_db + '-wal',
              bad_db + '-wal', tmp_db + '-shm', legacy_db + '-shm', bad_db + '-shm'):
        if os.path.exists(f):
            os.remove(f)
    os.rmdir(tmp_dir)

    # ---------- 6. 消费者视角 ----------
    from core.divination.hexagram_analyzer import HexagramAnalyzer
    from core.knowledge.knowledge_base import KnowledgeBase
    analyzer = HexagramAnalyzer()
    cases = {(2, 1): '泽天夬', (6, 6): '坎为水', (5, 2): '风泽中孚',
             (5, 6): '风水涣', (3, 6): '火水未济', (1, 2): '天泽履', (8, 2): '地泽临'}
    for (up, low), name in cases.items():
        got = analyzer.get_hexagram_info(up, low).get('name')
        check(got == name, 'HexagramAnalyzer(%d,%d) 期望 %s 实际 %s' % (up, low, name, got))
        kb = KnowledgeBase().get_hexagram_info(up, low).get('name')
        check(kb == name, 'KnowledgeBase(%d,%d) 期望 %s 实际 %s' % (up, low, name, kb))
    print('[消费者] %d 组先天数查表全部命中正确卦名' % len(cases))

    # ---------- 7. 玄空：删除 MOUNTAIN_TO_STAR 前后 calculate 等价 ----------
    import core.fengshui.xuan_kong as xk
    xk_path = os.path.join(ROOT, 'core', 'fengshui', 'xuan_kong.py')
    src = open(xk_path, encoding='utf-8').read()
    # 复原被删除的常量（它未被任何代码引用，复原后行为应与现状完全相同）
    src_before = src + (
        "\n\nMOUNTAIN_TO_STAR = {'子': 1, '午': 1, '癸': 2, '丁': 2, '艮': 3, '坤': 3,"
        " '甲': 4, '庚': 4, '乙': 5, '辛': 5, '丙': 6, '壬': 6, '巽': 7, '乾': 7,"
        " '震': 8, '兑': 8, '离': 9, '坎': 9}\n")
    ns = {'__name__': 'xk_before'}
    exec(compile(src_before, xk_path, 'exec'), ns)
    calc_before = ns['XuanKongCalculator']()
    calc_after = xk.XuanKongCalculator()
    samples = [
        ('子山午向', 2024, 2026),
        ('乾山巽向', 2004, 2026),
        ('子山午向', 1864, 1865),   # 一运，替卦分支会被调用
    ]
    for sui_xiang, build_year, cur_year in samples:
        a = calc_before.calculate(sui_xiang, build_year, cur_year)
        b = calc_after.calculate(sui_xiang, build_year, cur_year)
        same = json.dumps(a, sort_keys=True, ensure_ascii=False, default=str) == \
            json.dumps(b, sort_keys=True, ensure_ascii=False, default=str)
        check(same, '玄空输出变化：%s %s' % (sui_xiang, build_year))
        print('  %s / 建运年 %s / 流年 %s -> 输出一致=%s，盘面=%s'
              % (sui_xiang, build_year, cur_year, same, b.get('pattern_desc', b.get('pattern'))))
    check(not hasattr(xk, 'MOUNTAIN_TO_STAR'), 'MOUNTAIN_TO_STAR 仍存在于模块中')

    # ---------- 汇总 ----------
    print('\n===== 结果汇总 =====')
    print('通过断言：%d 条，失败：%d 条' % (PASS_COUNT, len(FAILS)))
    if FAILS:
        for f in FAILS:
            print(' -', f)
        return 1
    print('全部通过：64 卦编号 = 基准 64/64，迁移幂等，玄空输出等价。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
