import os
import sys

sys.path.append(os.getcwd())


import recas
from cache import DIMS


def get_dims():
    # mongodb를 사용하기 위한 모의 환경 시작
    dicFile = "data\\DimsWordsDict-210919_0.xlsx"
    dims = DIMS.DIMS(mongoHost="localhost", port=27017)

    dims.loadDictionaryExcel(file=dicFile)
    dims.print_DataFrame()
    db_name = "dimsTermDic"
    col_name = "dictionary"
    dims.mgc[db_name][col_name].drop()
    dims.insertDictionary(dbName=db_name, collectionName=col_name)
    collection = dims.connect2Collection(dbName=db_name, collectionName=col_name)
    return dims


if __name__ == "__main__":
    os.environ["JAVA_HOME"] = "external/jdk-17"
    os.environ["path"] = "external/Graphviz/bin"

    # mongodb 를 사용하기 위한 모의 환경 종료
    DIMS = get_dims()

    sentence_string_list = []
    train_data_path = "data\\sample\\train_data.txt"
    wiki_data_path = "data\\sample\\wiki_sentences_s.txt"

    data_path_list = [train_data_path, wiki_data_path]

    merged_sentence_data = []
    for path in data_path_list:
        try:
            with open(path, 'r') as f:
                merged_sentence_data += f.readlines()
        except:
            with open(path, 'r', encoding="utf-8") as f:
                merged_sentence_data += f.readlines()

    mfile_path = None
    komop_tag_path = "data\\sample\\komop_tags.txt"
    chunk_tag_path = "data\\sample\\chunk_tags.txt"
    chunk_rule_path = 'data\\sample\\chunk_rule.xlsx'
    komop_rule_path = "data\\sample\\komop_rule.xlsx"
    user_dict_path = "data\\sample\\user_dict.txt"

    recas = recas.Utill.Recas(
        chunk_rule_path,
        komop_rule_path,
        komop_tag_path,
        chunk_tag_path,
        user_dict_path,
        DIMS,
        mfile_path
    )
    recas.init_thread()

    save_model_path = "data\\sample\\model23.h5"

    recas.make_model_file(merged_sentence_data, save_model_path, 20)
