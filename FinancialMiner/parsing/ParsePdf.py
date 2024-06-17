# class import
from . import ParseLabels
from . import ParseDatesSymbols

from .DataClasses import *

import datetime
import calendar
import pandas as pd

# logging
from .. import get_logger

logger = get_logger()


def run(
    df_model_predictions: ModelOutput,
    df_rfc: DataFrame,
    parser_results: ParserData,
    parser_rules: ParserRules,
):
    # scan and extract text for the pages predicted by the model
    dict_text = get_predictions_text(
        df_model_predictions, parser_results.file_transcription
    )

    # first part of extraction
    """
    In the first run, extraction happens per line
    """
    extract = ParseLabels.extract_labels(dict_text, parser_rules)

    # extract overall page variables
    metric_count_dict = ParseLabels.metric_count_by_page(extract)

    # second part extraction
    """
    In the second run, we use overall page variables extracted after the first run
    to guide the second run for extraction
    """
    extract_updated = ParseLabels.merge_extract(
        dict_text,
        extract,  # never used again after this, so can be safely obliterated
        metric_count_dict,
        parser_rules,
    )

    # function to clean labels specific to the statement
    # to do: add logic to allow user to choose/input type of statement
    cleaned_label = clean_income_labels_dirty(extract_updated.copy())

    # function to extract text to be used for extracting dates
    # based on the position of the first metric captured by the process
    dates_data_dict = ParseDatesSymbols.extract_dates_text(dict_text, cleaned_label)

    # # function to extract dates from the text
    # # TODO: Clean out this cursed function ...
    dates_dict = ParseDatesSymbols.extract_dates(
        dates_data_dict, parser_rules, metric_count_dict
    )

    # # function to search for thousands patterns (used as multiplier)
    thousands_pattern_dict = ParseDatesSymbols.thousands_pattern_search(
        dict_text, dates_data_dict, parser_rules
    )

    # # function to combine all the peices together
    pdf_output = combine_labels_dates(cleaned_label, dates_dict, thousands_pattern_dict)

    # # final output into a dataframe
    df_output = last_period_to_df(pdf_output, df_rfc, parser_results.file_descriptions)

    # cleaning and filtering
    df_output = df_output[['PATH', 'label', 'amount', 'extract_period_end_date', 'multiplier']]
    df_output.columns = ['FILE', 'METRIC', 'AMOUNT', 'DATE', 'MULTIPLIER']
    return df_output


# extract text from saved data only for pages identified by the model
def get_predictions_text(df_model_predictions, dict_parser_data):
    predictions = dict(zip(df_model_predictions.FILE, df_model_predictions.PREDICTIONS))

    dict_text = {}

    for key in dict_parser_data.keys():
        if key in predictions.keys():
            dict_text[key] = []
            page_counter = 0

            for page in range(0, len(list(dict_parser_data[key].keys()))):
                if page in predictions[key]:
                    if page_counter == 0:
                        text = dict_parser_data[key][page]
                    else:
                        text.extend(dict_parser_data[key][page])

                    page_counter += 1

            # append text to the dictionary
            dict_text[key].extend(text)

    return dict_text


