# -*- coding: utf8 -*-


## ---------------------------------------- ... ---
# 1. 버전
#  1) 버전 코드		: 1.0.0
#  2) 최종 수정 날짜	: 211022
#  3) 최종 수정자	    : 아주대학교
#
# 2. 코드 목적
#  - parsetree 생성 후 생략된 주어 또는 목적어를 정해진 규칙에 따라 가져온다.
#
# 3. 주요 데이터 구조
#  - 복사된 노드에 대하여, pos값은 -1로 지정된다.
#
# 4. 공개 함수 설명
#  - ReBuild(self, parsetree)
#     리스트로 이어진 문장들의 주어(앞)를 가져온다.
#     종속 문장의 주어/목적어 가져온다.
#     해당 과정에서 특정 노드가 복제되며, 복제된 노드의 pos값은 -1을 가져 후에 구분이 가능하다.
#
#  - get_unique_sentences(nodelist)
#     노드 리스트(전체 문장)을 입력으로 받아 단위 문장 리스트를 출력한다.
#     여기서 단위 문장이란, 동사가 있는 절을 포함한다.
#
# ---------------------------------------- ... ---
from .Structure import *


# func_0: 리스트로 이어진 문장들의 주어(앞) 가져오기
# funk_1: 수식 문장의 주어가 없을 경우 상위 문장의 주어 또는 수식 대상을 주어로 가져오기(미구현)


def restore_skipped_chunk(rpt_item_sentences: List[RPTItemSentence]):
    """
    생략된 chunk(뒷문장의 주어, 수식문장의 주어 및 목적어)를 복원하는 함수
    Args:
        rpt_item_sentences: parse tree

    Returns:
        복원된 parse tree

    """
    rpt_item_sentences_clone = traverse_RPTItemSubs_deepcopy(rpt_item_sentences)
    rpt_item_sentences_func_0 = __traverse_rpt_item_sub_list_func_0(rpt_item_sentences_clone, None)

    output = rpt_item_sentences_func_0
    return output


def __traverse_rpt_item_func_0(rpt_item: RPTItem):
    if len(rpt_item.mod_list) > 0:
        rpt_item.mod_list = __traverse_rpt_item_sub_list_func_0(rpt_item.mod_list,
                                                                traverse_RPTItem_deepcopy(rpt_item, True, True))


def __traverse_rpt_item_sentence_func_0(rpt_item_sentence: RPTItemSentence, front_sbj_list, rpt_item_parent):
    __traverse_rpt_item_sub_list_func_0(rpt_item_sentence.sub_list, None)
    __traverse_rpt_item_sub_list_func_0(rpt_item_sentence.obj_list, None)
    __traverse_rpt_item_sub_list_func_0(rpt_item_sentence.adv_list, None)

    if len(rpt_item_sentence.sub_list) == 0:
        rpt_item_sentence.sub_list = traverse_RPTItemSubs_deepcopy(front_sbj_list, restored=True)

    # 수식하는 대상을 주어 또는 목적어로 가져옴
    if rpt_item_parent is not None:
        if True:  # 타동사일 때
            if len(rpt_item_sentence.obj_list) == 0:
                rpt_item_sentence.obj_list.append(traverse_RPTItem_deepcopy(rpt_item_parent, True, True))
            elif len(rpt_item_sentence.sub_list) == 0:
                rpt_item_sentence.sub_list.append(traverse_RPTItem_deepcopy(rpt_item_parent, True, True))
        else:
            if len(rpt_item_sentence.sub_list) == 0:
                rpt_item_sentence.sub_list.append(traverse_RPTItem_deepcopy(rpt_item_parent, True, True))

    return rpt_item_sentence.sub_list


def __traverse_rpt_item_sub_list_func_0(rpt_item_sub_list: List[RPTItemSub], rpt_item_parent):
    rpt_item_sentence_sbj = []
    output = []
    for rpt_item_sub in rpt_item_sub_list:
        if type(rpt_item_sub) == RPTItem:
            __traverse_rpt_item_func_0(rpt_item_sub)
        elif type(rpt_item_sub) == RPTItemSentence:
            rpt_item_sentence_sbj = __traverse_rpt_item_sentence_func_0(rpt_item_sub, rpt_item_sentence_sbj,
                                                                        rpt_item_parent)
        output.append(rpt_item_sub)
    return output


