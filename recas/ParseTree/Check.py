from .Structure import *


class ErrorStructure:
    pass


INPUT_TYPE = List[Tuple[Tuple[str, str], List[Tuple[str, str]]]]


def error_check(recas_sentence: INPUT_TYPE,
                rpt_item_sentences: List[RPTItemSentence],
                unidentified_rpt_item: List[RPTItem]):
    error_rck = error_check_recas_chunk()
    error_rpt = error_check_rpt_sentences(rpt_item_sentences)

    return error_rck + error_rpt


def error_check_recas_chunk():
    return []


def error_check_rpt_sentences(rpt_item_subs: List[RPTItemSentence]):
    """
    Parse Tree를 검사하여 에러 목록을 반환하는 함수
    Args:
        rpt_item_subs: Parse Tree로 구성된 문장

    Returns:
        에러 목록
    """
    data = {
        # 1520 4개 이상의 명사 나열
        "1520": {"limit": 4, "searched": []},
        # 2100 Parse Tree 조사를 제외한 말단 노드의 개수가 25개 초과
        "2100": {"limit": 25, "searched": []},
        # 2200 Parse Tree에서 주문장의 동사의 개수가 5개 이상
        "2200": {"limit": 5, "searched": []},
        # 2300 부사구 수가 [연속으로] 4개 이상
        "2300": {"limit": 4, "searched": []},
        # 2500 수식절의 수가 4개 이상
        "2500": {"limit": 4, "searched": []},
        # 2600 수식하는 절을 수식하는 절 사용
        "2600": {"passed_sen_mod_list": [], "searched": []},
        # 3100 문장에 주어가 없으면 오류
        "3100": {"searched": []},
        # 3500 자동사가 목적어를 가질 때, 단어사전 미구현 이슈로 무조건 타동사로 취급
        "3500": {"searched": []},
        # 3600 타동사가 목적어를 가지지 않을 때, 단어사전 미구현 이슈로 무조건 타동사로 취급
        "3600": {"searched": []},
        # 0000 주어보다 목적어
    }

    __traverse_RPTItemSubs_func_0(rpt_item_subs, data)

    error_list = []

    if len(data["1520"]["searched"]) != 0:
        error_list.append(("1520", data["1520"]["searched"]))

    if len(data["2100"]["searched"]) >= data["2100"]["limit"]:
        error_list.append(("2100", data["2100"]["searched"]))

    if len(data["2200"]["searched"]) != 0:
        error_list.append(("2200", data["2200"]["searched"]))

    if len(data["2300"]["searched"]) != 0:
        error_list.append(("2300", data["2300"]["searched"]))

    if len(data["2500"]["searched"]) >= data["2500"]["limit"]:
        error_list.append(("2500", data["2500"]["searched"]))

    if len(data["2600"]["searched"]) != 0:
        # 중복검사 필요, 중복검사 미구현
        error_list.append(("2600", data["2600"]["searched"]))

    if len(data["3100"]["searched"]) != 0:
        error_list.append(("3100", data["3100"]["searched"]))

    if len(data["3500"]["searched"]) != 0:
        error_list.append(("3500", data["3500"]["searched"]))

    if len(data["3600"]["searched"]) != 0:
        error_list.append(("3600", data["3600"]["searched"]))

    return error_list


def __traverse_RPTItem_func_0(rpt_item: RPTItem, data):
    """
    Parse Tree의 에러 검사를 위한 순회 중, RPT Item에 대한 로직을 구현하는 함수
    세부 로직은 각 에러 코드의 목적에 따라 구현
    Args:
        rpt_item: recas Parse Tree 객체
        data: 검사된 에러 정보

    Returns:
        None

    """
    if rpt_item.index != -1:
        data["2100"]["searched"].append(rpt_item.index)

    if len(rpt_item.mod_list) > 0 and type(rpt_item.mod_list[-1]) == RPTItemSentence:
        data["2500"]["searched"].append(rpt_item.mod_list[-1].index)

    if len(rpt_item.mod_list) > 0 and type(rpt_item.mod_list[-1]) == RPTItemSentence:
        if len(data["2600"]["passed_sen_mod_list"]) > 0:
            data["2600"]["searched"].append(rpt_item.mod_list[-1].index)
        data["2600"]["passed_sen_mod_list"].append(rpt_item.mod_list[-1].index)

    if len(rpt_item.mod_list) > 0:
        __traverse_RPTItemSubs_func_0(rpt_item.mod_list, data)

    if len(rpt_item.mod_list) > 0 and type(rpt_item.mod_list[-1]) == RPTItemSentence:
        del data["2600"]["passed_sen_mod_list"][-1]


