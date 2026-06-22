#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云智AI本地搜 - 主窗口 UI (开源版)

设计理念：玻璃态仪表盘风格
- 深色渐变背景，营造层次感
- 卡片采用玻璃态效果（半透明+边框光晕）
- 状态指示器动态脉冲效果

开源地址：
- GitHub: https://github.com/TheDigestif/YZ_AI_LocalSearch
- Gitee: https://gitee.com/yungantech/YZ_AI_LocalSearch

Powered by 云感数字科技 (https://www.yungantech.com)
"""

import sys
import os
import threading
import pyperclip
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
    QGraphicsBlurEffect, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath, QFontDatabase

from app.services.service_manager import ServiceManager
from app.utils.config import config
from app.utils.logger import log_manager

# 获取资源目录路径
if getattr(sys, 'frozen', False):
    RESOURCE_DIR = Path(sys._MEIPASS) / "app" / "resources"
else:
    RESOURCE_DIR = Path(__file__).parent.parent / "resources"

ICONS_DIR = RESOURCE_DIR / "icons"


# ========== Catppuccin Mocha 配色定义 ==========
class Colors:
    """配色体系 - Catppuccin Mocha"""
    BG_BASE = "#1e1e2e"
    BG_DEEP = "#181825"
    CARD_BG = "#313244"
    CARD_BORDER = "#45475a"
    CARD_GLOW = "#585b70"
    TEXT_PRIMARY = "#cdd6f4"
    TEXT_SECONDARY = "#a6adc8"
    TEXT_MUTED = "#6c7086"
    STATUS_ON = "#a6e3a1"
    STATUS_OFF = "#f38ba8"
    STATUS_WARN = "#f9e2af"
    ACCENT_BLUE = "#89b4fa"
    ACCENT_TEAL = "#94e2d5"
    ACCENT_GREEN = "#a6e3a1"
    ACCENT_RED = "#f38ba8"


class StatusSignaler(QObject):
    """状态信号发射器"""
    status_updated = pyqtSignal(bool, bool, bool)
    toggle_complete = pyqtSignal()


class PulseIndicator(QWidget):
    """脉冲状态指示器 - 运行时有呼吸光晕"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pulse_phase = 0
        self._running = False
        self._color = QColor(Colors.TEXT_MUTED)
        self.setFixedSize(14, 14)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(40)

    def set_state(self, running: bool):
        self._running = running
        self._color = QColor(Colors.STATUS_ON if running else Colors.TEXT_MUTED)

    def _animate(self):
        if self._running:
            self._pulse_phase = (self._pulse_phase + 6) % 360
        else:
            self._pulse_phase = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self._running:
            intensity = 0.3 + 0.4 * (abs((self._pulse_phase % 180) - 90) / 90.0)
            glow = QColor(self._color)
            glow.setAlphaF(intensity * 0.6)
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(-2, -2, 18, 18)
            core = QColor(self._color)
            core.setAlphaF(0.9 + intensity * 0.1)
            painter.setBrush(QBrush(core))
            painter.drawEllipse(1, 1, 12, 12)
        else:
            painter.setBrush(QBrush(QColor(Colors.TEXT_MUTED)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(3, 3, 8, 8)


class GlassCard(QFrame):
    """玻璃态卡片 - 半透明质感"""

    def __init__(self, title: str, info: str, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(49, 50, 68, 180);
                border: 1px solid rgba(69, 71, 90, 120);
                border-radius: 10px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        self.indicator = PulseIndicator(self)
        layout.addWidget(self.indicator)

        content = QVBoxLayout()
        content.setSpacing(3)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 14px; font-weight: 600;
                color: {Colors.TEXT_PRIMARY}; background: transparent;
            }}
        """)
        content.addWidget(self.title_lbl)

        self.status_lbl = QLabel("检测中...")
        self.status_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 12px; color: {Colors.TEXT_SECONDARY}; background: transparent;
            }}
        """)
        content.addWidget(self.status_lbl)
        layout.addLayout(content, 1)

        self.info_lbl = QLabel(info)
        self.info_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-family: 'Segoe UI Mono', 'Consolas', monospace;
                color: {Colors.TEXT_MUTED}; background: transparent;
                padding: 3px 6px;
            }}
        """)
        layout.addWidget(self.info_lbl)

    def sizeHint(self):
        return QSize(100, 52)

    def set_status(self, running: bool, text: str = None):
        self.indicator.set_state(running)
        status_text = text or ("运行中" if running else "已停止")
        color = Colors.STATUS_ON if running else Colors.TEXT_MUTED
        self.status_lbl.setText(status_text)
        self.status_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 12px; color: {color}; background: transparent;
            }}
        """)


