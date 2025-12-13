from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QTabWidget, QLineEdit,
    QTextEdit, QListWidget, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self) -> None:
        """初始化UI"""
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 基本设置标签页
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        
        # 主题选择
        theme_label = QLabel("主题:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.parent.theme_manager.get_available_themes())
        self.theme_combo.setCurrentText(self.parent.settings['appearance']['theme'])
        basic_layout.addRow(theme_label, self.theme_combo)
        
        # 字体大小
        font_size_label = QLabel("字体大小:")
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.parent.settings['appearance']['font_size'])
        basic_layout.addRow(font_size_label, self.font_size_spin)
        
        tab_widget.addTab(basic_tab, "外观")
        
        # 聊天设置标签页
        chat_tab = QWidget()
        chat_layout = QFormLayout(chat_tab)
        
        # 自动滚动
        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(self.parent.settings['chat']['auto_scroll'])
        chat_layout.addRow(self.auto_scroll_check)
        
        # 自动保存
        self.auto_save_check = QCheckBox("自动保存")
        self.auto_save_check.setChecked(self.parent.settings['chat']['auto_save'])
        chat_layout.addRow(self.auto_save_check)
        
        # 显示时间戳
        self.show_timestamp_check = QCheckBox("显示时间戳")
        self.show_timestamp_check.setChecked(self.parent.settings['chat']['show_timestamp'])
        chat_layout.addRow(self.show_timestamp_check)
        
        # 流式响应
        self.streaming_check = QCheckBox("流式响应")
        self.streaming_check.setChecked(self.parent.settings['chat']['streaming'])
        chat_layout.addRow(self.streaming_check)
        
        # 最大历史记录
        max_history_label = QLabel("最大历史记录:")
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(10, 1000)
        self.max_history_spin.setValue(self.parent.settings['chat']['max_history'])
        chat_layout.addRow(max_history_label, self.max_history_spin)
        
        tab_widget.addTab(chat_tab, "聊天")
        
        # 网络设置标签页
        network_tab = QWidget()
        network_layout = QFormLayout(network_tab)
        
        # 超时设置
        timeout_label = QLabel("超时时间(秒):")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setValue(self.parent.settings['network']['timeout'])
        network_layout.addRow(timeout_label, self.timeout_spin)
        
        # 重试次数
        retry_label = QLabel("重试次数:")
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 5)
        self.retry_spin.setValue(self.parent.settings['network']['retry_count'])
        network_layout.addRow(retry_label, self.retry_spin)
        
        # 使用代理
        self.use_proxy_check = QCheckBox("使用代理")
        self.use_proxy_check.setChecked(self.parent.settings['network']['use_proxy'])
        network_layout.addRow(self.use_proxy_check)
        
        tab_widget.addTab(network_tab, "网络")
        
        # 数据库设置标签页
        database_tab = QWidget()
        database_layout = QFormLayout(database_tab)
        
        # 启用数据库
        self.enable_db_check = QCheckBox("启用数据库")
        self.enable_db_check.setChecked(self.parent.settings['database']['enabled'])
        database_layout.addRow(self.enable_db_check)
        
        # 数据库类型
        db_type_label = QLabel("数据库类型:")
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(['mysql', 'postgresql', 'sqlite'])
        self.db_type_combo.setCurrentText(self.parent.settings['database']['type'])
        database_layout.addRow(db_type_label, self.db_type_combo)
        
        # 数据库主机
        db_host_label = QLabel("主机:")
        self.db_host_edit = QLineEdit()
        self.db_host_edit.setText(self.parent.settings['database']['host'])
        database_layout.addRow(db_host_label, self.db_host_edit)
        
        # 数据库端口
        db_port_label = QLabel("端口:")
        self.db_port_spin = QSpinBox()
        self.db_port_spin.setRange(1, 65535)
        self.db_port_spin.setValue(self.parent.settings['database']['port'])
        database_layout.addRow(db_port_label, self.db_port_spin)
        
        # 数据库名称
        db_name_label = QLabel("数据库名称:")
        self.db_name_edit = QLineEdit()
        self.db_name_edit.setText(self.parent.settings['database']['database'])
        database_layout.addRow(db_name_label, self.db_name_edit)
        
        # 数据库用户名
        db_user_label = QLabel("用户名:")
        self.db_user_edit = QLineEdit()
        self.db_user_edit.setText(self.parent.settings['database']['username'])
        database_layout.addRow(db_user_label, self.db_user_edit)
        
        # 数据库密码
        db_pass_label = QLabel("密码:")
        self.db_pass_edit = QLineEdit()
        self.db_pass_edit.setText(self.parent.settings['database']['password'])
        self.db_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        database_layout.addRow(db_pass_label, self.db_pass_edit)
        
        # 同步选项
        self.sync_on_startup_check = QCheckBox("启动时同步")
        self.sync_on_startup_check.setChecked(self.parent.settings['database']['sync_on_startup'])
        database_layout.addRow(self.sync_on_startup_check)
        
        # 同步间隔
        sync_interval_label = QLabel("同步间隔 (秒):")
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(60, 3600)  # 60-3600秒
        self.sync_interval_spin.setValue(self.parent.settings['database']['sync_interval'])
        database_layout.addRow(sync_interval_label, self.sync_interval_spin)
        
        # 选择性同步
        self.sync_config_check = QCheckBox("同步配置")
        self.sync_config_check.setChecked(self.parent.settings['database']['sync_config'])
        database_layout.addRow(self.sync_config_check)
        
        self.sync_conversations_check = QCheckBox("同步对话历史")
        self.sync_conversations_check.setChecked(self.parent.settings['database']['sync_conversations'])
        database_layout.addRow(self.sync_conversations_check)
        
        self.sync_memories_check = QCheckBox("同步记忆数据")
        self.sync_memories_check.setChecked(self.parent.settings['database']['sync_memories'])
        database_layout.addRow(self.sync_memories_check)
        
        # 测试连接按钮
        test_conn_btn = QPushButton("测试连接")
        test_conn_btn.clicked.connect(self._test_database_connection)
        database_layout.addRow(test_conn_btn)
        
        # 立即同步按钮
        sync_now_btn = QPushButton("立即同步")
        sync_now_btn.clicked.connect(self.parent.sync_database_now)
        database_layout.addRow(sync_now_btn)
        
        tab_widget.addTab(database_tab, "数据库")
        
        # 平台配置标签页
        platform_tab = QWidget()
        platform_layout = QVBoxLayout(platform_tab)
        
        # 平台列表
        platform_list_label = QLabel("可用平台:")
        platform_layout.addWidget(platform_list_label)
        
        self.platform_list = QListWidget()
        self.platform_list.addItems(self.parent.platforms.keys())
        self.platform_list.itemClicked.connect(self._on_platform_selected)
        platform_layout.addWidget(self.platform_list)
        
        # 平台详情编辑区域
        self.platform_details_group = QGroupBox("平台详情")
        details_layout = QFormLayout(self.platform_details_group)
        
        # 平台名称
        details_layout.addRow(QLabel("平台名称:"), QLabel(""))
        
        # API类型
        self.platform_api_type_edit = QLineEdit()
        details_layout.addRow(QLabel("API类型:"), self.platform_api_type_edit)
        
        # Base URL
        self.platform_base_url_edit = QLineEdit()
        details_layout.addRow(QLabel("Base URL:"), self.platform_base_url_edit)
        
        # 大模型列表
        self.platform_models_edit = QLineEdit()
        details_layout.addRow(QLabel("模型列表:\n(用逗号分隔)"), self.platform_models_edit)
        
        # API密钥
        self.platform_api_key_edit = QLineEdit()
        self.platform_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        details_layout.addRow(QLabel("API密钥:"), self.platform_api_key_edit)
        
        # API密钥提示
        self.platform_api_key_hint_edit = QLineEdit()
        details_layout.addRow(QLabel("API密钥提示:"), self.platform_api_key_hint_edit)
        
        # 启用状态
        self.platform_enabled_check = QCheckBox("启用")
        details_layout.addRow(self.platform_enabled_check)
        
        # 平台操作按钮
        platform_buttons = QHBoxLayout()
        
        # 添加平台按钮
        add_platform_btn = QPushButton("添加平台")
        add_platform_btn.clicked.connect(self._add_platform)
        platform_buttons.addWidget(add_platform_btn)
        
        # 删除平台按钮
        delete_platform_btn = QPushButton("删除平台")
        delete_platform_btn.clicked.connect(self._delete_platform)
        platform_buttons.addWidget(delete_platform_btn)
        
        # 保存平台按钮
        save_platform_btn = QPushButton("保存平台")
        save_platform_btn.clicked.connect(self._save_platform)
        platform_buttons.addWidget(save_platform_btn)
        
        details_layout.addRow(platform_buttons)
        platform_layout.addWidget(self.platform_details_group)
        
        tab_widget.addTab(platform_tab, "平台配置")
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 确定按钮
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # 重置按钮
        reset_button = QPushButton("重置")
        reset_button.clicked.connect(self.parent.settings_manager.reset_settings)
        button_layout.addWidget(reset_button)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(button_layout)
    
    def _test_database_connection(self) -> None:
        """测试数据库连接"""
        from PyQt6.QtWidgets import QMessageBox
        
        # 创建临时数据库配置
        temp_db_config = {
            'enabled': True,
            'type': self.db_type_combo.currentText(),
            'host': self.db_host_edit.text(),
            'port': self.db_port_spin.value(),
            'database': self.db_name_edit.text(),
            'username': self.db_user_edit.text(),
            'password': self.db_pass_edit.text()
        }
        
        # 创建临时数据库管理器测试连接
        from ..data.database import DatabaseManager
        temp_db_manager = DatabaseManager(self.parent, {'database': temp_db_config})
        
        # 测试连接
        if temp_db_manager.connect():
            QMessageBox.information(self, "成功", "数据库连接成功！")
            temp_db_manager.disconnect()
        else:
            QMessageBox.critical(self, "错误", "数据库连接失败！")
    
    def _on_platform_selected(self, item) -> None:
        """当平台被选中时，显示平台详情"""
        platform_name = item.text()
        platform_config = self.parent.platforms.get(platform_name, {})
        
        # 更新详情编辑区域
        self.platform_api_type_edit.setText(platform_config.get('api_type', ''))
        self.platform_base_url_edit.setText(platform_config.get('base_url', ''))
        self.platform_models_edit.setText(', '.join(platform_config.get('models', [])))
        self.platform_api_key_edit.setText(platform_config.get('api_key', ''))
        self.platform_api_key_hint_edit.setText(platform_config.get('api_key_hint', ''))
        self.platform_enabled_check.setChecked(platform_config.get('enabled', True))
    
    def _add_platform(self) -> None:
        """添加新平台"""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        
        # 获取新平台名称
        platform_name, ok = QInputDialog.getText(self, "添加平台", "请输入平台名称:")
        if ok and platform_name.strip():
            platform_name = platform_name.strip()
            if platform_name in self.parent.platforms:
                QMessageBox.warning(self, "警告", "平台名称已存在！")
                return
            
            # 创建新平台配置
            new_platform = {
                'name': platform_name,
                'api_type': 'openai',
                'base_url': 'https://api.openai.com/v1/chat/completions',
                'models': ['gpt-3.5-turbo'],
                'enabled': True,
                'api_key': '',
                'api_key_hint': 'sk-...'
            }
            
            # 添加到平台列表
            self.parent.platforms[platform_name] = new_platform
            self.platform_list.addItem(platform_name)
            self.platform_list.setCurrentRow(self.platform_list.count() - 1)
            self._on_platform_selected(self.platform_list.currentItem())
    
    def _delete_platform(self) -> None:
        """删除平台"""
        from PyQt6.QtWidgets import QMessageBox
        
        current_item = self.platform_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要删除的平台！")
            return
        
        platform_name = current_item.text()
        if len(self.parent.platforms) <= 1:
            QMessageBox.warning(self, "警告", "至少需要保留一个平台！")
            return
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", f"确定要删除平台 '{platform_name}' 吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 从平台列表中删除
            del self.parent.platforms[platform_name]
            self.platform_list.takeItem(self.platform_list.row(current_item))
            
            # 清空详情编辑区域
            self.platform_api_type_edit.clear()
            self.platform_base_url_edit.clear()
            self.platform_models_edit.clear()
            self.platform_api_key_edit.clear()
            self.platform_api_key_hint_edit.clear()
            self.platform_enabled_check.setChecked(False)
    
    def _save_platform(self) -> None:
        """保存平台配置"""
        from PyQt6.QtWidgets import QMessageBox
        
        current_item = self.platform_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要保存的平台！")
            return
        
        platform_name = current_item.text()
        
        # 解析模型列表
        models_str = self.platform_models_edit.text()
        models = [model.strip() for model in models_str.split(',') if model.strip()]
        
        # 更新平台配置
        self.parent.platforms[platform_name].update({
            'api_type': self.platform_api_type_edit.text(),
            'base_url': self.platform_base_url_edit.text(),
            'models': models,
            'api_key': self.platform_api_key_edit.text(),
            'api_key_hint': self.platform_api_key_hint_edit.text(),
            'enabled': self.platform_enabled_check.isChecked()
        })
        
        # 保存到文件
        self.parent.settings_manager.save_settings()
        QMessageBox.information(self, "成功", "平台配置已保存！")
    
    def accept(self) -> None:
        """接受设置"""
        # 应用设置
        new_settings = {
            'appearance': {
                'theme': self.theme_combo.currentText(),
                'font_size': self.font_size_spin.value()
            },
            'chat': {
                'auto_scroll': self.auto_scroll_check.isChecked(),
                'auto_save': self.auto_save_check.isChecked(),
                'show_timestamp': self.show_timestamp_check.isChecked(),
                'streaming': self.streaming_check.isChecked(),
                'max_history': self.max_history_spin.value()
            },
            'network': {
                'timeout': self.timeout_spin.value(),
                'retry_count': self.retry_spin.value(),
                'use_proxy': self.use_proxy_check.isChecked()
            },
            'database': {
                'enabled': self.enable_db_check.isChecked(),
                'type': self.db_type_combo.currentText(),
                'host': self.db_host_edit.text(),
                'port': self.db_port_spin.value(),
                'database': self.db_name_edit.text(),
                'username': self.db_user_edit.text(),
                'password': self.db_pass_edit.text(),
                'sync_on_startup': self.sync_on_startup_check.isChecked(),
                'sync_interval': self.sync_interval_spin.value(),
                'sync_config': self.sync_config_check.isChecked(),
                'sync_conversations': self.sync_conversations_check.isChecked(),
                'sync_memories': self.sync_memories_check.isChecked()
            }
        }
        
        # 保存平台配置
        self.parent.settings_manager.save_settings()
        
        # 更新设置
        self.parent.settings_manager.update_settings(new_settings)
        self.parent.settings = self.parent.settings_manager.settings
        
        # 应用主题
        self.parent.ui_manager.apply_theme(self.parent.settings['appearance']['theme'])
        
        # 更新流式响应复选框
        self.parent.streaming_checkbox.setChecked(self.parent.settings['chat']['streaming'])
        
        # 更新数据库管理器设置
        if self.parent.db_manager:
            self.parent.db_manager.settings = self.parent.settings
            self.parent.db_manager.db_config = self.parent.settings['database']
        
        # 更新平台下拉框
        self.parent.platform_combo.clear()
        available_platforms = [p for p, config in self.parent.platforms.items() if config['enabled']]
        self.parent.platform_combo.addItems(available_platforms)
        
        super().accept()

