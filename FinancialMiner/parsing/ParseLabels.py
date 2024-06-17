import pandas as pd
import numpy as np
import re

from .DataClasses import *
from ..__init__ import get_logger

logger = get_logger()


## helper function to clean numbers
def swap_listitems(
    mainkey, comparekey, number_dict, char_count=0, first=False, replace=True
):
    match = []
    if comparekey in number_dict.keys():
        for index, value_x in enumerate(number_dict[mainkey]):
            for value_y in number_dict[comparekey]:
                if first:
                    if value_y[:char_count] == value_x[:char_count]:
                        match.append(value_y)

                        if replace:
                            number_dict[mainkey][index] = value_y

                else:
                    if value_y[-char_count:] == value_x[-char_count:]:
                        match.append(value_y)

                        if replace:
                            number_dict[mainkey][index] = value_y

        # remove from original list
        number_dict[comparekey] = [x for x in number_dict[comparekey] if x not in match]

    return number_dict


## logic to extract labels
def extract_labels(
    data_dict: dict[str, LineList], parser_rules: ParserRules
) -> ExtractType:
    # dictionary for extract output
    # type hint added to help vscode :)
    extract: dict[str, dict[int, LineExtractInfo]] = {}

    for document in data_dict:
        extract[document] = {}  # dict[int, LineExtractInfo]

        for counter, line in enumerate(data_dict[document]):
            # TODO: replace with more generic logic
            # Logic for cleaning the input line
            old_text = re.findall("\.\d{3}", line)
            new_text = [i.replace(".", ",") for i in old_text]

            for i in range(0, len(new_text)):
                line = line.replace(old_text[i], new_text[i])

            remove_strings = set(
                parser_rules.excluded_strings
                + re.findall(parser_rules.exclusion_rules["note"], f" {line}")
            )

            for string in remove_strings:
                line = line.replace(string, "")

            # extract label and append it to the output dict
            label = re.findall("[a-zA-Z]+", line)
            label = " ".join(label)

            extract[document][counter] = LineExtractInfo(
                label if len(label) > 1 else "", [], [], 1
            )

            # get the index of the last character of the label
            add_to_numdict = []
            if label:
                label_end_index = line.rfind(label[-1])
                line_substr = " " + line[label_end_index:] + " "

                # Extract "-" and numbers < 100
                numbers_below_100 = re.findall(
                    parser_rules.numeric_matching_rules[99], line_substr
                )

                ## TODO: ask about why the logic below works

                if numbers_below_100:
                    numbers_below_100_last_index = line_substr.rfind(
                        numbers_below_100[-1][1:-1]
                    )
                else:
                    numbers_below_100_last_index = 9999

                dash_pattern = ["([ ][-][ ])"]
                dash_characters = re.findall(dash_pattern[0], line_substr)

                if dash_characters:
                    dash_characters_last_index = line_substr.rfind(
                        dash_characters[-1][1:-1]
                    )
                else:
                    dash_characters_last_index = 9999

                if numbers_below_100_last_index < dash_characters_last_index:
                    add_to_numdict = numbers_below_100 + [
                        "0" for dash in dash_characters
                    ]
                else:
                    add_to_numdict = [
                        "0" for dash in dash_characters
                    ] + numbers_below_100

            ##############################################################################
            ##############################################################################
            ## Logic to extract all patterns
            ##############################################################################
            ##############################################################################
            # extract numbers
            num_dict = {}
            for k in parser_rules.numeric_matching_rules.keys():
                if k != 99:
                    num_dict[k] = re.findall(
                        parser_rules.numeric_matching_rules[k], (" " + line)
                    )

            # remove empty keys
            num_dict = {k: v for k, v in num_dict.items() if v}

            ##############################################################################
            ##############################################################################
            ## combine all patterns - where multiple pattern exist
            ##############################################################################
            ##############################################################################
            # more than 1 keys exist (more than 1 sequences in the same row)
            if (2 in num_dict.keys()) & (len(num_dict.keys()) > 1):
                # match and swap 2 and 1
                # to do: put this into a user input dictionary
                num_dict = swap_listitems(
                    mainkey=2,
                    comparekey=1,
                    number_dict=num_dict.copy(),
                    char_count=4,
                    first=True,
                    replace=False,
                )

                # match and swap 2 and 4
                num_dict = swap_listitems(
                    mainkey=2,
                    comparekey=4,
                    number_dict=num_dict.copy(),
                    char_count=6,
                    first=True,
                    replace=True,
                )

                # match and swap 2 and 5
                num_dict = swap_listitems(
                    mainkey=2,
                    comparekey=5,
                    number_dict=num_dict.copy(),
                    char_count=6,
                    first=True,
                    replace=True,
                )

                # match and swap 2 and 6
                num_dict = swap_listitems(
                    mainkey=2,
                    comparekey=6,
                    number_dict=num_dict.copy(),
                    char_count=4,
                    first=False,
                    replace=True,
                )

                # match and swap 2 and 3
                num_dict = swap_listitems(
                    mainkey=2,
                    comparekey=3,
                    number_dict=num_dict.copy(),
                    char_count=7,
                    first=False,
                    replace=True,
                )

            # remove empty keys
            num_dict = {k: v for k, v in num_dict.items() if v}

            ##############################################################################
            ##############################################################################
            ## remove patterns to be excluded
            ##############################################################################
            ##############################################################################
            # remove from "1" where int count>4 ([\d4==True])
            count4 = re.findall(parser_rules.exclusion_rules["count4"], (" " + line))

            if 1 in num_dict.keys() and count4:
                num_dict[1] = [
                    x for x in num_dict[1] if x[:3] not in [t[:3] for t in count4]
                ]

            if (2 in num_dict.keys()) & (6 in num_dict.keys()):
                num_dict[2] = num_dict[2] + num_dict[6]
                del num_dict[6]

            # add numbers < 100 and "-"/0's
            if add_to_numdict:
                if len(num_dict.keys()) == 0:
                    num_dict[2] = add_to_numdict

            ##############################################################################
            ##############################################################################
            ## combine 1 & 2 - if exists
            ##############################################################################
            ##############################################################################

            # if 2 or more keys still exist
            if len(num_dict.keys()) > 1:
                if (1 in num_dict.keys()) & (2 in num_dict.keys()):
                    # read in all numbers
                    all_nums = re.findall(r"([ ][(-]?\d{1,3}[),]?)", (" " + line))

                    if count4:
                        all_nums = [
                            x for x in all_nums if x[:3] not in [t[:3] for t in count4]
                        ]

                    # the length of numbers should be equal to the sum of lists in the dict
                    if sum(len(v) for v in num_dict.values()) == len(all_nums):
                        value_list = [x for xs in (list(num_dict.values())) for x in xs]

                        for index, value_x in enumerate(all_nums):
                            for value_y in value_list:
                                if value_y[:3] == value_x[:3]:
                                    all_nums[index] = value_y

                        num_dict[1] = []
                        num_dict[2] = all_nums

                    else:
                        num_dict[2] = num_dict[2] + num_dict[1]
                        num_dict[1] = []

                else:
                    logger.error(f"Metric Extraction Error. {document}, {line}")

            # add numbers back to the label
            for key in num_dict.keys():
                if num_dict[key] != []:
                    extract[document][counter].numbers_list.append(num_dict[key])

    return extract


