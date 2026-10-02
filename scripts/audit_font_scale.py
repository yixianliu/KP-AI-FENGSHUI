# -*- coding: utf-8 -*-
"""
scripts/audit_font_scale.py — Font Scale 字号门禁（UI 升级 M1-2）

扫描 ui/ 下所有 .py（含 f-string 内的 QSS 字符串），检测 `font-size: Npx`
是否落在 7 级 Font Scale 白名单内，杜绝 14 / 16 / 13.5px 之类越界字号
（方案 Q05：hero_conclusion_block 曾出现 16 / 14 / 13.5px 三档越界）。

白名单（= Fonts 的 7 级 Font Scale，数值以 ui/styles.py 为唯一权威源）：
    28 / 20 / 17 / 15 / 13 / 12 / 11

已知豁免（在 EXEMPT 中登记，新增豁免必须写明理由）：
    · ui/export/pdf_exporter.py —— 打印专用 PDF_* 调色板，字号按 A4 纸张排版，
      与屏幕 Font Scale 体系无关（PDF_QINGHUA #4A7A90 ≠ Colors.QINGHUA）。
    · 空状态/装饰性大图标字号 40px / 36px —— 非文本层级，属图形占位。

用法：
    python scripts/audit_font_scale.py                # 扫描 ui/ 全目录
    python scripts/audit_font_scale.py ui/components/ # 扫描指定目录
    python scripts/audit_font_scale.py <file.py> [--allow-empty]

退出码：0 = 无越界命中；1 = 存在越界字号（打印 文件:行 明细）。

空转守卫（2026-09-29 第 7 轮补）：
    本脚本原本「total=0 即 return 0」，而 total 数的是**越界数**——若扫描目标
    为空目录、正则失效或文件读取失败，同样得到 0 并判绿，属典型空转假绿。
    现改为：先把「扫描文件数 / font-size 声明数」作为**校验量**打印出来，并在
    ① 文件数 0 ② 有读取失败 ③ 声明数 0（未加 --allow-empty）时一律 return 1。
"""
import re
import sys
from pathlib import Path

# 项目根目录（脚本在 scripts/ 下，向上一级）
ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / 'ui'

# 匹配 QSS 里的 font-size 声明（含 f-string 拼接后的形态）
# 说明：源码里既有 `font-size: 16px;` 常量形态，也有 `font-size: {Fonts.SZ_BODY};`
# 变量形态；后者由令牌产出恒合法，本脚本只拦截**数值字面量**。
FONT_SIZE_RE = re.compile(r'font-size:\s*([0-9]+(?:\.[0-9]+)?)px', re.I)

# 7 级 Font Scale 白名单（从 ui/styles.py 动态读取，避免两处硬编码漂移）
def _whitelist() -> set:
    """从 Fonts 读取 7 级字号构成白名单；导入失败时回退到文档写死的常量。"""
    try:
        sys.path.insert(0, str(ROOT))
        from ui.styles import Fonts
        return {float(getattr(Fonts, n)) for n in
                ('FS_HERO', 'FS_H1', 'FS_H2', 'FS_H3', 'FS_BODY',
                 'FS_CAPTION', 'FS_MICRO') if hasattr(Fonts, n)}
    except Exception:
        return {28.0, 20.0, 17.0, 15.0, 13.0, 12.0, 11.0}


# 文件级豁免（键 = 相对路径，值 = 允许出现的字号集合；None = 整文件豁免）
EXEMPT_FILES = {
    # 与 audit_style_tokens.py 同口径：styles.py 是设计令牌「单一真相源」，
    # 其中的字号是令牌定义本身，不是散落硬编码。
    'ui/styles.py': None,
    # 打印专用 PDF_* 调色板：字号按 A4 纸张排版，与屏幕 Font Scale 体系无关
    # （PDF_QINGHUA #4A7A90 ≠ Colors.QINGHUA，同属有意设计）。
    'ui/export/pdf_exporter.py': None,
}

