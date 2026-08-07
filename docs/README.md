# 项目文档中心（docs/）

本目录集中存放 KP-AI-FENGSHUI 的正式文档，取代原先散落在根目录与 `.trae/` 的草稿。

## 目录结构
```
docs/
├── README.md                      # 本文档：索引
├── architecture.md                # 架构说明与模块依赖关系
├── file_structure_report.html     # 文件结构梳理与分类分析报告（可视化）
└── plans/archive/                 # 历史设计/规格草稿归档（原 .trae/documents、.trae/specs）
    ├── *.md                       # 各阶段 UI / AI 改造方案草稿
    └── <feature>/                 # 功能规格三件套（spec / checklist / tasks）
```

## 文档导航
- **想了解整体文件分类** → 打开 `file_structure_report.html`（含分类清单、依赖图、整理建议）。
- **想了解架构与依赖** → 阅读 `architecture.md`（入口、UI 层、业务核心、存储层、AI 链路、Schema 生成链）。
- **历史方案查证** → 进入 `plans/archive/`，按文件名或功能目录检索。

## 约定
- 正式、面向维护者的文档放 `docs/` 根；一次性草稿与历史方案统一归档到 `plans/archive/`，不再散落根目录。
- `architecture.md` 与 `file_structure_report.html` 内容应保持一致；结构变更后同步更新。
