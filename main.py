# Standard library imports
import yaml

# Third-party imports
from FinancialMiner.Read import read
from FinancialMiner.ClassifyPDF import create_predictions
from FinancialMiner.parsing.ParsePdf import run, ParserData, ParserRules

# Load configuration from YAML file
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Extract specific rules and patterns from configuration
num_rules_dict = {int(k): v for k, v in config['parser_rules']['num_rules'].items()}
num_exclude_dict = config['parser_rules']['num_exclude']
remove_strings = config['parser_rules']['remove_strings']
replace_blanks = config['parser_rules']['replace_blanks']
date_pattern_dict = config['parser_rules']['date_pattern']
thousand_pattern = config['parser_rules']['thousand_pattern']
dict_label_search = config['parser_rules']['label_search']

if __name__ == '__main__':
    # Read and extract text from PDF file
    df, text_dict = read('pdfs/demo_financials.pdf')

    # Predict and classify PDF content
    model_df = create_predictions(config['classify_pdf'], df)

    # Parse PDF content using defined rules and patterns
    pdf_output = run(
        model_df,
        None,
        ParserData(text_dict, None),
        ParserRules(
            num_rules_dict,
            num_exclude_dict,
            remove_strings,
            replace_blanks,
            date_pattern_dict,
            thousand_pattern,
            dict_label_search
        )
    )

    # Save parsed output to a CSV file
    pdf_output.to_csv("Model_Extract.csv")
