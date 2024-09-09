
# MoneyList 

MoneyList 是一个使用 Python 和 PySide6 构建的个人财务管理应用程序。它允许用户跟踪收入和支出，可视化财务数据，并有效管理预算。

## 功能特点

- 添加、编辑和删除交易记录
- 按日期范围和类型（收入/支出）筛选交易
- 查看财务统计信息（总余额、收入和支出）
- 使用饼图和余额趋势图可视化财务数据
- 舒适的深色模式界面
- 支持 CSV 和 JSON 格式的数据导入和导出

## 系统要求

- Python 3.6+
- PySide6
- SQLite3

## 安装步骤

1. 克隆仓库：
   ````
   git clone https://github.com/yourusername/moneylist.git
   cd moneylist
   ```

2. 安装所需依赖：
   ````
   pip install PySide6
   ```

3. 运行应用程序：
   ````
   python main.py
   ```

## 使用说明

1. 运行 `main.py` 启动应用程序。
2. 使用"添加交易"按钮记录新的收入或支出。
3. 使用日期范围和类型选择器筛选交易。
4. 在表格中选择交易记录进行编辑或删除。
5. 在窗口底部查看财务统计信息和图表。
6. 使用相应的按钮导入或导出数据。

## 数据库

应用程序使用 SQLite 存储交易数据。数据库文件 `expenses.db` 将在应用程序所在的目录中创建。

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 许可证

本项目是开源的，遵循 [MIT 许可证](LICENSE)。