def clean_income_labels_dirty(extract: ExtractType) -> ExtractType:
    """function to clean "income" labels, only applicable to income statement
    inputs:
        extract: dictionary containing labels data
    output:
        output_dict: dictionary containing updated labels"""

    # identify empty labels to remove
    del_dict = {}
    for page in extract:
        del_dict[page] = {}
        for line in extract[page]:
            if (
                extract[page][line].label == ""
                and len(extract[page][line].numbers_list) == 0
            ):
                del_dict[page][line] = 1
    # remove empty labels
    for page, dict in del_dict.items():
        for line, value in dict.items():
            del extract[page][line]

    # clean labels
    for page in extract:
        label = []
        numbers = []

        keylist = list(extract[page].keys())
        for line in extract[page]:
            keylist_index = keylist.index(line)
            if not extract[page][line].numbers_list:
                # check for text
                if extract[page][line].label != "":
                    label = extract[page][line].label
                    if label.replace(" ", "").lower() in [
                        "revenue",
                        "income",
                        "revenues",
                    ]:
                        # second line from revenue should be expense (without numbers)
                        try:
                            if not extract[page][
                                keylist[keylist_index + 2]
                            ].numbers_list:
                                # check the value for the second line from revenue
                                check_label = extract[page][
                                    keylist[keylist_index + 2]
                                ].label
                                # if label == expense
                                if (
                                    (
                                        check_label.replace(" ", "").lower()[0:7]
                                        == "expense"
                                    )
                                    | (
                                        check_label.replace(" ", "").lower()
                                        in [
                                            "generalandadministrativeexpenses",
                                            "operatingexpenses",
                                        ]
                                    )
                                    | (
                                        check_label.replace(" ", "").lower()[0:17]
                                        == "operatingexpenses"
                                    )
                                ):
                                    try:
                                        extract[page][line].numbers_list = extract[
                                            page
                                        ][keylist[keylist_index + 1]].numbers_list
                                    except IndexError:
                                        print("No numbers found on page " + str(page))
                        except IndexError:
                            print(
                                "Indexerror on page "
                                + str(page)
                                + " and line "
                                + str(line)
                            )
                            continue

            elif extract[page][line].numbers_list:
                if extract[page][line].label == "":
                    numbers = extract[page][line]

            else:
                print(
                    "Error: More than 2 length or less than 1 length on page "
                    + str(page)
                    + " and line "
                    + str(line)
                )

            if label:
                if numbers:
                    extract[page][line].label = label

                    label = []
                    numbers = []

    # final output
    row_count = 0
    output_dict = {}
    for i in extract:
        output_dict[i] = {}
        for j in extract[i]:
            if extract[i][j].label and extract[i][j].numbers_list:
                output_dict[i][j] = extract[i][j]
                row_count += 1

    # print("Total Number of Rows:" + str(row_count))
    return output_dict


def clean_income_labels(extract: ExtractType) -> ExtractType:
    """function to clean "income" labels, only applicable to income statement
    inputs:
        extract: dictionary containing labels data
    output:
        output_dict: dictionary containing updated labels"""

    # remove empty lables form extract
    extract = {
        document: {
            key: line
            for key, line in lines.items()
            if (line.label or line.numbers_list)
        }
        for document, lines in extract.items()
    }

    # clean labels
    for document in extract:
        label = None
        numbers = None

        keylist = list(extract[document].keys())
        for line in extract[document]:
            keylist_index = keylist.index(line)
            if not extract[document][line].numbers_list:
                # check for text
                if extract[document][line].label != "":
                    label = extract[document][line].label
                    if label.replace(" ", "").lower() not in [
                        "revenue",
                        "income",
                        "revenues",
                    ]:
                        continue

                    # second line from revenue should be expense (without numbers)
                    if (
                        keylist_index + 2 < len(keylist)
                        and not extract[document][
                            keylist[keylist_index + 2]
                        ].numbers_list
                    ):
                        # check the value for the second line from revenue
                        check_label = (
                            extract[document][keylist[keylist_index + 2]]
                            .label.replace(" ", "")
                            .lower()
                        )
                        # if label == expense
                        patterns = [
                            ("expenses", 7),
                            ("generalandadministrativeexpenses", None),
                            ("operatingexpenses", 17),
                        ]

                        pattern_found = False
                        for pat, end in patterns:
                            end = end if end else len(check_label)
                            if check_label[:end] == pat:
                                pattern_found = True
                                break

                        if not pattern_found:
                            continue

                        if keylist_index + 1 < len(keylist):
                            extract[document][line].numbers_list = extract[document][
                                keylist[keylist_index + 1]
                            ].numbers_list
                        else:
                            logger.error(f"No numbers found on page: {document}")

                    else:
                        logger.error(
                            f"Format error on page: {document}, line:{line}, no entry found 2 lines after {label}"
                        )
                        continue

            elif len(extract[document][line].numbers_list) == 1:
                if extract[document][line].label == "":
                    numbers = extract[document][line].numbers_list[0]

            else:
                logger.error(
                    f"Invalid number of entries on page: {document}, line: {line}"
                )

            if label and numbers:
                extract[document][line].label = label

                label = []
                numbers = []

    output_dict = {
        document: {
            j: extract[document][j]
            for j in extract[document]
            if extract[document][j].numbers_list
        }
        for document in extract
    }

    return output_dict


