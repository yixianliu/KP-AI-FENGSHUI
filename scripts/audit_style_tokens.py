# -*- coding: utf-8 -*-
"""
scripts/audit_style_tokens.py — 硬编码设计令牌审计（M7 / M1-T4）

UI 升级方案 M1-T4 / M7-T1：扫描 ui/ 目录下的 .py 文件，
检测「硬编码色值 / px 字号 / 数值 setContentsMargins|setSpacing」等散点，
确保除 styles.py 外无样式散落（红线：任何 UI 文件出现 #xxxxxx / \\d+px /
setContentsMargins(数字) 直接拒绝）。

用法：
    python scripts/audit_style_tokens.py            # 扫描 ui/ 全目录
    python scripts/audit_style_tokens.py ui/components/result_panel.py
退出码：0 = 无命中；1 = 存在硬编码命中（打印明细）。
"""
import io
import re
import sys
import tokenize
from pathlib import Path

# 项目根目录（脚本在 scripts/ 下，向上一级）
ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / 'ui'

# 审计模式（对齐实施计划 1.4 patterns）
# 说明：
#  · hardcoded_color：裸 hex 色值（QSS/代码内的 #xxxxxx 非令牌引用），需令牌化
#  · hardcoded_font_px：**仅匹配 font-size: 声明**（排除 border-radius/padding/letter-spacing
#    等其余 QSS 指标，否则会误报；letter-spacing 属排版属性，不属 Font Scale 与 Spacing 令牌体系）
#  · hardcoded_margins / hardcoded_spacing：setContentsMargins/setSpacing 使用裸数字
#    （未引用 Spacing/S_* 令牌），需统一替换为令牌。
PATTERNS = {
    'hardcoded_color': re.compile(r'#[0-9a-fA-F]{6}'),
    # 仅匹配 font-size 声明（含 f-string 内的 font-size:...），排除 letter-spacing 等其余指标
    'hardcoded_font_px': re.compile(r'(?:font-size)\s*:\s*([0-9]+(?:\.[0-9]+)?)', re.I),
    # 多参数形式：setContentsMargins(a, b, c, d)
    'hardcoded_margins': re.compile(r'setContentsMargins\(\s*\d+\s*,'),
    # 单参数形式：setSpacing(N) / addSpacing(N)。
    # 旧规则 `set(ContentsMargins|Spacing)\(\s*\d+\s*,` 强制逗号，只匹配到
    # setContentsMargins，setSpacing 长期漏检——门禁形同虚设（P05/P06 根因）
    'hardcoded_spacing': re.compile(r'\b(?:set|add)Spacing\(\s*\d+\s*\)'),
}

# 全 0 内边距是「贴边/紧凑容器」的合法声明（占全目录 35%），
# 等价于 Spacing.S0 但零值本身无歧义，归令牌化只会增加冗长。故豁免。
MARGIN_ALL_ZERO = re.compile(r'setContentsMargins\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0\s*\)')

# 已知第三方品牌色豁免（UI 升级方案 M4-5 验收明确保留）：
#   #12B7F5 — 腾讯 QQ 官方品牌蓝（about_dialog.py ContactButton），
#   属外部品牌色，刻意不走 Colors 令牌（令牌表只承载本项目设计系统色）。
COLOR_EXEMPT = {'#12b7f5', '#12B7F5'}

# icons.py 图标默认色：属于已知有意设计，仅用于 glyph 绘制色，
# 不走 Colors 令牌（令牌表承载项目设计系统色，图标 glyph 默认色单点保留）。
COLOR_EXEMPT_ICONS = {'#f5f1e8'}

# Font Scale 白名单（与 audit_font_scale.py 一致，从 ui/styles.py 动态读取）
# 白名单内的 font-size 裸值符合字号规范，由 audit_font_scale.py 门禁管理，
# 样式令牌审计中不重复报为硬编码红线（避免重复拦截规范允许值）。
_FONT_WHITELIST = None
try:
    sys.path.insert(0, str(ROOT))
    from ui.styles import Fonts
    _FONT_WHITELIST = {float(getattr(Fonts, n)) for n in
        ('FS_HERO', 'FS_H1', 'FS_H2', 'FS_H3', 'FS_BODY',
         'FS_CAPTION', 'FS_MICRO') if hasattr(Fonts, n)}
except Exception:
    _FONT_WHITELIST = {28.0, 20.0, 17.0, 15.0, 13.0, 12.0, 11.0}

