#!/usr/bin/python3
# Runs with `python main.py`
# Configuration can be found in config.yml
# See readme.md for details

import os
import glob
import json
from csv import writer
import codecs
import re
import yaml

# Gets the integer from string
def int_or_text(text):
    return int(text) if text.isdigit() else text

# To sort by "page#"
# This is to make sure that "page10" comes after "page9" instead of "page1"
def sort_by_int_in_text(text):
    return [int_or_text(char) for char in re.split('(\d+)', text)]

# Class to read in the JSON files, parse out the desired keyword, and export as CSV
# Use JsonParser(config_dict).to_csv() where config_dict is a dictionary of configuration settings
# See Readme for expected values
class JsonParser:

    # Class constructor, sets all necessary data
    def __init__(self, config):
        # Set the config dict
        self.config = config
        # Will raise an exception and die if something is wrong
        self.validate_config()

        # Initialize the keyword storage
        self.keyword_list = []
        # Initialize the formatted/rotated keyword storage
        self.rotated_keyword_list = []

        # Set helper variable for generating the final rotated array
        self.max_length = 0

        # Set list of files and sort by "page#"
        files = glob.glob(self.config["input_files"])
        files.sort(key=sort_by_int_in_text)
        self.files = files

        # Do the work to extract the keyword from files
        self.extract_keyword_from_files()

        # Format the extracted keywords for export
        # We're reading in the data to export the data from each file as a row
        # But the export needs to be each file as a column
        # This function rotates the data
        self.rotate_keywords_for_export()

    # Validates the given configuration
    def validate_config(self):
        # Some of our config values are required. Make sure that these are set
        for required_value in ["input_files", "keyword", "output_file_path", "output_filename"]:
            if required_value not in self.config or len(self.config[required_value]) == 0:
                raise Exception("Invalid configuration! See Readme for expected configuration. "
                                "Value " + required_value + " is not set!")

        # Make sure files exist
        files = glob.glob(self.config["input_files"])
        if len(files) == 0:
            raise Exception("Invalid configuration! See Readme for expected configuration. "
                            "No files in path " + self.config["input_files"])

        # Check if the files are readable
        # Note: we're only checking to see if the first file is editable under the assumption that if one is,
        # they all are. If things are mysteriously not working, check this....
        if not os.access(files[0], os.R_OK):
            raise Exception("Invalid configuration! See Readme for expected configuration. "
                            "Input files are not readable!")

        # Check if output path is writable
        if not os.access(self.config["output_file_path"], os.W_OK):
            raise Exception("Invalid configuration! See Readme for expected configuration. "
                            "Output path is not writable!")

        # TODO: Add some additional validation in case the number manipulation section is enabled

        # Yay
        return

    # Read through each of the files and searches for the keyword either by the search path, or globally
    def extract_keyword_from_files(self):
        keyword = self.config["keyword"]
        export_filename_as_col_header = self.config["export_filename_as_col_header"]
        search_path = self.config["search_path"]
        for file in self.files:
            file_keywords = []
            if export_filename_as_col_header:
                file_keywords.append(os.path.basename(file))
            json_data = json.load(codecs.open(file, 'r', 'utf-8-sig'))
            if len(search_path) > 0:
                file_keywords = self.get_keyword_by_search_path(json_data, keyword, file_keywords, search_path)
            else:
                file_keywords = self.get_keyword_by_global(json_data, keyword, file_keywords)

            if len(file_keywords) > self.max_length:
                self.max_length = len(file_keywords)

            self.keyword_list.append(file_keywords)

    # Generator that recursively moved down defined nodes looking for keyword data
    def search_path_search(self, json_data, keyword, search_path_list, level):
        node_key = search_path_list[level]
        is_last_node = ( level == len(search_path_list) - 1 )

        # print("search_path_search | level: {}, node_key: {}, is_last_node: {}".format(level, node_key, is_last_node))

        for node_values in json_data[node_key]:
            if is_last_node and keyword in node_values:
                yield node_values[keyword]
            else:
                for value in self.search_path_search(node_values, keyword, search_path_list, level + 1):
                    yield value

    # Uses the search_path_search generator to get all values for the keyword based on a
    # well defined node path
    def get_keyword_by_search_path(self, json_data, keyword, file_keywords, search_path):
        search_path_list = [path_node.strip() for path_node in search_path.split(",")]
        for value in self.search_path_search(json_data, keyword, search_path_list, 0):
            file_keywords.append(self.manipulate_number_values(value))
        return file_keywords

    # Generator that recursively searches the file looking for keyword data
    def global_recursive_search(self, json_data, keyword):
        for k, v in json_data.items():
            if k == keyword:
                yield v
            elif isinstance(v, dict):
                for dict_val in self.global_recursive_search(v, keyword):
                    yield dict_val
            elif isinstance(v, list):
                for list_val in v:
                    for dict_val in self.global_recursive_search(list_val, keyword):
                        yield dict_val

    # Uses the global_recursive_search generator to get the values for all instances of keyword
    # anywhere within the JSON file
    def get_keyword_by_global(self, json_data, keyword, file_keywords):
        for value in self.global_recursive_search(json_data, keyword):
            file_keywords.append(self.manipulate_number_values(value))
        return file_keywords

    # Function to rotate the data so that we export rows as columns
    def rotate_keywords_for_export(self):
        self.rotated_keyword_list = [["" for x in range(len(self.files))] for y in range(self.max_length)]
        colI = 0
        for row in self.keyword_list:
            rowI = 0
            for rowVal in row:
                # print('{},{}: {}'.format(colI, rowI, rowVal))  # debug
                self.rotated_keyword_list[rowI][colI] = rowVal
                rowI += 1
            colI += 1

    # Manipulates the value depending on config
    # TODO: This function needs some additional validation to make sure that the values are well-defined
    def manipulate_number_values(self, value):
        if self.config["use_multiplier"]:
            if isinstance(value, float) or isinstance(value, int):
                if self.config["num_decimals"] == 0:
                    return int(value * float(self.config["multiplier"]))
                else:
                    return round(value * float(self.config["multiplier"]), self.config["num_decimals"])

        # Just return the original values
        return value

    # Outputs the files to CSV
    def to_csv(self):
        output_file = os.path.join(self.config["output_file_path"], self.config["output_filename"])
        if "{keyword}" in output_file:
            output_file = output_file.replace("{keyword}", self.config["keyword"])
        wtr = writer(open(output_file, 'w'), delimiter=',', lineterminator='\n')
        for x in self.rotated_keyword_list: wtr.writerows([x])


if __name__ == '__main__':
    # Open config file and extract settings
    with open(r'config.yml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        # Initialize the class and export as CSV
        JsonParser(config).to_csv()