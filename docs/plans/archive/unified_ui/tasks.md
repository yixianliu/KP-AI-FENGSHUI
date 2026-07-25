# 八字排盘应用 - 统一视觉风格实现计划

## [x] Task 1: 更新全局样式规范 (styles.py)
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 更新Colors类，统一配色规范
  - 更新Fonts类，统一字体规则和字号层级
  - 更新Spacing类，统一间距与圆角规范
  - 更新Stylesheets类，应用统一样式到所有控件
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `human-judgment` TR-1.1: 配色符合规范（背景#F9F7F3、卡片#FFFFFF、主标题#1A1A1A、正文#333333、强调色#2A4A3F、警示色#9C4444、边框#E0E0E0）
  - `human-judgment` TR-1.2: 字号层级正确（大标题19px、板块标题16px、重点文字18px、正文13px、备注11px）
  - `human-judgment` TR-1.3: 圆角规范正确（卡片8px、控件6px）

## [x] Task 2: 更新输入界面 (input_panel.py)
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 调整布局为居中单卡片形式
  - 添加出生地点选择下拉框
  - 添加高级设置折叠面板
  - 更新控件样式以匹配全局规范
  - 添加性别选择为切换按钮（乾造/坤造）
  - 添加早晚子时切换开关
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `human-judgment` TR-2.1: 布局居中，单张白色大卡片包裹
  - `human-judgment` TR-2.2: 控件顺序正确（性别→历法→日期→时辰→地点→高级设置）
  - `human-judgment` TR-2.3: 按钮样式符合规范（主按钮暗青色填充，次要按钮透明边框）

## [x] Task 3: 更新结果输出界面 (result_panel.py)
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 重新设计布局结构，按固定顺序排列卡片
  - 移除渐变背景，改为统一卡片样式
  - 修复文字溢出问题
  - 确保单一滚动条
  - 更新AI解析为5段式结构
  - 添加日柱高亮效果
- **Acceptance Criteria Addressed**: AC-6, AC-7
- **Test Requirements**:
  - `human-judgment` TR-3.1: 卡片顺序正确（命主信息→四柱排盘→五行分析→大运流年→AI解析）
  - `human-judgment` TR-3.2: 无文字溢出，文本自动适配
  - `human-judgment` TR-3.3: 仅右侧单一滚动条，无多层嵌套
  - `human-judgment` TR-3.4: 日柱有暗青色浅底高亮

## [x] Task 4: 更新主窗口布局 (main_window.py)
- **Priority**: P1
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 简化布局，移除首页直接进入输入界面
  - 更新头部样式为统一风格
  - 移除渐变和多余装饰
  - 确保整体界面一体化
- **Acceptance Criteria Addressed**: AC-1, AC-7
- **Test Requirements**:
  - `human-judgment` TR-4.1: 整体风格统一，无割裂感
  - `human-judgment` TR-4.2: 窗口自适应缩放，布局稳定

## [x] Task 5: 验证整体风格一致性
- **Priority**: P1
- **Depends On**: Task 1, Task 2, Task 3, Task 4
- **Description**: 
  - 检查所有界面的配色一致性
  - 检查字体和字号规范
  - 检查间距和圆角规范
  - 修复发现的不一致问题
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `human-judgment` TR-5.1: 输入和输出界面视觉高度一致
  - `human-judgment` TR-5.2: 整体风格极简素雅、专业严谨
