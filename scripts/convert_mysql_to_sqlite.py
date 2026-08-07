#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性转换脚本：将 Navicat 导出的 MySQL dump (database/base.sql)
转换为 SQLite 兼容的 schema + 数据脚本 (database/schema_sqlite.sql)。

用法:
    python scripts/convert_mysql_to_sqlite.py

设计要点:
- 字面量感知的语句切分（正确处理反引号标识符 / 单引号字符串 / 注释）。
- CREATE TABLE: 类型映射、AUTO_INCREMENT → INTEGER PRIMARY KEY AUTOINCREMENT，
  去除 ENGINE/CHARSET/COLLATE/COMMENT/USING BTREE/INDEX/FK 等 MySQL 专有语法，
  INDEX/KEY 转成独立的 CREATE INDEX 语句。
- INSERT: 把每个值解析为 Python 原生对象（正确解 MySQL 反斜杠转义），
  再用 SQLite 规则（单引号翻倍、无反斜杠转义）重新输出，避免 JSON 中 \\" 损坏。
"""
import os
import re
import sys
import sqlite3
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "database", "base.sql")
DST = os.path.join(ROOT, "database", "schema_sqlite.sql")


# --------------------------------------------------------------------------- #
# 1. 语句切分（字面量感知）
# --------------------------------------------------------------------------- #
def split_statements(sql: str):
    """按字面量感知的规则把整段 SQL 切分为独立语句列表。

    正确处理 MySQL dump 中的行注释(--)、块注释(/* */)、反引号标识符、
    单引号字符串（含反斜杠转义）与分号结束符，避免把字符串内的 ';' 误判为
    语句边界。

    Args:
        sql: 原始 MySQL 方言 SQL 文本。

    Returns:
        list[str]: 去掉首尾空白后的单条语句字符串列表。
    """
    stmts = []
    buf = []
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        # 行注释 -- ...
        if c == '-' and i + 1 < n and sql[i + 1] == '-':
            j = sql.find('\n', i)
            i = n if j == -1 else j + 1
            continue
        # 块注释 /* ... */
        if c == '/' and i + 1 < n and sql[i + 1] == '*':
            j = sql.find('*/', i + 2)
            i = n if j == -1 else j + 2
            continue
        # 反引号标识符
        if c == '`':
            buf.append(c)
            i += 1
            while i < n and sql[i] != '`':
                buf.append(sql[i])
                i += 1
            if i < n:
                buf.append('`')
                i += 1
            continue
        # 单引号字符串（MySQL 反斜杠转义）
        if c == "'":
            buf.append(c)
            i += 1
            while i < n:
                ch = sql[i]
                if ch == '\\' and i + 1 < n:
                    buf.append(ch)
                    buf.append(sql[i + 1])
                    i += 2
                    continue
                buf.append(ch)
                i += 1
                if ch == "'":
                    break
            continue
        # 语句结束
        if c == ';':
            s = ''.join(buf).strip()
            if s:
                stmts.append(s)
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    tail = ''.join(buf).strip()
    if tail:
        stmts.append(tail)
    return stmts


# --------------------------------------------------------------------------- #
# 2. 顶层逗号分割（尊重括号 / 反引号 / 字符串）
# --------------------------------------------------------------------------- #
def split_top_level(s: str, sep=','):
    """在顶层按分隔符切分，但尊重括号嵌套、反引号标识符与单引号字符串。

    用于把 CREATE TABLE 的列定义体或 INSERT 值元组按逗号拆开，而不会切断
    函数调用、字符串内部的逗号。

    Args:
        s: 待切分的文本（如括号内的列定义串）。
        sep: 分隔符，默认为逗号。

    Returns:
        list[str]: 顶层切分后的片段（已 strip）。
    """
    parts = []
    buf = []
    depth = 0
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == '`':
            buf.append(c)
            i += 1
            while i < n and s[i] != '`':
                buf.append(s[i])
                i += 1
            if i < n:
                buf.append('`')
                i += 1
            continue
        if c == "'":
            buf.append(c)
            i += 1
            while i < n:
                ch = s[i]
                if ch == '\\' and i + 1 < n:
                    buf.append(ch)
                    buf.append(s[i + 1])
                    i += 2
                    continue
                buf.append(ch)
                i += 1
                if ch == "'":
                    break
            continue
        if c == '(':
            depth += 1
            buf.append(c)
            i += 1
            continue
        if c == ')':
            depth -= 1
            buf.append(c)
            i += 1
            continue
        if c == sep and depth == 0:
            parts.append(''.join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    if buf:
        parts.append(''.join(buf).strip())
    return parts


# --------------------------------------------------------------------------- #
# 3. 类型映射
# --------------------------------------------------------------------------- #
def map_type(mysql_type: str) -> str:
    """把 MySQL 列类型映射为 SQLite 亲和类型。

    按类型基名归类：整数类→INTEGER，浮点/定点类→REAL，日期时间类、字符类、
    JSON/枚举/集合→TEXT，二进制类→BLOB，未知兜底→TEXT。

    Args:
        mysql_type: 含可选长度/精度的 MySQL 类型声明，如 'varchar(64)'。

    Returns:
        str: SQLite 兼容的类型名（INTEGER/REAL/TEXT/BLOB）。
    """
    t = mysql_type.lower()
    base = re.match(r'^(\w+)', t)
    base = base.group(1) if base else t
    if base in ('bigint', 'int', 'integer', 'tinyint', 'smallint',
                'mediumint', 'bit', 'bool', 'boolean'):
        return 'INTEGER'
    if base in ('decimal', 'numeric', 'double', 'float', 'real'):
        return 'REAL'
    if base in ('date', 'datetime', 'timestamp', 'time', 'year'):
        return 'TEXT'
    if base in ('char', 'varchar', 'text', 'tinytext', 'mediumtext',
                'longtext', 'json', 'enum', 'set'):
        return 'TEXT'
    if base in ('blob', 'tinyblob', 'mediumblob', 'longblob', 'binary',
                'varbinary'):
        return 'BLOB'
    return 'TEXT'


# --------------------------------------------------------------------------- #
# 4. CREATE TABLE 转换
# --------------------------------------------------------------------------- #
def convert_create_table(stmt: str):
    """把单条 CREATE TABLE 语句转换为 SQLite 建表语句与独立索引语句。

    处理要点：精确匹配最外层括号确定表体；解析列定义并做类型映射，
    AUTO_INCREMENT→INTEGER PRIMARY KEY AUTOINCREMENT；剥离 MySQL 专有的
    CHARACTER SET/COLLATE/COMMENT/ON UPDATE CURRENT_TIMESTAMP；将 PRIMARY KEY、
    UNIQUE/普通 KEY、INDEX 拆成独立的 CREATE INDEX 语句；丢弃外键约束。

    Args:
        stmt: 一条 MySQL CREATE TABLE 语句。

    Returns:
        tuple: (建表 SQL, [索引 SQL 列表])；无法识别时返回 (None, [])。
    """
    m = re.match(r'CREATE\s+TABLE\s+`([^`]+)`\s*\(', stmt, re.IGNORECASE)
    if not m:
        return None, []
    table = m.group(1)
    # 找到与首个 ( 匹配的 )
    start = stmt.index('(', m.start())
    depth = 0
    end = -1
    i = start
    n = len(stmt)
    while i < n:
        c = stmt[i]
        if c == '`':
            i += 1
            while i < n and stmt[i] != '`':
                i += 1
        elif c == "'":
            i += 1
            while i < n:
                if stmt[i] == '\\':
                    i += 2
                    continue
                if stmt[i] == "'":
                    break
                i += 1
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                end = i
                break
        i += 1
    body = stmt[start + 1:end]
    defs = split_top_level(body)

    columns = []          # (sqlite_col_sql, colname)
    pk_cols = []
    auto_col = None
    indexes = []          # (unique, index_name, [cols])

    for d in defs:
        dl = d.lstrip()
        upper = dl.upper()
        if upper.startswith('PRIMARY KEY'):
            cols = re.findall(r'`([^`]+)`', dl)
            pk_cols = cols
            continue
        if upper.startswith('UNIQUE KEY') or upper.startswith('UNIQUE INDEX'):
            cols = re.findall(r'`([^`]+)`', dl)
            if len(cols) >= 2:
                indexes.append((True, cols[0], cols[1:]))
            continue
        if upper.startswith('KEY ') or upper.startswith('INDEX '):
            cols = re.findall(r'`([^`]+)`', dl)
            if len(cols) >= 2:
                indexes.append((False, cols[0], cols[1:]))
            continue
        if upper.startswith('CONSTRAINT') or upper.startswith('FOREIGN KEY'):
            continue  # 丢弃外键约束
        # 普通列定义
        cm = re.match(r'`([^`]+)`\s+(.*)$', dl, re.DOTALL)
        if not cm:
            continue
        colname = cm.group(1)
        rest = cm.group(2)
        # 去除 CHARACTER SET / COLLATE
        rest = re.sub(r'CHARACTER\s+SET\s+\w+', '', rest, flags=re.IGNORECASE)
        rest = re.sub(r'COLLATE\s+\w+', '', rest, flags=re.IGNORECASE)
        # 去除 COMMENT '...'
        rest = re.sub(r"COMMENT\s+'(?:[^'\\]|\\.)*'", '', rest, flags=re.IGNORECASE)
        # 去除 ON UPDATE CURRENT_TIMESTAMP
        rest = re.sub(r'ON\s+UPDATE\s+CURRENT_TIMESTAMP(?:\(\))?', '', rest,
                      flags=re.IGNORECASE)
        # 类型
        tm = re.match(r'^\s*(\w+(?:\s*\([^)]*\))?)', rest)
        raw_type = tm.group(1) if tm else 'TEXT'
        sqlite_type = map_type(raw_type)
        after = rest[tm.end():] if tm else rest
        is_auto = bool(re.search(r'AUTO_INCREMENT', after, re.IGNORECASE))
        not_null = bool(re.search(r'\bNOT\s+NULL\b', after, re.IGNORECASE))
        # DEFAULT 值
        default = None
        dm = re.search(r"DEFAULT\s+('(?:[^'\\]|\\.)*'|CURRENT_TIMESTAMP(?:\(\))?|[-\w.]+)",
                       after, re.IGNORECASE)
        if dm:
            default = dm.group(1)
            if default.upper().startswith('CURRENT_TIMESTAMP'):
                default = 'CURRENT_TIMESTAMP'

        if is_auto:
            auto_col = colname
            columns.append(('"%s" INTEGER PRIMARY KEY AUTOINCREMENT' % colname,
                            colname))
            continue

        piece = '"%s" %s' % (colname, sqlite_type)
        if not_null:
            piece += ' NOT NULL'
        if default is not None:
            piece += ' DEFAULT %s' % default
        columns.append((piece, colname))

    col_sqls = [c[0] for c in columns]

    # 处理主键（非 auto 情形）
    if pk_cols and auto_col not in pk_cols:
        pk = ', '.join('"%s"' % c for c in pk_cols)
        col_sqls.append('PRIMARY KEY (%s)' % pk)
    # 若 pk 恰为单列 auto，已内联，无需额外处理

    create_sql = 'CREATE TABLE IF NOT EXISTS "%s" (\n    %s\n);' % (
        table, ',\n    '.join(col_sqls))

    index_sqls = []
    for unique, idx_name, cols in indexes:
        cols_sql = ', '.join('"%s"' % c for c in cols)
        uniq = 'UNIQUE ' if unique else ''
        index_sqls.append(
            'CREATE %sINDEX IF NOT EXISTS "%s_%s" ON "%s" (%s);'
            % (uniq, table, idx_name, table, cols_sql))

    return create_sql, index_sqls


# --------------------------------------------------------------------------- #
# 5. INSERT 转换
# --------------------------------------------------------------------------- #
_INSERT_RE = re.compile(
    r'INSERT\s+INTO\s+`([^`]+)`\s*(?:\(([^)]*)\)\s*)?VALUES\s*(.*)$',
    re.IGNORECASE | re.DOTALL)


def decode_mysql_string(lit: str) -> str:
    """lit 包含首尾单引号，返回解码后的 Python 字符串。"""
    s = lit[1:-1]
    out = []
    i, n = 0, len(s)
    esc = {'0': '\x00', 'b': '\b', 'n': '\n', 'r': '\r', 't': '\t',
           'Z': '\x1a', '\\': '\\', "'": "'", '"': '"', '%': '%', '_': '_'}
    while i < n:
        c = s[i]
        if c == '\\' and i + 1 < n:
            nxt = s[i + 1]
            out.append(esc.get(nxt, nxt))
            i += 2
            continue
        if c == "'" and i + 1 < n and s[i + 1] == "'":
            out.append("'")
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def parse_value(tok: str):
    """把 INSERT 值文本片段解析为对应的 Python 原生对象。

    NULL→None；单引号包裹→经 MySQL 转义解码后的字符串；纯数字→int/float；
    其余按字符串兜底，保证下游能正确重新输出为 SQLite 字面量。

    Args:
        tok: 切分出的单个值 token（可能含首尾空白与引号）。

    Returns:
        解析后的 Python 对象（None/int/float/str）。
    """
    tok = tok.strip()
    if tok.upper() == 'NULL':
        return None
    if tok.startswith("'"):
        return decode_mysql_string(tok)
    # 数字（int / float / 负数）
    if re.match(r'^-?\d+$', tok):
        return int(tok)
    if re.match(r'^-?\d*\.\d+$', tok):
        return float(tok)
    # 兜底当字符串
    return tok


def emit_sqlite_literal(v) -> str:
    """把 Python 值序列化为 SQLite 字面量字符串。

    规则：None→NULL；bool→0/1；int→原样；float→repr；字符串→单引号翻倍
    转义（不使用反斜杠转义，符合 SQLite 文本字面量规范）。

    Args:
        v: 任意 Python 标量（来自 parse_value 的输出）。

    Returns:
        str: 可直接拼入 SQL 的字面量文本。
    """
    if v is None:
        return 'NULL'
    if isinstance(v, bool):
        return '1' if v else '0'
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    s = str(v).replace("'", "''")
    return "'%s'" % s


def convert_insert(stmt: str):
    """把 MySQL INSERT 语句转换为一条或多条 SQLite INSERT 语句。

    解析顶层的值元组（尊重括号嵌套与字符串），逐元组把每个值经 parse_value
    解析后再用 SQLite 规则（emit_sqlite_literal）重新输出，从而正确保留
    JSON 等含转义的内容。

    Args:
        stmt: 一条 MySQL INSERT ... VALUES (...) 语句。

    Returns:
        list[str]: 转换后的 SQLite INSERT 语句列表（可能多条）。
    """
    m = _INSERT_RE.match(stmt)
    if not m:
        return []
    table = m.group(1)
    values_part = m.group(3).strip()
    # 提取顶层的 (...) 元组
    tuples = []
    depth = 0
    buf = []
    i, n = 0, len(values_part)
    started = False
    while i < n:
        c = values_part[i]
        if c == "'":
            buf.append(c)
            i += 1
            while i < n:
                ch = values_part[i]
                if ch == '\\' and i + 1 < n:
                    buf.append(ch)
                    buf.append(values_part[i + 1])
                    i += 2
                    continue
                buf.append(ch)
                i += 1
                if ch == "'":
                    break
            continue
        if c == '(':
            depth += 1
            if depth == 1:
                started = True
                buf = []
                i += 1
                continue
            buf.append(c)
            i += 1
            continue
        if c == ')':
            depth -= 1
            if depth == 0 and started:
                tuples.append(''.join(buf))
                buf = []
                started = False
                i += 1
                continue
            buf.append(c)
            i += 1
            continue
        if started:
            buf.append(c)
        i += 1

    out_stmts = []
    for tup in tuples:
        vals = split_top_level(tup)
        parsed = [parse_value(v) for v in vals]
        literals = ', '.join(emit_sqlite_literal(v) for v in parsed)
        out_stmts.append('INSERT INTO "%s" VALUES (%s);' % (table, literals))
    return out_stmts


# --------------------------------------------------------------------------- #
# 6. 主流程
# --------------------------------------------------------------------------- #
def main():
    """脚本主流程：读取 MySQL dump，生成 SQLite schema + 数据文件并自检。

    依次切分语句、转换 CREATE TABLE/INSERT，组装成带 PRAGMA 与事务的
    schema_sqlite.sql，最后用临时 sqlite 库导入验证表与行数。

    Returns:
        None
    """
    if not os.path.exists(SRC):
        print('ERROR: source not found: %s' % SRC)
        sys.exit(1)
    with open(SRC, 'r', encoding='utf-8') as f:
        sql = f.read()

    stmts = split_statements(sql)

    create_blocks = []
    index_blocks = []
    insert_blocks = []
    table_order = []

    for st in stmts:
        head = st.lstrip()[:20].upper()
        if head.startswith('CREATE TABLE'):
            create_sql, idx_sqls = convert_create_table(st)
            if create_sql:
                create_blocks.append(create_sql)
                index_blocks.extend(idx_sqls)
                mm = re.match(r'CREATE\s+TABLE\s+`([^`]+)`', st, re.IGNORECASE)
                if mm:
                    table_order.append(mm.group(1))
        elif head.startswith('INSERT'):
            insert_blocks.extend(convert_insert(st))
        # DROP TABLE / SET / 其他: 忽略

    out = []
    out.append('-- Auto-generated SQLite schema + data')
    out.append('-- Source: database/base.sql (MySQL dump)')
    out.append('-- Generator: scripts/convert_mysql_to_sqlite.py')
    out.append('PRAGMA foreign_keys = OFF;')
    out.append('BEGIN TRANSACTION;')
    out.append('')
    out.append('-- ==================== TABLES ====================')
    out.extend(create_blocks)
    out.append('')
    out.append('-- ==================== INDEXES ====================')
    out.extend(index_blocks)
    out.append('')
    out.append('-- ==================== DATA ====================')
    out.extend(insert_blocks)
    out.append('')
    out.append('COMMIT;')
    out.append('')

    text = '\n'.join(out)
    with open(DST, 'w', encoding='utf-8') as f:
        f.write(text)

    print('Wrote %s' % DST)
    print('Tables: %d, Indexes: %d, Inserts: %d'
          % (len(create_blocks), len(index_blocks), len(insert_blocks)))

    # 自检：用临时 sqlite 库导入验证
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    try:
        con = sqlite3.connect(tmp.name)
        con.executescript(text)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        print('\nVerification: %d tables created' % len(tables))
        total = 0
        for t in tables:
            cur.execute('SELECT COUNT(*) FROM "%s"' % t)
            cnt = cur.fetchone()[0]
            total += cnt
            print('  %-28s %6d rows' % (t, cnt))
        print('Total rows: %d' % total)
        con.close()
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


if __name__ == '__main__':
    main()
