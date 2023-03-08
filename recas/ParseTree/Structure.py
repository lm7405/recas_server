from typing import List, Tuple, Type, Union, Dict


class ChunkItem:
    text: str = None
    tag: str = None

    def __init__(self, chunk_text: str, chunk_tag: str):
        self.text = chunk_text
        self.tag = chunk_tag

    def merge(self, next_chunk_item: "ChunkItem",  new_chunk_tag):
        new_text = self.text + " " + next_chunk_item.text
        new_tag = new_chunk_tag
        return ChunkItem(new_text, new_tag)


class KomoPItem:
    text: str = None
    tag: str = None

    def __init__(self, komop_text: str, komop_tag: str):
        self.text = komop_text
        self.tag = komop_tag


class RecasItem:
    chunk_item: ChunkItem = None
    komop_sentence: List[KomoPItem] = None

    def __init__(self, chunk_item: ChunkItem = None, komop_sentence: List[KomoPItem] = None,
                 raw: Tuple[Tuple[str, str], List[Tuple[str, str]]] = None):
        if raw is not None:
            try:
                if type(raw) != tuple and type(raw) != list:
                    raise
                elif len(raw) != 2:
                    raise

                raw_chunk_item = raw[0]
                if type(raw_chunk_item) != tuple and type(raw_chunk_item) != list:
                    raise
                elif len(raw_chunk_item) != 2:
                    raise
                elif type(raw_chunk_item[0]) != str:
                    raise
                elif type(raw_chunk_item[1]) != str:
                    raise

                if type(raw[1]) != list:
                    raise
                for raw_komop_item in raw[1]:
                    if type(raw_komop_item) != tuple and type(raw_komop_item) != list:
                        raise
                    elif len(raw_komop_item) != 2:
                        raise
                    elif type(raw_komop_item[0]) != str:
                        raise
                    elif type(raw_komop_item[1]) != str:
                        raise

                self.chunk_item = ChunkItem(raw_chunk_item[0], raw_chunk_item[1])
                self.komop_sentence = []
                for raw_komop_item in raw[1]:
                    self.komop_sentence.append(KomoPItem(raw_komop_item[0], raw_komop_item[1]))

            except Exception as e:
                raise e

        elif chunk_item is not None and KomoPItem is not None:
            self.chunk_item = chunk_item
            self.komop_sentence = komop_sentence
        else:
            raise

    def merge_chunk(self, next_recas_item: "RecasItem", new_chunk_tag: str):
        new_chunk_item = self.chunk_item.merge(next_recas_item.chunk_item, new_chunk_tag)
        new_komop_sentence = self.komop_sentence + next_recas_item.komop_sentence
        return RecasItem(new_chunk_item, new_komop_sentence)


RPTItemSub = Union["RPTItem", "RPTItemSentence"]


class RPTItem:
    item: RecasItem
    index: int
    mod_list: List[RPTItemSub]

    def __init__(self, item: RecasItem, index: int, mod_list: [RPTItemSub] = None):
        self.item = item
        self.index = index
        self.mod_list = mod_list
        if self.mod_list is None:
            self.mod_list = []

    def merge_chunk(self, next_rpt_item: "RPTItem", new_chunk_tag):
        new_recas_item = self.item.merge_chunk(next_rpt_item.item, new_chunk_tag)
        return RPTItem(new_recas_item, self.index, self.mod_list)


class RPTItemSentence:
    sub_list: List[Union[RPTItem]]
    obj_list: List[Union[RPTItem]]
    adv_list: List[Union[RPTItem]]
    vrb: RPTItem
    index: int

    def __init__(self, vrb: RPTItem):
        self.sub_list = []
        self.obj_list = []
        self.adv_list = []
        self.vrb = vrb
        self.index = vrb.index

    def merge_chunk(self, next_rpt_item, new_chunk_tag):
        self.vrb = self.vrb.merge_chunk(next_rpt_item, new_chunk_tag)


class RPTItemTraverse:

    do_rpt_item_start = None
    do_rpt_item_end = None

    def __init__(self, traverse_data: Dict):
        TRAVERSE_KEY = ("do_rpt_item_start", )
        for key, func_item in traverse_data.items():
            if key in TRAVERSE_KEY:
                pass


def __traverse_check_func_sub(func_id_p: str, func_id_c: str):
    if len(func_id_p) < len(func_id_c):
        return False
    for i in range(len(func_id_c)):
        if func_id_p[i] != func_id_c[i]:
            return False
    return True


