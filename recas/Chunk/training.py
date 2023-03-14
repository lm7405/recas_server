from tensorflow.keras.layers import LSTM, Embedding, Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import EarlyStopping


def training(word_index_len, komoran_sentences, rule_sentences, saved_model_file, epochs: int):
    """
    Trains a chunking model using the given data and saves the trained model to a file.

    Args:
        word_index_len (int): The length of the word index.
        komoran_sentences (numpy.ndarray): An array of encoded sentences using the Komoran tokenizer.
        rule_sentences (numpy.ndarray): An array of encoded chunk tags for each sentence.
        saved_model_file (str): The file path to save the trained model.
        epochs (int): The number of training epochs to run.

    Returns:
        None.
    """
    # word_index_len = MakingData.Dictionary()
    # komoran_sentences, rule_sentences = MakingData.padding()
    # saved_model_file='data\\Chunk\\model2.h5'

    model1 = Sequential()
    model1.add(Embedding(word_index_len + 1, 32))
    model1.add(LSTM(32, activation='tanh', ))
    model1.add(Dense(32, activation='relu'))
    model1.add(Dense(rule_sentences.shape[1], activation='sigmoid'))

    model1.summary()

    es = EarlyStopping(monitor='loss', mode='min', patience=20)

    model1.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    model1.fit(komoran_sentences, rule_sentences, epochs=epochs, batch_size=5, callbacks=[es])

    model1_loss_and_metrics = model1.evaluate(komoran_sentences, rule_sentences, batch_size=5)

    print("---------------------------------------------------------------")
    print("model1_loss_and_metrics: ", model1_loss_and_metrics)

    model1.save(saved_model_file)





