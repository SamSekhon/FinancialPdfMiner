import pandas as pd
import numpy as np
import re
import itertools
import calendar

from .DataClasses import *

from ..__init__ import get_logger

logger = get_logger()


def extract_dates_text(
    data_dict: dict[str, LineList], cleaned_labels_dict: ExtractType
) -> FileDateInfo:
    # function to extract dates text i.e, all text before the first extracted label
    # inputs:
    #   cleaned_labels_dict: dictionary containing cleaned label values
    # outputs:
    #   dates_data_dict: dictionary containing dates data (data before the first row containing labels)
    #   nodata_dict: dictionary contaning pdfs where no data exists

    label_start_dict = {}

    for document, info in cleaned_labels_dict.items():
        if info:
            # TODO: doing the below dosen't gaurntee you the first line
            label_start_dict[document] = list(cleaned_labels_dict[document])[0]
        else:
            logger.error(f"No data found in file: {document}. {info}")

    # extract all data preceding the first row containing labels and convert it into a single string
    dates_data_dict = {}
    for document in label_start_dict:
        # the 6 is a buffer we added to ensure we are not missing any dates.
        # It was "experimentally determined"
        dates_text = data_dict[document][: label_start_dict[document] + 6]
        dates_data_dict[document] = " ".join(dates_text)

    return dates_data_dict


def extract_dates(
    dates_data_dict: FileDateInfo,
    parser_rules: ParserRules,
    metric_count_dict: dict[str, MetricsCount],
) -> dict[str, list[DateTuple]]:
    dates_dict: dict[str, list[DateTuple]] = {}

    for document, date_data in dates_data_dict.items():
        metric_count = metric_count_dict[document]

        # We select the first match that is

        if match_1 := fn_format_monthname_date_year(
            date_data, parser_rules, metric_count, document
        ):
            dates_dict[document] = match_1

            max_numcount = metric_counts_dates(metric_count, document)
            if max_numcount == len(match_1):
                continue

        if match_2 := fn_format_mm_dd_yyyy(
            date_data, parser_rules, metric_count, document
        ):
            dates_dict[document] = match_2
            continue

        if match_3 := fn_format_yyyy_mm_dd(
            date_data, parser_rules, metric_count, document
        ):
            dates_dict[document] = match_3
            continue

        if match_4 := fn_format_dd_mmm_yy(
            date_data, parser_rules, metric_count, document
        ):
            dates_dict[document] = match_4
            continue

        logger.error(f"No date match in {document}")

    return dates_dict


def metric_counts_dates(metric_count: MetricsCount, document: str) -> int | None:
    max_numcount = [
        k for k, v in metric_count.items() if v == max(metric_count.values())
    ]

    if len(max_numcount):
        return max_numcount[-1]
    else:
        logger.error(f"Max num count 0 in document:{document}")
        return None


def search_dates(
    pattern: str, text: str, metric_count: MetricsCount, document: str
) -> tuple[list[str] | None, int | None]:
    dates_list = re.findall(pattern, text)

    if dates_list:
        max_numcount = metric_counts_dates(metric_count, document)
        if not max_numcount:
            max_numcount = 0
        dates_list = dates_list[-max_numcount:]

        # Regex matches are either individual strings or a tuple, containing all
        # matching groups. If the regex has matching groups, we take the first match
        # which is the entire string
        dates_list = [item if type(item) == str else item[0] for item in dates_list]
        return dates_list, max_numcount
    else:
        return None, None


def fn_format_monthname_date_year(
    date_data: str, parser_rules: ParserRules, metric_count: MetricsCount, document: str
) -> list[DateTuple]:
    dates_list = []
    # extract individual date items
    months = re.findall(
        parser_rules.date_rules["format_monthname_date_year"]["months"][0],
        date_data.lower(),
    )

    if not months:
        months = re.findall(
            parser_rules.date_rules["format_monthname_date_year"]["months"][1],
            date_data.lower(),
        )
        if months:
            for abbr in range(0, len(months)):
                months[abbr] = (
                    calendar.month_name[
                        list(calendar.month_abbr).index(months[abbr].title())
                    ]
                ).lower()

    dates = re.findall(
        parser_rules.date_rules["format_monthname_date_year"]["dates"][0],
        date_data.lower(),
    )

    if not dates:
        dates = re.findall(
            parser_rules.date_rules["format_monthname_date_year"]["dates"][1],
            date_data.lower(),
        )

    years = re.findall(
        parser_rules.date_rules["format_monthname_date_year"]["years"][0],
        date_data.lower(),
    )

    # append to a list
    dates_list.append(months)
    dates_list.append([re.sub("[^0-9]", "", date) for date in dates])
    dates_list.append([re.sub("[^0-9]", "", year) for year in years])

    # product of all date items
    dates_list = list(itertools.product(*dates_list))

    # check if dates list exists
    if not dates_list:
        return []

    # maximum number count
    max_numcount = metric_counts_dates(metric_count, document)

    if not max_numcount:
        max_numcount = 0

    # match length
    if max_numcount != len(date_data):
        logger.error(
            f"value count error: max numount ({max_numcount}) and dates dict ({len(date_data)}) length mismatch"
        )

    # input dates based on cutoff from metric_count_dict
    # Note, there was a try catch here, with error message
    # logger.error(f"Error in Max Numcount or Dates Dict. {i}, {dates_list}")
    return dates_list[-max_numcount:]


