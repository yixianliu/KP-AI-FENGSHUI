# AI内容显示问题修复计划 - 第二版

## 一、问题分析

### 1.1 异常表现
从运行日志中发现关键问题：
- **API返回数据正常**：包含完整的JSON格式分析结果
- **主窗口接收数据为空**：`{'personality': [], 'career': [], 'marriage': [], 'health': [], 'suggestions': []}`

### 1.2 问题根因定位

**关键日志分析**：
```
[AI分析器] 完整响应: ```json
{
  "personality": [...]
}
```
```

API返回的内容包含**Markdown代码块格式**（```json ... ```），导致：
1. JSON解析失败（因为有 ```json 前缀）
2. 文本解析方法无法正确提取JSON数据
3. 最终返回空字典

### 1.3 数据流转失败点

| 步骤 | 状态 | 问题 |
|------|------|------|
| 1. API返回数据 | ✅ 正常 | 包含完整JSON |
| 2. 移除代码块标记 | ❌ 缺失 | 未处理Markdown格式 |
| 3. JSON解析 | ❌ 失败 | 因代码块标记导致解析失败 |
| 4. 文本解析 | ❌ 失败 | 无法提取JSON结构 |
| 5. UI显示 | ❌ 失败 | 接收空数据 |

## 二、修复方案

### 2.1 文件修改清单

| 文件路径 | 修改内容 | 优先级 |
|----------|----------|--------|
| `core/ai_analyzer.py` | 在JSON解析前移除Markdown代码块标记 | **高** |

### 2.2 修复步骤

#### 步骤1：修改响应处理逻辑
在尝试JSON解析前，先移除Markdown代码块标记：
- 移除 ```` ```json ```` 前缀
- 移除 ```` ``` ```` 后缀

#### 步骤2：优化文本解析方法
如果JSON解析失败，尝试更智能的文本解析

## 三、实施代码

```python
# 在 _analyze_via_api 方法中修改
if full_response:
    # 移除Markdown代码块标记
    full_response = full_response.strip()
    if full_response.startswith('```json'):
        full_response = full_response[7:]  # 移除 ```json
    elif full_response.startswith('```'):
        full_response = full_response[3:]   # 移除 ```
    
    if full_response.endswith('```'):
        full_response = full_response[:-3]  # 移除结尾的 ```
    
    full_response = full_response.strip()
    
    try:
        result = json.loads(full_response)
        return self._validate_and_format_result(result)
    except json.JSONDecodeError:
        return self._parse_text_response(full_response)
```

## 四、测试验证

### 4.1 功能测试
- 验证带代码块标记的响应能正确解析
- 验证纯JSON响应能正确解析
- 验证文本响应能正确解析

### 4.2 日志验证
- 检查解析前的原始响应
- 检查解析后的JSON数据
- 检查UI接收的数据

## 五、风险评估

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 代码块格式变化 | JSON解析失败 | 添加多种格式兼容处理 |
| 响应格式不一致 | UI显示异常 | 加强数据格式校验 |
| 编码问题 | 解析失败 | 确保UTF-8编码处理 |

---

**计划完成时间**：预计10分钟完成修复和测试。