import pandas as pd
import numpy as np
import fitz
import os
import io

from PIL import Image
import pytesseract


from nltk.corpus import stopwords
stopw = stopwords.words("english")

from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()


def read(filename):
    # create table, which will eventually be converted to numpy
    pdf_dict = {"FILE": [], "PAGE_NUMBER": [], "WORDS": [], "COUNT_NUMBERS": []}
    # dictionary 
    text_dict = {}

    # initialize document object
    with fitz.open(filename) as doc:

        text_dict[filename] = {}

        # initialize page counter
        number_pages = 0

        for page in doc:

            # adding file and page number to the table
            pdf_dict["FILE"].append(filename)
            pdf_dict["PAGE_NUMBER"].append(number_pages)

            # extracting text from pdf page
            pix = page.get_pixmap(dpi=200)
            text = pytesseract.image_to_string(
                pix_to_image(pix), config=r"--psm 6"
            )

            # Splitting text into lines and adding those
            # to the output text_dict
            lines_page = text.split("\n")
            text_dict[filename][number_pages] = lines_page
            # text_dict[file].append(lines_page)

            # Refer to the below for the behaviour of translate
            # https://docs.python.org/3/library/stdtypes.html#str.translate
            trans_map = str.maketrans(
                {c: None for c in "“-”(’)●–,—.%/:;'\"$§_‘°?«»ﬁ[•]~|`{}!−�"}
            )

            # remove all lines that are white space. Then for each remaining line
            # * strip off trailing and leading white space
            # * convert all characters to lower case
            # * filter out all the characters described in the trans_map
            # * split the line into individual words
            words_page = [
                line.strip().lower().translate(trans_map).split(" ")
                for line in lines_page
                if not line.isspace()
            ]

            # create a list of the words on the page, and count the
            # number of numeric values before filtering them out
            words2_page = []
            numbers_count = 0

            for line in words_page:
                for word in line:
                    if len(word) > 0:
                        # I cannot believe there is no
                        # built in for this ...
                        try:
                            _ = float(word)
                            numbers_count += 1
                        except:
                            words2_page.append(word)

            words_lemm = [
                lemmatizer.lemmatize(word)
                for word in words2_page
                if word not in stopw
            ]

            pdf_dict["WORDS"].append(words_lemm)
            pdf_dict["COUNT_NUMBERS"].append(numbers_count)

            number_pages += 1

    # convert to dataframe and add dummy variables
    df = pd.DataFrame(pdf_dict)

    # Adding dummy variables
    df["NUMBERS<5"] = df["COUNT_NUMBERS"].apply(
        lambda value: 1 if (value < 5) else 0
    )
    df["WORDS<20"] = df["WORDS"].apply(lambda value: 1 if len(value) < 20 else 0)
    df["PAGE>12"] = df["PAGE_NUMBER"].apply(lambda value: 1 if (value > 12) else 0)

    return df, text_dict


def osd_detection(pix):
    image_bytes = pix.tobytes('png')
    image = Image.open(io.BytesIO(image_bytes))
    osd_dict = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT, config = "--psm 0")
    return osd_dict

def pix_to_image(pix):
    bytes = np.frombuffer(pix.samples, dtype = np.uint8)
    img = bytes.reshape(pix.height, pix.width, pix.n)
    return img

def text_extract_with_osd(pix, rotation = int):
    image_bytes = pix.tobytes('png')
    image = Image.open(io.BytesIO(image_bytes))

    corrected_image = image.rotate(-rotation, expand = True)
    text = pytesseract.image_to_string(corrected_image, config = r"--psm 6")

    return text