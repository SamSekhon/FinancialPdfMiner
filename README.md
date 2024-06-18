# FinancialPDFMiner

The problem I am addressing is the extraction of financial data from Financial Statement PDFs without the need to train a model on a specific dataset or utilize large language models, which can be resource-intensive. In this module, I leverage general accounting principles to create a highly generic parsing module capable of extracting financial information from any of the three core financial statements: Income Statement, Cash Flow Statement, and Statement of Financial Position.

The classification models were trained using labeled open-source data. The champion model is a Naive Bayes classifier, with an XGBoost classifier serving as the secondary (challenger) model. For the modeling approach, I process all the pages of a given PDF and classify each page as either a target (relevant) or not.

I chose the Naive Bayes model over XGBoost because it performs exceptionally well on statements that are split across multiple pages. This is due to the Naive Bayes model’s independence assumption, meaning it does not consider the relationships between words in the statement for classification, unlike XGBoost, which does. The classification model  achieved an F1 score of 0.99, indicating high accuracy and reliability in identifying financial statements in a given PDF.

## Overview

The goal of FinancialPDFMiner is to automate the extraction of financial data from PDF files, which are commonly used for publishing financial statements. This tool streamlines the extraction process by leveraging machine learning for page classification and customizable parsing rules for data extraction.

The process follows the following steps:

1. **Read:** PDF File is read using Pytesseract (optionally EasyOCR) with OSD correction if needed. Each page is saved as a seperate chunk.
2. **Classify:** Multinomial Naives Bayes Classifier is used to tag each extracted page. The classifier assigns each page 1 or 0 based on the probability of it being the target page.
3. **Parse:** Pages tagged as 1 or the target page are scraped using the parser module. See below for full details on the parsing steps.


## Demo: Income Statement

**INPUT**
![Alt text](<data/income_pdf.png>)

**OUTPUT**
![Alt text](<data/incomeextract.jpg>)

## Files and Functionality

- **main.py**: Main script integrating the entire process:
  - **OCR and PDF Reading**: Utilizes `read` from `FinancialMiner.Read` to read PDFs using OCR.
  - **Classification**: Uses `create_predictions` from `FinancialMiner.ClassifyPDF` to classify pages as financial statements of interest.
  - **Parsing**: Executes `run` from `FinancialMiner.parsing.ParsePdf` to parse and extract information from identified financial statement pages using defined parsing rules.

- **config.yaml**: Configuration file containing settings for parser rules and PDF classification parameters. Currently supports configuration for income and financial position statements extraction.

- **models/**:
  - **'StatementName'_model_mnb.sav**: Trained Naive Bayes Multinomial classifier model file. Current support for Financial Position and Income Statement.
  - **'StatementName'_vocab.txt**: Vocabulary file for creating the feature matrix for the specific statement.

## Classification Models

The models used in FinancialPDFMiner are trained Naive Bayes Multinomial classifiers. Each model (`model.sav`) in the `models/` directory is accompanied by a vocabulary file to create the feature matrix. These models were trained using a diverse set of labeled financial data, enabling them to classify pages within PDF documents as relevant financial statements with high accuracy.

The classification process utilizes a Bag of Words representation, where the presence of specific words (from the respective vocabularies) in a page's content determines its classification as an income statement or cash flow statement.

These models play a crucial role in automating the initial identification of relevant financial statements within PDF documents, streamlining the subsequent extraction and parsing processes.

## Parsing Module

The parsing module in this project extracts crucial information from financial statements using a structured approach. Here’s how it works:

### Row Wise Parsing

Financial statements typically follow a format where each line contains structured data.
"Revenue 133,130 133,110"

The parsing begins by using regular expressions (regex) to extract these structured lines row by row from the financial statement pages. Each line is parsed to identify labels and their associated numeric values.

### Page Wise Parsing

After extracting data row by row, the parsing module aggregates this information to understand the structure of the financial statement. Key tasks in this phase include:

- **Determining the Number of Periods:** Based on the row-wise parsing results, the module identifies the number of periods of historical data available (e.g., in the above example, there are 2 periods: 133,130 and 133,110).

- **Cleaning and Standardization:** Special symbols such as dashes (—), m-dashes (–), and others are cleaned or standardized during this phase to ensure consistency in data representation.

### Date Extraction

Using regex, the parsing module identifies and extracts dates embedded within the financial statements. These dates are crucial for organizing the parsed data accurately.

### Data Representation

Finally, the parsed information is structured and organized into a dataframe format. This format allows for easy manipulation, analysis, and integration with other data sources or analytical tools.

#### Example Workflow

1. **Row-wise Parsing:** Identify lines matching the expected format.
2. **Page-wise Analysis:** Aggregate data to understand historical periods and clean special symbols.
3. **Date Extraction:** Use regex patterns to locate and extract dates.
4. **Dataframe Creation:** Structure parsed data into a dataframe for further processing.

This approach ensures that the financial data extracted from statements is accurate, structured, and ready for subsequent analysis or reporting tasks.

## Installation

1. Clone the repository:

git clone https://github.com/SamSekhon/FinancialPdfMiner.git

cd FinancialPDFMiner


2. Install dependencies:

pip install -r requirements.txt


Ensure all dependencies, including those listed in `requirements.txt`, are installed in your environment.

## Usage

1. Ensure your PDF files are placed in the `pdfs` directory or adjust paths accordingly.

2. Modify `config.yaml` to select the appropriate model for the statement of interest.

3. Run the main script:

python main.py


This script will:
- Read the specified PDF (`pdfs/demo_financials.pdf` in the example).
- Use OCR to extract text from the PDF.
- Classify pages to identify relevant financial statements.
- Parse and extract structured data based on configured rules.
- Output the extracted data to `Model_Extract.csv`.

## Future Enhancements

In future updates, we aim to enhance FinancialPDFMiner by:
- Adding support for additional document formats.
- Adding support for all statement types.
- Improving classification accuracy and parsing efficiency.
- Integrating more robust error handling and logging mechanisms.

## Contributing

Contributions to FinancialPDFMiner are welcome! 

Feel free to submit pull requests for bug fixes, new features, or enhancements that can benefit users extracting financial data from PDF documents.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT) - see the LICENSE file for details.
