"""服务管理模块 - 管理SearXNG和MCP Server进程"""
import os
import sys
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import requests

# 项目根目录（兼容PyInstaller打包和开发环境）
if getattr(sys, 'frozen', False):
    # PyInstaller打包后
    PROJECT_ROOT = Path(sys.executable).parent
    SOURCE_DIR = PROJECT_ROOT
    PYTHON_EXE = PROJECT_ROOT / "python" / "python.exe"
    WEBAPP_PATH = PROJECT_ROOT / "python" / "Lib" / "site-packages" / "searx" / "webapp.py"
    MCP_SERVER_DIR = PROJECT_ROOT / "src" / "mcp_searxng"
    MCP_SERVER_PATH = MCP_SERVER_DIR / "server.py"
else:
    # 开发/发布环境 - 自动检测项目根目录（service_manager.py 在 app/services/ 下）
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    SOURCE_DIR = PROJECT_ROOT
    PYTHON_EXE = SOURCE_DIR / "python" / "python.exe"
    WEBAPP_PATH = SOURCE_DIR / "python" / "Lib" / "site-packages" / "searx" / "webapp.py"
    MCP_SERVER_DIR = SOURCE_DIR / "src" / "mcp_searxng"
    MCP_SERVER_PATH = MCP_SERVER_DIR / "server.py"