def __traverse_RPTItemSentence_func_0(rpt_item_sentence: RPTItemSentence, data):
    """
    Parse Tree의 에러 검사를 위한 순회 중, RPT Item Sentence에 대한 로직을 구현하는 함수
    세부 로직은 각 에러 코드의 목적에 따라 구현
    Args:
        rpt_item_sentence: recas Parse Tree Sentence 객체
        data: 검사된 에러 정보

    Returns:
        None

    """
    if len(rpt_item_sentence.adv_list) > data["2300"]["limit"]:
        for rpt_item in rpt_item_sentence.adv_list:
            data["2300"]["searched"].append(rpt_item.index)

    if len(rpt_item_sentence.sub_list) == 0:
        if rpt_item_sentence.vrb.item.komop_sentence[0].tag not in ["TBF", "TOPRS"]:
            data["3100"]["searched"].append(rpt_item_sentence.vrb.index)

    if len(rpt_item_sentence.obj_list) != 0 and False:
        data["3500"]["searched"].append(rpt_item_sentence.vrb.index)

    if len(rpt_item_sentence.obj_list) == 0:
        if rpt_item_sentence.vrb.item.komop_sentence[0].tag not in ["TBF", "TOPRS"]:
            data["3600"]["searched"].append(rpt_item_sentence.vrb.index)

    __traverse_RPTItemSubs_func_0(rpt_item_sentence.sub_list, data)
    __traverse_RPTItemSubs_func_0(rpt_item_sentence.obj_list, data)
    __traverse_RPTItemSubs_func_0(rpt_item_sentence.adv_list, data)


def __traverse_RPTItemSubs_func_0(rpt_item_subs: List[RPTItemSub], data):
    """
    Parse Tree의 에러 검사를 위한 순회 중, RPT Item Subs에 대한 로직을 구현하는 함수
    세부 로직은 각 에러 코드의 목적에 따라 구현
    Args:
        rpt_item_subs: recas Parse Tree Subs 객체
        data: 검사된 에러 정보

    Returns:
        None

    """
    if len(rpt_item_subs) >= data["1520"]["limit"] and type(rpt_item_subs[0]) == RPTItem:
        for rpt_item_sub in rpt_item_subs:
            if type(rpt_item_sub) == RPTItem:
                data["1520"]["searched"].append(rpt_item_sub.index)
            else:
                raise

    if len(rpt_item_subs) >= data["2200"]["limit"] and type(rpt_item_subs[0]) == RPTItemSentence:
        for rpt_item_sub in rpt_item_subs:
            if type(rpt_item_sub) == RPTItemSentence:
                data["2200"]["searched"].append(rpt_item_sub.index)
            else:
                raise

    for rpt_item_sub in rpt_item_subs:
        if type(rpt_item_sub) == RPTItem:
            __traverse_RPTItem_func_0(rpt_item_sub, data)
        elif type(rpt_item_sub) == RPTItemSentence:
            __traverse_RPTItemSentence_func_0(rpt_item_sub, data)
        else:
            raise



'''
* 1320 동사를 나열할 때는 “~(하)고, ~(하)거나, ~(하)며,”이외 사용              -> (검토필요)
* 1510 명사의 나열 시 ",“, ”와“, ”과“, ”혹은“, ”그리고“, ” 및" 연결 어미 사용   -> (검토필요)
2400 연속된 소유격 수가 3개 이상                              -> (확인 필요) 소유격?
'''