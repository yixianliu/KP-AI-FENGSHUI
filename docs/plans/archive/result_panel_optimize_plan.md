# 内容展示界面优化方案

## 一、需求分析

根据用户要求，需要对内容展示界面进行全面优化，重点解决以下问题：

### 1.1 排版问题
- 文本格式不规范，段落不清晰
- 间距设置不合理，影响阅读体验

### 1.2 宽度问题
- 内容板块显示宽度受限
- 可视区域不够大，内容显示不完整

### 1.3 布局结构问题
- 整体布局缺乏层次感
- 可读性需要提升

---

## 二、现有代码分析

### 2.1 当前布局结构
```python
ResultPanel
├── QScrollArea
│   └── scroll_content (QWidget)
│       ├── BaziHighlightCard (八字排盘结果)
│       ├── wuxing_card (五行分布)
│       ├── shishen_card (十神分析)
│       ├── geju_card (命局格局)
│       ├── major_fortune_card (大运分析)
│       ├── annual_fortune_card (流年运势)
│       ├── monthly_fortune_card (流月运势)
│       ├── mingli_card (命理元素)
│       └── ai_analysis_card (AI综合分析)
```

### 2.2 主要问题点

| 问题 | 位置 | 当前状态 | 优化方向 |
|------|------|----------|----------|
| 滚动区域margin过大 | scroll_layout.setContentsMargins(24, 24, 24, 24) | 限制内容宽度 | 减小margin |
| 卡片间距不一致 | scroll_layout.setSpacing(24) | 可能过宽或过窄 | 调整为统一合理间距 |
| 内容区域padding过多 | ResultCard.content_layout.setContentsMargins(28, 28, 28, 28) | 占用过多空间 | 优化padding值 |
| 行高设置不一致 | 各标签行高设置不一 | 影响阅读体验 | 统一行高为1.8-2.0 |
| 表格列宽不合理 | QHeaderView.Stretch | 列宽分配不均 | 优化列宽策略 |
| 列表项padding | LIST_WIDGET中item padding | 可能影响紧凑性 | 调整padding |

---

## 三、优化方案

### 3.1 修改 `ui/styles.py`
- 调整卡片样式的padding
- 优化列表项的padding
- 统一文本行高设置

### 3.2 修改 `ui/components/result_panel.py`
- 减小滚动区域的margin
- 优化卡片内部布局间距
- 调整表格列宽策略
- 优化AI分析部分的布局结构
- 增加内容区域的宽度

---

## 四、详细实施步骤

### 步骤1：优化样式定义 (`ui/styles.py`)
1. 调整卡片内容区域的padding从28px减小到20px
2. 调整列表项的padding从16px 20px调整为12px 16px
3. 统一文本行高为1.9

### 步骤2：优化滚动区域布局 (`ui/components/result_panel.py`)
1. 修改scroll_layout的margin从24px减小到16px
2. 调整卡片之间的spacing从24px调整为20px
3. 优化ResultCard的内容padding

### 步骤3：优化表格布局
1. 调整十神分析表格的列宽分配策略
2. 增加表格行高以提升可读性

### 步骤4：优化AI分析板块
1. 调整各AI分析部分的布局间距
2. 优化文本排版，增加段落间距

### 步骤5：测试验证
1. 运行程序验证界面显示
2. 检查内容是否完整显示
3. 验证排版是否整洁有序

---

## 五、风险与应对

| 风险 | 应对措施 |
|------|----------|
| 布局错乱 | 逐步修改，每次修改后测试 |
| 内容溢出 | 确保scroll_area正常工作 |
| 样式冲突 | 保持样式定义的一致性 |

---

## 六、交付物

1. 更新后的 `ui/styles.py`
2. 更新后的 `ui/components/result_panel.py`
