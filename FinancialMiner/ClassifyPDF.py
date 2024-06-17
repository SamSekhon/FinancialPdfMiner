import pandas as pd
import numpy as np
import pickle
import more_itertools as mit


def create_feature_matrix(path, vocab_filename, df):
    with open(f"{path}{vocab_filename}") as file:
        vocab_freq = [line.strip() for line in file]

    # Creating the vocabulary matrix
    matrix = pd.DataFrame(columns=vocab_freq)
    for words in df["WORDS"]:
        new_row = []
        for column in matrix.columns:
            if column not in words:
                new_row.append(0)
            else:
                count_words = {}
                for word in words:
                    if word not in count_words:
                        count_words[word] = 1
                    else:
                        count_words[word] += 1
                new_row.append(count_words[column])
        matrix.loc[len(matrix)] = new_row

    # Adding dummy variables
    matrix["NUMBERS<5"] = df["NUMBERS<5"]
    matrix["WORDS<20"] = df["WORDS<20"]
    matrix["PAGE>12"] = df["PAGE>12"]
    matrix.insert(0, "NUMBERS<5", matrix.pop("NUMBERS<5"))
    matrix.insert(0, "WORDS<20", matrix.pop("WORDS<20"))
    matrix.insert(0, "PAGE>12", matrix.pop("PAGE>12"))

    return matrix


def create_tfidf_vocab(feature_matrix):
    vocab_freq = np.sum(feature_matrix > 0, axis=0)
    idf_vocab = np.log(len(feature_matrix) / vocab_freq)
    tf_idf_vocab = feature_matrix * idf_vocab
    tf_idf_vocab["PAGE>12"] = tf_idf_vocab["PAGE>12"].apply(lambda value: value * 10)
    tf_idf_vocab.fillna(0, inplace=True)

    return tf_idf_vocab


def create_model_predictions(path, model_filename, feature_df, original_df):
    model = pickle.load(open(path + model_filename, "rb"))
    y_pred = model.predict(feature_df)

    results = pd.DataFrame(columns=["FILE", "PAGE_NUMBER", "Y_PRED"])
    results["FILE"] = original_df["FILE"]
    results["PAGE_NUMBER"] = original_df["PAGE_NUMBER"]
    results["Y_PRED"] = y_pred

    return results


def helper_clean_predictions(df_model_predictions):
    # filter to keep only the predictions
    df = df_model_predictions.loc[df_model_predictions.Y_PRED == 1]

    # fix page number datatype
    df["PAGE_NUMBER"] = df["PAGE_NUMBER"].astype("Int64")

    # Convert predictions to list of page numbers
    df_grouped = (
        df.groupby("FILE")["PAGE_NUMBER"].apply(list).reset_index(name="PAGE_LIST")
    )

    # keep the longest consecutive list ()
    df_grouped["PAGE_LIST"] = df_grouped["PAGE_LIST"].apply(
        lambda x: [list(group) for group in mit.consecutive_groups(x)]
    )

    # only keep the longest consecutive pages or the first prediction (if multiple non consecutive pages)
    df_grouped["PREDICTIONS"] = df_grouped["PAGE_LIST"].apply(lambda v: max(v, key=len))

    return df_grouped[["FILE", "PREDICTIONS"]]


def create_predictions(model_pipeline_dict, df):
    # create features matrix
    feature_matrix = create_feature_matrix(
        model_pipeline_dict["model_objects_filepath"],
        model_pipeline_dict["vocab_freq_filename"],
        df,
    )

    # create tfidf df
    feature_df = create_tfidf_vocab(feature_matrix)

    # predict
    results_df = create_model_predictions(
        model_pipeline_dict["model_objects_filepath"],
        model_pipeline_dict["model_filename"],
        feature_df,
        df,
    )

    # clean predictions
    results_df_cleaned = helper_clean_predictions(results_df)

    return results_df_cleaned
