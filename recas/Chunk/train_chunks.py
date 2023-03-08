from recas.Chunk import making_data
from recas.Chunk.training import training
import os


def train_chunks(
        statement_list,
        komop_tag_path,
        chunk_tag_path,
        komop_tokenizer,
        mfile_path,
        epochs
):
    komoran_list, rule_list, rule_list_list = making_data.convert_model_input(statement_list, komop_tokenizer)
    komop_pos_dic, _, chunk_pos_dic, _, word_index_len = \
        making_data.dictionary(komop_dic=komop_tag_path, chunk_dic=chunk_tag_path)
    komoran_sentences = making_data.komoran_encoding(komoran_list, komop_pos_dic)
    chunk_sentences = making_data.chunk_encoding(rule_list_list, chunk_pos_dic)
    komoran_sentences, rule_sentences = making_data.padding(komoran_sentences, chunk_sentences)

    training(word_index_len, komoran_sentences, rule_sentences, mfile_path, epochs)

    return print(os.path.isfile(mfile_path))
