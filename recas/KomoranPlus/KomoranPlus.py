#!/recas/KomoranPlus/KomoranPlus.py
# -*- coding: utf-8 -*-
"""Komoran Plus 모듈

    ---------------------------------------- ... ---
    1. 버전
     1) 버전 코드		: 1.0.0
     2) 최종 수정 날짜	: 220603
     3) 최종 수정자	    : 아주대학교

    2. 코드 목적
     - 문장의 형태소를 분석하여 원하는 Tag로 분류함
     - Komoran의 기능과 유사하며, recas의 목적에 따라 수정된 결과를 출력

    3. 외부 라이브러리 의존성
     - konlpy
     - numpy
    ---------------------------------------- ... ---

"""

import json
import numpy as np
from konlpy.tag import Komoran
from typing import List

from . import SequenceRule
from . import RecoverPosition
from recas.Dict import make_dict_rule, make_tokenizer_user_dict_from_dict_table

print_error = False


def make_json_output(file_name, output):
    """json화 함수

     지정된 경로에 json 파일을 생성

    Args:
        file_name (test): json 파일 저장 이름
        output (any): 저장 대상의, json 화 할 수 있는 형태의 객체

    Returns:
       bool: true일 시 성공, false 일 시 실패
    """
    try:
        with open(file_name + '.json', 'w', encoding='utf-8') as make_file:
            json.dump(output, make_file, ensure_ascii=False, indent="\t")
        return True
    except:
        return False


def get_letter_from_tokens(sentence, tokens):
    """토큰 정보 복원 함수

     토큰이 가지고 있더 위치 정보와 변형 전 문자열을 확인하여 반환하는 함수

    Args:
        sentence(string): 원본 문장
        tokens(list[Tuple[string, string]]): komoran.pos를 수행하여 나온 결과. 토큰 리스트

    Returns:
        List[List[Tuple[string, string], string, Tuple(int, int)]]:
         다음 형태로 구성된 정보가 리스트로 묶여 반환됨
          List[토큰, 원본 문자열, 위치정보]
           토큰(Tuple[string, string]): (단어 문자열, Tag 문자열)로 구성된 토큰
           원본 문자열(string): 토큰화 되기 전 문장에서의 문자열
           위치 정보(Tuple[int, int]) (시작 위치, 종료 위치)로 구성된 Tuple
    """

    recover_list = RecoverPosition.get_pos_from_seq(sentence, tokens)
    output = []
    try:
        for token, l0, l1 in recover_list:
            output.append([token, sentence[l0:l1+1], (l0, l1)])
        return output
    except:
        print("Error during process next list.")
        print(recover_list)


def komo2recas(sentence, tokenizer, rule_class_komop, rule_class_chunk, err_check_list):
    """문장을 komop, recas 토큰으로 바꾸어주는 함수

    Args:
        sentence(string): 원본 문장
        tokenizer(konlpy.tag.Komoran.komoran): 코모란 형태소 분석기 객체
        rule_class_komop: komop 규칙이 포함된 rule_class
        rule_class_chunk: chunk 규칙이 포함된 rule_class
        err_check_list(List[str]): 해당 리스트에 토큰 명이 포함되지 않을 경우 에러 토큰으로 취급함

    Returns:
        List[]
         (komop tag 리스트, chunk tag)의 리스트를 반환
        # TODO
    """

    if len(sentence) == 0:
        return False

    unit_token_list = make_predict_data(sentence, tokenizer, rule_class_komop, rule_class_chunk, err_check_list)
    output = []
    pass_count = 0
    tmp = []
    for item in unit_token_list:
        tmp.append(item[0])
    unit_token_list = tmp

    for i in range(len(unit_token_list)):
        if pass_count > 0:
            pass_count -= 1
            continue
        else:
            for j in range(min(len(unit_token_list)-i, 3), 0, -1):
                temp_list = []
                for k in range(j):
                    temp_list += unit_token_list[i + k]
                converted = rule_class_chunk.convert(temp_list, err_check_list)
                if len(converted) == 1 and converted[0][1] != 'ERR':
                    output.append((temp_list, converted[0]))
                    pass_count = j - 1
                    break
                elif j == 1:
                    converted = rule_class_chunk.convert(unit_token_list[i], err_check_list)
                    output.append((unit_token_list[i], converted[0]))

    return output


