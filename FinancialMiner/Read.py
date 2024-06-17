# Standard library imports
import os
import io

# Third-party imports
import pandas as pd
import numpy as np
import fitz
from PIL import Image
import pytesseract
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Initialize NLTK resources
stopw = stopwords.words("english")
lemmatizer = WordNetLemmatizer()

def read(filename):
    """
    Read PDF file and extract text and metadata.

    Args:
        filename (str): Path to the PDF file.

    Returns:
        pandas.DataFrame: DataFrame containing extracted data from PDF.
        dict: Dictionary containing extracted text per page.
    """

    # Initialize dictionaries and table
    pdf_dict = {"FILE": [], "PAGE_NUMBER": [], "WORDS": [], "COUNT_NUMBERS": []}
    text_dict = {}

    # Open PDF file using fitz
    with fitz.open(filename) as doc:

        text_dict[filename] = {}
        number_pages = 0

        for page in doc:
            # Add file and page number to the table
            pdf_dict["FILE"].append(filename)
            pdf_dict["PAGE_NUMBER"].append(number_pages)

            # Extract text from PDF page using pytesseract
            pix = page.get_pixmap(dpi=200)
            text = pytesseract.image_to_string(pix_to_image(pix), config=r"--psm 6")

            # Split text into lines and add to text_dict
            lines_page = text.split("\n")
            text_dict[filename][number_pages] = lines_page

            # Translation map for special characters
            trans_map = str.maketrans({c: None for c in "“-”(’)●–,—.%/:;'\"$§_‘°?«»ﬁ[•]~|`{}!−�"})

            # Process lines to extract words and count numbers
            words_page = [
                line.strip().lower().translate(trans_map).split(" ")
                for line in lines_page
                if not line.isspace()
            ]

            words2_page = []
            numbers_count = 0

            for line in words_page:
                for word in line:
                    if len(word) > 0:
                        try:
                            _ = float(word)
                            numbers_count += 1
                        except:
                            words2_page.append(word)

            # Lemmatize words and remove stopwords
            words_lemm = [
                lemmatizer.lemmatize(word)
                for word in words2_page
                if word not in stopw
            ]

            # Append processed data to pdf_dict
            pdf_dict["WORDS"].append(words_lemm)
            pdf_dict["COUNT_NUMBERS"].append(numbers_count)

            number_pages += 1

    # Convert pdf_dict to DataFrame
    df = pd.DataFrame(pdf_dict)

    # Add dummy variables to DataFrame
    df["NUMBERS<5"] = df["COUNT_NUMBERS"].apply(lambda value: 1 if (value < 5) else 0)
    df["WORDS<20"] = df["WORDS"].apply(lambda value: 1 if len(value) < 20 else 0)
    df["PAGE>12"] = df["PAGE_NUMBER"].apply(lambda value: 1 if (value > 12) else 0)

    return df, text_dict

def osd_detection(pix):
    """
    Perform orientation and script detection on an image.

    Args:
        pix (fitz.Pixmap): Pixmap object representing an image page.

    Returns:
        dict: Dictionary containing orientation and script detection results.
    """
    image_bytes = pix.tobytes('png')
    image = Image.open(io.BytesIO(image_bytes))
    osd_dict = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT, config="--psm 0")
    return osd_dict

def pix_to_image(pix):
    """
    Convert fitz.Pixmap to PIL Image.

    Args:
        pix (fitz.Pixmap): Pixmap object representing an image.

    Returns:
        numpy.ndarray: NumPy array representing the image.
    """
    bytes = np.frombuffer(pix.samples, dtype=np.uint8)
    img = bytes.reshape(pix.height, pix.width, pix.n)
    return img

def text_extract_with_osd(pix, rotation=0):
    """
    Extract text from an image after correcting orientation.

    Args:
        pix (fitz.Pixmap): Pixmap object representing an image page.
        rotation (int): Rotation angle for image correction.

    Returns:
        str: Extracted text from the corrected image.
    """
    image_bytes = pix.tobytes('png')
    image = Image.open(io.BytesIO(image_bytes))

    corrected_image = image.rotate(-rotation, expand=True)
    text = pytesseract.image_to_string(corrected_image, config=r"--psm 6")

    return text