# 全项目豁免字号：**装饰性图形 / 图标 glyph**（非文本层级，不承载阅读语义）。
# 实测这些尺寸只用于 ☯ / 🔮 / ⛰ 一类的图形占位、空状态大图标与 emoji 徽标，
# 强行套 7 级 Font Scale 会破坏既有视觉权重，故登记豁免。
# ⚠️ 新增豁免必须在此写明理由，禁止静默加数字。
EXEMPT_SIZES = {22.0, 24.0, 26.0, 30.0, 36.0, 40.0, 56.0, 64.0}


def _is_exempt(rel: str, size: float) -> bool:
    if size in EXEMPT_SIZES:
        return True
    if rel in EXEMPT_FILES:
        allowed = EXEMPT_FILES[rel]
        if allowed is None or size in allowed:
            return True
    return False


def scan_file(path: Path, rel: str, whitelist: set):
    """扫描单个文件。

    Returns:
        tuple: (越界命中 [(line_no, size_str, snippet)], 命中的 font-size 声明总数,
                文件是否成功读取)。
    """
    hits = []
    try:
        text = path.read_text(encoding='utf-8-sig', errors='replace')
    except OSError:
        # 读不到文件必须**显式可见**：静默跳过等于「没查也算过」（假绿）。
        return hits, 0, False
    decls = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in FONT_SIZE_RE.finditer(line):
            raw = m.group(1)
            try:
                size = float(raw)
            except ValueError:
                continue
            decls += 1
            if _is_exempt(rel, size):
                continue
            if size in whitelist:
                continue
            hits.append((line_no, raw, line.strip()[:90]))
    return hits, decls, True


def main(argv) -> int:
    # --allow-empty：单文件 ad-hoc 扫描时放行「0 条 font-size 声明」。
    # 默认（跑全 ui/）不放行 —— 一条声明都没匹配到说明正则失效或路径错误，
    # 此时「0 越界」是**空转**，不是达标。
    allow_empty = '--allow-empty' in argv[1:]
    argv = [a for a in argv if a != '--allow-empty']

    # 解析目标：默认 ui/ 目录，可传目录或文件
    if len(argv) > 1:
        targets = []
        for arg in argv[1:]:
            p = Path(arg)
            if not p.is_absolute():
                p = ROOT / p
            if p.is_dir():
                targets.extend(sorted(p.rglob('*.py')))
            elif p.exists():
                targets.append(p)
    else:
        targets = sorted(UI_DIR.rglob('*.py'))

    whitelist = _whitelist()
    total = 0        # 越界命中数
    decls = 0        # 匹配到的 font-size 声明总数（校验量）
    files = 0        # 成功读取并扫描的文件数
    unreadable = []  # 读取失败的文件（必须可见，不可静默跳过）
    for path in targets:
        try:
            rel = str(path.relative_to(ROOT)).replace('\\', '/')
        except ValueError:
            rel = str(path)
        hits, n_decl, readable = scan_file(path, rel, whitelist)
        if not readable:
            unreadable.append(rel)
            continue
        files += 1
        decls += n_decl
        if hits:
            print(f"\n== {rel} ==")
            for line_no, raw, snippet in hits:
                print(f"  L{line_no:>4}  font-size: {raw}px  (非 Font Scale)")
                print(f"          {snippet}")
            total += len(hits)

    print("\n" + "=" * 64)
    print(f"汇总: {decls - total}/{decls} 项通过"
          f"（扫描 {files} 个文件，font-size 声明 {decls} 处，越界 {total} 处）")

    # ── 空转守卫：0 项也「绿」的门禁比没有门禁更危险 ──────────────
    if files == 0:
        print("audit_font_scale: 未扫描到任何 .py 文件 —— 门禁空转 ❌")
        return 1
    if unreadable:
        print(f"audit_font_scale: {len(unreadable)} 个文件读取失败 ❌ -> {unreadable[:5]}")
        return 1
    if decls == 0 and not allow_empty:
        print("audit_font_scale: 未匹配到任何 font-size 声明 —— 门禁空转 ❌"
              "（正则失效或路径错误；确需扫描无字号文件请加 --allow-empty）")
        return 1

    if total == 0:
        print(f"audit_font_scale: 无越界字号（白名单={sorted(whitelist, reverse=True)}）✅")
        return 0
    print(f"audit_font_scale: 共 {total} 处越界字号 ⚠️")
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