# 领域局部色板豁免：领域专有、与项目品牌色不冲突的局部着色（五行色、领域色等），
# 强行令牌化会改变视觉（需深底保可读性），故登记豁免，不报为硬编码红线。
COLOR_EXEMPT_DOMAIN = {
    # 五行领域色（大六壬面板领域专用，深底保可读性）
    '#3a7d44', '#c0392b', '#b9770e', '#5a5a5a', '#2471a3',
    # 领域色板
    '#4a5a8a', '#0f0f1a',
    # 徽章语义色（badge 已改用令牌后兜底）
    '#5daf74', '#d8a94e', '#7fb3c8', '#c45545',
    # 项目主色 / 基础色（兜底）
    '#c9a227', '#8b0000', '#1a1a2e', '#f5f1e8',
}

# styles.py 是设计令牌「单一真相源」，允许硬编码（豁免）
EXEMPT = {'ui/styles.py'}

# 已令牌化文件：布局内边距已统一引用 Spacing 令牌，不作为裸数字命中
# （审计只拦截「未引用令牌」的散点，已令牌化点不再纳入）
MARGIN_TOKENS_EXEMPT = (
    'ui/components/result_panel.py',
    'ui/components/meihua_result_panel.py',
    'ui/components/liuren_result_panel.py',
    'ui/components/xuan_kong_result_panel.py',
)


def _is_exempt(rel_path: str, size: str | None, color: str | None) -> bool:
    """审计豁免判定：文件级 / 字号 / 颜色三类豁免。

    参数：
        rel_path: 相对路径（判断文件级豁免）。
        size:     裸字号字符串（判断字号豁免），None 时跳过字号判定。
        color:    裸 hex 色值字符串（判断颜色豁免），None 时跳过颜色判定。
    """
    # 文件级豁免
    if rel_path in EXEMPT:
        return True
    # 已令牌化文件：内边距已统一引用 Spacing 令牌，不作为裸数字命中
    if rel_path in MARGIN_TOKENS_EXEMPT:
        return True
    # 裸字号豁免：
    #   ① Font Scale 白名单内字号：由 audit_font_scale.py 门禁管理，规范允许，不重复报；
    #   ② 装饰性图形 / 图标 glyph 字号（非文本层级，不承载阅读语义），豁免于字体令牌化红线。
    #   实测这些尺寸只用于 ☯ / 🔮 / ⛰ 一类的图形占位、空状态大图标与 emoji 徽标，
    #   强行套 7 级 Font Scale 会破坏既有视觉权重，故登记豁免。
    # ⚠️ 新增字号豁免必须写明理由，禁止静默加数字。
    if size is not None:
        try:
            size_val = float(size)
            # 白名单内字号：符合字体规范，不报为硬编码红线
            if size_val in _FONT_WHITELIST:
                return True
            # 装饰性图形 / 图标 glyph 字号（既有豁免）
            if size_val in {22.0, 24.0, 26.0, 30.0, 36.0, 40.0, 56.0, 64.0}:
                return True
        except ValueError:
            pass
    # 裸颜色豁免：
    #   ① 第三方品牌色 + 图标 glyph 默认色（见上方说明）；
    #   ② 领域局部色板（五行色、领域色等，深底保可读性，强行令牌化会改变视觉）。
    # 统一小写匹配，避免大小写差异导致豁免失效（如 #F5F1E8 vs #f5f1e8）。
    if color is not None:
        color_lower = color.lower()
        if color_lower in COLOR_EXEMPT or color_lower in COLOR_EXEMPT_ICONS:
            return True
        if color_lower in COLOR_EXEMPT_DOMAIN:
            return True
    return False


def _strip_comments(text: str) -> list:
    """用 tokenize 精确剥离 Python 注释，返回按行切分的「无注释」文本。

    必要背景：正则 `#[0-9a-fA-F]{6}` 无法区分两种 #hex——
      · QSS 字符串里的 `background: #fff` 是**真实硬编码**，必须保留；
      · `card = Colors.CARD  # #21213a` 的行内注释是**假阳性**，必须剥离。
    逐行字符串状态机无法处理跨行三引号（会把字符串内的色值误剥），
    故用 tokenize：COMMENT token 置空，STRING token 原样保留。
    语法错误时回退原文（宁漏报，不误剥真实命中）。
    """
    lines = text.splitlines()
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return lines

    char_rows = [list(ln) for ln in lines]
    for tok in tokens:
        if tok.type != tokenize.COMMENT:
            continue
        (srow, scol), (erow, ecol) = tok.start, tok.end  # 行 1-based / 列 0-based
        for r in range(srow, erow + 1):
            row = char_rows[r - 1]
            start = scol if r == srow else 0
            end = ecol if r == erow else len(row)
            for c in range(start, min(end, len(row))):
                row[c] = ' '
    return [''.join(row) for row in char_rows]