def fn_format_mm_dd_yyyy(
    date_data: str, parser_rules: ParserRules, metric_count: MetricsCount, document: str
) -> list[DateTuple]:
    dates_list, max_numcount = search_dates(
        parser_rules.date_rules["format_mm_dd_yyyy"], date_data, metric_count, document
    )

    if dates_list and max_numcount == len(dates_list):
        # input dates based on cutoff from metric_count_dict
        dates_list = dates_list[-max_numcount:]
        cleaned_dates = []
        try:
            for item in dates_list:
                date = item.split("/")
                date[0] = date[0].lstrip("0")
                date[0] = (calendar.month_name[int(date[0])]).lower()
                cleaned_dates.append(tuple(date))
        except ValueError:
            pass

        return cleaned_dates

    return []


def fn_format_yyyy_mm_dd(
    date_data: str, parser_rules: ParserRules, metric_count: MetricsCount, document: str
) -> list[DateTuple]:
    dates_list, max_numcount = search_dates(
        parser_rules.date_rules["format_yyyy_mm_dd"],
        date_data.lower(),
        metric_count,
        document,
    )

    if dates_list and max_numcount == len(dates_list):
        # input dates based on cutoff from metric_count_dict
        dates_list = dates_list[-max_numcount:]

        cleaned_dates = []
        for item in dates_list:
            date = item.split("-")
            date[1] = date[1].lstrip("0")
            date[1] = (calendar.month_name[int(date[1])]).lower()
            # realign to month, date, year format
            date.append(date.pop(0))

            cleaned_dates.append(tuple(date))

        return cleaned_dates

    return []


def fn_format_dd_mmm_yy(
    date_data: str, parser_rules: ParserRules, metric_count: MetricsCount, document: str
) -> list[DateTuple]:
    dates_list, max_numcount = search_dates(
        parser_rules.date_rules["format_dd_mmm_yy"],
        date_data.lower(),
        metric_count,
        document,
    )

    if dates_list and max_numcount == len(dates_list):
        # input dates based on cutoff from metric_count_dict
        dates_list = dates_list[-max_numcount:]

        cleaned_dates = []
        for item in dates_list:
            date = item.split("-")
            date[1] = (
                calendar.month_name[list(calendar.month_abbr).index(date[1].title())]
            ).lower()
            date[2] = "20" + str(date[2])
            # realign to month, date, year
            date.insert(0, date.pop(1))

            cleaned_dates.append(tuple(date))

        return cleaned_dates

    return []


def thousands_pattern_search(
    data_dict: dict[str, LineList],
    dates_data_dict: FileDateInfo,
    parser_rules: ParserRules,
) -> dict[str, int]:
    multiples_dict: dict[str, int] = {}
    for document in data_dict:
        for line in data_dict[document]:
            if re.findall(parser_rules.multiplier_rules["patterns"], line):
                multiples_dict[document] = 1000

        if document not in dates_data_dict:
            continue

        if re.findall(
            parser_rules.multiplier_rules["words"], dates_data_dict[document].lower()
        ):
            multiples_dict[document] = 1000

    return multiples_dict


def label_search_to_df(
    dates_data_dict: FileDateInfo, parser_rules: ParserRules
) -> DataFrame:
    # search labels and append to label_dict
    label_dict = {}
    for document in dates_data_dict.keys():
        label_dict[document] = []
        for label in parser_rules.additional_labels.keys():
            text = re.findall(
                parser_rules.additional_labels[label], dates_data_dict[document].lower()
            )
            if text:
                label_dict[document].append(re.sub("[^a-zA-Z]+", "", text[0]))
            else:
                label_dict[document].append("na")

    # map the dict to filepath and convert to df
    cols = list(parser_rules.additional_labels.keys())
    cols.insert(0, "document")

    df = pd.DataFrame(columns=cols)

    row_num = 0
    for document in label_dict.keys():
        df.loc[row_num] = [
            document,
            label_dict[document][0],
            label_dict[document][1],
            label_dict[document][2],
        ]

        row_num += 1

    # cleaning dataframe
    df.replace(
        {"na": 0, "unaudited": 1, "audited": 1, "yearended": 1, "yearsended": 1},
        inplace=True,
    )

    df.rename({"document": "filepath"}, axis=1, inplace=True)

    return df[["filepath", "unaudited", "audited", "annual"]]
