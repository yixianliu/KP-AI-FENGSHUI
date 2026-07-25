# Bazi (八字) 排盘应用增强计划

## 1. 需求分析

### 1.1 现有功能
当前应用已实现基础功能：
- 四柱八字排盘（年柱、月柱、日柱、时柱）
- 五行分析（木火土金水）
- 十神分析
- 命局格局分析
- 导出功能（CSV/Excel/PDF）

### 1.2 增强需求
根据用户需求，需要新增以下功能模块：

#### 运势信息 (Fortune Information)
1. **大运 (Major Fortune Periods)** - 详细时间段及分析
2. **流年 (Annual Fortune)** - 含每年小运
3. **流月 (Monthly Fortune)** - 月度运势解读

#### 命理元素 (Numerology Elements)
1. **主星 (Main Stars)** - 综合特性与影响
2. **天干地支分析** - 相互关系解读
3. **藏干 (Hidden Stems)** - 识别及其影响
4. **星运 (Star Fortune)** - 星曜分类解读
5. **自坐 (Self-Seat)** - 日主与日支关系
6. **空亡 (Emptiness)** - 识别及影响
7. **纳音 (Nayin)** - 五行属性
8. **神煞 (Gods and Demons)** - 详细解释

#### 增强UI
1. 重新布局组织所有内容
2. 清晰的视觉层次和分组
3. **AI分析专区**：
   - 八字命盘综合解读
   - 性格特征分析
   - 人生趋势与机遇挑战
   - 五行匹配兼容性
   - 实用建议

---

## 2. 技术架构设计

### 2.1 新增核心模块

| 模块 | 文件路径 | 功能说明 |
|------|----------|----------|
| 运势计算器 | `core/yunshi.py` | 大运、流年、流月计算 |
| 命理元素分析器 | `core/mingli.py` | 主星、藏干、纳音、神煞等 |
| AI分析引擎 | `core/ai_analyzer.py` | 综合分析与解读生成 |

### 2.2 UI组件更新

| 组件 | 文件路径 | 更新内容 |
|------|----------|----------|
| 运势卡片 | `ui/components/result_panel.py` | 新增大运、流年、流月卡片 |
| 命理元素卡片 | `ui/components/result_panel.py` | 新增主星、藏干、纳音、神煞卡片 |
| AI分析卡片 | `ui/components/result_panel.py` | 新增AI综合分析卡片 |

### 2.3 数据流架构

```
输入面板 → BaZiCalculator → 四柱八字
                          ↓
              ┌───────────┼───────────┐
              ↓           ↓           ↓
        WuXingAnalyzer ShiShenAnalyzer YunShiCalculator
              ↓           ↓           ↓
              └───────────┼───────────┘
                          ↓
                    MingLiAnalyzer
                          ↓
                    AIAnalyzer
                          ↓
                    ResultPanel (UI展示)
```

---

## 3. 实施步骤

### 3.1 阶段一：核心命理模块开发

**任务1: 创建运势计算器 (yunshi.py)**
- 大运计算（每10年一步大运）
- 流年计算（每年运势）
- 小运计算（每年小运）
- 流月计算（每月运势）

**任务2: 创建命理元素分析器 (mingli.py)**
- 主星分析（紫微斗数主星）
- 天干地支关系分析
- 藏干识别与影响
- 星运分析
- 自坐分析（日柱天干与地支关系）
- 空亡计算（空亡查法）
- 纳音五行计算
- 神煞识别（常见神煞如天德、月德、桃花等）

**任务3: 创建AI分析引擎 (ai_analyzer.py)**
- 综合命盘解读
- 性格特征提取
- 人生趋势分析
- 五行平衡建议

### 3.2 阶段二：UI组件增强

**任务4: 更新ResultPanel**
- 新增运势卡片（大运、流年、流月）
- 新增命理元素卡片（主星、藏干、纳音、神煞）
- 新增AI分析卡片
- 重新组织布局结构

**任务5: 更新MainWindow**
- 集成新分析器
- 更新计算流程

### 3.3 阶段三：测试与优化