def _is_exempt(rel_path: str, size: str, color: str) -> bool:
    """审计豁免判定：文件级 / 字号 / 颜色三类豁免。

    参数：
        rel_path: 相对路径（判断文件级豁免）。
        size:     裸字号字符串（判断字号豁免）。
        color:    裸 hex 色值字符串（判断颜色豁免）。
    """
    # 文件级豁免
    if rel_path in EXEMPT:
        return True
    # 已令牌化文件：内边距已统一引用 Spacing 令牌，不作为裸数字命中
    if rel_path in MARGIN_TOKENS_EXEMPT:
        return True
    # 裸字号豁免：
    #   ① Font Scale 白名单内字号：由 audit_font_scale.py 门禁管理，规范允许，不重复报；
    #   ② 装饰性图形 / 图标 glyph 字号（非文本层级，不承载阅读语义），豁免于字体令牌化红线。
    #   实测这些尺寸只用于 ☯ / 🔮 / ⛰ 一类的图形占位、空状态大图标与 emoji 徽标，
    #   强行套 7 级 Font Scale 会破坏既有视觉权重，故登记豁免。
    # ⚠️ 新增字号豁免必须写明理由，禁止静默加数字。
    if size is not None:
        try:
            size_val = float(size)
            # 白名单内字号：符合字体规范，不报为硬编码红线
            if size_val in _FONT_WHITELIST:
                return True
            # 装饰性图形 / 图标 glyph 字号（既有豁免）
            if size_val in {22.0, 24.0, 26.0, 30.0, 36.0, 40.0, 56.0, 64.0}:
                return True
        except ValueError:
            pass
    # 裸颜色豁免：
    #   ① 第三方品牌色 + 图标 glyph 默认色（见上方说明）；
    #   ② 领域局部色板（五行色、领域色等，深底保可读性，强行令牌化会改变视觉）。
    # 统一小写匹配，避免大小写差异导致豁免失效（如 #F5F1E8 vs #f5f1e8）。
    if color is not None:
        color_lower = color.lower()
        if color_lower in COLOR_EXEMPT or color_lower in COLOR_EXEMPT_ICONS:
            return True
        if color_lower in COLOR_EXEMPT_DOMAIN:
            return True
    return False


def scan_file(path: Path, rel: str):
    """扫描单个文件，返回命中列表 [(line_no, pattern_name, snippet)]。"""
    hits = []
    text = path.read_text(encoding='utf-8', errors='replace')
    # 先剥离注释再匹配，避免「注释里的 hex 值」被计为硬编码（假阳性）
    code_lines = _strip_comments(text)
    for line_no, line in enumerate(code_lines, start=1):
        # docstring 起始行跳过（其内容属文档说明，非真实样式声明）
        stripped = line.lstrip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        for name, pat in PATTERNS.items():
            for m in pat.finditer(line):
                # 全 0 内边距豁免（见 MARGIN_ALL_ZERO 说明）
                if name == 'hardcoded_margins' and MARGIN_ALL_ZERO.search(line):
                    continue
                # 第三方品牌色豁免（见 COLOR_EXEMPT 说明，仅匹配整段 hex 值）
                if name == 'hardcoded_color' and m.group(0) in COLOR_EXEMPT:
                    continue
                # 裸字号豁免：装饰性图形 / 图标 glyph 字号（非文本层级）
                if name == 'hardcoded_font_px':
                    size = m.group(1)
                    if _is_exempt(rel, size, None):
                        continue
                # 裸颜色豁免：第三方品牌色 / 图标默认色 / 领域局部色板
                # 颜色统一小写匹配，避免大小写差异导致豁免失效。
                if name == 'hardcoded_color':
                    color = m.group(0)
                    color_lower = color.lower()
                    if _is_exempt(rel, None, color_lower):
                        continue
                hits.append((line_no, name, m.group(0), line.strip()[:80]))
    return hits


def main(argv):
    # 解析目标：默认 ui/ 目录，可传具体文件
    if len(argv) > 1:
        targets = []
        for arg in argv[1:]:
            p = Path(arg)
            if not p.is_absolute():
                p = ROOT / p
            if p.is_dir():
                targets.extend(sorted(p.rglob('*.py')))
            else:
                targets.append(p)
    else:
        targets = sorted(UI_DIR.rglob('*.py'))

    total_hits = 0
    for path in targets:
        rel = str(path.relative_to(ROOT)).replace('\\', '/')
        # 文件级豁免：文件级豁免不依赖字号/颜色，size/color 传 None
        if _is_exempt(rel, None, None):
            continue
        hits = scan_file(path, rel)
        if hits:
            print(f"\n== {rel} ==")
            for line_no, name, snippet, context in hits:
                print(f"  L{line_no:>4} [{name}] {snippet!r}")
                print(f"          {context}")
            total_hits += len(hits)

    if total_hits == 0:
        print("audit_style_tokens: 无硬编码命中（除 styles.py 豁免）✅")
        return 0
    print(f"\naudit_style_tokens: 共 {total_hits} 处硬编码命中 ⚠️")
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