class StatisticsDialog(QDialog):
    """统计报告对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("统计报告")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.init_ui()
    
    def init_ui(self) -> None:
        """初始化UI"""
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 统计概览标签页
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        # 获取统计数据
        stats_summary = self.parent.stats_manager.get_statistics_summary()
        
        # 创建统计概览区域
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        
        # 格式化统计数据
        stats_content = "统计概览\n\n"
        stats_content += f"总对话数: {stats_summary['total_conversations']}\n"
        stats_content += f"总消息数: {stats_summary['total_messages']}\n"
        stats_content += f"用户消息数: {stats_summary['user_messages']}\n"
        stats_content += f"AI消息数: {stats_summary['ai_messages']}\n"
        stats_content += f"平均响应时间: {stats_summary['average_response_time']}秒\n"
        stats_content += f"最小响应时间: {stats_summary['min_response_time']}秒\n"
        stats_content += f"最大响应时间: {stats_summary['max_response_time']}秒\n"
        stats_content += f"总对话时长: {stats_summary['total_duration']}分钟\n\n"
        
        # 添加响应时间分布
        stats_content += "响应时间分布:\n"
        distribution = stats_summary['response_time_distribution']
        stats_content += f"  - 快速 (< 1秒): {distribution['fast']}次\n"
        stats_content += f"  - 正常 (1-5秒): {distribution['normal']}次\n"
        stats_content += f"  - 较慢 (5-10秒): {distribution['slow']}次\n"
        stats_content += f"  - 很慢 (> 10秒): {distribution['very_slow']}次\n"
        
        stats_text.setPlainText(stats_content)
        summary_layout.addWidget(stats_text)
        
        tab_widget.addTab(summary_tab, "统计概览")
        
        # 每日统计标签页
        daily_tab = QWidget()
        daily_layout = QVBoxLayout(daily_tab)
        
        daily_stats_text = QTextEdit()
        daily_stats_text.setReadOnly(True)
        
        daily_stats = self.parent.stats_manager.get_daily_statistics()
        daily_content = "每日统计\n\n"
        
        if daily_stats:
            for date in sorted(daily_stats.keys()):
                stats = daily_stats[date]
                daily_content += f"日期: {date}\n"
                daily_content += f"  - 消息总数: {stats['messages']}\n"
                daily_content += f"  - 用户消息: {stats['user_messages']}\n"
                daily_content += f"  - AI消息: {stats['ai_messages']}\n"
                daily_content += f"  - 平均响应时间: {stats['average_response_time']}秒\n\n"
        else:
            daily_content += "暂无每日统计数据\n"
        
        daily_stats_text.setPlainText(daily_content)
        daily_layout.addWidget(daily_stats_text)
        
        tab_widget.addTab(daily_tab, "每日统计")
        
        # 导出按钮
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        export_button = QPushButton("导出统计数据")
        export_button.clicked.connect(self.parent.export_statistics)
        export_layout.addWidget(export_button)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(export_layout)

class PersonalInfoDialog(QDialog):
    """个人信息对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("个人信息")
        self.setMinimumWidth(400)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.init_ui()
    
    def init_ui(self) -> None:
        """初始化UI"""
        # 主布局
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 加载现有个人信息
        personal_info = self.parent.load_personal_info()
        
        # 创建输入框
        self.name_edit = QLineEdit(personal_info.get("name", ""))
        self.email_edit = QLineEdit(personal_info.get("email", ""))
        self.phone_edit = QLineEdit(personal_info.get("phone", ""))
        self.address_edit = QLineEdit(personal_info.get("address", ""))
        
        # 添加到表单
        form_layout.addRow("姓名", self.name_edit)
        form_layout.addRow("邮箱", self.email_edit)
        form_layout.addRow("电话", self.phone_edit)
        form_layout.addRow("地址", self.address_edit)
        
        # 添加表单到主布局
        layout.addLayout(form_layout)
        
        # 按钮布局
        button_layout = QVBoxLayout()
        
        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_personal_info)
        button_layout.addWidget(save_btn)
        
        # 添加按钮布局到主布局
        layout.addLayout(button_layout)
    
    def _save_personal_info(self) -> None:
        """保存个人信息"""
        from PyQt6.QtWidgets import QMessageBox
        
        personal_info = {
            "name": self.name_edit.text(),
            "email": self.email_edit.text(),
            "phone": self.phone_edit.text(),
            "address": self.address_edit.text()
        }
        
        if self.parent.save_personal_info(personal_info):
            QMessageBox.information(self, "成功", "个人信息已保存！")
            self.accept()
        else:
            QMessageBox.error(self, "错误", "保存个人信息失败！")

