# -*- coding: utf-8 -*-
"""验证「AI 结论文本块切分」（M3-4）合规。

校验点（针对 ui.components.collapsible_card._split_blocks）：
  1. 空文本 → [('p', '')]；
  2. 纯文本（含多段）按 \\n 切分为段落（空行忽略）；
  3. 代码围栏 ```...``` 切为独立 ('code', 代码文本) 块；
  4. 围栏前/后文本各自切段，混合顺序正确；
  5. 带语言标签围栏 ```python...``` 正确识别；
  6. 多段代码围栏均识别；
  7. 未闭合围栏（仅开头无结尾）整体按段落处理，绝不抛异常；
  8. 围栏内代码去除结尾换行（rstrip('\\n')）。

退出码：0 = 全部通过；1 = 存在切分逻辑违规。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ui.components.collapsible_card import _split_blocks


def _check(name, ok, detail=''):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def main():
    all_pass = True
    print("=" * 64)
    print("verify_content_blocks: AI 结论文本块切分校验（M3-4）")
    print("=" * 64)

    # 1. 空文本
    print("\n[1] 空文本 → [('p', '')]")
    r = _split_blocks('')
    ok = r == [('p', '')]
    all_pass = _check("空文本返回单段落空串", ok, f"={r}") and all_pass

    # 2. 纯文本多段
    print("\n[2] 纯文本多段切分（空行忽略）")
    r = _split_blocks('第一段\n第二段\n\n第三段')
    ok = r == [('p', '第一段'), ('p', '第二段'), ('p', '第三段')]
    all_pass = _check("纯文本按 \\n 分段、忽略空行", ok, f"={r}") and all_pass

    # 3. 单个代码围栏
    print("\n[3] 单个代码围栏 → ('code', ...) 块")
    r = _split_blocks('```\ncode line\n```')
    ok = r == [('code', 'code line')]
    all_pass = _check("围栏内容切为独立代码块", ok, f"={r}") and all_pass

    # 4. 围栏 + 前后文本混合
    print("\n[4] 前后文本 + 代码混合顺序")
    r = _split_blocks('前文段落\n```\nprint(1)\n```\n后文段落')
    ok = r == [('p', '前文段落'), ('code', 'print(1)'), ('p', '后文段落')]
    all_pass = _check("混合顺序：p / code / p", ok, f"={r}") and all_pass

    # 5. 带语言标签围栏
    print("\n[5] 带语言标签围栏（```python）")
    r = _split_blocks('```python\nx = 1\n```')
    ok = r == [('code', 'x = 1')]
    all_pass = _check("```python 围栏识别正确", ok, f"={r}") and all_pass

    # 6. 多段代码围栏
    print("\n[6] 多段代码围栏均识别")
    r = _split_blocks('a\n```\ncode1\n```\nb\n```js\ncode2\n```\nc')
    ok = r == [('p', 'a'), ('code', 'code1'), ('p', 'b'),
               ('code', 'code2'), ('p', 'c')]
    all_pass = _check("多围栏按出现顺序切分", ok, f"={r}") and all_pass

    # 7. 未闭合围栏不抛异常，整体按段落
    print("\n[7] 未闭合围栏（无结尾 ```）不抛异常")
    try:
        r = _split_blocks('```\n未闭合代码')
        ok = isinstance(r, list) and all(k in ('p', 'code') for k, _ in r)
        detail = f"={r}"
    except Exception as e:  # noqa: BLE001
        ok = False
        detail = f"抛出异常: {type(e).__name__}: {e}"
    all_pass = _check("未闭合围栏降级为段落、无异常", ok, detail) and all_pass

    # 8. 代码块去除结尾换行
    print("\n[8] 代码块去除结尾换行（rstrip('\\n')）")
    r = _split_blocks('```\nline1\nline2\n\n```')
    ok = r == [('code', 'line1\nline2')]
    all_pass = _check("代码内容以换行结尾时被剥离", ok, f"={r}") and all_pass

    print("\n" + "=" * 64)
    if all_pass:
        print("verify_content_blocks: 文本块切分全部合规 ✅")
        return 0
    print("verify_content_blocks: 文本块切分校验未通过 ❌")
    return 1


if __name__ == '__main__':
    sys.exit(main())
