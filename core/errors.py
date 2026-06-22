from enum import Enum
from typing import Dict, Any


class ErrorCode(Enum):
    """错误码枚举"""
    SUCCESS = 0
    VALIDATION_ERROR = 1001
    DATABASE_CONNECTION_ERROR = 2001
    DATABASE_QUERY_ERROR = 2002
    API_KEY_MISSING = 3001
    API_REQUEST_ERROR = 3002
    API_TIMEOUT = 3003
    CALCULATION_ERROR = 4001
    UNKNOWN_ERROR = 9999


class AppException(Exception):
    """应用基础异常类"""
    
    def __init__(self, error_code: ErrorCode, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'error_code': self.error_code.value,
            'message': self.message,
            'details': self.details
        }


class ValidationError(AppException):
    """参数校验异常"""
    def __init__(self, message: str, field: str = None):
        details = {'field': field} if field else {}
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details)


class DatabaseConnectionError(AppException):
    """数据库连接异常"""
    def __init__(self, message: str):
        super().__init__(ErrorCode.DATABASE_CONNECTION_ERROR, message)


class DatabaseQueryError(AppException):
    """数据库查询异常"""
    def __init__(self, message: str):
        super().__init__(ErrorCode.DATABASE_QUERY_ERROR, message)


class ApiKeyMissingError(AppException):
    """API密钥缺失异常"""
    def __init__(self):
        super().__init__(
            ErrorCode.API_KEY_MISSING,
            "API密钥未配置，请设置环境变量 ERNIE_API_KEY"
        )


class ApiRequestError(AppException):
    """API请求异常"""
    def __init__(self, message: str, status_code: int = None):
        details = {'status_code': status_code} if status_code else {}
        super().__init__(ErrorCode.API_REQUEST_ERROR, message, details)


class ApiTimeoutError(AppException):
    """API超时异常"""
    def __init__(self, message: str = "API请求超时"):
        super().__init__(ErrorCode.API_TIMEOUT, message)


class CalculationError(AppException):
    """计算异常"""
    def __init__(self, message: str):
        super().__init__(ErrorCode.CALCULATION_ERROR, message)


class ResultStatus(Enum):
    """分析结果状态"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


def build_error_result(
    report_id: int = None,
    error_type: str = 'UnknownError',
    error_message: str = '',
    start_time: float = None
) -> Dict[str, Any]:
    """
    构建错误结果统一格式
    
    Args:
        report_id: 报告ID
        error_type: 错误类型
        error_message: 错误信息
        start_time: 开始时间戳
    
    Returns:
        错误结果字典
    """
    import time
    elapsed = round(time.time() - start_time, 2) if start_time else None
    
    return {
        'success': False,
        'report_id': report_id,
        'error_type': error_type,
        'error_message': error_message,
        'elapsed_seconds': elapsed,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }


def build_success_result(
    report_id: int = None,
    data: Dict[str, Any] = None,
    start_time: float = None
) -> Dict[str, Any]:
    """
    构建成功结果统一格式
    
    Args:
        report_id: 报告ID
        data: 业务数据
        start_time: 开始时间戳
    
    Returns:
        成功结果字典
    """
    import time
    elapsed = round(time.time() - start_time, 2) if start_time else None
    
    return {
        'success': True,
        'report_id': report_id,
        'data': data or {},
        'elapsed_seconds': elapsed,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }