import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QDialog, 
                               QFormLayout, QComboBox, QDialogButtonBox, QDateEdit, QMessageBox,
                               QFileDialog, QGroupBox, QCalendarWidget)
from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtGui import QDoubleValidator, QPainter, QColor, QPalette
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QDateTimeAxis, QValueAxis
from database import Database
import csv
import json
import codecs

class TransactionDialog(QDialog):
    def __init__(self, parent=None, transaction=None):
        super().__init__(parent)
        self.setWindowTitle("添加/编辑交易")
        self.layout = QFormLayout(self)
        self.transaction = transaction

        # 日期选择
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        # 类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["收入", "支出"])
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setValidator(QDoubleValidator(0, 1000000, 2))
        self.description_edit = QLineEdit()

        self.layout.addRow("日期:", self.date_edit)
        self.layout.addRow("类型:", self.type_combo)
        self.layout.addRow("金额:", self.amount_edit)
        self.layout.addRow("描述:", self.description_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addRow(self.button_box)

        if transaction:
            self.date_edit.setDate(QDate.fromString(transaction[1], "yyyy-MM-dd"))
            self.type_combo.setCurrentText(transaction[2])
            self.amount_edit.setText(str(transaction[3]))
            self.description_edit.setText(transaction[4])

    def get_data(self):
        try:
            amount = float(self.amount_edit.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的金额")
            return None
        
        return {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "type": self.type_combo.currentText(),
            "amount": amount,
            "description": self.description_edit.text()
        }

class ExpenseTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MoneyList")
        self.setGeometry(100, 100, 1000, 600)
        
        self.db = Database()
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.setup_ui()
        
    def setup_ui(self):
        # 添加按钮布局
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("添加交易")
        self.add_button.clicked.connect(self.add_transaction)
        self.edit_button = QPushButton("编辑交易")
        self.edit_button.clicked.connect(self.edit_transaction)
        self.delete_button = QPushButton("删除交易")
        self.delete_button.clicked.connect(self.delete_transaction)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        self.layout.addLayout(button_layout)

        # 筛选控件
        filter_layout = QHBoxLayout()
        
        # 设置默认的开始日期为三个月前
        default_start_date = QDate.currentDate().addMonths(-3)
        self.start_date = QDateEdit(default_start_date)
        self.start_date.setCalendarPopup(True)
        
        # 设置默认的结束日期为今天
        default_end_date = QDate.currentDate()
        self.end_date = QDateEdit(default_end_date)
        self.end_date.setCalendarPopup(True)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["全部", "收入", "支出"])
        self.filter_button = QPushButton("筛选")
        self.filter_button.clicked.connect(self.filter_transactions)
        filter_layout.addWidget(QLabel("开始日期:"))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("结束日期:"))
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(QLabel("类型:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(self.filter_button)
        self.layout.addLayout(filter_layout)

        # 显示交易记录的表格
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "日期", "类型", "金额", "描述"])
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.layout.addWidget(self.table)

        # 统计信息
        stats_layout = QHBoxLayout()
        self.balance_label = QLabel()
        self.income_label = QLabel()
        self.expense_label = QLabel()
        stats_layout.addWidget(self.balance_label)
        stats_layout.addWidget(self.income_label)
        stats_layout.addWidget(self.expense_label)
        self.layout.addLayout(stats_layout)

        # 图表部分
        chart_layout = QHBoxLayout()
        self.pie_chart = QChartView()
        self.balance_chart = QChartView()
        chart_layout.addWidget(self.pie_chart)
        chart_layout.addWidget(self.balance_chart)
        self.layout.addLayout(chart_layout)

        # 导入/导出按钮
        io_layout = QHBoxLayout()
        self.import_button = QPushButton("导入数据")
        self.import_button.clicked.connect(self.import_data)
        self.export_button = QPushButton("导出数据")
        self.export_button.clicked.connect(self.export_data)
        io_layout.addWidget(self.import_button)
        io_layout.addWidget(self.export_button)
        self.layout.addLayout(io_layout)

        self.load_transactions()
        
    def on_cell_double_clicked(self, row, column):
        if column in [1, 2]:  # 日期或类型列
            transaction_id = int(self.table.item(row, 0).text())
            self.edit_transaction(transaction_id)

    def add_transaction(self):
        dialog = TransactionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.db.add_transaction(**data)
                self.load_transactions()

    def edit_transaction(self, transaction_id=None):
        if transaction_id is None:
            selected_items = self.table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "警告", "请选择要编辑的交易")
                return
            row = selected_items[0].row()
            transaction_id = int(self.table.item(row, 0).text())
        
        transaction = self.db.get_transaction(transaction_id)
        dialog = TransactionDialog(self, transaction)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.db.update_transaction(transaction_id, **data)
                self.load_transactions()

    def delete_transaction(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要删除的交易")
            return
        row = selected_items[0].row()
        transaction_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, "确认", "确定要删除这笔交易吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_transaction(transaction_id)
            self.load_transactions()

    def filter_transactions(self):
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        transaction_type = self.type_filter.currentText()
        if transaction_type == "全部":
            transaction_type = None
        self.load_transactions(start_date, end_date, transaction_type)

    def load_transactions(self, start_date=None, end_date=None, transaction_type=None):
        if start_date is None:
            start_date = self.start_date.date().toString("yyyy-MM-dd")
        if end_date is None:
            end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        transactions = self.db.get_transactions(start_date, end_date, transaction_type)
        self.table.setRowCount(len(transactions))
        for row, transaction in enumerate(transactions):
            for col, value in enumerate(transaction):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 所有列都设置为不可编辑
                self.table.setItem(row, col, item)
        
        self.update_stats()
        self.update_charts()

    def update_stats(self):
        balance = self.db.get_balance()
        income = self.db.get_total_income()
        expense = self.db.get_total_expense()
        self.balance_label.setText(f"总余额: {balance:.2f}")
        self.income_label.setText(f"总收入: {income:.2f}")
        self.expense_label.setText(f"总支出: {expense:.2f}")

    def update_charts(self):
        # 饼图部分
        pie_series = QPieSeries()
        income = self.db.get_total_income()
        expense = self.db.get_total_expense()
        pie_series.append("收入", income)
        pie_series.append("支出", expense)
        
        pie_chart = QChart()
        pie_chart.addSeries(pie_series)
        pie_chart.setTitle("收支比例")
        self.pie_chart.setChart(pie_chart)

        # 余额趋势图
        balance_series = QLineSeries()
        transactions = self.db.get_transactions()
        
        if transactions:
            balance = 0
            for index, transaction in enumerate(transactions, start=1):
                amount = float(transaction[3])
                if transaction[2] == "支出":
                    amount = -amount
                balance += amount
                balance_series.append(index, balance)

            balance_chart = QChart()
            balance_chart.addSeries(balance_series)
            balance_chart.setTitle("余额变化")

            axis_x = QValueAxis()
            axis_x.setTitleText("交易数")
            axis_x.setLabelFormat("%d")
            axis_x.setRange(1, len(transactions))

            axis_y = QValueAxis()
            axis_y.setTitleText("余额")
            axis_y.setLabelFormat("%.2f")

            balance_chart.addAxis(axis_x, Qt.AlignBottom)
            balance_chart.addAxis(axis_y, Qt.AlignLeft)
            balance_series.attachAxis(axis_x)
            balance_series.attachAxis(axis_y)

            self.balance_chart.setChart(balance_chart)

    def import_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "导入数据", "", "CSV Files (*.csv);;JSON Files (*.json)")
        if file_name:
            if file_name.endswith('.csv'):
                self.import_csv(file_name)
            elif file_name.endswith('.json'):
                self.import_json(file_name)

    def export_data(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "导出数据", "", "CSV Files (*.csv);;JSON Files (*.json)")
        if file_name:
            if file_name.endswith('.csv'):
                self.export_csv(file_name)
            elif file_name.endswith('.json'):
                self.export_json(file_name)

    def import_csv(self, file_name):
        with open(file_name, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.db.add_transaction(**row)
        self.load_transactions()

    def export_csv(self, file_name):
        transactions = self.db.get_transactions()
        with codecs.open(file_name, 'w', encoding='utf-8-sig') as csvfile:
            fieldnames = ['date', 'type', 'amount', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for transaction in transactions:
                writer.writerow({
                    'date': transaction[1],
                    'type': transaction[2],
                    'amount': transaction[3],
                    'description': transaction[4]
                })

    def import_json(self, file_name):
        with open(file_name, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            for transaction in data:
                self.db.add_transaction(**transaction)
        self.load_transactions()

    def export_json(self, file_name):
        transactions = self.db.get_transactions()
        data = []
        for transaction in transactions:
            data.append({
                'date': transaction[1],
                'type': transaction[2],
                'amount': transaction[3],
                'description': transaction[4]
            })
        with codecs.open(file_name, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式为 Fusion
    app.setStyle("Fusion")
    
    # 创建自定义调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    
    # 应用调色板
    app.setPalette(palette)
    
    # 设置样式表
    app.setStyleSheet("""
    QToolTip { 
        color: #ffffff; 
        background-color: #2a82da; 
        border: 1px solid white; 
    }
    
    QTableWidget {
        gridline-color: #353535;
    }
    
    QHeaderView::section {
        background-color: #353535;
        color: white;
        padding: 5px;
        border: 1px solid #2a82da;
    }
    
    QTableWidget::item:selected {
        background-color: #2a82da;
    }
    
    QPushButton {
        background-color: #2a82da;
        color: white;
        padding: 5px;
        border: none;
        border-radius: 3px;
    }
    
    QPushButton:hover {
        background-color: #3498db;
    }
    
    QPushButton:pressed {
        background-color: #1c6399;
    }
    
    QLineEdit, QComboBox, QDateEdit {
        background-color: #353535;
        border: 1px solid #2a82da;
        color: white;
        padding: 3px;
        border-radius: 3px;
    }
    """)
    
    window = ExpenseTracker()
    window.show()
    sys.exit(app.exec())