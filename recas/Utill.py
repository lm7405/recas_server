
from typing import List, Tuple
from pydantic import BaseModel
from tensorflow.keras.models import load_model
import time
import json
from .ParseTree import *
from recas.KomoranPlus import KomoranPlus

INPUT_TYPE = List[Tuple[Tuple[str, str], List[Tuple[str, str]]]]


def get_recas_process_class(init_data) -> "Recas":
    recas_process_class = Recas(
        init_data["chunk_rule_path"],
        init_data["komop_rule_path"],
        init_data["komop_tag_path"],
        init_data["chunk_tag_path"],
        init_data["user_dict_path"],
        init_data["DIMS"],
        init_data["mfile_path"]
    )
    recas_process_class.init_thread()
    return recas_process_class


class RecasMission:
    class CheckingInput(BaseModel):
        sentence: str
        pm_id: str = "common"

    class RunSentences:
        def __init__(self, check_input_list: List["RecasMission.CheckingInput"], debug=False):
            self.debug = debug
            self.checking_input_list = check_input_list

        def __call__(self, recas_class: "Recas"):
            output = []
            for checking_input in self.checking_input_list:
                recas_class.make_recas_sentence(
                    sentence=checking_input.sentence,
                    visualize_debug=self.debug,
                    pm_id=checking_input.pm_id
                )
            return output

    class RunSentence:
        def __init__(self, check_input: "RecasMission.CheckingInput", debug=False):
            self.debug = debug
            self.checking_input = check_input

        def __call__(self, recas_class: "Recas"):
            return recas_class.make_recas_sentence(
                sentence=self.checking_input.sentence,
                visualize_debug=self.debug,
                pm_id=self.checking_input.pm_id
            )

    class AddDict:
        def __init__(self, word_data):
            self.word_data = word_data

        def __call__(self, recas_class: "Recas"):
            result = recas_class.komop_tokenizer.add_dict(self.word_data)
            recas_class.komo_tokenizer = recas_class.komop_tokenizer.tokenizer
            return result

    class RemoveDict:
        def __init__(self, word_data):
            self.word_data = word_data

        def __call__(self, recas_class: "Recas"):
            result = recas_class.komop_tokenizer.remove_dict(self.word_data)
            recas_class.komo_tokenizer = recas_class.komop_tokenizer.tokenizer
            return result

    class UpdateDict:
        def __init__(self, word_data):
            self.word_data = word_data

        def __call__(self, recas_class: "Recas"):
            result = recas_class.komop_tokenizer.update_dict(self.word_data)
            recas_class.komo_tokenizer = recas_class.komop_tokenizer.tokenizer
            return result


