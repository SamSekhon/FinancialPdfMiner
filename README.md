# FinancialPDFMiner

FinancialPDFMiner is an NLP-based tool designed to extract financial statements information from PDF documents. The process involves using OCR to read PDFs, employing a classification model to identify relevant financial statement pages, and utilizing a parsing module to extract structured information from those pages.

## Overview

The goal of FinancialPDFMiner is to automate the extraction of financial data from PDF files, which are commonly used for publishing financial statements. This tool streamlines the extraction process by leveraging machine learning for page classification and customizable parsing rules for data extraction.

## Files and Functionality

- **main.py**: Main script integrating the entire process:
  - **OCR and PDF Reading**: Utilizes `read` from `FinancialMiner.Read` to read PDFs using OCR.
  - **Classification**: Uses `create_predictions` from `FinancialMiner.ClassifyPDF` to classify pages as financial statements of interest.
  - **Parsing**: Executes `run` from `FinancialMiner.parsing.ParsePdf` to parse and extract information from identified financial statement pages using defined parsing rules.

- **config.yaml**: Configuration file containing settings for parser rules and PDF classification parameters. Currently supports configuration for income and financial position statements extraction.

- **models/**:
  - **'StatementName'_model_mnb.sav**: Trained Naive Bayes Multinomial classifier model file. Current support for Financial Position and Income Statement.
  - **'StatementName'_vocab.txt**: Vocabulary file for creating the feature matrix for the specific statement.

### Classification Models

The models used in FinancialPDFMiner are trained Naive Bayes Multinomial classifiers. Each model (`model.sav`) in the `models/` directory is accompanied by a vocabulary file to create the feature matrix. These models were trained using a diverse set of labeled financial data, enabling them to classify pages within PDF documents as relevant financial statements with high accuracy.

The classification process utilizes a Bag of Words representation, where the presence of specific words (from the respective vocabularies) in a page's content determines its classification as an income statement or cash flow statement.

These models play a crucial role in automating the initial identification of relevant financial statements within PDF documents, streamlining the subsequent extraction and parsing processes.

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
