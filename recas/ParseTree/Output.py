from .Structure import *


def rpt_item_sentence2raw(rpt_item_sentence: RPTItemSentence):
    """
    parse tree를 class가 json 형태로 바꾸기 위해 변환하는 함수 중 rpt item sentence 부분을 담당
    Args:
        rpt_item_sentence: rpt_item_sentence 객체

    Returns:
        json에서 변환 가능하도록 구성된 데이터

    """
    if rpt_item_sentence is not None:
        output = {"SUB": [], "OBJ": [], "ADV": [], "VRB": rpt_item2raw(rpt_item_sentence.vrb)}

        tmp = rpt_item_sentence.sub_list[:]
        while len(tmp) > 0:
            output["SUB"].append(rpt_item2raw(tmp.pop()))
        output["SUB"].reverse()

        tmp = rpt_item_sentence.obj_list[:]
        while len(tmp) > 0:
            output["OBJ"].append(rpt_item2raw(tmp.pop()))
        output["OBJ"].reverse()

        tmp = rpt_item_sentence.adv_list[:]
        while len(tmp) > 0:
            output["ADV"].append(rpt_item2raw(tmp.pop()))
        output["ADV"].reverse()

        return output
    else:
        raise


def rpt_item2raw(rpt_item: RPTItem):
    """
    parse tree를 class가 json 형태로 바꾸기 위해 변환하는 함수 중 rpt item 부분을 담당
    Args:
        rpt_item: rpt_item 객체

    Returns:
        json에서 변환 가능하도록 구성된 데이터

    """
    if rpt_item is not None:
        output = {"item": [], "index": rpt_item.index, "mod": []}
        output["item"].append(recas_item2raw(rpt_item.item))
        for mod in rpt_item.mod_list:
            output["mod"].append(rpt_item_sub2raw(mod))
        return output
    else:
        raise


def rpt_item_sub2raw(rpt_item_sub: RPTItemSub):
    """
    parse tree를 class가 json 형태로 바꾸기 위해 변환하는 함수 중 rpt item subs 부분을 담당
    Args:
        rpt_item_sub: rpt_item_sub 객체

    Returns:
        json에서 변환 가능하도록 구성된 데이터

    """
    if type(rpt_item_sub) == RPTItem:
        return rpt_item2raw(rpt_item_sub)
    elif type(rpt_item_sub) == RPTItemSentence:
        return rpt_item_sentence2raw(rpt_item_sub)
    else:
        raise


def recas_item2raw(recas_item: RecasItem):
    """
    parse tree를 class가 json 형태로 바꾸기 위해 변환하는 함수 중 recas_item 부분을 담당
    Args:
        recas_item: recas_item 객체

    Returns:
        json에서 변환 가능하도록 구성된 데이터

    """
    output = (chunk_item2raw(recas_item.chunk_item), [])
    for komop_item in recas_item.komop_sentence:
        output[1].append(komop_item2raw(komop_item))
    return output


def chunk_item2raw(chunk_item: ChunkItem):
    """
    parse tree를 class가 json 형태로 바꾸기 위해 변환하는 함수 중 chunk_item 부분을 담당
    Args:
        chunk_item: chunk_item 객체

    Returns:
        json에서 변환 가능하도록 구성된 데이터

    """
    output = (chunk_item.text, chunk_item.tag)
    return output


def komop_item2raw(komop_item: KomoPItem):
    """
    parse tree를 class가 json 형태로 바꾸기 위해 변환하는 함수 중 komop_item 부분을 담당
    Args:
        komop_item: komop_item 객체

    Returns:
        json에서 변환 가능하도록 구성된 데이터

    """
    output = (komop_item.text, komop_item.tag)
    return output