def __traverse_RPTItem(rpt_item: RPTItem, func_id: str, info: Dict):
    rpt_item_item = rpt_item.item
    index = rpt_item.index
    rpt_item_mod = __traverse_RPTItemSubs(rpt_item.mod_list, func_id + 'm', info)

    new_rpt_item = RPTItem(rpt_item_item, index, rpt_item_mod)

    return new_rpt_item


def __traverse_RPTItemSentence(rpt_item_sentence: RPTItemSentence, func_id: str, info: Dict):
    new_sub_list = __traverse_RPTItemSubs(rpt_item_sentence.sub_list, func_id + 's', info)
    new_obj_list = __traverse_RPTItemSubs(rpt_item_sentence.obj_list, func_id + 'o', info)
    new_adv_list = __traverse_RPTItemSubs(rpt_item_sentence.adv_list, func_id + 'a', info)
    new_vrb = __traverse_RPTItem(rpt_item_sentence.vrb, func_id + 'v', info)

    new_rpt_item_sentence = RPTItemSentence(new_vrb)
    new_rpt_item_sentence.sub_list = new_sub_list
    new_rpt_item_sentence.obj_list = new_obj_list
    new_rpt_item_sentence.adv_list = new_adv_list

    return new_rpt_item_sentence


def __traverse_RPTItemSubs(rpt_item_subs: List[RPTItemSub], func_id: str, info: Dict):
    if rpt_item_subs is None:
        return None
    new_rpt_item_subs = []
    for rpt_item_sub in rpt_item_subs:
        rpt_item_sub_type = type(rpt_item_sub)
        if rpt_item_sub_type == RPTItem:
            new_rpt_item_sub = __traverse_RPTItem(rpt_item_sub, func_id + 'l', info)
            new_rpt_item_subs.append(new_rpt_item_sub)
        elif rpt_item_sub_type == RPTItemSentence:
            new_rpt_item_sub = __traverse_RPTItemSentence(rpt_item_sub, func_id + 'l', info)
            new_rpt_item_subs.append(new_rpt_item_sub)
        else:
            raise
    return new_rpt_item_subs


def traverse_RPTItem_deepcopy(rpt_item: RPTItem, restored=False, no_child=False, no_sentence=False):
    rpt_item_item = rpt_item.item
    index = rpt_item.index
    if restored:
        index = -1

    if no_child:
        new_rpt_item = RPTItem(rpt_item_item, index)
    else:
        rpt_item_mod = traverse_RPTItemSubs_deepcopy(rpt_item.mod_list, restored, no_child, no_sentence)
        new_rpt_item = RPTItem(rpt_item_item, index, rpt_item_mod)

    return new_rpt_item


def traverse_RPTItemSentence_deepcopy(rpt_item_sentence: RPTItemSentence, restored=False, no_child=False, no_sentence=False):
    new_sub_list = traverse_RPTItemSubs_deepcopy(rpt_item_sentence.sub_list, restored, no_sentence)
    new_obj_list = traverse_RPTItemSubs_deepcopy(rpt_item_sentence.obj_list, restored, no_sentence)
    new_adv_list = traverse_RPTItemSubs_deepcopy(rpt_item_sentence.adv_list, restored, no_sentence)
    new_vrb = traverse_RPTItem_deepcopy(rpt_item_sentence.vrb, restored, no_sentence)

    new_rpt_item_sentence = RPTItemSentence(new_vrb)
    new_rpt_item_sentence.sub_list = new_sub_list
    new_rpt_item_sentence.obj_list = new_obj_list
    new_rpt_item_sentence.adv_list = new_adv_list

    return new_rpt_item_sentence


def traverse_RPTItemSubs_deepcopy(rpt_item_subs: List[RPTItemSub], restored=False, no_child=False, no_sentence=False):
    if rpt_item_subs is None:
        return None
    new_rpt_item_subs = []
    for rpt_item_sub in rpt_item_subs:
        rpt_item_sub_type = type(rpt_item_sub)
        if rpt_item_sub_type == RPTItem:
            new_rpt_item_sub = traverse_RPTItem_deepcopy(rpt_item_sub, restored, no_sentence)
            new_rpt_item_subs.append(new_rpt_item_sub)
        elif rpt_item_sub_type == RPTItemSentence:
            if no_sentence is False:
                new_rpt_item_sub = traverse_RPTItemSentence_deepcopy(rpt_item_sub, restored)
                new_rpt_item_subs.append(new_rpt_item_sub)
        else:
            raise
    return new_rpt_item_subs