def komo2recas_(sentence, tokenizer, rule_class_komop, rule_class_chunk, err_check_list):
    """미사용 함수

    """
    if len(sentence) == 0:
        return False

    unit_token_list = make_predict_data(sentence, tokenizer, rule_class_komop, rule_class_chunk, err_check_list)
    output = []
    pass_count = 0
    tmp = []
    for item in unit_token_list:
        tmp.append(item[0])
    unit_token_list = tmp

    for i in range(len(unit_token_list)):
        if pass_count > 0:
            pass_count -= 1
            continue
        else:
            for j in range(len(unit_token_list)-i, 0, -1):
                temp_list = []
                for k in range(j):
                    temp_list += unit_token_list[i + k]
                converted = rule_class_chunk.convert(temp_list, err_check_list)
                if len(converted) == 1 and converted[0][1] != 'ERR':
                    output.append((temp_list, converted[0]))
                    pass_count = j - 1
                    break
                elif j == 1:
                    converted = rule_class_chunk.convert(unit_token_list[i], err_check_list)
                    output.append((unit_token_list[i], converted[0]))

    return output


def make_training_data(sentences, tokenizer, rule_class_komop,
                       rule_class_chunk, err_check_list,
                       output_path=None, txt_path=None):
    """학습용 데이터를 생성하는 함수

    Args:
        sentences(str): 원본 문장
        tokenizer: 코모란 토크나이저 객체
        rule_class_komop: komop 룰을 적용한 룰클래스 객체
        rule_class_chunk: chunk 룰을 적용한 룰클래스 객체
        err_check_list: 토큰의 tag가 리스트에 있지 않을 시 error 토큰으로 판정
        output_path: 생성한 학습 데이터를 저장하는 경로
        txt_path: 파일로부터 문장들을 읽어올 시 해당 파일 경로

    Returns:
        학습 데이터
    """
    train_data = []
    if txt_path is not None:
        with open(txt_path, 'r', encoding='UTF8') as file_data:
            while True:
                line = file_data.readline()
                if not line:
                    break
                sentences = line.split(".")
                for sentence in sentences:
                    sentence = sentence.replace('\n', '')
                    if len(sentence) > 0:
                        train_data += komo2recas(sentence + '.', tokenizer, rule_class_komop, rule_class_chunk,
                                                 err_check_list)

    if sentences is not None:
        for sentence in sentences:
            if len(sentence) == 0:
                continue
            train_data += komo2recas(sentence, tokenizer, rule_class_komop, rule_class_chunk, err_check_list)

    if output_path is not None:
        make_json_output(output_path, train_data)
        np.savez(output_path, train_data)

    return train_data


def make_predict_data(sentence, tokenizer, rule_class_komop, rule_class_chunk, err_check_list):
    """

    Args:
        sentence: 대상 문장 텍스트
        tokenizer: 코모란 토크나이저 객체
        rule_class_komop: komop 룰을 적용한 룰클래스 객체
        rule_class_chunk: chunk 룰을 적용한 룰클래스 객체
        err_check_list: 토큰의 tag가 리스트에 있지 않을 시 error 토큰으로 판정

    Returns:
        예측 결과
    """
    if len(sentence.strip()) == 0:
        return []
    sentence = sentence.replace('\n', ' ')
    komo_token_list = tokenizer.pos(sentence)
    pos_data = get_letter_from_tokens(sentence, komo_token_list)

    def pos_item2token(pos_item_list):
        output_ = []
        for pos_item in pos_item_list:
            output_.append(pos_item[0])
        output_komop = rule_class_komop.convert(output_)
        output_chunk = rule_class_chunk.convert(output_komop, err_check_list)
        return output_komop, output_chunk

    output = []
    output_item = []
    try:
        for i, item in enumerate(pos_data):
            if len(output_item) == 0:
                output_item.append(item)
            elif (output_item[-1][2][1] - item[2][0]) >= -1:
                output_item.append(item)
            elif (output_item[-1][2][1] - item[2][0]) == -2:
                output.append(pos_item2token(output_item))
                output_item = [item]
            else:
                output.append(pos_item2token(output_item))
                output_item = [item]
        output.append(pos_item2token(output_item))
    except Exception as ex:
        print("ERROR at pos_item2token, " + str(pos_data))

    return output


