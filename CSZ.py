import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QDesktopWidget, QVBoxLayout, \
    QHBoxLayout, QGroupBox, QRadioButton, QGridLayout, QFormLayout, QDialog
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QObject, QTimer
import pyqtgraph as pg
import serial
import time
import struct
import os
import csv



# class SERIAL():
#     def __init__(self):
#         self.ser = serial.Serial('COM20', 230400, timeout=0.001)
#         self.column = ['滚转角', '滚转角速度', '俯仰角', '俯仰角速度', '航向角', '航向角速度', '高度', '空速', '经度', '纬度', '1号舵机', '5号舵机', '3号舵机', '6号舵机', '7号舵机', '8号舵机', '9号舵机', '10号舵机',
#                        '巡航标志位', '故障类型', '故障位置', '卡死舵面pwm', '期望滚转角', '滚转控制量', '期望俯仰角', '俯仰控制量', '飞行数据接收', '故障诊断', '故障类型', '故障定位', '容错参数接收', '滚转角容错控制量',
#                        '俯仰角容错控制量', '俯仰角制导kp', '俯仰角制导ki', '俯仰角制导kd','滚转角控制器kp','滚转角控制器ki', '滚转角控制器kd', '俯仰角控制器kp', '俯仰角控制器ki', '俯仰角控制器kd',
#                        '偏航角控制器kp', '偏航角控制器ki', '偏航角控制器kd', '预留1', '预留2','预留3','预留4','预留5','预留6', '时间戳', '校验位']  # 列表头名称
#
#     # i为四位(字节)，h两位，b一位,f为浮点  <低位在前，>高位在前    <8f3i 表示低位在前，8个float,3个int32
#     def read_usb(self):
#         while True:
#             # 判断帧头
#             if self.ser.in_waiting > 0:
#                 if self.ser.read(1) == b'\x55':
#                     if self.ser.read(1) == b'\xAA':
#                         # 读取帧头后面163个字节
#                         data = self.ser.read(167)
#                         if len(data) == 167 and (sum(data[:-1]) & 0xff) == data[-1]:
#                             return struct.unpack(f"<10f8h3bh4f5b20fib", data)
#                         else:
#                             self.ser.read_all()
#                             print("!!!!!!!!")
#                             return 0
#
#     #保存数据
#     def save_data(self, data):
#         with open(r'D:\logdata.csv', mode='a', newline='') as file:
#             writer = csv.writer(file)
#             writer.writerow(data)
#
#     def write_usb(self, data):
#         byte_list = [b'\x55', b'\xAA']
#         for i in range(len(data)):
#             x = struct.pack('<f', data[i])
#             x = [hex(byte) for byte in x]
#             byte_list = (byte_list + [bytes([int(z, 16)]) for z in x])
#         byte_sum = sum(int.from_bytes(byte, 'little') for byte in byte_list[2:])
#         check_flag = byte_sum & 0xff
#         check_flag = check_flag.to_bytes(1, 'little')
#         byte_list.append(check_flag)
#         self.ser.write(b''.join(byte_list))
#
#     def initfloder(self):
#         with open(r'D:\logdata.csv', mode='a', newline='') as file:
#             writer = csv.writer(file)
#             writer.writerow(self.column)


