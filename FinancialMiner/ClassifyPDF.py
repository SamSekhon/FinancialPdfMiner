# Standard library imports
import pickle

# Third-party imports
import pandas as pd
import numpy as np
import more_itertools as mit

def create_feature_matrix(path, vocab_filename, df):
    """
    Create a feature matrix based on vocabulary frequency and document words.

    Args:
        path (str): Path to vocabulary files.
        vocab_filename (str): Filename of vocabulary.
        df (pandas.DataFrame): DataFrame containing words extracted from documents.

    Returns:
        pandas.DataFrame: Feature matrix containing word counts and dummy variables.
    """
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
    """
    Create TF-IDF vocabulary matrix based on the feature matrix.

    Args:
        feature_matrix (pandas.DataFrame): Feature matrix with word counts and dummy variables.

    Returns:
        pandas.DataFrame: TF-IDF weighted feature matrix.
    """
    vocab_freq = np.sum(feature_matrix > 0, axis=0)
    idf_vocab = np.log(len(feature_matrix) / vocab_freq)
    tf_idf_vocab = feature_matrix * idf_vocab
    tf_idf_vocab["PAGE>12"] = tf_idf_vocab["PAGE>12"].apply(lambda value: value * 10)
    tf_idf_vocab.fillna(0, inplace=True)

    return tf_idf_vocab


def create_model_predictions(path, model_filename, feature_df, original_df):
    """
    Create predictions using a trained model.

    Args:
        path (str): Path to model files.
        model_filename (str): Filename of the trained model.
        feature_df (pandas.DataFrame): DataFrame containing features for prediction.
        original_df (pandas.DataFrame): Original DataFrame with file and page number information.

    Returns:
        pandas.DataFrame: DataFrame with file, page number, and model predictions.
    """
    model = pickle.load(open(path + model_filename, "rb"))
    y_pred = model.predict(feature_df)

    results = pd.DataFrame(columns=["FILE", "PAGE_NUMBER", "Y_PRED"])
    results["FILE"] = original_df["FILE"]
    results["PAGE_NUMBER"] = original_df["PAGE_NUMBER"]
    results["Y_PRED"] = y_pred

    return results


def helper_clean_predictions(df_model_predictions):
    """
    Clean predictions by filtering and organizing page numbers.

    Args:
        df_model_predictions (pandas.DataFrame): DataFrame with model predictions.

    Returns:
        pandas.DataFrame: DataFrame with cleaned and organized predictions.
    """
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
    """
    Create predictions pipeline: feature matrix creation, TF-IDF calculation, model predictions, and cleaning.

    Args:
        model_pipeline_dict (dict): Dictionary containing model pipeline parameters.
        df (pandas.DataFrame): DataFrame containing data to process.

    Returns:
        pandas.DataFrame: DataFrame with cleaned predictions.
    """
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