## metric count per page (used to get expected numbers per row)
def metric_count_by_page(extract: ExtractType) -> dict[str, MetricsCount]:
    metric_count_dict = {}
    for document in extract:
        metric_count_dict[document] = {}
        for line_info in extract[document].values():
            if len(line_info.numbers_list) > 1:
                break

            if len(line_info.numbers_list) == 0:
                continue

            num_count = len(line_info.numbers_list[0])
            if num_count not in metric_count_dict[document]:
                metric_count_dict[document][num_count] = 1
            else:
                metric_count_dict[document][num_count] += 1

    return metric_count_dict


## part 2 of the extract, using the initial extract as reference
def merge_extract(
    data_dict: dict[str, LineList],
    extract: ExtractType,
    metric_count_dict: dict[str, MetricsCount],
    parser_rules: ParserRules,
) -> ExtractType:
    flag_count = 0
    for document in extract:
        for line in extract[document]:
            if not metric_count_dict[document]:
                continue

            # count of numbers that should exist -- based on max count
            max_numcount = [
                k
                for k, v in metric_count_dict[document].items()
                if v == max(metric_count_dict[document].values())
            ][-1]

            # only count numbers (numbers == key:value[1])
            if not extract[document][line].numbers_list:
                continue

            if len(extract[document][line].numbers_list) == 0:
                continue

            if len(extract[document][line].numbers_list) > 1:
                # 'Edge' case (happens a ton)
                flag_count += 1

            num_count = len(extract[document][line].numbers_list[0])

            if num_count == max_numcount:
                continue

            # extract and clean all numbers
            all_int = re.findall(r"[\d.,]+", data_dict[document][line])

            # remove ineligible numbers
            count4 = re.findall(
                parser_rules.exclusion_rules["count4"],
                (" " + data_dict[document][line]),
            )

            remove = []
            for num in all_int:
                for fours in count4:
                    compare_length = len(re.sub(" ", "", fours))

                    if num[:compare_length] == re.sub(" ", "", fours):
                        remove.append(num)

                    elif num[-compare_length:] == re.sub(" ", "", fours):
                        remove.append(num)

            all_int = [x for x in all_int if x not in remove]

            # do we need to add or remove a number?
            if num_count < max_numcount:
                # any items in extract, not in all_int?
                match = []
                for num in all_int:
                    for scan in extract[document][line].numbers_list[0]:
                        compare_length = len(
                            re.sub(" ", "", re.sub(r"([()-])", "", scan))
                        )
                        if num[:compare_length] == re.sub(
                            " ", "", re.sub(r"([()-])", "", scan)
                        ):
                            match.append(scan)
                        elif num[-compare_length:] == re.sub(
                            " ", "", re.sub(r"([()-])", "", scan)
                        ):
                            match.append(scan)
                        else:
                            pass

                no_match = [
                    i for i in extract[document][line].numbers_list[0] if i not in match
                ]

                if no_match:
                    logger.error(
                        f"all_int should contain all integers in extract. {document}. {line}"
                    )
                    flag_count += 1

                # capture numbers <100
                if len(all_int) == max_numcount:
                    extract[document][line].numbers_list.append(all_int)
                # replace(-/blanks with 0)
                elif len(all_int) < max_numcount:
                    updated_all_int = re.findall(r"[\d.,-]+", data_dict[document][line])
                    for num in range(0, len(updated_all_int)):
                        for symbol in parser_rules.zero_characters:
                            if updated_all_int[num] == symbol:
                                updated_all_int[num] = "0"

                    if len(updated_all_int) == max_numcount:
                        extract[document][line].numbers_list.append(updated_all_int)
                    else:
                        logger.error(
                            f"Count of #'s extracted is less than expected #'s from overall page extract {document}. {line}"
                        )
                        flag_count += 1
                else:
                    logger.error(
                        f"Count of #'s extracted is more than expected #'s from overall page extract {document}. {line}"
                    )
                    flag_count += 1

    logger.info(f"Total Flags: {flag_count}")
    return extract
