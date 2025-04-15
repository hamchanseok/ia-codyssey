#313131 RGB[49,49,49] 숫자버튼
#F69906 RGB[246,153,6] 연산버튼
#A0A0A0 RGB[160,160,160] AC, +/- % 버튼
#폰트 : San Francisco

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QVBoxLayout
from PyQt5.QtCore import Qt


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('iPhone 스타일 계산기')
        self.setFixedSize(300, 400)
        self.setStyleSheet('background-color: black;')
        self.create_ui()

    def create_ui(self):
        main_layout = QVBoxLayout()
        self.display = QLineEdit()
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        self.display.setFixedHeight(60)
        self.display.setStyleSheet('font-size: 24px; font-family: "San Francisco"; color: white; background-color: black; border: none;')

        main_layout.addWidget(self.display)

        grid_layout = QGridLayout()
        buttons = [
            ('C', 0, 0), ('+/-', 0, 1), ('%', 0, 2), ('÷', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('x', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('0', 4, 0, 1, 2), ('.', 4, 2), ('=', 4, 3)
        ]

        for btn in buttons:
            if len(btn) == 3:
                label, row, col = btn
                rowspan, colspan = 1, 1
            elif len(btn) == 5:
                label, row, col, rowspan, colspan = btn
            else:
                continue

            button = QPushButton(label)
            button.setFixedSize(60 * colspan, 60 * rowspan)
            radius = 30 if colspan == 1 else 60  # 원형에 가깝게
            color = self.get_button_color(label)
            button.setStyleSheet(
                f'font-size: 18px; font-family: "San Francisco"; background-color: {color}; color: white;'
                f'border: none; border-radius: {radius}px;')
            button.clicked.connect(self.button_clicked)
            grid_layout.addWidget(button, row, col, rowspan, colspan)

        main_layout.addLayout(grid_layout)
        self.setLayout(main_layout)

    def get_button_color(self, label):
        if label in ('C', '+/-', '%'):
            return '#A0A0A0'  # 회색
        elif label in ('÷', 'x', '-', '+', '='):
            return '#F69906'  # 주황
        else:
            return '#313131'  # 숫자 버튼 (진한 회색)

    def button_clicked(self):
        sender = self.sender()
        current_text = self.display.text()
        label = sender.text()

        if label == 'C':
            self.display.setText('')
        elif label == '=':
            try:
                expression = current_text.replace('÷', '/').replace('x', '*')
                result = str(eval(expression))
                self.display.setText(result)
            except Exception:
                self.display.setText('Error')
        elif label == '+/-':
            if current_text:
                if current_text.startswith('-'):
                    self.display.setText(current_text[1:])
                else:
                    self.display.setText('-' + current_text)
        else:
            self.display.setText(current_text + label)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec_())