from recas.Chunk import making_data
from recas.Chunk.predict import sentence_to_word_index, change, change_modified, change_modified2


def predict_chunks(
        sentences_komop,
        komop_tag_path,
        chunk_tag_path,
        model
):
    """
    Predicts the chunk tags of given sentences using a trained model and returns the predicted chunks.

    Args:
        sentences_komop (List[str]): A list of sentences to predict chunk tags for.
        komop_tag_path (str): The path to the dictionary file containing the part-of-speech tags of the sentences.
        chunk_tag_path (str): The path to the dictionary file containing the chunk tags of the sentences.
        model (Any): The trained model to use for prediction.

    Returns:
        List[List[str]]: A list of lists of predicted chunk tags for each sentence.
    """
    komop_pos_dic, num_to_word_dic, chunk_pos_dic, chunk_num_to_word_dic, word_index_len = \
        making_data.dictionary(komop_dic=komop_tag_path, chunk_dic=chunk_tag_path)
    test_sentences, sen = sentence_to_word_index(sentences_komop, komop_pos_dic)

    # 결과
    test_result = []
    for k in range(len(test_sentences)):
        output = change_modified(test_sentences[k], sen[k], chunk_num_to_word_dic, model)
        test_result.append(output)
    return test_result
