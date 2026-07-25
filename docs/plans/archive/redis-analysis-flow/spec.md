# AI风水命理分析系统 - Redis数据流程改造 PRD

## Overview
- **Summary**: 将现有GUI界面的排盘和起卦流程改造为基于Redis的数据流转模式，实现输入数据暂存、AI分析调用、结果持久化和GUI轮询展示的完整业务流程
- **Purpose**: 通过Redis实现数据的临时存储和跨进程/跨线程的数据共享，提升系统的可扩展性和数据安全性
- **Target Users**: 使用该风水命理工具的用户

## Goals
- 实现排盘/起卦输入数据在Redis中的规范存储与过期管理
- 建立AI分析流程与Redis的数据交互机制
- 实现GUI界面通过轮询机制从Redis实时读取分析结果
- 确保数据传输完整性、操作原子性和界面响应及时性

## Non-Goals (Out of Scope)
- 不修改现有MySQL数据库存储逻辑（作为持久化备份保留）
- 不改变现有的AI分析算法和业务逻辑
- 不增加新的命理分析功能
- 不修改GUI界面的视觉设计风格

## Background & Context
- 当前系统使用MySQL作为主要存储，AI分析流程已通过AnalysisPipeline实现
- 系统架构：PySide6 GUI → AnalysisPipeline → AI模型 → MySQL存储
- 需要引入Redis作为中间缓存层，实现：
  - 输入数据的临时存储（设置过期时间）
  - 分析任务状态的实时追踪
  - AI分析结果的暂存供GUI轮询

## Functional Requirements
- **FR-1**: 用户点击"开始排盘"按钮时，系统将输入数据完整存入Redis，设置合理过期时间
- **FR-2**: 用户点击"梅花易数"模块的"起卦"按钮时，系统将起卦参数完整存入Redis，设置合理过期时间
- **FR-3**: AI分析流程从Redis读取已存储的相关内容作为输入参数
- **FR-4**: AI分析完成后，将报告数据格式验证后保存到Redis指定key中
- **FR-5**: GUI界面通过轮询机制从Redis读取最新报告内容并展示
- **FR-6**: 实现完整的异常处理机制，包括Redis连接失败、数据格式错误、AI调用失败等

## Non-Functional Requirements
- **NFR-1**: Redis数据存储格式统一规范，便于跨模块解析
- **NFR-2**: 数据过期时间合理设置（输入数据24小时，分析结果7天）
- **NFR-3**: GUI轮询间隔合理（初始1秒，最多30次，避免过度请求）
- **NFR-4**: 异常情况给予用户明确提示，不影响系统稳定性

## Constraints
- **Technical**: Python 3.x, PySide6, Redis 7.0+, 现有代码结构
- **Business**: 保持原有功能不变，仅增加Redis数据流转
- **Dependencies**: 需要安装redis Python库

## Assumptions
- Redis服务已安装并运行在本地默认端口（6379）
- 系统已有config.ini配置文件用于Redis配置
- 用户已安装基础依赖包

## Acceptance Criteria

### AC-1: 八字排盘数据Redis存储
- **Given**: 用户在八字排盘页面填写完整参数
- **When**: 点击"开始排盘"按钮
- **Then**: 输入数据完整存入Redis，key格式为`bazi:input:{task_id}`，设置24小时过期
- **Verification**: `programmatic`

### AC-2: 梅花易数起卦数据Redis存储
- **Given**: 用户在梅花易数页面选择起卦方式并填写参数
- **When**: 点击"起卦"按钮
- **Then**: 起卦数据完整存入Redis，key格式为`meihua:input:{task_id}`，设置24小时过期
- **Verification**: `programmatic`

### AC-3: AI分析从Redis读取数据
- **Given**: 数据已存入Redis
- **When**: AI分析流程启动
- **Then**: 从Redis读取对应key的输入数据作为分析参数
- **Verification**: `programmatic`

### AC-4: AI分析结果Redis存储
- **Given**: AI分析完成并返回报告数据
- **When**: 结果格式验证通过
- **Then**: 报告数据存入Redis，key格式为`{type}:result:{task_id}`，设置7天过期
- **Verification**: `programmatic`

### AC-5: GUI轮询读取分析结果
- **Given**: AI分析正在进行或已完成
- **When**: GUI启动轮询机制
- **Then**: 每隔1秒从Redis读取结果状态，最多30次，成功后展示结果
- **Verification**: `human-judgment`

### AC-6: 异常处理与用户提示
- **Given**: Redis连接失败、数据格式错误或AI调用失败
- **When**: 系统检测到异常
- **Then**: 显示明确的错误提示，不阻塞后续操作
- **Verification**: `human-judgment`

## Open Questions
- [ ] Redis服务器地址和端口是否需要配置化？（默认使用本地6379）
- [ ] 是否需要为不同用户设置隔离的Redis命名空间？