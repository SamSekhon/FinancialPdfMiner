from dataclasses import dataclass
from pandas import DataFrame
from datetime import date
from typing import Any

# The output given by pytesseract
ModelOutput = DataFrame

# maps page numbers to a list of lines on that page
# TODO: convert the value to a list of list of strings,
# rather than a dict
FileText = dict[str : list[str]]

# represents a list lines from a document
LineList = list[str]


@dataclass
class ParserData:
    # Maps filenames to transcriptions.
    file_transcription: dict[str, FileText]

    # A data frame describing information about all the
    # files we are looking to process. Note that this includes
    # a number of files not included in the above, to save processing
    # time (since they aren't important for us)
    file_descriptions: DataFrame


@dataclass
class ParserRules:
    # regexes for matching numbers in a
    # document
    numeric_matching_rules: dict[int, str]

    # regexes for finding explicitly
    # excluded patterns
    exclusion_rules: dict[str, str]

    # strings to be filtered out
    # of the page
    # TODO: merge this into exclusion
    # rules
    excluded_strings: list[str]

    # set of characters which can be
    # taken to mean 0 in a financial
    # statement
    zero_characters: list[str]

    # regexes for matching dates
    # in various formats
    # the Any below really should be
    # either list[str] or dict[str, list[str]].
    # TODO: fix this
    date_rules: dict[str, Any]

    # A set of rules to describe accounting
    # short hands for multipliers. Currently
    # only used to handler multipliers of 1000
    multiplier_rules: dict[str, list[str]]

    # A set of rules to search for specific
    # labels. creates tags for audited,
    # unaudited and annual
    additional_labels: dict[str, str]


# Month, day, year
DateTuple = tuple[str, str, str]


@dataclass
class LineExtractInfo:
    # The string label on a line (IE revenue)
    label: str

    # List of all the numeric values found on the line
    # (the reason they are strings is because they are regex
    # matches)
    numbers_list: list[list[str]]

    # the periods for the values found on the line
    # the actual type is waiting on me figuring out
    # all the dates stuff
    dates: list[DateTuple]

    # multiplier. Indicates a multiplier
    # on the listed numeric value
    multiplier: int | None


# maps every line in every document to information
# about that line. (Note, this is used after documents
# are converted to line lists by get_predictions_text)
ExtractType = dict[str, dict[int, LineExtractInfo]]

# maps possible count values to the number of lines
# which have that number of metrics.
MetricsCount = dict[int, int]

# maps files to strings of text, which contain dates
FileDateInfo = dict[str, str]

# The result of searching a string of text and finding
# values which may represent dates. (The optional types
# are in the case that no matches are found)
SearchDateResult = tuple[list[str] | None, int | None]
