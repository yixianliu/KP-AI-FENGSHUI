# AI风水命理分析系统 - Redis数据流程改造实现计划

## [x] Task 1: 安装Redis依赖并创建Redis管理模块
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 安装redis Python库
  - 创建`core/redis_manager.py`模块，封装Redis连接、数据存储、读取、过期时间设置等功能
  - 支持从config.ini读取Redis配置
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4, AC-6
- **Test Requirements**:
  - `programmatic` TR-1.1: RedisManager能正确连接本地Redis（默认端口6379）
  - `programmatic` TR-1.2: 能正确执行set/get/delete操作
  - `programmatic` TR-1.3: 能正确设置过期时间
- **Notes**: 需要处理Redis连接失败的异常情况

## [x] Task 2: 修改AnalysisPipeline支持Redis数据流转
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 修改`core/analysis_pipeline.py`，在分析流程中集成Redis数据读写
  - AI分析前从Redis读取输入数据
  - AI分析后将结果写入Redis
  - 支持任务状态追踪（pending/analyzing/completed/failed）
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-6
- **Test Requirements**:
  - `programmatic` TR-2.1: 分析流程能从Redis正确读取输入数据
  - `programmatic` TR-2.2: 分析完成后能正确写入结果到Redis
  - `programmatic` TR-2.3: 能正确更新任务状态
- **Notes**: 保持与MySQL存储的兼容，不影响现有流程

## [x] Task 3: 修改GUI主窗口实现排盘数据Redis存储
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 修改`ui/main_window.py`的`_on_bazi()`方法，将排盘输入数据存入Redis
  - 修改`_on_meihua()`方法，将起卦参数存入Redis
  - 生成唯一task_id用于关联输入数据和分析结果
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-6
- **Test Requirements**:
  - `programmatic` TR-3.1: 点击"开始排盘"后数据正确存入Redis
  - `programmatic` TR-3.2: 点击"起卦"后数据正确存入Redis
  - `human-judgment` TR-3.3: 存储失败时给予用户提示
- **Notes**: 存储成功后再执行后续分析流程

## [x] Task 4: 修改AI分析Worker支持Redis轮询
- **Priority**: high
- **Depends On**: Task 1, Task 2
- **Description**: 
  - 修改`ui/components/ai_analysis_worker.py`，支持从Redis读取分析结果
  - 在AI分析完成后通知GUI通过Redis获取结果
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-5
- **Test Requirements**:
  - `programmatic` TR-4.1: Worker能从Redis读取分析结果
  - `programmatic` TR-4.2: 结果数据格式正确
- **Notes**: Worker仍保持后台线程执行模式

## [x] Task 5: 实现GUI轮询机制读取Redis结果
- **Priority**: high
- **Depends On**: Task 1, Task 2
- **Description**: 
  - 在`ui/main_window.py`中实现轮询机制
  - 使用QTimer每隔1秒从Redis读取任务状态和结果
  - 最多轮询30次（30秒超时），成功后展示结果
- **Acceptance Criteria Addressed**: AC-5, AC-6
- **Test Requirements**:
  - `human-judgment` TR-5.1: GUI能实时显示分析进度状态
  - `human-judgment` TR-5.2: 分析完成后能正确展示结果
  - `human-judgment` TR-5.3: 超时后显示友好提示
- **Notes**: 轮询间隔可根据实际情况调整

## [x] Task 6: 更新配置文件和依赖
- **Priority**: medium
- **Depends On**: Task 1
- **Description**: 
  - 更新`config.ini.example`添加Redis配置项
  - 更新`requirements.txt`添加redis依赖
- **Acceptance Criteria Addressed**: NFR-1, NFR-2
- **Test Requirements**:
  - `programmatic` TR-6.1: 配置文件能正确读取Redis参数
  - `programmatic` TR-6.2: redis库能正常安装
- **Notes**: 配置项包括host、port、password、db等

## [x] Task 7: 异常处理与用户提示完善
- **Priority**: medium
- **Depends On**: Task 1-5
- **Description**: 
  - 完善所有Redis操作的异常处理
  - 统一错误提示格式
  - 确保异常情况下不阻塞主流程
- **Acceptance Criteria Addressed**: AC-6, NFR-4
- **Test Requirements**:
  - `human-judgment` TR-7.1: Redis连接失败时显示明确提示
  - `human-judgment` TR-7.2: 数据格式错误时显示明确提示
  - `human-judgment` TR-7.3: AI调用失败时显示明确提示
- **Notes**: 使用QMessageBox显示错误信息

## [x] Task 8: 测试验证与文档更新
- **Priority**: low
- **Depends On**: Task 1-7
- **Description**: 
  - 验证完整业务流程（排盘→Redis存储→AI分析→Redis结果→GUI展示）
  - 验证梅花易数流程（起卦→Redis存储→AI分析→Redis结果→GUI展示）
  - 验证异常情况处理
- **Acceptance Criteria Addressed**: 所有AC
- **Test Requirements**:
  - `human-judgment` TR-8.1: 八字排盘完整流程正常运行
  - `human-judgment` TR-8.2: 梅花易数完整流程正常运行
  - `human-judgment` TR-8.3: 异常情况处理正确
- **Notes**: 需要实际运行系统进行测试