class Recas:
    komop_tokenizer: any
    model: any
    komo_tokenizer: any

    def __init__(
            self,
            chunk_rule_path,
            komop_rule_path,
            komop_tag_path,
            chunk_tag_path,
            user_dict_path,
            dims,
            load_model_path
    ):
        self.chunk_rule_path = chunk_rule_path
        self.komop_rule_path = komop_rule_path
        self.user_dict_path = user_dict_path
        self.load_model_path = load_model_path
        self.komop_tag_path = komop_tag_path
        self.chunk_tag_path = chunk_tag_path
        self.dims = dims
        dict_table, _ = self.dims.executeQuery()
        self.komop_tokenizer = KomoranPlus(
            chunk_rule_path=self.chunk_rule_path,
            komop_rule_path=self.komop_rule_path,
            user_dict_path=self.user_dict_path,
            dict_table=dict_table,
        )

    def init_thread(self):
        self.komop_tokenizer.init_thread()
        if self.load_model_path is not None:
            self.model = load_model(self.load_model_path)
        self.komo_tokenizer = self.komop_tokenizer.tokenizer

    def export_text_data(self, sentence_text: str, sentence_chunk,
                         testcase_text="",
                         sentence_info="",):
        text_data = sentence_text
        komoran_data = self.komo_tokenizer.pos(sentence_text)
        komoran_plus_data = ""
        chunk_data = ""
        for chunk in sentence_chunk:
            for item in chunk[1]:
                komoran_plus_data += str(item) + ", "
            chunk_data += str(chunk[0]) + ", "

        output = ""
        output += "Original Sentence\n" + text_data + "\n\n"
        output += "Komoran Output\n" + str(komoran_data) + "\n\n"
        output += "Komoran+ Output\n" + komoran_plus_data + "\n\n"
        output += "Chunk Output\n" + chunk_data + "\n\n"
        if len(sentence_info) != 0:
            output += "Unit Sentence Info Output\n" + sentence_info + "\n\n"
        if len(testcase_text) != 0:
            output += "Testcase Output\n" + testcase_text + "\n\n"

        return output

    @staticmethod
    def read_text(text_path):
        file_path = text_path
        try:
            with open(file_path, 'r', encoding="UTF8") as f:
                text = f.readlines()
        except Exception:
            with open(file_path, 'r') as f:
                text = f.readlines()
        return text

    def predict_chunks(self, sentence):
        from recas.Chunk import predict_chunks

        sentences = sentence.split("\n")

        sentences_komop = []
        for sentence in sentences:
            sentence_komop = self.komop_tokenizer.get_predict_data(sentence)
            sentences_komop.append(sentence_komop)
        predict_chunks_ = predict_chunks.predict_chunks(
            sentences_komop,
            self.komop_tag_path,
            self.chunk_tag_path,
            self.model
        )
        output = []
        for i in range(len(sentences)):
            new_item = []
            for j in range(len(predict_chunks_[i])):
                item = (predict_chunks_[i][j], sentences_komop[i][j][0])
                new_item.append(item)
            output.append(new_item)

        return output

    def make_model_file(
            self,
            sentences: list,
            save_model_path: str,
            epochs: int
    ):
        from recas.Chunk.train_chunks import train_chunks
        train_chunks(
            sentences,
            self.komop_tag_path,
            self.chunk_tag_path,
            self.komop_tokenizer,
            save_model_path,
            epochs
        )

    # TODO pm_id 적용
    def make_recas_sentence(self, sentence: str, result_path="result", signal_names=None,
                            chunk_debug=True, visualize_debug=False, pm_id="common"):
        tokenizer_ = self.komop_tokenizer

        file_name = str(time.time())
        save_name = result_path + "/" + file_name
        if len(sentence) == 0:
            return {}
        if chunk_debug:
            sentence_chunk = tokenizer_.get_dummy_chunk(sentence)
        else:
            # sentence_chunk_ = tokenizer_.get_dummy_chunk(sentence)
            sentence_chunk = self.predict_chunks(sentence)[0]
        parse_tree_err, parse_tree_crt = generate_parse_tree(sentence_chunk)
        parse_tree_restored = restore_skipped_chunk(parse_tree_crt)
        error_list = error_check(sentence_chunk, parse_tree_restored, parse_tree_err)

        unit_sentences = get_unit_sentence(parse_tree_crt)
        unit_sentences_info = get_unit_sentence_info(parse_tree_crt)
        if len(parse_tree_err) == 0:
            testcase_text = get_testcase_text(parse_tree_crt, signal_names)
            text_data = self.export_text_data(
                sentence, sentence_chunk, testcase_text,
                json.dumps(unit_sentences_info, indent=4, ensure_ascii=False),
                )
        else:
            text_data = self.export_text_data(
                sentence, sentence_chunk, "",
                json.dumps(unit_sentences_info, indent=4, ensure_ascii=False))
            testcase_text = ""

        if visualize_debug:
            self.draw_sentence(sentence_chunk, parse_tree_restored, parse_tree_err, error_list, save_name)
        output = {
            "sentence_chunk": sentence_chunk,
            "parse_tree_crt": parse_tree_crt,
            "parse_tree_err": parse_tree_err,
            "parse_tree_restored": parse_tree_restored,
            "unit_sentence": unit_sentences,
            "error_list": error_list,
            "save_name": save_name,
            "unit_sentence_info": unit_sentences_info,
            "testcase_text": testcase_text,
            "text_data": text_data
        }

        return output

    @staticmethod
    def draw_sentence(sentence_chunk, parse_tree_restored, parse_tree_err, error_list, save_name):
        sentence_text = ""
        print_restored = True
        parse_tree_crt = parse_tree_restored

        for item in sentence_chunk:
            sentence_text += str(item[0])
        if print_restored:
            visualize(parse_tree_restored, parse_tree_err, sentence_text, error_list, save_name)
        else:
            visualize(parse_tree_crt, parse_tree_err, sentence_text, error_list, save_name)
