"""批量更新 import 引用路径（core.X → 新子包路径）"""

import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 模块 → 新路径 映射
MOVES = {
    "bazi_calculator": "bazi.bazi_calculator",
    "bazi_types": "bazi.bazi_types",
    "bazi_batch": "bazi.bazi_batch",
    "wuxing": "bazi.wuxing",
    "shishen": "bazi.shishen",
    "mingli": "bazi.mingli",
    "geju_analyzer": "bazi.geju_analyzer",
    "yunshi": "bazi.yunshi",
    "yuncheng": "bazi.yuncheng",
    "_baazi_compat": "bazi._baazi_compat",
    "meihua": "divination.meihua",
    "hexagram_analyzer": "divination.hexagram_analyzer",
    "hexagram_data": "divination.hexagram_data",
    "liuren": "divination.liuren",
    "knowledge_base": "knowledge.knowledge_base",
    "rag_knowledge": "knowledge.rag_knowledge",
    "analysis_storage": "knowledge.analysis_storage",
    "analysis_fallback": "knowledge.analysis_fallback",
    "data_integration": "knowledge.data_integration",
    "data_validator": "knowledge.data_validator",
    "data_validator_v2": "knowledge.data_validator_v2",
}

# 需要扫描的目录
SCAN_DIRS = ["core", "ui", "service", "tests", "scripts"]


def fix_import_lines(content: str) -> tuple[str, int]:
    """修复 content 中的 import 行，返回 (新内容, 修改次数)"""
    count = 0
    lines = content.split("\n")

    for i, line in enumerate(lines):
        original = line
        # 处理 from core.X import ...
        for old_mod, new_mod in MOVES.items():
            old_path = f"core.{old_mod}"
            new_path = f"core.{new_mod}"
            # 匹配 from core.X import 或 import core.X
            # 先处理 "from core.X import"
            if f"from {old_path}" in line:
                line = line.replace(f"from {old_path}", f"from {new_path}")
                count += 1
            # 处理 "import core.X"
            if f"import {old_path}" in line:
                line = line.replace(f"import {old_path}", f"import {new_path}")
                count += 1
            # 处理 "--hidden-import=core.X"
            if f"--hidden-import={old_path}" in line:
                line = line.replace(f"--hidden-import={old_path}", f"--hidden-import={new_path}")
                count += 1
        # 处理字符串形式的 hiddenimports 列表（.spec 文件）
        for old_mod, new_mod in MOVES.items():
            old_str = f"'core.{old_mod}'"
            new_str = f"'core.{new_mod}'"
            if old_str in line:
                line = line.replace(old_str, new_str)
                count += 1
            old_str2 = f'"{old_mod}"'
            new_str2 = f'"{new_mod}"'
            # 不匹配纯字符串，避免误改

        lines[i] = line

    new_content = "\n".join(lines)
    return new_content, count


def main():
    total_files_changed = 0
    total_lines_changed = 0

    for scan_dir in SCAN_DIRS:
        dir_path = os.path.join(ROOT, scan_dir)
        if not os.path.exists(dir_path):
            continue
        for root, dirs, files in os.walk(dir_path):
            for fname in files:
                if not fname.endswith((".py", ".spec")):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    print(f"  读取失败: {fpath} - {e}")
                    continue
                new_content, cnt = fix_import_lines(content)
                if cnt > 0:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    rel = os.path.relpath(fpath, ROOT)
                    print(f"  ✓ {rel}: {cnt} 处修改")
                    total_files_changed += 1
                    total_lines_changed += cnt

    print(f"\n=== 完成: {total_files_changed} 个文件, {total_lines_changed} 处修改 ===")


if __name__ == "__main__":
    main()