class ModernButton(QPushButton):
    """现代质感按钮"""

    def __init__(self, text: str, style_type: str = "default", parent=None):
        super().__init__(text, parent)
        self._style_type = style_type
        self._is_active = False
        self.setMinimumHeight(38)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh_style()

    def set_active(self, active: bool):
        self._is_active = active
        self._refresh_style()

    def _refresh_style(self):
        if self._style_type == "primary":
            if self._is_active:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #f38ba8, stop:1 #eba0ac);
                        color: {Colors.BG_BASE}; border: none; border-radius: 8px;
                        font-size: 13px; font-weight: 600; padding: 10px 16px;
                    }}
                    QPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #eba0ac, stop:1 #f38ba8);
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #a6e3a1, stop:1 #94e2d5);
                        color: {Colors.BG_BASE}; border: none; border-radius: 8px;
                        font-size: 13px; font-weight: 600; padding: 10px 16px;
                    }}
                    QPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #94e2d5, stop:1 #a6e3a1);
                    }}
                """)
        elif self._style_type == "secondary":
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(69, 71, 90, 150);
                    color: {Colors.TEXT_PRIMARY};
                    border: 1px solid rgba(88, 91, 112, 100);
                    border-radius: 8px; font-size: 13px; font-weight: 500;
                    padding: 10px 16px;
                }}
                QPushButton:hover {{
                    background-color: rgba(88, 91, 112, 180);
                    border-color: rgba(166, 233, 161, 80);
                }}
            """)
        elif self._style_type == "ghost":
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {Colors.TEXT_SECONDARY};
                    border: 1px solid rgba(108, 112, 134, 80);
                    border-radius: 8px; font-size: 12px; font-weight: 500;
                    padding: 8px 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba(49, 50, 68, 100);
                    color: {Colors.TEXT_PRIMARY};
                }}
            """)


class MainWindow(QMainWindow):
    """主窗口 - 开源版"""

    VERSION = "3.3"

    def __init__(self):
        super().__init__()

        self.signaler = StatusSignaler()
        self.signaler.status_updated.connect(self._update_status)
        self.signaler.toggle_complete.connect(self._enable_toggle)

        self.setWindowTitle("云智AI本地搜")
        self.setMinimumWidth(400)

        # 设置窗口图标
        icon_path = ICONS_DIR / "app_icon.png"
        if icon_path.exists():
            from PyQt5.QtGui import QIcon
            self.setWindowIcon(QIcon(str(icon_path)))

        # 深色渐变背景
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_BASE}, stop:1 {Colors.BG_DEEP});
            }}
        """)

        # 服务管理器
        self.service_manager = ServiceManager(config, log_manager)
        self.service_manager.set_status_callback(self._on_status_change)

        # 构建界面
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 18, 20, 16)
        main_layout.setSpacing(0)

        # === 标题区 ===
        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        icon_lbl = QLabel("⌕")
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 22px; font-weight: 300;
                color: {Colors.ACCENT_TEAL}; background: transparent;
            }}
        """)
        title_row.addWidget(icon_lbl)

        title_lbl = QLabel("云智 AI 本地搜")
        title_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 17px; font-weight: 600;
                color: {Colors.TEXT_PRIMARY}; background: transparent;
            }}
        """)
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        # 开源版标记
        oss_label = QLabel("开源版")
        oss_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px; font-weight: 500;
                color: {Colors.ACCENT_TEAL}; background: transparent;
                border: 1px solid {Colors.ACCENT_TEAL};
                border-radius: 4px; padding: 2px 8px;
            }}
        """)
        title_row.addWidget(oss_label)

        main_layout.addLayout(title_row)
        main_layout.addSpacing(12)

        # === 分隔线 ===
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: rgba(108, 112, 134, 60);")
        main_layout.addWidget(sep)
        main_layout.addSpacing(14)

        # === 状态卡片 ===
        self.searxng_card = GlassCard("搜索引擎服务", f":{config.searxng_port}")
        main_layout.addWidget(self.searxng_card)
        main_layout.addSpacing(10)

        self.mcp_card = GlassCard("MCP 服务", f":{config.mcp_port}")
        main_layout.addWidget(self.mcp_card)
        main_layout.addSpacing(10)

        self.proxy_card = GlassCard("代理连接", config.proxy_address or "未配置")
        main_layout.addWidget(self.proxy_card)
        main_layout.addSpacing(16)

        # === 按钮区 ===
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_toggle = ModernButton("启动服务", "primary")
        self.btn_toggle.clicked.connect(self._toggle)
        btn_row.addWidget(self.btn_toggle, 1)

        self.btn_copy = ModernButton("复制配置", "secondary")
        self.btn_copy.clicked.connect(self._copy_config)
        btn_row.addWidget(self.btn_copy, 1)

        main_layout.addLayout(btn_row)
        main_layout.addSpacing(10)

        # === 设置按钮行 ===
        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(10)

        self.btn_settings = ModernButton("设置", "ghost")
        self.btn_settings.clicked.connect(self._open_settings)
        btn_row2.addWidget(self.btn_settings)

        main_layout.addLayout(btn_row2)
        main_layout.addSpacing(12)

        # === 公司信息 ===
        company_layout = QVBoxLayout()
        company_layout.setSpacing(2)

        company_row = QHBoxLayout()
        company_row.addStretch()
        company_btn = QPushButton("Powered by 云感数字科技")
        company_btn.setMinimumHeight(24)
        company_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_MUTED};
                border: none; font-size: 11px; padding: 2px 8px;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_TEAL};
            }}
        """)
        company_btn.setCursor(Qt.PointingHandCursor)
        company_btn.clicked.connect(lambda: os.startfile("https://www.yungantech.com"))
        company_row.addWidget(company_btn)
        company_row.addStretch()
        company_layout.addLayout(company_row)

        # 官网网址
        url_row = QHBoxLayout()
        url_row.addStretch()
        website_lbl = QLabel("https://www.yungantech.com")
        website_lbl.setStyleSheet(f"""
            QLabel {{
                background: transparent; color: {Colors.TEXT_MUTED};
                font-size: 10px; padding: 0px 8px;
            }}
        """)
        url_row.addWidget(website_lbl)
        url_row.addStretch()
        company_layout.addLayout(url_row)

        main_layout.addLayout(company_layout)

        # === 版本脚标 ===
        main_layout.addSpacing(4)
        version_lbl = QLabel(f"v{self.VERSION} 开源版")
        version_lbl.setAlignment(Qt.AlignRight)
        version_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 10px; font-weight: 400;
                color: {Colors.TEXT_MUTED}; background: transparent;
            }}
        """)
        main_layout.addWidget(version_lbl)

        # 状态追踪
        self._searxng_on = False
        self._mcp_on = False
        self._is_operating = False
        self._operation_complete = False

        # 定时检测
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_status)
        self.timer.start(3000)
        self._check_status()

        # 自动启动服务
        if config.start_services_on_launch:
            QTimer.singleShot(500, self._auto_start)

    def _auto_start(self):
        """自动启动服务"""
        threading.Thread(target=self.service_manager.start_all, daemon=True).start()

    def _check_status(self):
        threading.Thread(target=self._check_thread, daemon=True).start()

    def _check_thread(self):
        s_on = self.service_manager.is_searxng_running()
        m_on = self.service_manager.is_mcp_running()
        p_ok = config.proxy_enabled and self.service_manager.check_proxy()
        self.signaler.status_updated.emit(s_on, m_on, p_ok)

    def _update_status(self, s_on, m_on, p_ok):
        self._searxng_on = s_on
        self._mcp_on = m_on

        self.searxng_card.set_status(s_on)
        self.mcp_card.set_status(m_on)

        if config.proxy_enabled:
            self.proxy_card.set_status(p_ok, "已连接" if p_ok else "连接失败")
        else:
            self.proxy_card.set_status(False, "未启用")

        if self._operation_complete:
            self._is_operating = False
            self._operation_complete = False
            all_on = s_on and m_on
            self.btn_toggle.set_active(all_on)
            self.btn_toggle.setText("停止服务" if all_on else "启动服务")
            self.btn_toggle.setEnabled(True)
        elif not self._is_operating:
            all_on = s_on and m_on
            self.btn_toggle.set_active(all_on)
            self.btn_toggle.setText("停止服务" if all_on else "启动服务")

    def _on_status_change(self):
        self._check_status()

    def _toggle(self):
        """启动/停止服务切换"""
        self.btn_toggle.setEnabled(False)
        self._is_operating = True
        if self._searxng_on and self._mcp_on:
            self.btn_toggle.setText("停止中...")
            threading.Thread(target=self._stop_thread, daemon=True).start()
        else:
            self.btn_toggle.setText("启动中...")
            threading.Thread(target=self._start_thread, daemon=True).start()

    def _stop_thread(self):
        self.service_manager.stop_all()
        self.signaler.toggle_complete.emit()

    def _start_thread(self):
        self.service_manager.start_all()
        self.signaler.toggle_complete.emit()

    def _enable_toggle(self):
        self._operation_complete = True
        self._check_status()

    def _copy_config(self):
        url = f"http://localhost:{config.mcp_port}/sse"
        text = f"""请帮我配置本地搜索 MCP 服务。

