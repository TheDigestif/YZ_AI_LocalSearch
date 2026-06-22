"""设置窗口 UI - 开源版"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QGroupBox, QSpacerItem, QSizePolicy,
    QMessageBox, QTextEdit, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt


class SettingsWindow(QDialog):
    """设置窗口类（开源版）"""

    def __init__(self, parent, config, log_manager, service_manager=None):
        super().__init__(parent)

        self.config = config
        self.log = log_manager
        self.service_manager = service_manager

        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)

        # 设置样式
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-size: 13px; }
            QLineEdit {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 4px 8px; font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #89b4fa; }
            QLineEdit:disabled { background-color: #45475a; color: #6c7086; }
            QPushButton {
                background-color: #45475a; color: #cdd6f4;
                border: none; border-radius: 6px;
                padding: 10px 20px; font-size: 13px; font-weight: 500;
            }
            QPushButton:hover { background-color: #585b70; }
            QCheckBox {
                color: #cdd6f4; font-size: 13px; spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px; height: 18px; border-radius: 4px;
                border: 2px solid #45475a; background-color: #313244;
            }
            QCheckBox::indicator:checked {
                background-color: #89b4fa; border-color: #89b4fa;
            }
            QCheckBox::indicator:hover { border-color: #89b4fa; }
            QGroupBox {
                color: #cdd6f4; border: 1px solid #45475a;
                border-radius: 10px; margin-top: 30px;
                font-size: 15px; font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 12px; top: 8px;
            }
        """)

        self._create_widgets()

        # 保存原始代理设置
        self._orig_proxy_enabled = self.config.proxy_enabled
        self._orig_proxy_address = self.config.proxy_address

        # 居中显示
        self.adjustSize()
        parent_geo = parent.geometry()
        x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
        y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
        self.move(x, y)

    def _create_widgets(self):
        """创建 UI 组件"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # ========== 常规设置 ==========
        general_group = QGroupBox("常规设置")
        general_layout = QVBoxLayout(general_group)
        general_layout.setContentsMargins(16, 16, 16, 16)
        general_layout.setSpacing(10)

        self.autostart_cb = QCheckBox("开机自动启动")
        self.autostart_cb.setChecked(self.config.autostart)
        general_layout.addWidget(self.autostart_cb)

        self.minimize_on_close_cb = QCheckBox("关闭时最小化到托盘")
        self.minimize_on_close_cb.setChecked(self.config.minimize_on_close)
        general_layout.addWidget(self.minimize_on_close_cb)

        self.start_services_cb = QCheckBox("启动时自动运行服务")
        self.start_services_cb.setChecked(self.config.start_services_on_launch)
        general_layout.addWidget(self.start_services_cb)

        main_layout.addWidget(general_group)

        # ========== 网络设置 ==========
        network_group = QGroupBox("网络设置")
        network_layout = QVBoxLayout(network_group)
        network_layout.setContentsMargins(16, 16, 16, 16)
        network_layout.setSpacing(8)

        searxng_port_layout = QHBoxLayout()
        searxng_port_layout.setSpacing(8)
        searxng_port_label = QLabel("搜索引擎端口")
        searxng_port_label.setFixedWidth(90)
        searxng_port_layout.addWidget(searxng_port_label)
        self.searxng_port_entry = QLineEdit()
        self.searxng_port_entry.setText(str(self.config.searxng_port))
        self.searxng_port_entry.setFixedWidth(80)
        searxng_port_layout.addWidget(self.searxng_port_entry)
        searxng_port_layout.addStretch()
        network_layout.addLayout(searxng_port_layout)

        mcp_port_layout = QHBoxLayout()
        mcp_port_layout.setSpacing(8)
        mcp_port_label = QLabel("MCP服务端口")
        mcp_port_label.setFixedWidth(90)
        mcp_port_layout.addWidget(mcp_port_label)
        self.mcp_port_entry = QLineEdit()
        self.mcp_port_entry.setText(str(self.config.mcp_port))
        self.mcp_port_entry.setFixedWidth(80)
        mcp_port_layout.addWidget(self.mcp_port_entry)
        mcp_port_layout.addStretch()
        network_layout.addLayout(mcp_port_layout)

        main_layout.addWidget(network_group)

        # ========== 代理设置 ==========
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QVBoxLayout(proxy_group)
        proxy_layout.setContentsMargins(16, 16, 16, 16)
        proxy_layout.setSpacing(8)

        self.proxy_cb = QCheckBox("启用代理")
        self.proxy_cb.setChecked(self.config.proxy_enabled)
        self.proxy_cb.stateChanged.connect(self._on_proxy_toggle)
        proxy_layout.addWidget(self.proxy_cb)

        proxy_addr_layout = QHBoxLayout()
        proxy_addr_layout.setSpacing(8)
        proxy_addr_label = QLabel("代理地址")
        proxy_addr_label.setFixedWidth(90)
        proxy_addr_layout.addWidget(proxy_addr_label)
        self.proxy_entry = QLineEdit()
        self.proxy_entry.setText(self.config.proxy_address or "http://127.0.0.1:7890")
        self.proxy_entry.setPlaceholderText("http://127.0.0.1:7890")
        proxy_addr_layout.addWidget(self.proxy_entry)
        proxy_layout.addLayout(proxy_addr_layout)

        main_layout.addWidget(proxy_group)

        # ========== 免责声明 ==========
        disclaimer_row = QHBoxLayout()
        disclaimer_row.addStretch()

        self.btn_disclaimer = QPushButton("查看免责声明")
        self.btn_disclaimer.setMinimumHeight(28)
        self.btn_disclaimer.setStyleSheet("""
            QPushButton {
                background: transparent; color: #6c7086;
                border: none; font-size: 12px; padding: 4px 8px;
            }
            QPushButton:hover { color: #89b4fa; }
        """)
        self.btn_disclaimer.clicked.connect(self._show_disclaimer)
        disclaimer_row.addWidget(self.btn_disclaimer)

        main_layout.addLayout(disclaimer_row)
        main_layout.addSpacing(8)

        # ========== 按钮区域 ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setMinimumWidth(70)
        self.btn_cancel.setMinimumHeight(34)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #585b70; color: #cdd6f4;
                border-radius: 6px; padding: 8px 16px;
            }
            QPushButton:hover { background-color: #6c7086; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("保存设置")
        self.btn_save.setMinimumWidth(90)
        self.btn_save.setMinimumHeight(34)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border-radius: 6px; padding: 8px 16px; font-weight: 500;
            }
            QPushButton:hover { background-color: #b4befe; }
        """)
        self.btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)

        self._on_proxy_toggle(self.proxy_cb.isChecked())

    def _on_proxy_toggle(self, state):
        enabled = state == Qt.Checked
        self.proxy_entry.setEnabled(enabled)

    def _on_save(self):
        """保存设置"""
        # 端口配置
        try:
            searxng_port = int(self.searxng_port_entry.text())
            mcp_port = int(self.mcp_port_entry.text())
            if searxng_port <= 0 or searxng_port > 65535 or mcp_port <= 0 or mcp_port > 65535:
                raise ValueError("端口号无效")
            if searxng_port == mcp_port:
                raise ValueError("搜索引擎端口和 MCP 端口不能相同")
        except ValueError as e:
            QMessageBox.warning(self, "参数错误", f"端口设置无效: {e}")
            return

        # 检查是否需要重启服务
        need_restart = False
        if self.service_manager:
            if (searxng_port != self.config.searxng_port or
                mcp_port != self.config.mcp_port):
                need_restart = True

        # 保存配置
        self.config.searxng_port = searxng_port
        self.config.mcp_port = mcp_port
        self.config.autostart = self.autostart_cb.isChecked()
        self.config.minimize_on_close = self.minimize_on_close_cb.isChecked()
        self.config.start_services_on_launch = self.start_services_cb.isChecked()
        self.config.proxy_enabled = self.proxy_cb.isChecked()
        self.config.proxy_address = self.proxy_entry.text() if self.proxy_cb.isChecked() else ""

        # 保存到配置文件
        self.config.save()

        # 如果服务在运行且端口有变化，提示重启
        if need_restart and self.service_manager:
            running = (self.service_manager.is_searxng_running() or
                      self.service_manager.is_mcp_running())
            if running:
                reply = QMessageBox.question(
                    self, "重启服务",
                    "端口设置已更改，需要重启服务才能生效。\n是否立即重启？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.service_manager.restart_all()

        self.accept()

    def _show_disclaimer(self):
        """显示免责声明"""
        disclaimer_text = """
<h2 style="color: #89b4fa; text-align: center;">云智AI本地搜 免责声明</h2>
<p style="color: #6c7086; text-align: center; font-size: 11px;">最后更新日期：2026年6月22日 | 版本：v3.3 开源版</p>
<hr style="background-color: #45475a; border: none; height: 1px;">

<h3 style="color: #a6e3a1;">第一章 总则</h3>

<p style="color: #cdd6f4; line-height: 1.8;">
<b>第一条 软件性质</b><br>
云智AI本地搜（以下简称"本软件"）是一款本地化互联网信息检索工具，为用户提供便捷的多搜索引擎查询入口。本软件为开源软件，遵循 MIT 许可证发布。
</p>

<p style="color: #cdd6f4; line-height: 1.8;">
<b>第二条 工具属性</b><br>
本软件仅作为信息检索工具，其功能限于向用户指定的搜索引擎发送查询请求并展示返回结果。本软件自身不生成、不存储、不修改任何搜索结果内容。
</p>

<h3 style="color: #a6e3a1;">第二章 用户责任</h3>

<p style="color: #cdd6f4; line-height: 1.8;">
<b>第三条 合法使用义务</b><br>
用户承诺使用本软件进行的所有搜索活动均符合中华人民共和国法律法规及用户所在地的相关法律规定。用户不得利用本软件搜索、获取、传播违法信息或从事任何违法违规活动。
</p>

<p style="color: #cdd6f4; line-height: 1.8;">
<b>第四条 使用风险自担</b><br>
用户使用本软件的一切风险和后果由用户自行承担。本软件开发者（云感数字科技）不对用户使用本软件所产生的任何直接或间接损失承担责任。
</p>

<h3 style="color: #a6e3a1;">第三章 第三方服务免责</h3>

<p style="color: #cdd6f4; line-height: 1.8;">
<b>第五条 搜索引擎服务</b><br>
本软件的正常运行依赖于第三方搜索引擎服务的可用性。开发者与各搜索引擎服务提供者不存在合作关系、代理关系或授权关系。搜索引擎服务的可用性、准确性、合法性由相应服务提供者独立负责。
</p>

<p style="color: #cdd6f4; line-height: 1.8;">
<b>第六条 搜索结果内容</b><br>
本软件呈现的搜索结果内容完全来源于第三方搜索引擎，开发者不对搜索结果的真实性、准确性、合法性、完整性、时效性承担任何责任。用户应自行判断并甄别搜索结果信息。
</p>

<h3 style="color: #a6e3a1;">第四章 免责条款</h3>

<p style="color: #cdd6f4; line-height: 1.8;">
<b>第七条 无担保声明</b><br>
本软件按"现状"提供，不提供任何形式的明示或默示担保，包括但不限于适销性、特定用途适用性和非侵权的担保。
</p>

<p style="color: #cdd6f4; line-height: 1.8;">
<b>第八条 责任限制</b><br>
在任何情况下，开发者对因使用本软件产生的任何索赔、损害或其他责任不承担责任，无论是基于合同、侵权或其他法律理论。
</p>

<hr style="background-color: #45475a; border: none; height: 1px;">
<p style="color: #6c7086; text-align: center; font-size: 11px;">
本免责声明的最终解释权归云感数字科技所有。<br>
如有疑问，请访问 https://www.yungantech.com 或通过 GitHub Issues 联系我们。
</p>
"""

        dialog = QDialog(self)
        dialog.setWindowTitle("免责声明")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e2e; border: none;
            }
            QScrollBar:vertical {
                background: #313244; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #45475a; border-radius: 5px; min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)

        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        text_widget.setHtml(disclaimer_text)
        text_widget.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e; border: none;
                color: #cdd6f4; font-size: 13px;
            }
        """)
        content_layout.addWidget(text_widget)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        close_btn = QPushButton("我已了解")
        close_btn.setMinimumHeight(36)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border-radius: 6px; padding: 10px 24px;
                font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { background-color: #b4befe; }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dialog.exec_()
