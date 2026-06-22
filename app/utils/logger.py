"""日志工具模块"""
import logging
from datetime import datetime
from typing import Callable, List


class LogManager:
    """日志管理类"""

    def __init__(self, max_lines: int = 1000):
        self._logs: List[str] = []
        self._max_lines = max_lines
        self._callbacks: List[Callable[[str], None]] = []

    def add_callback(self, callback: Callable[[str], None]) -> None:
        """添加日志回调函数"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str], None]) -> None:
        """移除日志回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def log(self, message: str, level: str = "INFO") -> None:
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"

        self._logs.append(log_line)

        # 限制日志行数
        if len(self._logs) > self._max_lines:
            self._logs = self._logs[-self._max_lines:]

        # 触发回调
        for callback in self._callbacks:
            try:
                callback(log_line)
            except Exception:
                pass

    def info(self, message: str) -> None:
        self.log(message, "INFO")

    def error(self, message: str) -> None:
        self.log(message, "ERROR")

    def warning(self, message: str) -> None:
        self.log(message, "WARN")

    def success(self, message: str) -> None:
        self.log(message, "OK")

    def clear(self) -> None:
        """清空日志"""
        self._logs.clear()

    def get_logs(self) -> List[str]:
        """获取所有日志"""
        return self._logs.copy()

    def get_text(self) -> str:
        """获取日志文本"""
        return "\n".join(self._logs)


# 全局日志实例
log_manager = LogManager()