**任务6: 功能测试**
- 验证新增功能正确性
- 测试UI布局适配

**任务7: 导出功能扩展**
- 更新导出模块支持新数据

---

## 4. 文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `core/yunshi.py` | 新建 | 运势计算模块 |
| `core/mingli.py` | 新建 | 命理元素分析模块 |
| `core/ai_analyzer.py` | 新建 | AI分析引擎 |
| `core/__init__.py` | 修改 | 导出新模块 |
| `ui/components/result_panel.py` | 修改 | 新增卡片组件 |
| `ui/main_window.py` | 修改 | 集成新分析器 |
| `ui/export/base_exporter.py` | 修改 | 支持新数据导出 |

---

## 5. 数据结构设计

### 5.1 运势数据结构

```python
# 大运信息
major_fortune = {
    'periods': [
        {
            'start_year': int,      # 开始年份
            'end_year': int,        # 结束年份
            'ganzhi': str,          # 大运干支
            'age_start': int,       # 起始年龄
            'age_end': int,         # 结束年龄
            'analysis': str         # 分析解读
        }
    ]
}

# 流年信息
annual_fortune = {
    'years': [
        {
            'year': int,            # 年份
            'ganzhi': str,          # 年干支
            'minor_fortune': str,   # 小运
            'analysis': str         # 年度分析
        }
    ]
}

# 流月信息
monthly_fortune = {
    'months': [
        {
            'year': int,            # 年份
            'month': int,           # 月份
            'ganzhi': str,          # 月干支
            'analysis': str         # 月度分析
        }
    ]
}
```

### 5.2 命理元素数据结构

```python
# 主星信息
main_stars = {
    'stars': [
        {
            'name': str,            # 星名
            'category': str,        # 类别（如紫微、天府等）
            'characteristics': str, # 特性描述
            'influence': str        # 影响分析
        }
    ]
}

# 纳音信息
nayin = {
    'year': {'element': str, 'description': str},
    'month': {'element': str, 'description': str},
    'day': {'element': str, 'description': str},
    'hour': {'element': str, 'description': str}
}

# 神煞信息
shensha = {
    'positive': [
        {
            'name': str,            # 神煞名称
            'location': str,        # 位置（年柱/月柱/日柱/时柱）
            'description': str      # 描述
        }
    ],
    'negative': [
        {
            'name': str,
            'location': str,
            'description': str
        }
    ]
}
```

### 5.3 AI分析数据结构

```python
ai_analysis = {
    'overview': str,               # 综合概述
    'personality': [str],          # 性格特征列表
    'life_trends': str,            # 人生趋势
    'opportunities': [str],        # 机遇
    'challenges': [str],           # 挑战
    'compatibility': str,          # 五行匹配
    'recommendations': [str]       # 建议
}
```

---

## 6. 风险与注意事项

### 6.1 技术风险
1. **命理算法准确性**：需确保大运、流年、神煞等计算符合传统命理规则
2. **性能优化**：大量数据计算可能影响响应速度，需考虑缓存机制
3. **UI布局复杂度**：新增内容较多，需合理组织避免信息过载

### 6.2 数据准确性保障
1. 大运起运年龄计算（顺行/逆行）
2. 空亡计算（年空、日空）
3. 神煞判定规则的准确性

### 6.3 测试要点
1. 不同出生日期的排盘验证
2. 农历/公历转换正确性
3. 导出功能完整性
4. UI响应式布局适配

---

## 7. 预期成果

完成后，应用将具备以下增强功能：
1. **完整运势分析**：大运、流年、流月三级运势解读
2. **深度命理元素分析**：主星、藏干、纳音、神煞等完整解读
3. **AI综合分析**：基于命盘的智能解读和建议
4. **专业UI展示**：清晰的信息架构和视觉层次

---

## 8. 时间估算

| 阶段 | 预计时长 |
|------|----------|
| 核心模块开发 | 3-4天 |
| UI组件增强 | 2-3天 |
| 测试优化 | 1-2天 |
| 总计 | 6-9天 |

---

**计划版本**: v1.0  
**创建日期**: 2024年  
**状态**: 待审批