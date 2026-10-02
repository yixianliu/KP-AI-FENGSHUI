# -*- coding: utf-8 -*-
"""
ai/rag/chunker.py — 古籍文本切分器

将古籍文献切分为 500-800 字符块，保留上下文连贯性。
切分策略：
  1. 优先在句号/段末切分
  2. 不超过最大块长度
  3. 重叠窗口保留 50 字符上下文
"""
from __future__ import annotations

import re


# 古籍常见分段标点
_SPLIT_PATTERNS = [
    r'[。！？]',           # 句末标点
    r'[；;]',             # 分号
    r'[,，]',             # 逗号（辅助）
]

#: 单块最小字符数（大文本切分时使用）
MIN_CHUNK_LEN = 500
#: 单块最大字符数
MAX_CHUNK_LEN = 800
#: 重叠窗口字符数
OVERLAP = 50
#: 兜底最小块长度（用于短文本，确保至少输出一个块）
MIN_FALLBACK_LEN = 100


def chunk_text(text: str, min_len: int = MIN_CHUNK_LEN,
               max_len: int = MAX_CHUNK_LEN,
               overlap: int = OVERLAP) -> list[dict]:
    """将文本切分为知识块。

    Args:
        text: 原始古籍文本
        min_len: 最小块长度（字符数）
        max_len: 最大块长度（字符数）
        overlap: 重叠窗口（字符数），用于保留上下文

    Returns:
        list[dict]: 每块包含 'text', 'start_pos', 'end_pos', 'chunk_id'
    """
    if not text or not text.strip():
        return []

    # 预处理：移除多余空白
    text = re.sub(r'\s+', ' ', text)

    # 按段落切分
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    chunks: list[dict] = []
    chunk_id = 0
    current_buf = ""

    for para in paragraphs:
        # 单个段落过长则内部再切分
        if len(para) > max_len:
            # 内部按标点切分
            sentences = re.split(r'([。！？])', para)
            inner_buf = ""
            for i, part in enumerate(sentences):
                inner_buf += part
                if len(inner_buf) >= max_len or (i + 2 < len(sentences) and sentences[i + 1] in ('。', '！', '？')):
                    if len(inner_buf) >= min_len:
                        chunks.append(_make_chunk(inner_buf, chunk_id))
                        chunk_id += 1
                    # 重叠部分保留
                    if overlap > 0 and len(inner_buf) > overlap:
                        inner_buf = inner_buf[-overlap:]
                    else:
                        inner_buf = ""
            if inner_buf and len(inner_buf) >= min_len:
                chunks.append(_make_chunk(inner_buf, chunk_id))
                chunk_id += 1
            continue

        # 累积到缓冲区
        current_buf += para + " "
        if len(current_buf) >= max_len:
            if len(current_buf) >= min_len:
                chunks.append(_make_chunk(current_buf, chunk_id))
                chunk_id += 1
                # 保留尾部重叠
                if overlap > 0:
                    current_buf = current_buf[-overlap:]
                else:
                    current_buf = ""

    # 剩余不足一块的内容
    if current_buf and len(current_buf) >= min_len:
        chunks.append(_make_chunk(current_buf, chunk_id))

    # 重新编号
    for i, chunk in enumerate(chunks):
        chunk['chunk_id'] = i

    return chunks


def _make_chunk(text: str, chunk_id: int) -> dict:
    """构建单条知识块记录"""
    return {
        'chunk_id': chunk_id,
        'text': text.strip(),
        'length': len(text),
    }


def load_corpus_from_dir(dir_path: str, encoding: str = 'utf-8') -> list[dict]:
    """从目录加载所有 .txt 文件并切分。

    Args:
        dir_path: 古籍文本目录路径
        encoding: 文件编码

    Returns:
        list[dict]: 所有知识块列表
    """
    import os
    all_chunks: list[dict] = []
    chunk_id = 0

    for fname in sorted(os.listdir(dir_path)):
        if not fname.endswith('.txt'):
            continue
        fpath = os.path.join(dir_path, fname)
        try:
            with open(fpath, 'r', encoding=encoding) as f:
                text = f.read()
            source = fname.replace('.txt', '')
            chunks = chunk_text(text)
            for c in chunks:
                c['source'] = source
            all_chunks.extend(chunks)
            chunk_id += len(chunks)
        except Exception as e:
            print(f"[RAG] 加载 {fname} 失败: {e}")

    return all_chunks
