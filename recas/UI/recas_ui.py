import sys
import os
from typing import List, Optional, Dict
from pydantic import BaseModel
from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap
from recas.FastAPI_Server.structure import *

import requests
import json
import time


path = os.path.dirname(os.path.abspath(__file__))


# 화면을 띄우는데 사용되는 Class 선언
class WindowClass(QtWidgets.QMainWindow, uic.loadUiType(path + "\\recas.ui")[0]):
    sub_tab: List
    data_table: Dict[str, RecasRequirement2] = {}
    image_data_table: Dict = {}

    def __init__(self, debug_info=None):
        super().__init__()
        self.init_qt()
        self.init_action()
        self.host = "http://localhost:8000"

        # 디버그 코드
        if "default_sentences" in debug_info:
            self.input_text.setText(debug_info["default_sentences"])

    def init_qt(self):
        # 내부 아이템들 연결
        self.setupUi(self)
        self.treeView.setModel(QStandardItemModel())

    def init_action(self):
        self.pushButton.clicked.connect(self.push_button_start_clicked)
        self.pushButton_new.clicked.connect(self.push_button_new_clicked)
        self.pushButton_update.clicked.connect(self.push_button_update_clicked)
        self.pushButton_delete.clicked.connect(self.push_button_remove_clicked)
        self.treeView.doubleClicked.connect(self.tree_view_item_double_clicked)
        self.toolButton.clicked.connect(self.push_button_refresh_clicked)

    def init_cache(self):
        pass

    def push_button_start_clicked(self):
        text = self.input_text.toPlainText()
        sentence_list = text.split("\n")
        result_list = []
        for sentence in sentence_list:
            if len(sentence.rstrip()) != 0:
                param = [RecasRequirement2(pm_ID="common", req_ID=str(time.time()), req_str=sentence)]
                send_data = RecasReq2(method="", param=param)
                url = self.host + "/recas/check_2"
                try:
                    response = requests.post(url=url, data=json.dumps(send_data.dict()))
                    response_content_json_str = response.content.decode('utf-8')
                    response_content_json = json.loads(response_content_json_str)
                    result_list.append(response_content_json)

                except Exception as ex:
                    print(ex)

        # 출력 화면 생성
        model = self.treeView.model()
        count = 0
        for list_item in result_list:
            for value in list_item.values():
                value_ = RecasRequirement2.parse_obj(value)
                sentence_item = QStandardItem(value_.req_str)
                model.setItem(count, 0, sentence_item)
                count += 1
                self.data_table[value_.req_str] = value_

    def push_button_new_clicked(self):
        text = self.textEdit_1.toPlainText()
        recas_type = self.textEdit_2.toPlainText()
        recas_ver_type = self.textEdit_3.toPlainText()
        tokenizer_type = self.textEdit_4.toPlainText()
        word_data = {
            "text": text,
            "recas_type": recas_type,
            "recas_ver_type": recas_ver_type,
            "tokenizer_type": tokenizer_type
        }
        if self.use_worker:
            self.worker.add_dict(word_data)
        else:
            self.recas.komop_tokenizer.add_dict(word_data)

    def push_button_update_clicked(self):
        text = self.textEdit_1.toPlainText()
        recas_type = self.textEdit_2.toPlainText()
        recas_ver_type = self.textEdit_3.toPlainText()
        tokenizer_type = self.textEdit_4.toPlainText()
        word_data = {
            "text": text,
            "recas_type": recas_type,
            "recas_ver_type": recas_ver_type,
            "tokenizer_type": tokenizer_type
        }
        if self.use_worker:
            self.worker.update_dict(word_data)
        else:
            self.recas.komop_tokenizer.update_dict(word_data)

    def push_button_remove_clicked(self):
        text = self.textEdit_1.toPlainText()
        recas_type = self.textEdit_2.toPlainText()
        recas_ver_type = self.textEdit_3.toPlainText()
        tokenizer_type = self.textEdit_4.toPlainText()
        word_data = {
            "text": text,
            "recas_type": recas_type,
            "recas_ver_type": recas_ver_type,
            "tokenizer_type": tokenizer_type
        }
        if self.use_worker:
            self.worker.remove_dict(word_data)
        else:
            self.recas.komop_tokenizer.remove_dict(word_data)

    def tree_view_item_double_clicked(self, index):
        model = self.treeView.model()
        sentence_key = model.data(index)
        if sentence_key in self.data_table:
            output_data = self.data_table[sentence_key]
            self.output_1.setText(output_data.fullStr["text_data"])

            req_id = output_data.req_ID
            url = self.host + "/recas/result/" + req_id

            try:
                response = requests.get(url=url)
            except Exception:
                raise
            if req_id in self.image_data_table:
                pixmap = self.image_data_table[req_id]
                self.output_2.setPixmap(pixmap)
            else:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.image_data_table[req_id] = pixmap
                self.output_2.setPixmap(pixmap)
        else:
            pass

    def push_button_refresh_clicked(self):
        pass


def show_main_window(debug_info=None):
    app = QtWidgets.QApplication(sys.argv)
    main_window_ = WindowClass(debug_info)

    main_window_.show()
    app.exec_()


if __name__ == "__main__":
    show_main_window()



