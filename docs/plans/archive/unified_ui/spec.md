# 八字排盘应用 - 统一视觉风格规范文档

## Overview
- **Summary**: 为八字排盘应用创建统一的视觉风格，输入界面和结果输出界面采用完全一致的配色、字体、圆角、间距和控件样式，打造极简AI命理专业风。
- **Purpose**: 解决现有界面割裂、风格反差问题，提供专业、素雅、高级的命理工具体验。
- **Target Users**: 需要进行八字排盘的命理爱好者和专业人士。

## Goals
- 实现输入界面和结果输出界面的视觉高度统一
- 采用低饱和国风专业色系，打造极简素雅风格
- 建立统一的字体规则、字号层级和间距规范
- 修复排版混乱问题，确保自适应窗口布局稳定

## Non-Goals (Out of Scope)
- 添加新的命理分析功能
- 修改核心算法逻辑
- 支持移动端响应式布局

## Background & Context
- 现有代码基于PyQt5框架，包含输入面板和结果面板两个主要界面
- 当前界面存在视觉风格不一致问题，需要统一规范
- 用户要求专业严谨的命理工具质感，无花哨装饰

## Functional Requirements
- **FR-1**: 全局配色规范统一应用于输入和输出界面
- **FR-2**: 统一的字体规则和字号层级
- **FR-3**: 统一的间距与圆角规范
- **FR-4**: 输入界面包含性别选择、历法切换、日期选择、时辰选择、出生地点和高级设置
- **FR-5**: 结果输出界面按固定顺序展示命主信息、四柱排盘、五行分析、大运流年和AI解析
- **FR-6**: 修复文字溢出、多重滚动条、布局错乱等问题

## Non-Functional Requirements
- **NFR-1**: 界面留白充足，杜绝拥挤堆叠
- **NFR-2**: 窗口自适应缩放，布局不乱、元素不挤压
- **NFR-3**: 所有卡片自带低透明度柔和阴影
- **NFR-4**: 无花纹、无贴图、无渐变、无多余装饰

## Constraints
- **Technical**: 基于PyQt5框架，Python语言
- **Dependencies**: 现有核心算法模块（baazi、wuxing、shishen等）

## Assumptions
- 用户使用桌面端设备，主要在Windows环境运行
- 用户需要长期阅读，注重排版舒适度

## Acceptance Criteria

### AC-1: 配色规范统一
- **Given**: 应用运行中
- **When**: 切换输入界面和结果界面
- **Then**: 配色保持一致（背景#F9F7F3、卡片#FFFFFF、主标题#1A1A1A、正文#333333、强调色#2A4A3F、警示色#9C4444、边框#E0E0E0）
- **Verification**: `human-judgment`

### AC-2: 字体规则统一
- **Given**: 应用运行中
- **When**: 查看任意界面文字
- **Then**: 中文使用思源黑体，数字/英文使用等宽字体
- **Verification**: `human-judgment`

### AC-3: 字号层级统一
- **Given**: 应用运行中
- **When**: 查看界面文字
- **Then**: 页面大标题19px加粗、板块标题16px加粗、重点文字18px加粗、常规正文13px、辅助备注11px浅灰色
- **Verification**: `human-judgment`

### AC-4: 间距与圆角规范统一
- **Given**: 应用运行中
- **When**: 查看卡片和控件
- **Then**: 卡片圆角8px、控件圆角6px、卡片内边距22px、模块间距18px
- **Verification**: `human-judgment`

### AC-5: 输入界面布局规范
- **Given**: 在输入界面
- **When**: 查看表单
- **Then**: 居中布局，控件顺序为性别选择→历法切换→出生日期→出生时辰→出生地点→高级设置
- **Verification**: `human-judgment`

### AC-6: 结果界面布局规范
- **Given**: 在结果界面
- **When**: 查看排盘结果
- **Then**: 按顺序展示命主基础信息、四柱核心排盘、五行格局分析、大运流年、AI智能解析
- **Verification**: `human-judgment`

### AC-7: 排版错乱修复
- **Given**: 调整窗口大小
- **When**: 查看界面
- **Then**: 无文字溢出、单一滚动条、布局稳定
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要保留首页（HomePage），还是直接进入输入界面？
- [ ] 高级设置面板是否需要默认收起？