def get_unit_sentence(rpt_item_sentences: List[RPTItemSentence], qua=False):
    copied = traverse_RPTItemSubs_deepcopy(rpt_item_sentences)
    cond_sentences = __traverse_rpt_item_sub_list_func_1(copied, 0, qua=qua)

    return cond_sentences


def get_unit_sentence_info(rpt_item_sentences: List[RPTItemSentence]):
    output = []

    unit_sentences = get_unit_sentence(rpt_item_sentences, qua=True)
    for i, (qua0, qua1, qua2, unit_sentence) in enumerate(unit_sentences):
        sentence_info = {
            "TYPE": "M",  # "C"/"M",
            "ID": i,  # 문장번호(INT),
            "QUA": "",  # QUA 형태 참조,
            "SUB": "",  # 명사 형태 참조,
            "OBJ": "",  # 명사 형태 참조,
            "ADV": "",  # ADV 형태 참조,
            "VER": "",  # VER 형태 참조,
            "TRS": "",
            "TIM": "",
        }
        if qua2 is not None:
            sentence_info["QUA"] = [qua0, qua1, qua2]
        sub_list = []
        for item in unit_sentence.sub_list:
            sub_list.append(RPTItem2text(item))
        sentence_info["SUB"] = str(sub_list)

        obj_list = []
        for item in unit_sentence.obj_list:
            obj_list.append(RPTItem2text(item))
        sentence_info["OBJ"] = str(obj_list)

        adv_list = []
        for item in unit_sentence.adv_list:
            adv_list.append(RPTItem2text(item))

        if len(unit_sentence.adv_list) > 0:
            adv_usage = unit_sentence.adv_list[-1].item.komop_sentence[-1].text
            sentence_info["adv"] = str({"TARGET": adv_list, "USAGE": adv_usage})

        sentence_info["VER"] = str(RPTItem2text(unit_sentence.vrb))

        # "~하기 시작"이 있을 때 "시작" -> TRG
        searched_tim = search_RPTItem_contain_komop_tag(unit_sentence.adv_list, "TRS")
        if searched_tim is not None:
            sentence_info["TIM"] = str(searched_tim)

        # "전", "중", 후", "도중"이 있을 때 "전" -> TBF
        searched_trg = search_RPTItem_contain_komop_tag(unit_sentence.adv_list, "TBF")
        if searched_trg is not None:
            sentence_info["TRS"] = str(searched_trg)

        output.append(sentence_info)
        if unit_sentence.vrb.item.chunk_item.tag in ["VVCC"]:
            for output_ in output:
                output_["TYPE"] = "C"

    return output