服务名称：yz_local_search
连接方式：SSE
连接地址：{url}

MCP 配置（Claude Code - .claude.json 或 .mcp.json）：
```json
{{
  "mcpServers": {{
    "yz_local_search": {{
      "type": "sse",
      "url": "{url}"
    }}
  }}
}}
```

工具说明：
- web_search: 网页搜索，支持多引擎（Google、Bing、Baidu、Sogou等）
- image_search: 图片搜索
"""
        try:
            pyperclip.copy(text)
            self._show_copy_success_box()
        except:
            pass

    def _show_copy_success_box(self):
        """显示复制成功提示弹窗"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("配置已复制")
        dialog.setFixedSize(420, 200)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_BASE};
                border: 1px solid {Colors.CARD_BORDER};
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY}; font-size: 13px; line-height: 1.5;
            }}
            QPushButton {{
                background-color: {Colors.ACCENT_TEAL};
                color: {Colors.BG_BASE}; border: none; border-radius: 6px;
                padding: 10px 24px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #94e2d5; }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 20)
        layout.setSpacing(15)

        msg = QLabel("配置提示词已复制到剪贴板！\n\n粘贴至 Claude Code 或其他 AI 助手，按提示完成 MCP 配置。\n也可直接编辑 ~/.claude.json 手动配置。")
        msg.setAlignment(Qt.AlignCenter)
        msg.setWordWrap(True)
        layout.addWidget(msg)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        btn_ok.setFixedSize(100, 36)
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        dialog.exec_()

    def _open_settings(self):
        from app.ui.settings_window import SettingsWindow
        dialog = SettingsWindow(self, config, log_manager, self.service_manager)
        if dialog.exec_():
            self._refresh_display()

    def _refresh_display(self):
        """刷新界面显示（端口、代理等）"""
        self.searxng_card.info_lbl.setText(f":{config.searxng_port}")
        self.mcp_card.info_lbl.setText(f":{config.mcp_port}")

        if config.proxy_enabled and config.proxy_address:
            self.proxy_card.info_lbl.setText(config.proxy_address)
        else:
            self.proxy_card.info_lbl.setText("未配置")

        self._check_status()

    def _show_warning_box(self, title: str, message: str):
        """显示统一风格的警告弹窗"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(QMessageBox.Warning)
        msg.setStyleSheet("""
            QMessageBox { background-color: #1e1e2e; }
            QMessageBox QLabel { color: #cdd6f4; font-size: 13px; }
            QPushButton {
                background-color: #45475a; color: #cdd6f4;
                border-radius: 8px; padding: 10px 20px;
                min-width: 80px; font-weight: 500;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        msg.exec_()

    def closeEvent(self, e):
        if config.minimize_on_close:
            e.ignore()
            self.hide()
        else:
            self.timer.stop()
            e.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