class OscilloscopeWidget(QtWidgets.QWidget):
    def __init__(self, DATA, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.wave_type1 = 'None'
        self.wave_type2 = 'None'

        # Add dropdown menus to select wave types
        self.wave_type1_combo = QtWidgets.QComboBox()
        self.wave_type2_combo = QtWidgets.QComboBox()
        for wave_type in ['None', 'pitch', 'roll', 'yaw', 'pitch_w', 'roll_w', 'yaw_w', 'h', 'v', 'Deg6', 'Deg7', 'Deg8', 'Deg9', 'roll_u', 'pitch_u', 'roll_fu', 'pitch_fu']:
            self.wave_type1_combo.addItem(wave_type)
            self.wave_type2_combo.addItem(wave_type)
        self.wave_type1_combo.currentTextChanged.connect(self.update_wave_types)
        self.wave_type2_combo.currentTextChanged.connect(self.update_wave_types)

        self.layout.addWidget(self.wave_type1_combo)
        self.layout.addWidget(self.wave_type2_combo)

        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

        # Set background color to white
        #self.plot_widget.setBackground('w')

        # Add legend to the plot widget
        self.plot_widget.addLegend()

        # Create two plot items for the two waveforms
        self.plot1 = self.plot_widget.plot(pen='y', name=self.wave_type1)
        self.plot2 = self.plot_widget.plot(pen='r', name=self.wave_type2)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)  # Update rate in milliseconds
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

        self.x = range(500)
        self.ptr = 0

        self.data = DATA

        self.update_wave_types()

    def update_wave_types(self):
        self.wave_type1 = self.wave_type1_combo.currentText()
        self.wave_type2 = self.wave_type2_combo.currentText()

    def generate_wave(self, wave_type):
        self.x = range(len(self.data))
        if wave_type == 'roll':
            return [row[0] for row in self.data]
        elif wave_type == 'roll_w':
            return [row[1] for row in self.data]
        elif wave_type == 'pitch':
            return [row[2] for row in self.data]
        elif wave_type == 'pitch_w':
            return [row[3] for row in self.data]
        elif wave_type == 'yaw':
            return [row[4] for row in self.data]
        elif wave_type == 'yaw_w':
            return [row[5] for row in self.data]
        elif wave_type == 'h':
            return [row[6] for row in self.data]
        elif wave_type == 'v':
            return [row[7] for row in self.data]
        elif wave_type == 'Deg6':
            return [row[13] for row in self.data]
        elif wave_type == 'Deg7':
            return [row[14] for row in self.data]
        elif wave_type == 'Deg8':
            return [row[15] for row in self.data]
        elif wave_type == 'Deg9':
            return [row[16] for row in self.data]
        elif wave_type == 'roll_u':
            return [row[23] for row in self.data]
        elif wave_type == 'pitch_u':
            return [row[25] for row in self.data]
        elif wave_type == 'roll_fu':
            return [row[31] for row in self.data]
        elif wave_type == 'pitch_fu':
            return [row[32] for row in self.data]
        elif wave_type == 'None':
            return 0


    def update_plot(self):
        self.y1 = self.generate_wave(self.wave_type1)
        self.y2 = self.generate_wave(self.wave_type2)
        if self.y1 != 0:
            self.plot1.setData(self.x, self.y1, name=self.wave_type1)
        if self.y2 != 0:
            self.plot2.setData(self.x, self.y2, name=self.wave_type2)
        self.ptr += 0.1


class Window2(QtWidgets.QMainWindow):
    def __init__(self, DATA):
        super().__init__()
        self.setWindowTitle("波形监测")
        self.setGeometry(100, 100, 1200, 800)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QGridLayout(self.central_widget)

        # Add oscilloscope widgets with dropdown menus
        self.oscilloscope1 = OscilloscopeWidget(DATA)
        self.oscilloscope2 = OscilloscopeWidget(DATA)
        self.oscilloscope3 = OscilloscopeWidget(DATA)
        self.oscilloscope4 = OscilloscopeWidget(DATA)
        self.oscilloscope5 = OscilloscopeWidget(DATA)
        self.oscilloscope6 = OscilloscopeWidget(DATA)

        self.layout.addWidget(self.oscilloscope1, 0, 0)
        self.layout.addWidget(self.oscilloscope2, 0, 1)
        self.layout.addWidget(self.oscilloscope3, 0, 2)
        self.layout.addWidget(self.oscilloscope4, 1, 0)
        self.layout.addWidget(self.oscilloscope5, 1, 1)
        self.layout.addWidget(self.oscilloscope6, 1, 2)