#
# import sys
# import os
# from cache import DIMS
# from typing import List
# from PyQt5 import uic, QtWidgets
# from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap
# from recas.Worker.worker import Worker
# from recas.Worker.recasworkers import recas_init_data
# from recas.Utill import get_recas_process_class
#
#
# def get_dims():
#     # mongodb를 사용하기 위한 모의 환경 시작
#     dicFile = "data\\DimsWordsDict-210919_0.xlsx"
#     dims = DIMS.DIMS(mongoHost="localhost", port=27017)
#
#     dims.loadDictionaryExcel(file=dicFile)
#     dims.print_DataFrame()
#     dbName = "dimsTermDic"
#     colName = "dictionary"
#     dims.mgc[dbName][colName].drop()
#     dims.insertDictionary(dbName=dbName, collectionName=colName)
#     collection = dims.connect2Collection(dbName=dbName, collectionName=colName)
#     return dims
#
#
# path = os.path.dirname(os.path.abspath(__file__))
#
#
# # 화면을 띄우는데 사용되는 Class 선언
# class WindowClass(QtWidgets.QMainWindow, uic.loadUiType(path + "\\recas.ui")[0]):
#     sub_tab: List
#     data_table = {}
#     use_worker = True
#
#     def __init__(self):
#         super().__init__()
#         self.init_qt()
#         self.init_action()
#         self.worker = Worker()
#         self.recas = get_recas_process_class(recas_init_data)
#         get_dims()
#
#     def init_qt(self):
#         # 내부 아이템들 연결
#         self.setupUi(self)
#         self.treeView.setModel(QStandardItemModel())
#
#     def init_action(self):
#         self.pushButton.clicked.connect(self.push_button_clicked)
#         self.pushButton_new.clicked.connect(self.pushButton_new_clicked)
#         self.pushButton_update.clicked.connect(self.pushButton_update_clicked)
#         self.pushButton_delete.clicked.connect(self.push_button_remove_clicked)
#         self.treeView.doubleClicked.connect(self.tree_view_item_double_clicked)
#
#     def init_cache(self):
#         pass
#
#     def push_button_clicked(self):
#         text = self.input_text.toPlainText()
#         sentence_list = text.split("\n")
#         if self.use_worker:
#             output_list = self.worker.run_sentence_list(sentence_list, debug=True)
#         else:
#             output_list = self.recas.make_recas_sentence(sentence_list, visualize_debug=True, debug_output=True)
#
#         # 출력 화면 생성
#         model = self.treeView.model()
#         for i, output in enumerate(output_list):
#             if "save_name" in output:
#                 sentence_item = QStandardItem(output["save_name"])
#                 model.setItem(i, 0, sentence_item)
#                 self.data_table[output["save_name"]] = output_list[i]
#
#     def pushButton_new_clicked(self):
#         text = self.textEdit_1.toPlainText()
#         recas_type = self.textEdit_2.toPlainText()
#         recas_ver_type = self.textEdit_3.toPlainText()
#         tokenizer_type = self.textEdit_4.toPlainText()
#         word_data = {
#             "text": text,
#             "recas_type": recas_type,
#             "recas_ver_type": recas_ver_type,
#             "tokenizer_type": tokenizer_type
#         }
#         if self.use_worker:
#             self.worker.add_dict(word_data)
#         else:
#             self.recas.komop_tokenizer.add_dict(word_data)
#
#     def pushButton_update_clicked(self):
#         text = self.textEdit_1.toPlainText()
#         recas_type = self.textEdit_2.toPlainText()
#         recas_ver_type = self.textEdit_3.toPlainText()
#         tokenizer_type = self.textEdit_4.toPlainText()
#         word_data = {
#             "text": text,
#             "recas_type": recas_type,
#             "recas_ver_type": recas_ver_type,
#             "tokenizer_type": tokenizer_type
#         }
#         if self.use_worker:
#             self.worker.update_dict(word_data)
#         else:
#             self.recas.komop_tokenizer.update_dict(word_data)
#
#     def push_button_remove_clicked(self):
#         text = self.textEdit_1.toPlainText()
#         recas_type = self.textEdit_2.toPlainText()
#         recas_ver_type = self.textEdit_3.toPlainText()
#         tokenizer_type = self.textEdit_4.toPlainText()
#         word_data = {
#             "text": text,
#             "recas_type": recas_type,
#             "recas_ver_type": recas_ver_type,
#             "tokenizer_type": tokenizer_type
#         }
#         if self.use_worker:
#             self.worker.remove_dict(word_data)
#         else:
#             self.recas.komop_tokenizer.remove_dict(word_data)
#
#     def tree_view_item_double_clicked(self, index):
#         model = self.treeView.model()
#         sentence_key = model.data(index)
#         if sentence_key in self.data_table:
#             output_data = self.data_table[sentence_key]
#             self.output_1.setText(output_data["text_data"])
#             img_path = output_data["save_name"] + ".jpg"
#             self.output_2.setPixmap(QPixmap(img_path))
#         else:
#             pass
#
#
# def show_main_window():
#     app = QtWidgets.QApplication(sys.argv)
#     main_window_ = WindowClass()
#
#     main_window_.show()
#     app.exec_()
#
#
# if __name__ == "__main__":
#     show_main_window()

