"""
Redis管理模块
封装Redis连接、数据存储、读取、过期时间设置等功能
支持从config.ini读取Redis配置
"""
import json
import logging
import configparser
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import timedelta

import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

DEFAULT_REDIS_CONFIG = {
    'host': '127.0.0.1',
    'port': 6379,
    'password': '',
    'db': 0,
    'socket_timeout': 10,
    'socket_connect_timeout': 10,
    'decode_responses': True,
}

DEFAULT_EXPIRE_INPUT = 86400
DEFAULT_EXPIRE_RESULT = 604800


class RedisManagerError(Exception):
    """Redis管理异常基类"""
    pass


class RedisConnectionError(RedisManagerError):
    """Redis连接异常"""
    pass


class RedisOperationError(RedisManagerError):
    """Redis操作异常"""
    pass


class RedisManager:
    """
    Redis管理器
    负责管理Redis连接和数据读写操作
    """

    def __init__(self, config_path: str = None):
        """
        初始化Redis管理器

        Args:
            config_path: 配置文件路径，默认使用项目根目录的config.ini
        """
        self.config_path = config_path
        self.redis_config = self._load_config()
        self._client = None
        self._connected = False

    def _load_config(self) -> Dict[str, Any]:
        """
        从config.ini读取Redis配置

        Returns:
            Redis配置字典
        """
        config = DEFAULT_REDIS_CONFIG.copy()

        if self.config_path is None:
            project_root = Path(__file__).resolve().parent.parent
            config_path = project_root / 'config.ini'
        else:
            config_path = Path(self.config_path)

        if not config_path.exists():
            logger.info(f"[Redis管理] 未找到配置文件，使用默认配置: {config}")
            return config

        try:
            parser = configparser.ConfigParser()
            parser.read(config_path, encoding='utf-8')

            if 'redis' in parser:
                section = parser['redis']
                if section.get('host'):
                    config['host'] = section['host']
                if section.get('port'):
                    config['port'] = int(section['port'])
                if section.get('password'):
                    config['password'] = section['password']
                if section.get('db'):
                    config['db'] = int(section['db'])
                if section.get('socket_timeout'):
                    config['socket_timeout'] = int(section['socket_timeout'])
                if section.get('socket_connect_timeout'):
                    config['socket_connect_timeout'] = int(section['socket_connect_timeout'])

            logger.info(f"[Redis管理] 配置加载成功: host={config['host']}, port={config['port']}, db={config['db']}")
        except Exception as e:
            logger.warning(f"[Redis管理] 配置读取失败，使用默认配置: {e}")

        return config

    def get_client(self) -> redis.Redis:
        """
        获取Redis客户端连接

        Returns:
            Redis客户端对象

        Raises:
            RedisConnectionError: 连接失败
        """
        if self._client is not None and self._connected:
            return self._client

        try:
            logger.info(f"[Redis管理] 连接Redis: {self.redis_config['host']}:{self.redis_config['port']}")
            self._client = redis.Redis(**self.redis_config)
            self._client.ping()
            self._connected = True
            logger.info("[Redis管理] Redis连接成功")
            return self._client
        except ConnectionError as e:
            logger.error(f"[Redis管理] Redis连接失败: {e}")
            self._connected = False
            raise RedisConnectionError(f"Redis连接失败: {e}") from e
        except RedisError as e:
            logger.error(f"[Redis管理] Redis操作失败: {e}")
            self._connected = False
            raise RedisConnectionError(f"Redis操作失败: {e}") from e

    def is_connected(self) -> bool:
        """
        检查Redis连接状态

        Returns:
            是否已连接
        """
        if self._client is None:
            return False
        try:
            self._client.ping()
            self._connected = True
            return True
        except RedisError:
            self._connected = False
            return False

    def test_connection(self) -> bool:
        """
        测试Redis连接

        Returns:
            连接是否成功
        """
        try:
            self.get_client()
            return True
        except RedisConnectionError:
            return False

    def _encode_value(self, value: Any) -> str:
        """
        编码值为JSON字符串

        Args:
            value: 要编码的值

        Returns:
            JSON字符串
        """
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.error(f"[Redis管理] JSON编码失败: {e}")
            raise RedisOperationError(f"数据编码失败: {e}") from e

    def _decode_value(self, value: Optional[str]) -> Any:
        """
        解码JSON字符串为Python对象

        Args:
            value: Redis存储的值

        Returns:
            解码后的Python对象
        """
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"[Redis管理] JSON解码失败: {e}, value={value}")
            raise RedisOperationError(f"数据解码失败: {e}") from e

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置键值对

        Args:
            key: 键名
            value: 值
            expire: 过期时间（秒）

        Returns:
            是否成功

        Raises:
            RedisConnectionError: 连接失败
            RedisOperationError: 操作失败
        """
        try:
            client = self.get_client()
            encoded_value = self._encode_value(value)
            if expire is not None:
                client.set(key, encoded_value, ex=expire)
            else:
                client.set(key, encoded_value)
            logger.debug(f"[Redis管理] 设置键: {key}, 过期时间: {expire}")
            return True
        except RedisConnectionError:
            raise
        except RedisError as e:
            logger.error(f"[Redis管理] 设置键失败: {key}, 错误: {e}")
            raise RedisOperationError(f"设置键失败: {e}") from e

    def get(self, key: str) -> Any:
        """
        获取键的值

        Args:
            key: 键名

        Returns:
            解码后的值，不存在返回None

        Raises:
            RedisConnectionError: 连接失败
            RedisOperationError: 操作失败
        """
        try:
            client = self.get_client()
            value = client.get(key)
            if value is None:
                logger.debug(f"[Redis管理] 键不存在: {key}")
                return None
            return self._decode_value(value)
        except RedisConnectionError:
            raise
        except RedisError as e:
            logger.error(f"[Redis管理] 获取键失败: {key}, 错误: {e}")
            raise RedisOperationError(f"获取键失败: {e}") from e

    def delete(self, key: str) -> int:
        """
        删除键

        Args:
            key: 键名

        Returns:
            删除的键数量

        Raises:
            RedisConnectionError: 连接失败
            RedisOperationError: 操作失败
        """
        try:
            client = self.get_client()
            count = client.delete(key)
            logger.debug(f"[Redis管理] 删除键: {key}, 数量: {count}")
            return count
        except RedisConnectionError:
            raise
        except RedisError as e:
            logger.error(f"[Redis管理] 删除键失败: {key}, 错误: {e}")
            raise RedisOperationError(f"删除键失败: {e}") from e

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 键名

        Returns:
            是否存在

        Raises:
            RedisConnectionError: 连接失败
            RedisOperationError: 操作失败
        """
        try:
            client = self.get_client()
            return client.exists(key) > 0
        except RedisConnectionError:
            raise
        except RedisError as e:
            logger.error(f"[Redis管理] 检查键存在失败: {key}, 错误: {e}")
            raise RedisOperationError(f"检查键存在失败: {e}") from e

    def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间

        Args:
            key: 键名
            seconds: 过期时间（秒）

        Returns:
            是否成功

        Raises:
            RedisConnectionError: 连接失败
            RedisOperationError: 操作失败
        """
        try:
            client = self.get_client()
            return client.expire(key, seconds)
        except RedisConnectionError:
            raise
        except RedisError as e:
            logger.error(f"[Redis管理] 设置过期时间失败: {key}, 错误: {e}")
            raise RedisOperationError(f"设置过期时间失败: {e}") from e

    def ttl(self, key: str) -> int:
        """
        获取键的剩余过期时间

        Args:
            key: 键名

        Returns:
            剩余时间（秒），-1表示永不过期，-2表示键不存在

        Raises:
            RedisConnectionError: 连接失败
            RedisOperationError: 操作失败
        """
        try:
            client = self.get_client()
            return client.ttl(key)
        except RedisConnectionError:
            raise
        except RedisError as e:
            logger.error(f"[Redis管理] 获取TTL失败: {key}, 错误: {e}")
            raise RedisOperationError(f"获取TTL失败: {e}") from e

    def set_task_input(self, task_type: str, task_id: str, data: Dict[str, Any],
                      expire: int = DEFAULT_EXPIRE_INPUT) -> bool:
        """
        设置任务输入数据

        Args:
            task_type: 任务类型（bazi/meihua）
            task_id: 任务ID
            data: 输入数据
            expire: 过期时间（秒）

        Returns:
            是否成功
        """
        key = f"{task_type}:input:{task_id}"
        return self.set(key, data, expire)

    def get_task_input(self, task_type: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务输入数据

        Args:
            task_type: 任务类型（bazi/meihua）
            task_id: 任务ID

        Returns:
            输入数据，不存在返回None
        """
        key = f"{task_type}:input:{task_id}"
        return self.get(key)

    def set_task_result(self, task_type: str, task_id: str, data: Dict[str, Any],
                        expire: int = DEFAULT_EXPIRE_RESULT) -> bool:
        """
        设置任务结果数据

        Args:
            task_type: 任务类型（bazi/meihua）
            task_id: 任务ID
            data: 结果数据
            expire: 过期时间（秒）

        Returns:
            是否成功
        """
        key = f"{task_type}:result:{task_id}"
        return self.set(key, data, expire)

    def get_task_result(self, task_type: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务结果数据

        Args:
            task_type: 任务类型（bazi/meihua）
            task_id: 任务ID

        Returns:
            结果数据，不存在返回None
        """
        key = f"{task_type}:result:{task_id}"
        return self.get(key)

    def set_task_status(self, task_type: str, task_id: str, status: str,
                        expire: int = DEFAULT_EXPIRE_INPUT) -> bool:
        """
        设置任务状态

        Args:
            task_type: 任务类型（bazi/meihua）
            task_id: 任务ID
            status: 状态（pending/analyzing/completed/failed）
            expire: 过期时间（秒）

        Returns:
            是否成功
        """
        key = f"{task_type}:status:{task_id}"
        return self.set(key, status, expire)

    def get_task_status(self, task_type: str, task_id: str) -> Optional[str]:
        """
        获取任务状态

        Args:
            task_type: 任务类型（bazi/meihua）
            task_id: 任务ID

        Returns:
            状态，不存在返回None
        """
        key = f"{task_type}:status:{task_id}"
        return self.get(key)

    def delete_task(self, task_type: str, task_id: str) -> int:
        """
        删除任务相关的所有键

        Args:
            task_type: 任务类型（bazi/meihua）
            task_id: 任务ID

        Returns:
            删除的键数量
        """
        keys = [
            f"{task_type}:input:{task_id}",
            f"{task_type}:result:{task_id}",
            f"{task_type}:status:{task_id}"
        ]
        try:
            client = self.get_client()
            count = client.delete(*keys)
            logger.debug(f"[Redis管理] 删除任务: {task_type}:{task_id}, 数量: {count}")
            return count
        except RedisConnectionError:
            raise
        except RedisError as e:
            logger.error(f"[Redis管理] 删除任务失败: {task_type}:{task_id}, 错误: {e}")
            raise RedisOperationError(f"删除任务失败: {e}") from e

    def scan_keys(self, pattern: str, count: int = 100) -> list:
        """
        扫描匹配模式的键

        Args:
            pattern: 键的匹配模式
            count: 每次扫描的数量

        Returns:
            匹配的键列表
        """
        try:
            client = self.get_client()
            keys = []
            for key in client.scan_iter(pattern=pattern, count=count):
                keys.append(key)
            return keys
        except RedisConnectionError:
            raise
        except RedisError as e:
            logger.error(f"[Redis管理] 扫描键失败: {pattern}, 错误: {e}")
            raise RedisOperationError(f"扫描键失败: {e}") from e


_default_redis_manager = None


def get_redis_manager(config_path: str = None) -> RedisManager:
    """
    获取默认的Redis管理器实例（单例模式）

    Args:
        config_path: 配置文件路径

    Returns:
        RedisManager实例
    """
    global _default_redis_manager
    if _default_redis_manager is None or config_path:
        _default_redis_manager = RedisManager(config_path)
    return _default_redis_manager