class ServiceManager:
    """服务管理类"""

    def __init__(self, config, log_manager):
        self.config = config
        self.log = log_manager

        # 进程句柄
        self._searxng_process: Optional[subprocess.Popen] = None
        self._mcp_process: Optional[subprocess.Popen] = None

        # 状态回调
        self._status_callback: Optional[Callable] = None

    def set_status_callback(self, callback: Callable) -> None:
        """设置状态变化回调"""
        self._status_callback = callback

    def _notify_status(self) -> None:
        """通知状态变化"""
        if self._status_callback:
            self._status_callback()

    # ========== SearXNG 管理 ==========

    def start_searxng(self) -> bool:
        """启动 SearXNG 服务"""
        if self.is_searxng_running():
            self.log.warning("SearXNG 已在运行")
            return True

        try:
            self.log.info("启动 SearXNG...")

            if not WEBAPP_PATH.exists():
                self.log.error(f"找不到 webapp.py: {WEBAPP_PATH}")
                return False

            if not PYTHON_EXE.exists():
                self.log.error(f"找不到 python.exe: {PYTHON_EXE}")
                return False

            cmd = [str(PYTHON_EXE), str(WEBAPP_PATH)]
            self.log.info(f"启动命令: {cmd}")

            # 创建环境变量，添加代理设置
            env = os.environ.copy()
            if self.config.proxy_enabled and self.config.proxy_address:
                proxy_addr = self.config.proxy_address
                env["HTTP_PROXY"] = proxy_addr
                env["HTTPS_PROXY"] = proxy_addr
                env["ALL_PROXY"] = proxy_addr
                self.log.info(f"已设置代理环境变量: {proxy_addr}")

            # 创建进程，隐藏窗口
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            self._searxng_process = subprocess.Popen(
                cmd,
                cwd=str(SOURCE_DIR),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env
            )

            # 等待服务启动
            for _ in range(30):
                time.sleep(1)
                if self.is_searxng_running():
                    self.log.success(f"SearXNG 就绪 (端口 {self.config.searxng_port})")
                    self._notify_status()
                    return True

            self.log.error("SearXNG 启动超时")
            return False

        except Exception as e:
            self.log.error(f"启动 SearXNG 失败: {e}")
            return False

    def stop_searxng(self) -> bool:
        """停止 SearXNG 服务"""
        try:
            self.log.info("停止 SearXNG...")

            if self._searxng_process:
                self._searxng_process.terminate()
                try:
                    self._searxng_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._searxng_process.kill()
                self._searxng_process = None

            port = self.config.searxng_port
            self._kill_process_by_port(port)

            if self.is_searxng_running():
                self.log.warning("SearXNG 可能仍在运行")
            else:
                self.log.success("SearXNG 已停止")

            self._notify_status()
            return True

        except Exception as e:
            self.log.error(f"停止 SearXNG 失败: {e}")
            return False

    def is_searxng_running(self) -> bool:
        """检查 SearXNG 是否运行"""
        return self._check_port(self.config.searxng_port)

    # ========== MCP Server 管理 ==========

    def start_mcp_server(self) -> bool:
        """启动 MCP Server"""
        if self.is_mcp_running():
            self.log.warning("MCP Server 已在运行")
            return True

        try:
            self.log.info("启动 MCP Server...")

            # 设置环境变量传递端口配置
            env = os.environ.copy()
            env["SEARXNG_PORT"] = str(self.config.searxng_port)
            env["SEARXNG_URL"] = f"http://localhost:{self.config.searxng_port}"
            env["MCP_PORT"] = str(self.config.mcp_port)

            # 优先使用 Python 直接运行 server.py
            if PYTHON_EXE.exists() and MCP_SERVER_PATH.exists():
                cmd = [str(PYTHON_EXE), str(MCP_SERVER_PATH)]
                self.log.info(f"使用源码启动 MCP: {cmd}")
            else:
                self.log.error("找不到 MCP 服务启动方式")
                return False

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            self._mcp_process = subprocess.Popen(
                cmd,
                cwd=str(SOURCE_DIR),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )

            # 等待服务启动
            for _ in range(10):
                time.sleep(1)
                if self.is_mcp_running():
                    self.log.success(f"MCP Server 就绪 (端口 {self.config.mcp_port})")
                    self._notify_status()
                    return True

            self.log.error("MCP Server 启动超时")
            return False

        except Exception as e:
            self.log.error(f"启动 MCP Server 失败: {e}")
            return False

    def stop_mcp_server(self) -> bool:
        """停止 MCP Server"""
        try:
            self.log.info("停止 MCP Server...")

            if self._mcp_process:
                self._mcp_process.terminate()
                try:
                    self._mcp_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._mcp_process.kill()
                self._mcp_process = None

            port = self.config.mcp_port
            self._kill_process_by_port(port)

            if self.is_mcp_running():
                self.log.warning("MCP Server 可能仍在运行")
            else:
                self.log.success("MCP Server 已停止")

            self._notify_status()
            return True

        except Exception as e:
            self.log.error(f"停止 MCP Server 失败: {e}")
            return False

    def is_mcp_running(self) -> bool:
        """检查 MCP Server 是否运行"""
        return self._check_port(self.config.mcp_port)

    # ========== 代理检测 ==========

    def check_proxy(self) -> bool:
        """检测代理是否可用"""
        if not self.config.proxy_enabled:
            return False

        proxy_address = self.config.proxy_address
        if not proxy_address:
            return False

        try:
            proxies = {
                "http": proxy_address,
                "https": proxy_address
            }
            response = requests.get(
                "https://www.google.com",
                proxies=proxies,
                timeout=3
            )
            return response.status_code in [200, 302]
        except Exception:
            return False

    # ========== 工具方法 ==========

    def _check_port(self, port: int) -> bool:
        """检查端口是否被监听"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                return result == 0
        except Exception:
            return False

    def _kill_process_by_port(self, port: int) -> bool:
        """通过端口查找并终止进程"""
        try:
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=5
            )

            lines = result.stdout.strip().split('\n')
            pids = set()

            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids.add(pid)

            if not pids:
                return False

            for pid in pids:
                subprocess.run(
                    ['taskkill', '/F', '/PID', pid],
                    capture_output=True,
                    timeout=5
                )
                self.log.info(f"终止进程 PID: {pid}")

            return True

        except Exception as e:
            self.log.error(f"查找/终止进程失败: {e}")
            return False

    def start_all(self) -> bool:
        """启动所有服务"""
        results = []
        results.append(self.start_searxng())
        results.append(self.start_mcp_server())
        return all(results)

    def stop_all(self) -> bool:
        """停止所有服务"""
        results = []
        results.append(self.stop_mcp_server())
        results.append(self.stop_searxng())
        return all(results)

    def restart_all(self) -> bool:
        """重启所有服务"""
        self.stop_all()
        time.sleep(2)
        return self.start_all()
