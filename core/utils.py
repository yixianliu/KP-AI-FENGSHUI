import re
import hashlib
from typing import Dict, Any, Optional


def generate_report_id() -> str:
    """
    生成唯一报告ID
    
    Returns:
        报告ID字符串
    """
    import uuid
    import time
    timestamp = int(time.time())
    uid = uuid.uuid4().hex[:8]
    return f"RPT{timestamp}{uid}"


def format_datetime(dt) -> str:
    """
    格式化日期时间
    
    Args:
        dt: datetime对象或时间戳
    
    Returns:
        格式化的日期字符串
    """
    if dt is None:
        return ''
    
    if isinstance(dt, (int, float)):
        import time
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dt))
    
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def validate_username(username: str) -> bool:
    """
    校验用户名格式
    
    Args:
        username: 用户名
    
    Returns:
        是否有效
    """
    if not username or not isinstance(username, str):
        return False
    
    if len(username) < 3 or len(username) > 20:
        return False
    
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', username))


def validate_password(password: str) -> bool:
    """
    校验密码强度
    
    Args:
        password: 密码
    
    Returns:
        是否有效
    """
    if not password or not isinstance(password, str):
        return False
    
    if len(password) < 6:
        return False
    
    return True


def hash_password(password: str) -> str:
    """
    密码哈希（SHA256）
    
    Args:
        password: 明文密码
    
    Returns:
        哈希值
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def safe_get(dictionary: Dict[str, Any], key: str, default=None) -> Any:
    """
    安全获取字典值
    
    Args:
        dictionary: 字典
        key: 键
        default: 默认值
    
    Returns:
        值或默认值
    """
    if dictionary is None or not isinstance(dictionary, dict):
        return default
    return dictionary.get(key, default)


def clamp(value: int, min_val: int, max_val: int) -> int:
    """
    将值限制在指定范围内
    
    Args:
        value: 输入值
        min_val: 最小值
        max_val: 最大值
    
    Returns:
        限制后的值
    """
    return max(min_val, min(value, max_val))


def convert_to_int(value, default: int = 0) -> int:
    """
    安全转换为整数
    
    Args:
        value: 输入值
        default: 默认值
    
    Returns:
        整数值
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def convert_to_float(value, default: float = 0.0) -> float:
    """
    安全转换为浮点数
    
    Args:
        value: 输入值
        default: 默认值
    
    Returns:
        浮点数值
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_birth_date(date_str: str) -> Optional[tuple]:
    """
    解析出生日期
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
    
    Returns:
        (年, 月, 日) 元组，解析失败返回None
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    match = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$', date_str)
    if not match:
        return None
    
    try:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
            return (year, month, day)
    except ValueError:
        pass
    
    return None


def parse_birth_time(time_str: str) -> Optional[tuple]:
    """
    解析出生时间
    
    Args:
        time_str: 时间字符串，格式 HH:MM
    
    Returns:
        (小时, 分钟) 元组，解析失败返回None
    """
    if not time_str or not isinstance(time_str, str):
        return None
    
    match = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
    if not match:
        return None
    
    try:
        hour, minute = int(match.group(1)), int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
    except ValueError:
        pass
    
    return None


def is_valid_city(city: str) -> bool:
    """
    校验城市名称
    
    Args:
        city: 城市名称
    
    Returns:
        是否有效
    """
    if not city or not isinstance(city, str):
        return False
    
    return bool(re.match(r'^[\u4e00-\u9fa5a-zA-Z]+$', city.strip()))