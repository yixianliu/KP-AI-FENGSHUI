# 风水八字排盘程序 - 信息录入首页 - 实施任务清单

## [x] 任务 1: 创建独立首页组件 HomePage
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 创建新的 HomePage 组件类
  - 设计整体布局结构
  - 实现居中对称布局框架
  - 采用简约国风设计风格
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-8, AC-9
- **Test Requirements**:
  - `programmatic` TR-1.1: HomePage 组件可以正常实例化
  - `programmatic` TR-1.2: 组件布局采用居中对称结构
  - `human-judgement` TR-1.3: 整体风格简约大方，无多余装饰
- **Notes**: 创建文件 `ui/components/home_page.py`

## [x] 任务 2: 实现年份选择控件
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 实现年份下拉选择控件
  - 年份范围：1900年 - 当前年份+10年
  - 采用统一圆角简约样式
- **Acceptance Criteria Addressed**: AC-3, AC-9
- **Test Requirements**:
  - `programmatic` TR-2.1: 年份控件包含完整年份范围
  - `programmatic` TR-2.2: 年份选择交互正常
  - `human-judgement` TR-2.3: 样式符合规范要求

## [x] 任务 3: 实现月份和日期选择控件
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 实现月份下拉选择（1-12月）
  - 实现日期下拉选择
  - 根据所选月份和年份自动调整天数
  - 处理闰年2月特殊情况
- **Acceptance Criteria Addressed**: AC-4, AC-9
- **Test Requirements**:
  - `programmatic` TR-3.1: 月份包含完整1-12月选项
  - `programmatic` TR-3.2: 日期根据月份和年份自动调整
  - `programmatic` TR-3.3: 闰年2月显示29天
  - `human-judgement` TR-3.4: 样式符合规范要求

## [x] 任务 4: 实现时辰选择控件
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 实现出生时辰下拉选择
  - 包含完整12时辰：子、丑、寅、卯、辰、巳、午、未、申、酉、戌、亥
  - 每个时辰标注对应的时间范围
- **Acceptance Criteria Addressed**: AC-5, AC-9
- **Test Requirements**:
  - `programmatic` TR-4.1: 时辰包含完整12个选项
  - `programmatic` TR-4.2: 每个时辰包含对应的时间范围
  - `human-judgement` TR-4.3: 样式符合规范要求

## [x] 任务 5: 实现性别选择控件
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 实现性别单选按钮（男/女）
  - 默认无选择状态
  - 提供清晰的选中状态反馈
- **Acceptance Criteria Addressed**: AC-6, AC-9
- **Test Requirements**:
  - `programmatic` TR-5.1: 性别单选按钮功能正常
  - `programmatic` TR-5.2: 默认无选择状态
  - `human-judgement` TR-5.3: 选中状态反馈清晰
  - `human-judgement` TR-5.4: 样式符合规范要求

## [x] 任务 6: 实现开始排盘按钮
- **Priority**: P0
- **Depends On**: 任务 2, 3, 4, 5
- **Description**:
  - 实现【开始排盘】主按钮
  - 设计简约大气、视觉突出的样式
  - 实现点击事件处理
  - 按钮放置于录入项下方合适位置
- **Acceptance Criteria Addressed**: AC-7, AC-9
- **Test Requirements**:
  - `programmatic` TR-6.1: 按钮点击事件响应正常
  - `human-judgement` TR-6.2: 按钮视觉突出，符合简约大气风格
  - `human-judgement` TR-6.3: 位置符合视觉流自然引导

## [x] 任务 7: 集成首页与主窗口
- **Priority**: P0
- **Depends On**: 任务 1-6
- **Description**:
  - 使用 QStackedWidget 管理首页和结果页
  - 修改 main_window.py，集成 HomePage
  - 实现点击开始排盘后切换到结果页的逻辑
  - 保持现有结果展示功能完整
- **Acceptance Criteria Addressed**: AC-8
- **Test Requirements**:
  - `programmatic` TR-7.1: 首页正常显示在主窗口中
  - `programmatic` TR-7.2: 点击开始排盘后成功显示结果页
  - `programmatic` TR-7.3: 现有结果展示功能保持完整
  - `human-judgement` TR-7.4: 页面切换流程顺畅自然

## [x] 任务 8: 优化样式和交互细节
- **Priority**: P1
- **Depends On**: 任务 1-7
- **Description**:
  - 优化控件间距和留白
  - 统一所有控件样式细节
  - 添加输入验证和错误提示
  - 优化交互反馈效果
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-9
- **Test Requirements**:
  - `human-judgement` TR-8.1: 整体视觉效果协调统一
  - `human-judgement` TR-8.2: 交互反馈流畅自然
  - `human-judgement` TR-8.3: 输入验证提示清晰友好

## [x] 任务 9: 窗口自适应和响应式优化
- **Priority**: P1
- **Depends On**: 任务 1-8
- **Description**:
  - 优化窗口尺寸自适应逻辑
  - 确保在不同分辨率下布局美观
  - 测试最小窗口尺寸显示效果
  - 设置合适的最小窗口尺寸
- **Acceptance Criteria Addressed**: AC-2, AC-8
- **Test Requirements**:
  - `human-judgement` TR-9.1: 在不同窗口尺寸下布局保持美观
  - `human-judgement` TR-9.2: 最小窗口尺寸下内容完整显示
  - `programmatic` TR-9.3: 最小窗口尺寸设置合理
