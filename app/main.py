#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云智AI本地搜 - 桌面应用入口 (PyQt5版本)

使用内嵌 Python 运行:
    python app/main.py

功能:
    - 管理 SearXNG 搜索引擎服务
    - 管理 MCP Server 服务
    - 提供可视化界面
    - 系统托盘支持
"""

import sys
import os

# 添加项目根目录到 Python 路径
if getattr(sys, 'frozen', False):
    # PyInstaller打包后，使用exe所在目录
    project_root = os.path.dirname(sys.executable)
else:
    # 开发环境
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, project_root)

# 设置Qt插件路径（必须在导入PyQt5之前）
if not getattr(sys, 'frozen', False):
    # 仅在非打包模式下设置（打包模式PyInstaller会自动处理）
    qt_plugins = os.path.join(project_root, "python", "Lib", "site-packages", "PyQt5", "Qt5", "plugins")
    if os.path.exists(qt_plugins):
        os.environ["QT_PLUGIN_PATH"] = qt_plugins

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer

from app.ui.main_window import MainWindow
from app.utils.config import config
from app.utils.logger import log_manager
from app.services.service_manager import ServiceManager


class TrayIcon:
    """系统托盘类 (PyQt5版本)"""

    def __init__(self, config, log_manager, service_manager, main_window):
        self.config = config
        self.log = log_manager
        self.service_manager = service_manager
        self.main_window = main_window

        # 创建托盘图标
        self.tray = QSystemTrayIcon(self._create_icon(), main_window)
        self.tray.setToolTip("云智AI本地搜")

        # 创建菜单
        menu = QMenu(main_window)

        show_action = QAction("显示主窗口", main_window)
        show_action.triggered.connect(self._on_show)
        menu.addAction(show_action)

        menu.addSeparator()

        start_action = QAction("启动服务", main_window)
        start_action.triggered.connect(self._on_start)
        menu.addAction(start_action)

        stop_action = QAction("停止服务", main_window)
        stop_action.triggered.connect(self._on_stop)
        menu.addAction(stop_action)

        menu.addSeparator()

        exit_action = QAction("退出", main_window)
        exit_action.triggered.connect(self._on_exit)
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)

        # 双击显示窗口
        self.tray.activated.connect(self._on_tray_activated)

    def _create_icon(self, running=True):
        """创建托盘图标"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制圆形背景
        color = QColor(29, 185, 84) if running else QColor(100, 100, 100)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)

        # 绘制搜索图标 (简化放大镜)
        painter.setPen(QColor(255, 255, 255))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(20, 16, 20, 20)  # 圆形部分

        # 手柄
        painter.drawLine(36, 32, 48, 44)

        painter.end()

        return QIcon(pixmap)

    def show(self):
        """显示托盘图标"""
        self.tray.show()

    def update_icon(self, running=True):
        """更新托盘图标状态"""
        self.tray.setIcon(self._create_icon(running))

    def _on_tray_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._on_show()

    def _on_show(self):
        """显示主窗口"""
        self.main_window.show()
        self.main_window.activateWindow()

    def _on_start(self):
        """启动服务"""
        self.service_manager.start_all()
        self.update_icon(True)

    def _on_stop(self):
        """停止服务"""
        self.service_manager.stop_all()
        self.update_icon(False)

    def _on_exit(self):
        """退出应用"""
        self.tray.hide()
        self.main_window.close()
        QApplication.quit()


def main():
    """应用入口"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 全局字体设置
    font = QFont()
    font.setFamily("Microsoft YaHei UI")
    font.setPointSize(10)
    app.setFont(font)

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 创建托盘图标（如果启用）
    tray = None
    if config.minimize_to_tray:
        tray = TrayIcon(config, log_manager, window.service_manager, window)
        tray.show()

    # 运行主循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()