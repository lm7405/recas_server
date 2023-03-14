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
    """
    Trains a chunking model using the given training data and saves the trained model to a file.

    Args:
        statement_list (List[str]): A list of training statements to use for training the model.
        komop_tag_path (str): The path to the dictionary file containing the part-of-speech tags of the training data.
        chunk_tag_path (str): The path to the dictionary file containing the chunk tags of the training data.
        komop_tokenizer (Any): The tokenizer to use for the part-of-speech tags.
        mfile_path (str): The file path to save the trained model.
        epochs (int): The number of training epochs to run.

    Returns:
        bool: True if the trained model file was successfully saved.
    """
    komoran_list, rule_list, rule_list_list = making_data.convert_model_input(statement_list, komop_tokenizer)
    komop_pos_dic, _, chunk_pos_dic, _, word_index_len = \
        making_data.dictionary(komop_dic=komop_tag_path, chunk_dic=chunk_tag_path)
    komoran_sentences = making_data.komoran_encoding(komoran_list, komop_pos_dic)
    chunk_sentences = making_data.chunk_encoding(rule_list_list, chunk_pos_dic)
    komoran_sentences, rule_sentences = making_data.padding(komoran_sentences, chunk_sentences)

    training(word_index_len, komoran_sentences, rule_sentences, mfile_path, epochs)

    return print(os.path.isfile(mfile_path))