class TaskManagementDialog(QDialog):
    """任务管理对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("任务管理")
        self.setMinimumSize(500, 400)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.init_ui()
    
    def init_ui(self) -> None:
        """初始化UI"""
        # 主布局
        layout = QVBoxLayout(self)
        
        # 任务输入布局
        input_layout = QHBoxLayout()
        
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("输入新任务...")
        input_layout.addWidget(self.task_input)
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._add_task)
        input_layout.addWidget(add_btn)
        
        layout.addLayout(input_layout)
        
        # 任务列表
        self.task_list = QListWidget()
        # 加载现有任务
        self._load_tasks()
        layout.addWidget(self.task_list)
        
        # 任务操作按钮布局
        task_btn_layout = QHBoxLayout()
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self._delete_task)
        task_btn_layout.addWidget(delete_btn)
        
        complete_btn = QPushButton("完成")
        complete_btn.clicked.connect(self._complete_task)
        task_btn_layout.addWidget(complete_btn)
        
        layout.addLayout(task_btn_layout)
        
        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_tasks)
        layout.addWidget(save_btn)
    
    def _load_tasks(self) -> None:
        """加载任务列表"""
        task_records = self.parent.load_task_records()
        tasks = task_records.get("tasks", [])
        self.task_list.clear()
        for task in tasks:
            status = "[已完成] " if task.get("completed", False) else "[未完成] "
            self.task_list.addItem(f"{status}{task.get('content', '')}")
    
    def _add_task(self) -> None:
        """添加新任务"""
        task_content = self.task_input.text().strip()
        if task_content:
            self.task_list.addItem(f"[未完成] {task_content}")
            self.task_input.clear()
    
    def _delete_task(self) -> None:
        """删除选中的任务"""
        selected_items = self.task_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.task_list.takeItem(self.task_list.row(item))
    
    def _complete_task(self) -> None:
        """标记任务为完成/未完成"""
        selected_items = self.task_list.selectedItems()
        if selected_items:
            for item in selected_items:
                text = item.text()
                if text.startswith("[未完成] "):
                    new_text = text.replace("[未完成] ", "[已完成] ")
                    item.setText(new_text)
                else:
                    new_text = text.replace("[已完成] ", "[未完成] ")
                    item.setText(new_text)
    
    def _save_tasks(self) -> None:
        """保存任务列表"""
        from PyQt6.QtWidgets import QMessageBox
        
        tasks = []
        for i in range(self.task_list.count()):
            item_text = self.task_list.item(i).text()
            if item_text.startswith("[已完成] "):
                task_content = item_text.replace("[已完成] ", "")
                completed = True
            else:
                task_content = item_text.replace("[未完成] ", "")
                completed = False
            tasks.append({
                "content": task_content,
                "completed": completed,
                "timestamp": self.parent.get_current_timestamp()
            })
        
        task_records = {"tasks": tasks}
        if self.parent.save_task_records(task_records):
            QMessageBox.information(self, "成功", "任务列表已保存！")
            self.accept()
        else:
            QMessageBox.error(self, "错误", "保存任务列表失败！")
