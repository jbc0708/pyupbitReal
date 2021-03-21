from PyQt5.QtWidgets import QApplication, QWidget, QTableWidgetItem
from PyQt5.QtCore import*
from PyQt5 import uic
import sys
import pyupbit
import websocket
import json
import sys

main_ui = uic.loadUiType(".//main.ui")[0]

class Worker(QThread):
    recieve_data = pyqtSignal(dict)
    def __init__(self):
        super().__init__()
        self.ws = websocket.WebSocketApp("wss://api.upbit.com/websocket/v1",
                        on_message = self.on_message,
                        on_error = self.on_error,
                        on_close = self.on_close)

    def run(self):
        self.ws.run_forever()

    def requestCode(self, codes):
        sendData = '[{"ticket":"test"},{"type":"ticker","codes": [%s]}]'%codes
        self.ws.send(sendData)
        

    def on_close(self, ws):
        print("close")

    def on_error(self, ws, error):
        print(error)

    def on_message(self, ws, message):
        get_message = json.loads(message.decode('utf-8'))
        #print(get_message,"\n")
        self.recieve_data.emit(get_message)

class Main(QWidget, main_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        
        self.code_of_requested = []
        self.setCodeToCombo()

        self.worker = Worker()
        self.worker.recieve_data.connect(self.print_data)
        self.worker.start()

        self.button_request.clicked.connect(self.infoRequest)
        self.combo_code.currentTextChanged.connect(self.changeButtonText)

    @pyqtSlot(dict)
    def print_data(self, data):
        #print(data)
        code = data.get("code")
        current_price = data.get('trade_price')
        temp_time = data.get('trade_time')
        temp_hour = int(temp_time[:2]) + 9 if int(temp_time[:2]) + 9 < 24 else int(temp_time[:2]) - 15
        hour = str(temp_hour) if temp_hour > 9 else "0"+str(temp_hour)
        min = temp_time[2:4]
        sec = temp_time[4:]
        time = hour+":"+min+":"+sec

        if code in self.code_of_requested:
            index = self.code_of_requested.index(code)
            
            self.table_info.setItem(index, 1, QTableWidgetItem(str(current_price)))
            self.table_info.setItem(index, 2, QTableWidgetItem(time))
        

    def changeButtonText(self):
        code = self.combo_code.currentText()
        if code not in self.code_of_requested:
            self.button_request.setText("요청하기")
        else:
            self.button_request.setText("중단하기")

    def setCodeToCombo(self):
        tickers = pyupbit.get_tickers()
        value_of_combo = [""]
        for i in tickers:
            if "KRW-" in i: 
                value_of_combo.append(i)
        self.combo_code.addItems(value_of_combo)
        self.combo_code.setCurrentIndex(0)

    def infoRequest(self):
        code = self.combo_code.currentText()
        if code != "":
            if code not in self.code_of_requested:
                self.code_of_requested.append(code)
                self.table_info.setRowCount(len(self.code_of_requested))
                row = len(self.code_of_requested) - 1
                self.table_info.setItem(row, 0, QTableWidgetItem(code))
                codes = ''
                for i in self.code_of_requested:
                    codes+='"%s"'%i
                    if self.code_of_requested.index(i) != len(self.code_of_requested)-1: codes+=", "
                self.worker.requestCode(codes)
            else:
                index = self.code_of_requested.index(code)
                self.code_of_requested.pop(index)
                self.table_info.setRowCount(len(self.code_of_requested))
                for i in range(index, len(self.code_of_requested)):
                    self.table_info.setItem(i, 0, QTableWidgetItem(self.code_of_requested[i]))
            self.combo_code.setCurrentIndex(0)
            self.button_request.setText("요청하기")

            

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())