def combine_labels_dates(
    labels_dict: ExtractType,
    dates_dict: dict[str, list[DateTuple]],
    thousands_dict: dict[str, int],
) -> ExtractType:
    """function to combine labels and dates data
    inputs:
        labels_dict: dictionary containing labels data
        dates_dict: dictionary containing dates data
        thousands_dict: dictionary containing any thousands patterns identified
    output:
        labels_dict: updated labels dictionary with dates appended"""
    for i in labels_dict.keys():
        for j in labels_dict[i]:
            if i in dates_dict:
                labels_dict[i][j].dates = dates_dict[i]

            if i in thousands_dict:
                labels_dict[i][j].multiplier = thousands_dict[i]

    return labels_dict


def last_period_to_df(
    pdf_output: ExtractType,
    df_rfc: DataFrame,
    df_parser_filepath_variables: DataFrame = None,
) -> DataFrame:
    """function to convert the final outputs to a dataframe
    inputs:
        pdf_output: dictionary of dictionaries containing all extracted data
    output:
        df: dataframe containing the final outputs
    """

    df = pd.DataFrame(columns=["PATH", "label", "amount", "extract_date", "multiplier"])

    row_num = 0
    for document in pdf_output:
        for row in pdf_output[document]:
            df.loc[row_num] = [
                document,
                pdf_output[document][row].label,
                pdf_output[document][row].numbers_list[0][0],
                # grab the month of the first date listed
                pdf_output[document][row].dates[0]
                if pdf_output[document][row].dates
                else None,
                pdf_output[document][row].multiplier,
            ]

            row_num += 1

    # append the document path back to the df (to identify files read)
    # df[["PATH"]] = pd.DataFrame(
    #     (df["document"].map(dict_document_map)).tolist(), index=df.index
    # )

    logger.info(f"DF Merged shape from start : {df.shape}")

    # additional logic (multiplier found but no date found)
    """
    This logic is to normalize dates from tuple objects
    """
    df.loc[(df["extract_date"] == 1000), "multiplier"] = 1000
    df.loc[(df["extract_date"] == 1000), "extract_date"] = None

    date_list = df["extract_date"].to_list()

    joined_date_list = []
    for date in date_list:
        try:
            joined_date_list.append("-".join(date))
        except:
            joined_date_list.append("NA")

    df = df.assign(extract_date_updated=joined_date_list)

    df["extract_period_end_date"] = pd.to_datetime(
        df["extract_date_updated"], format="%B-%d-%Y", errors="coerce"
    )

    """
    Additional cleaning on dates
    """

    # convert to month end date
    df["extract_period_end_date"] = df["extract_period_end_date"].apply(
        helper_last_day_of_month
    )

    """
    End of Date formatting and cleaning
    """

    # check to see if "amount" field contains -, ( or, ) if so, flag it as negative
    df["negative_flag"] = df["amount"].apply(
        (lambda val: -1 if {"-", "(", ")"} & set(val) else 1)
    )

    return df


# read in rfc data file
def read_rfc_data(filepath, cols=["SUB_ID", "CAP_CAL_AS_DATE"]) -> DataFrame:
    df = pd.read_csv(filepath)

    # Filter and remove duplicates
    df = df[cols]
    # latest date is kept per subid
    df.sort_values(by=cols, ascending=False, inplace=True)
    df.drop_duplicates(subset=cols[0], keep="first", inplace=True)

    # only keep sub_ids where length=10
    df = df.loc[df[cols[0]].astype(str).map(len) == 10]

    # convert to datetime
    df[cols[1]] = pd.to_datetime(df[cols[1]], errors="coerce")

    # remove nulls
    df.dropna(inplace=True)

    return df


def helper_last_day_of_month(date):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = date.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    try:
        return next_month - datetime.timedelta(days=next_month.day)
    except ValueError:
        return None