def get_testcase_text(rpt_item_sentences: List[RPTItemSentence], signal_names: List[str]):
    SIGN_TABLE = {
        "후": "<",
        "이후": "<=",
        "전": ">",
        "이전": ">=",
        "같": "==",
        "틀리": "!=",
        "다르": "!=",
        "아니": "!=",
        "크": ">",
        "길": ">",
        "작": "<",
        "적": "<",
        "짧": "<",
        "이상": ">=",
        "초과": ">",
        "이하": "<=",
        "미만": "<",
    }

    cond_sentence_index = -1
    for i, rpt_item_sentence in enumerate(rpt_item_sentences):
        if rpt_item_sentence.vrb.item.chunk_item.tag in ["VVTC", "VVEC", "VVCC"]:
            cond_sentence_index = i

    # cond_sentences: List[RPTItemSentence] = __traverse_rpt_item_sub_list_func_1(
    #     rpt_item_sentences[:cond_sentence_index + 1], 0)
    cond_sentences: List[RPTItemSentence] = rpt_item_sentences[:cond_sentence_index + 1]

    output = ""
    for unit_sentence in cond_sentences:
        unit_exp = ""
        # 신호 확인
        if len(unit_sentence.obj_list) > 0:
            in_sig = rpt_item_list2str(unit_sentence.obj_list)
        elif len(unit_sentence.sub_list) > 0:
            in_sig = rpt_item_list2str(unit_sentence.sub_list)
        elif unit_sentence.vrb.item.chunk_item.tag in ["VVEC", "VVEL", "VVEE"]:
            in_sig = ""
        else:
            continue

        # 다음과 같은 예시에 대하여 (신호==On)을 생성 / 신호를 On으로 전송한다.
        for item in unit_sentence.adv_list:
            last_pos = item.item.komop_sentence[-1]
            if last_pos.tag == "JKBA" and last_pos.text in ["로", "으로"]:
                in_sig += "==" + komop_item_list2str(item.item.komop_sentence[:-1])
                break

        unit_exp += in_sig

        # 트리거 조건
        for i, komop_item in enumerate(unit_sentence.vrb.item.komop_sentence):
            if komop_item.tag == "TRS":
                unit_exp += " && " + "tense==1"
        for chunk_item in unit_sentence.adv_list:
            text = chunk_item.item.chunk_item.text
            tag = chunk_item.item.chunk_item.tag
            if tag in ["TIMB", "TIMG", "TIMS", "TIMO", "TIML", ]:
                if text in ["도중"]:
                    unit_exp += " && " + "tense==2"
                    break
                elif text in ["후"]:
                    flag = False
                    # 임시 코드
                    for mod_item in chunk_item.mod_list:
                        if type(mod_item) == RPTItem and mod_item.item.chunk_item.tag in ["QNT"]:
                            mod_item_text = mod_item.item.chunk_item.text
                            unit_exp += " && " + mod_item_text + SIGN_TABLE[text] + "timer"
                            flag = True
                    if flag is False:
                        unit_exp += " && " + "tense==3"
                    break
        ver_chunk_item = unit_sentence.vrb
        for ver_komop_item in ver_chunk_item.item.komop_sentence:
            text = ver_komop_item.text
            tag = ver_komop_item.tag
            if tag in ["TBF", "TIMB", "TIMG", "TIMS", "TIMO", "TIML", ]:
                if text in ["도중"]:
                    unit_exp += " && " + "tense==2"
                    break
                elif text in ["후"]:
                    flag = False
                    # 임시 코드
                    for mod_item in ver_chunk_item.mod_list:
                        if type(mod_item) == RPTItem and mod_item.item.chunk_item.tag in ["QNT"]:
                            mod_item_text = mod_item.item.chunk_item.text
                            unit_exp += " && " + mod_item_text + SIGN_TABLE[text] + "timer"
                            flag = True
                    if flag is False:
                        unit_exp += " && " + "tense==3"
                    break

        # 동사에 시제가 포함될 때
        for i, komop_item in enumerate(unit_sentence.vrb.item.komop_sentence):
            if komop_item.tag == "VCP":
                # 이상, 이하, 미만, 초과, ~이면
                if i > 0:
                    target_text = unit_sentence.vrb.item.komop_sentence[i - 1].text
                    target_tag = unit_sentence.vrb.item.komop_sentence[i - 1].tag

                    if target_text in ["이상", "이하", "미만", "초과", ]:
                        unit_exp = rpt_item_list2str(unit_sentence.sub_list) \
                                   + SIGN_TABLE[target_text] \
                                   + rpt_item_list2str(unit_sentence.vrb.mod_list)
                    elif target_text in ["후"]:
                        flag = False

                        for mod_item in unit_sentence.vrb.mod_list:
                            if type(mod_item) == RPTItem and mod_item.item.chunk_item.tag in ["QNT"]:
                                mod_item_text = mod_item.item.chunk_item.text
                                unit_exp += mod_item_text + SIGN_TABLE[target_text] + "timer"
                                flag = True
                        if flag is False:
                            unit_exp += " && " + "tense==3"
                    elif target_tag in ["TOPRE"]:
                        unit_exp = komop_item_list2str(unit_sentence.vrb.item.komop_sentence[1:i])
                    else:
                        unit_exp = rpt_item_list2str(unit_sentence.sub_list) \
                                   + "==" \
                                   + target_text

            elif komop_item.tag == "TBF3":
                unit_exp = rpt_item_list2str(unit_sentence.sub_list) \
                           + SIGN_TABLE[komop_item.text] \
                           + rpt_item_list2str(unit_sentence.vrb.mod_list)

            elif komop_item.tag == "VVA" and komop_item.text in ["크", "작", "길", "적", "짧"]:
                for chunk_item in unit_sentence.adv_list:
                    for i2, komop_item2 in enumerate(chunk_item.item.komop_sentence):
                        if komop_item2.tag == "JKB" and komop_item2.text == "보다" and i2 > 0:
                            target_text = chunk_item.item.komop_sentence[i2 - 1].text
                            unit_exp = rpt_item_list2str(unit_sentence.sub_list) \
                                       + SIGN_TABLE[komop_item.text] \
                                       + target_text
        output += " && (" + unit_exp + ")"
    if len(output) > 5:
        return output[4:]
    return output


