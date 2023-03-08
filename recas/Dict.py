# -*- coding: utf8 -*-

# ---------------------------------------- ... ---
# 1. 버전
#  1) 버전 코드		: 1.0.0
#  2) 최종 수정 날짜	: 211022
#  3) 최종 수정자	    : 아주대학교
#
# 2. 코드 목적
#  - 단어사전 DB로부터 전체 단어사전 정보를 수신한다.
#  - 코모란 사용자 사전을 생성한다.
#  - 단어 변환 규칙을 생성한다.(단어사전으로부터)
#
# 3. 주요 데이터 구조
#  dict_table = [dict_item, dict_item, ...]
#  dict_item = {"text":             <string>, //단어사전에 등록된 단어 문자열
#               "recas_type":       <string>, //등록된 단어가 표시될 recas 품사명
#               "recas_ver_type":   <string>, //등록된 단어가 동사격이라면, 목적어 및 부사어 문장성분의 필요 여부
#               "tokenizer":        <string>, //현재는 "komo"으로 고정)
#               "tokenizer_type":   <string>, //"NNP", "NNG", "SW", "VV" 등의 코모란 품사명
#               "category":         <string>}
#
# 4. 공개 함수 설명
#  - load_dict_rule(dict_table=None, dims=None)
#     사전 table 또는 사전 DB를 입력받아 사전 룰을 반환
#     사전 DB를 입력받을 경우 DB 로부터 table 을 가져옴
#     코모란 형태소분석기가 사용할 사용자 사전을 생성함
#
#  - get_dict_table(dims):
#     dims 로부터 dict_table 을 수신하여 반환
#
# 3. 외부 라이브러리 의존성
#  - konlpy=0.5.2
#
# ---------------------------------------- ... ---
from pydantic import BaseModel


class WordManager(object):
    def __init__(self):
        raise

    def synchronize(self):
        raise

    def make_user_dict(self):
        raise

    def append(self):
        raise

    def remove(self):
        raise

    def modify(self):
        raise


def make_dict_rule(dict_table, komoran_dict_path):
    # 코모란에서 토큰 분석을 위해 사용할 사전을 생성
    make_tokenizer_user_dict_from_dict_table(dict_table, komoran_dict_path)

    # tokenizer_type을 recas_type으로 바꾸기 위한 규칙을 생성
    word_dict = make_word_dict_from_dict_table(dict_table)

    return word_dict


def make_tokenizer_user_dict_from_dict_table(dict_table, komoran_dict_path):
    with open(komoran_dict_path, 'w', encoding='UTF8') as f:
        for item in dict_table:
            f.write(str(item["text"]) + "\t" + str(item["tokenizer_type"]) + "\n")
        if len(dict_table) > 0:
            f.write(dict_table[-1]["text"] + "\t" + dict_table[-1]["tokenizer_type"])
    return komoran_dict_path


def make_word_dict_from_dict_table(dict_table):
    word_dict = {}
    for item in dict_table:
        key = item["text"]
        value = item
        word_dict[key] = value
    return word_dict