class KomoranPlus:
    """
    #TODO
    """
    tokenizer: any
    err_check_list = ["SUB", "OBJ", "MOD", "ADV", "NNPL", "NNGL", "QNT", "TIMB", "TIMG", "TIMS", "TIMO", "TIML",
                      "VVCL", "VVCC", "VVCG", "VVCE", "VVTL", "VVTC", "VVTG", "VVTE", "NNPG", "TOPRN",
                      "VVEL", "VVEC", "VVEG", "VVEE", "COND_KEY"]

    dict_used_rule_class: List[SequenceRule.RuleClass] = []

    def __init__(
            self,
            chunk_rule_path: str,
            komop_rule_path: str,
            user_dict_path: str,
            dict_table=None,
            tags_save_path: str = None
    ):
        # 단어사전
        if dict_table is not None:
            word_dict = make_dict_rule(dict_table=dict_table, komoran_dict_path=user_dict_path)
        else:
            word_dict = {}
        # dict_rule = None

        # 초기화(객체 생성)
        self.user_dict_path = user_dict_path
        self.rule_class_komop = SequenceRule.RuleClass(komop_rule_path, word_dict=word_dict)
        self.dict_used_rule_class.append(self.rule_class_komop)
        self.rule_class_komop_no_dict = SequenceRule.RuleClass(komop_rule_path)
        self.rule_class_chunk = SequenceRule.RuleClass(chunk_rule_path)

    def init_thread(self):
        self.tokenizer = Komoran(userdic=self.user_dict_path)

    def init_dict(self):
        make_tokenizer_user_dict_from_dict_table(self.dict_used_rule_class[0].word_dict, self.user_dict_path)
        self.tokenizer = Komoran(userdic=self.user_dict_path)

    def get_training_data(self, sentences, txt_path=None):
        return make_training_data(sentences,
                                  self.tokenizer, self.rule_class_komop_no_dict, self.rule_class_chunk,
                                  self.err_check_list, txt_path
                                  )

    def get_predict_data(self, sentence):
        predict = make_predict_data(sentence, self.tokenizer, self.rule_class_komop, self.rule_class_chunk, None)
        return predict

    def get_dummy_chunk(self, sentence):
        data_ = komo2recas(sentence, self.tokenizer, self.rule_class_komop, self.rule_class_chunk, self.err_check_list)
        output = []
        for item in data_:
            new_item = (item[1], item[0])
            output.append(new_item)

        return output

    # item = {"text": "", "recas_type": "", "recas_ver_type": "", "tokenizer": "", "tokenizer_type": ""}
    def add_dict(self, item):
        for rule_class in self.dict_used_rule_class:
            if rule_class.word_dict is not None:
                if item["text"] not in rule_class.word_dict:
                    rule_class.word_dict[item["text"]] = item
                    self.init_dict()
                    return True
                else:
                    return False
            else:
                raise

    def remove_dict(self, item):
        for rule_class in self.dict_used_rule_class:
            if rule_class.word_dict is not None:
                if item["text"] in rule_class.word_dict:
                    del rule_class.word_dict[item["text"]]
                    self.init_dict()
                    return True
                else:
                    return False
            else:
                raise

    def update_dict(self, item):
        for rule_class in self.dict_used_rule_class:
            if rule_class.word_dict is not None:
                if item["text"] in rule_class.word_dict:
                    rule_class.word_dict[item["text"]] = item
                    self.init_dict()
                    return True
                else:
                    return False
            else:
                raise