def rpt_item_list2str(rpt_item_list: List[RPTItem]):
    output = ""
    for rpt_item in rpt_item_list:
        for komop_item in rpt_item.item.komop_sentence:
            if komop_item.tag not in ["LIST", "LISTAND", "LISTOR", "JKSA", "JKBA", "JKOA", "JKGA", "JKB", "JKG"]:
                output += komop_item.text
                output += " && "
    return output[:-4]


def komop_item_list2str(komop_item_list: List[KomoPItem]):
    output = ""
    for komop_item in komop_item_list:
        output += komop_item.text
    return output


def __traverse_rpt_item_func_1(rpt_item: RPTItem, sentence_num, sub_target=None, qua=False):
    output = []
    if len(rpt_item.mod_list) > 0:
        output += __traverse_rpt_item_sub_list_func_1(rpt_item.mod_list, sentence_num,
                                                      (sub_target[0], rpt_item.item.chunk_item.text), qua)
        rpt_item.mod_list = traverse_RPTItemSubs_deepcopy(rpt_item.mod_list, no_sentence=True)
    return output


def __traverse_rpt_item_sentence_func_1(rpt_item_sentence: RPTItemSentence, sentence_num, sub_target=None, qua=False):
    output = []
    output += __traverse_rpt_item_sub_list_func_1(rpt_item_sentence.sub_list, sentence_num + len(output), ("SUB", None),
                                                  qua)
    output += __traverse_rpt_item_sub_list_func_1(rpt_item_sentence.obj_list, sentence_num + len(output), ("OBJ", None),
                                                  qua)
    output += __traverse_rpt_item_sub_list_func_1(rpt_item_sentence.adv_list, sentence_num + len(output), ("ADV", None),
                                                  qua)
    if sub_target is not None:
        if qua:
            output.append([sentence_num + len(output), sub_target[0], sub_target[1], rpt_item_sentence])
        else:
            output.append(rpt_item_sentence)
    else:
        if qua:
            output.append([sentence_num + len(output), -1, None, rpt_item_sentence])
        else:
            output.append(rpt_item_sentence)
    return output


def __traverse_rpt_item_sub_list_func_1(rpt_item_sub_list: List[RPTItemSub], sentence_num, sub_target=None, qua=False):
    output = []
    for i, rpt_item_sub in enumerate(rpt_item_sub_list):
        if type(rpt_item_sub) == RPTItem:
            output += __traverse_rpt_item_func_1(rpt_item_sub, sentence_num + len(output), sub_target, qua=qua)
        elif type(rpt_item_sub) == RPTItemSentence:
            output += __traverse_rpt_item_sentence_func_1(rpt_item_sub, sentence_num + len(output), sub_target, qua=qua)

    return output


def RPTItem2text(target: RPTItem):
    output = {
        "TEXT": target.item.chunk_item.text
    }
    if len(target.mod_list) > 0:
        text = RPTItem2text_sub(target.mod_list)
        output["MODIFY"] = text
    return output


def RPTItem2text_sub(target: Union[RPTItem, RPTItemSentence, List[RPTItemSub]]):
    if isinstance(target, RPTItem):
        output = target.item.chunk_item.text
        if len(target.mod_list) > 0:
            output = RPTItem2text_sub(target.mod_list) + " " + output
        return output

    elif isinstance(target, List):
        output = ""
        for item in target:
            output += RPTItem2text_sub(item) + ","
        return output[:-1]
    elif isinstance(target, RPTItemSentence):
        raise
    else:
        raise


def search_RPTItem_contain_komop_tag(target: Union[RPTItem, RPTItemSentence, List[RPTItemSub]], tag_text):
    output = None
    if isinstance(target, RPTItem):
        output = is_KomoPItem_contain(target.item.komop_sentence, tag_text)
        if output is None and len(target.mod_list) > 0:
            output = search_RPTItem_contain_komop_tag(target.mod_list, tag_text)
        return output

    elif isinstance(target, List):
        for item in target:
            if output is None:
                output = search_RPTItem_contain_komop_tag(item, tag_text)
            else:
                return output
        return output
    elif isinstance(target, RPTItemSentence):
        raise
    else:
        raise


def is_KomoPItem_contain(target: List[KomoPItem], tag_text):
    for komopitem in target:
        if komopitem.tag == tag_text:
            return komopitem.text
    return None
