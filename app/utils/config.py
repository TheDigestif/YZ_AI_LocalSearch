"""配置管理模块"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
import yaml

# 项目根目录（兼容PyInstaller打包）
if getattr(sys, 'frozen', False):
    # PyInstaller打包后，使用exe所在目录
    PROJECT_ROOT = Path(sys.executable).parent
    CONFIG_DIR = PROJECT_ROOT / "config"
    SEARXNG_SETTINGS = CONFIG_DIR / "settings.yml"  # SearXNG从cwd/config加载
else:
    # 开发/发布环境 - 自动检测项目根目录（config.py 在 app/utils/ 下）
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    CONFIG_DIR = PROJECT_ROOT / "config"
    SEARXNG_SETTINGS = CONFIG_DIR / "settings.yml"

CONFIG_FILE = CONFIG_DIR / "app_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "searxng_port": 18888,  # 使用更不常见的端口避免冲突
    "mcp_port": 19000,      # 使用更不常见的端口避免冲突
    "proxy_enabled": False,  # 默认不启用代理
    "proxy_address": "",
    "autostart": False,
    "minimize_on_close": False,  # 默认关闭时直接退出
    "start_services_on_launch": True,  # 启动时自动运行服务
}


class Config:
    """配置管理类"""

    def __init__(self):
        self.config_dir = CONFIG_DIR  # 添加配置目录属性
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                # 合并默认配置（处理新增配置项）
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self._config:
                        self._config[key] = value
            except Exception as e:
                print(f"加载配置失败: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save()
        return self._config

    def save(self) -> bool:
        """保存配置文件"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)

            # 同步代理设置到 SearXNG settings.yml
            self._sync_proxy_to_searxng()

            # 同步端口设置到 SearXNG settings.yml
            self._sync_port_to_searxng()

            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def _sync_proxy_to_searxng(self) -> None:
        """同步代理设置到 SearXNG settings.yml"""
        try:
            if not SEARXNG_SETTINGS.exists():
                print(f"SearXNG settings.yml 不存在: {SEARXNG_SETTINGS}")
                return

            # 读取 settings.yml
            with open(SEARXNG_SETTINGS, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f)

            if not settings:
                settings = {}

            # 确保 outgoing 节点存在
            if 'outgoing' not in settings:
                settings['outgoing'] = {}

            # 更新代理配置
            proxy_enabled = self._config.get("proxy_enabled", False)
            proxy_address = self._config.get("proxy_address", "")

            if proxy_enabled and proxy_address:
                # 启用代理：设置代理地址（字典格式，分别指定http和https）
                settings['outgoing']['proxies'] = {
                    'http': proxy_address,
                    'https': proxy_address
                }
                print(f"已启用代理: {proxy_address}")
            else:
                # 禁用代理：移除代理配置
                if 'proxies' in settings['outgoing']:
                    del settings['outgoing']['proxies']
                print("已禁用代理")

            # 写回 settings.yml
            with open(SEARXNG_SETTINGS, 'w', encoding='utf-8') as f:
                yaml.dump(settings, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        except Exception as e:
            print(f"同步代理设置到 SearXNG 失败: {e}")

    def _sync_port_to_searxng(self) -> None:
        """同步端口设置到 SearXNG settings.yml"""
        try:
            if not SEARXNG_SETTINGS.exists():
                print(f"SearXNG settings.yml 不存在: {SEARXNG_SETTINGS}")
                return

            # 读取 settings.yml
            with open(SEARXNG_SETTINGS, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f)

            if not settings:
                settings = {}

            # 确保 server 节点存在
            if 'server' not in settings:
                settings['server'] = {}

            # 更新端口配置
            searxng_port = self._config.get("searxng_port", 18888)
            settings['server']['port'] = searxng_port
            print(f"已设置 SearXNG 端口: {searxng_port}")

            # 写回 settings.yml
            with open(SEARXNG_SETTINGS, 'w', encoding='utf-8') as f:
                yaml.dump(settings, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        except Exception as e:
            print(f"同步端口设置到 SearXNG 失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self._config[key] = value

    def update(self, config: Dict[str, Any]) -> None:
        """批量更新配置"""
        self._config.update(config)

    @property
    def all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    # 便捷属性
    @property
    def searxng_port(self) -> int:
        return self._config.get("searxng_port", 18888)

    @property
    def mcp_port(self) -> int:
        return self._config.get("mcp_port", 19000)

    @property
    def proxy_enabled(self) -> bool:
        return self._config.get("proxy_enabled", False)

    @property
    def proxy_address(self) -> str:
        return self._config.get("proxy_address", "")

    @property
    def autostart(self) -> bool:
        return self._config.get("autostart", False)

    @property
    def minimize_to_tray(self) -> bool:
        return self._config.get("minimize_to_tray", True)

    @property
    def minimize_on_close(self) -> bool:
        return self._config.get("minimize_on_close", False)

    @property
    def start_services_on_launch(self) -> bool:
        return self._config.get("start_services_on_launch", True)


# 全局配置实例
config = Config()