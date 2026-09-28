# -*- coding: utf-8 -*-
"""
scripts/download_icons.py — 批量下载 SVG 图标（M1-T6，一次性开发工具）

从 Iconify（tabler-outline，Apache 2.0）下载 25 个图标到 assets/icons/。
运行时零新增依赖，仅开发用。需外网。

用法：
    python scripts/download_icons.py
"""
import pathlib
import sys

import requests

TABLER = "https://api.iconify.design/tabler/{name}.svg"
NAMES = [
    # 模块导航
    "infinity", "flower", "globe", "mountain",
    # 工具栏
    "robot", "copy", "download", "file-text", "file-spreadsheet", "layout-2",
    # 设置
    "settings", "info-circle", "circle-x", "circle-check",
    "alert-circle", "loader",
    # 通用
    "chevron-down", "chevron-up", "chevron-left", "chevron-right",
    "refresh", "search", "map-pin", "calendar",
]

# 业务名 → tabler 源名映射（落地到 assets/icons/ 用业务名）
NAME_MAP = {
    "infinity": "bazi",
    "flower": "meihua",
    "globe": "liuren",
    "mountain": "xuan-kong",
    "robot": "robot",
    "copy": "copy",
    "download": "export",
    "file-text": "export-pdf",
    "file-spreadsheet": "export-excel",
    "layout-2": "collapse-all",
    "settings": "settings",
    "info-circle": "info",
    "circle-x": "danger",
    "circle-check": "success",
    "alert-circle": "warning",
    "loader": "loading",
    "chevron-down": "arrow-down",
    "chevron-up": "arrow-up",
    "chevron-left": "arrow-left",
    "chevron-right": "arrow-right",
    "refresh": "refresh",
    "search": "search",
}


def main():
    out = pathlib.Path(__file__).resolve().parent.parent / "assets" / "icons"
    out.mkdir(parents=True, exist_ok=True)
    license = out / "LICENSE.md"
    license.write_text(
        "# 图标来源\n\n"
        "全部 SVG 图标来自 [Iconify](https://iconify.design) 的 "
        "`tabler-outline` 图标集，Apache License 2.0 授权。\n"
        "下载脚本：`scripts/download_icons.py`。\n",
        encoding="utf-8",
    )
    ok, fail = 0, 0
    for src in NAMES:
        dst = NAME_MAP.get(src, src)
        try:
            r = requests.get(TABLER.format(name=src), timeout=15)
            r.raise_for_status()
            (out / f"{dst}.svg").write_bytes(r.content)
            ok += 1
            print(f"  ✓ {dst}.svg  <- {src}")
        except Exception as e:
            fail += 1
            print(f"  ✗ {dst}.svg  <- {src}: {e}", file=sys.stderr)
    print(f"\ndownload_icons: 成功 {ok} / 失败 {fail}（需外网；失败可离线手工补 SVG）")
    return 0 if fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