class monitor_zjj():
    def __init__(self):
        # self.ser = SERIAL()
        # self.ser.initfloder()
        self.data = []

        self.app = QApplication(sys.argv)

        self.window = QWidget()
        self.window.setWindowTitle('地面检测')  # 设置窗口标题
        self.window.resize(1000, 600)  # 设置窗口大小

        self.number = 1
        self.label = []
        self.label2 = []
        self.label3 = []
        self.edit = []
        self.fly_data = ['滚转角:', '滚转角速度:', '俯仰角:', '俯仰角速度:', '航向角:', '航向角速度:', '高度:', '空速:', '经度:', '纬度:', '1号舵机:', '5号舵机:', '3号舵机:',
                    '6号舵机:', '7号舵机:', '8号舵机:', '9号舵机:', '10号舵机:', '巡航标志位:', '故障类型:', '故障位置:', '卡死舵面pwm:', '期望滚转角:', '滚转控制量:', '期望俯仰角:', '俯仰控制量:']
        self.diagnose_control_data = ['飞行数据接收:', '故障诊断:', '故障类型:', '故障定位:', '容错参数接收:',
                                      '滚转角容错控制量:', '俯仰角容错控制量:', '俯仰角制导kp:', '俯仰角制导ki:','俯仰角制导kd:','滚转角控制器kp:',
                                      '滚转角控制器ki:','滚转角控制器kd:', '俯仰角控制器kp:', '俯仰角控制器ki:', '俯仰角控制器kd:','容错通道选择:',
                                      '偏航角控制器kp:', '偏航角控制器ki:', '偏航角控制器kd:','预留4:', '预留5:', '预留6:', '预留7:','预留8:']

        self.write_data = ['俯仰角制导kp:', '俯仰角制导ki:','俯仰角制导kd:','滚转角控制器kp:', '滚转角控制器ki:',
                           '滚转角控制器kd:', '俯仰角控制器kp:', '俯仰角控制器ki:', '俯仰角控制器kd:','容错通道选择:', '偏航角控制器kp:', '偏航角控制器ki:', '偏航角控制器kd:',
                           '参数14: ', '参数15: ', '参数16: ', '参数17: ', '参数18: ']

        self.DATA = []
        self.jishu = 0
        self.canshu = [-0.2, 0, -0.1, -100, -10, -10, 10, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]

    def data_oscilloscope(self):
        self.window2 = Window2(self.DATA)
        self.window2.show()

    def get_data(self):
        a = time.time()
        data = self.ser.read_usb()
        print('数据', data)
        if data == 0:
            data = self.data
        self.data = data
        self.ser.save_data(data)
        print('循环时间', time.time()-a)

        # if len(self.DATA) < 100:
        #     if self.jishu<10:
        #         self.jishu += 1
        #     else:
        #         self.DATA.append(data)
        #         self.jishu = 0
        # else:
        #     if self.jishu<10:
        #         self.jishu += 1
        #     else:
        #         self.DATA.pop(0)
        #         self.DATA.append(data)
        #         self.jishu = 0

        if len(self.DATA) < 500:
                self.DATA.append(data)
        else:
                self.DATA.pop(0)
                self.DATA.append(data)

    def write(self):
        write_data = []
        for i in range(len(self.edit)):
            data = self.edit[i].text()
            if data:
               write_data.append(float(data))
            else:
               write_data.append(-77)
        print(write_data)
        self.ser.write_usb(write_data)


        byte_list = [b'\x55', b'\xAA']
        for i in range(len(write_data)):
            x = struct.pack('<f', write_data[i])
            x = [hex(byte) for byte in x]
            byte_list = (byte_list + [bytes([int(z, 16)]) for z in x])
        byte_sum = sum(int.from_bytes(byte, 'big') for byte in byte_list[2:])
        check_flag = byte_sum & 0xff
        check_flag = check_flag.to_bytes(1, 'little')
        byte_list.append(check_flag)
        print(b''.join(byte_list))
        #self.ser.write_usb(write_data)

    def data_jz(self):
        layout = QVBoxLayout()

        d1 = QGroupBox("信息接收")
        d1.setStyleSheet("font-size: 16px; color: black; font-weight: bold; text-align: center;")
        d1.setAlignment(Qt.AlignHCenter)
        b1 = QHBoxLayout()

        # 内置第一个盒子
        v1 = QGroupBox("飞行信息")
        v1.setAlignment(Qt.AlignHCenter)
        l1 = QHBoxLayout()
        v1_1 = QGroupBox()
        l1_1 = QVBoxLayout()
        v1_2 = QGroupBox()
        l1_2 = QVBoxLayout()
        for i in range(int(len(self.fly_data)/2)):
            label = QLabel()
            label.setText(self.fly_data[i])
            label.setFixedSize(170, 30)
            label.setStyleSheet("border: 1px solid black; padding: 0px")
            l1_1.addWidget(label)
            self.label.append(label)
        for i in range(int(len(self.fly_data)/2)):
            label = QLabel()
            label.setText(self.fly_data[i+int(len(self.fly_data)/2)])
            label.setFixedSize(200, 30)
            label.setStyleSheet("border: 1px solid black; padding: 0px")
            l1_2.addWidget(label)
            self.label.append(label)
        v1_1.setLayout(l1_1)
        l1.addWidget(v1_1)
        v1_2.setLayout(l1_2)
        l1.addWidget(v1_2)

        # 内置第二个盒子
        v2 = QGroupBox("故障与容错")
        v2.setAlignment(Qt.AlignHCenter)
        l2 = QHBoxLayout()
        v2_1 = QGroupBox()
        l2_1 = QVBoxLayout()
        v2_2 = QGroupBox()
        l2_2 = QVBoxLayout()
        for i in range(12):
            label = QLabel()
            label.setText(self.diagnose_control_data[i])
            label.setFixedSize(300, 30)
            label.setStyleSheet("border: 1px solid black; padding: 0px")
            l2_1.addWidget(label)
            self.label2.append(label)
        for i in range(13):
            label = QLabel()
            label.setText(self.diagnose_control_data[i+int(len(self.diagnose_control_data)/2)])
            label.setFixedSize(300, 30)
            label.setStyleSheet("border: 1px solid black; padding: 0px")
            l2_2.addWidget(label)
            self.label2.append(label)
        v2_1.setLayout(l2_1)
        l2.addWidget(v2_1)
        v2_2.setLayout(l2_2)
        l2.addWidget(v2_2)

        # 内置第三个盒子
        v3 = QGroupBox("附加功能")
        v3.setAlignment(Qt.AlignHCenter)
        l3 = QVBoxLayout()
        btn1 = QPushButton("波形显示")
        btn1.clicked.connect(self.data_oscilloscope)
        l3.addWidget(btn1)

        v1.setLayout(l1)
        b1.addWidget(v1)
        v2.setLayout(l2)
        b1.addWidget(v2)
        v3.setLayout(l3)
        b1.addWidget(v3)

        d2 = QGroupBox("数据发送")
        d2.setStyleSheet("font-size: 16px; color: black; font-weight: bold; text-align: center;")
        d2.setAlignment(Qt.AlignHCenter)
        b2 = QHBoxLayout()

        v4 = QGroupBox()
        l4 = QVBoxLayout()
        v5 = QGroupBox()
        l5 = QVBoxLayout()
        v6 = QGroupBox()
        l6 = QVBoxLayout()
        for i in range(int(len(self.write_data) / 2)):
            label = QLabel()
            label.setText(self.write_data[i])
            label.setFixedSize(200, 30)
            label.setStyleSheet("border: 1px solid black; padding: 0px")
            edit = QLineEdit()  # 添加文本框,指定文本框所在的窗口
            edit.setText(str(self.canshu[i]))
            edit.setFixedSize(300, 30)
            label.setBuddy(edit)
            ll = QHBoxLayout()
            ll.addWidget(label)
            ll.addSpacing(-27)
            ll.addWidget(edit)
            l4.addLayout(ll)
            self.label3.append(label)
            self.edit.append(edit)
        for i in range(int(len(self.write_data) / 2)):
            label = QLabel()
            label.setText(self.write_data[i + int(len(self.write_data) / 2)])
            label.setFixedSize(200, 30)
            label.setStyleSheet("border: 1px solid black; padding: 0px")
            edit = QLineEdit()  # 添加文本框,指定文本框所在的窗口
            edit.setText(str(self.canshu[i + int(len(self.write_data) / 2)]))
            edit.setFixedSize(300, 30)
            label.setBuddy(edit)
            ll = QHBoxLayout()
            ll.addWidget(label)
            ll.addSpacing(-27)
            ll.addWidget(edit)
            l5.addLayout(ll)
            self.label3.append(label)
            self.edit.append(edit)
        btn2 = QPushButton("发送")
        btn2.clicked.connect(self.write)
        l6.addWidget(btn2)

        v4.setLayout(l4)
        b2.addWidget(v4)
        v5.setLayout(l5)
        b2.addWidget(v5)
        v6.setLayout(l6)
        b2.addWidget(v6)

        d1.setLayout(b1)
        layout.addWidget(d1)
        d2.setLayout(b2)
        layout.addWidget(d2)

        self.window.setLayout(layout)


    def update(self):
        self.get_data()
        for i in range(len(self.fly_data)):
            self.label[i].setText(self.fly_data[i]+str(self.data[i]))
        for i in range(len(self.diagnose_control_data)):
            self.label2[i].setText(self.diagnose_control_data[i]+str(self.data[i+len(self.fly_data)]))
        for i in range(len(self.write_data)):
            self.label3[i].setText(self.write_data[i]+str(self.data[i+len(self.fly_data)+7]))

    def run(self):
        self.data_jz()
        self.window.show()  # 展示窗口
        timer = QTimer()
        timer.timeout.connect(self.update)
        timer.start(10)  # 每隔1秒更新一次文本
        self.app.exec()  # 程序进入循环等待



if __name__ == '__main__':
    monitor = monitor_zjj()
    monitor.run()
