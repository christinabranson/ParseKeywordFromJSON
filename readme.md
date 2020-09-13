# ParseKeywordFromJSON
## A flexible Python script to parse keyword values from JSON files

Written for a friend that needed to extract the data from multiple JSON files into a certain format.

## Installation

Written for Python3. Uses native functions except for PyYAML for the configuration. See requirements.txt.

Set your desired config in config.yml and run `python main.py`.

## Config

Configuration is set in the config.yml file. Here's some documentation:
Value               | Required? | Description
------              | --------- |-------------
input_files         | **Required.** | Absolute or relative path of the json files. Should end in something like `*.json`
keyword             | **Required.** | The keyword to extract data from. Should be a singular item.
output_file_path    | **Required.** | Absolute or relative path of the directory location to output to.
output_filename     | **Required.** | Name of the file. Use `{keyword}` to have the script automatically insert the value keyword
search_path         | Optional.     | The search path. Use an empty string to recursively search the entire JSON files. Use comma separated node names to only search a specific tree.
export_filename_as_col_header | Optional. | True or False to include the filename for each JSON file as the column header of the final export.
use_multiplier      | Optional.     | *Note: Only used when the extracted data is numeric.* Whether to multiply the final reported data, ie to report milliseconds as seconds
multiplier          | Optional.     | *Note: Only used when the extracted data is numeric.* The multiplier value.
num_decimals        | Optional.     | *Note: Only used when the extracted data is numeric.* How many digits to round to. If set to 0, will convert to int.

### On search_path

For the following JSON example, the value `"segments,words"` for the search_path parameter is fitting.

```json
{
    "segments": [
        {
            "words": [
                {
                    "keyword": 1,
                },
                {
                    "keyword": 2,
                }
        }
    ]
}
```
## TODO

Per friend's requirements, he requested that some of the numerical values given in the JSON files be multipled by 100 to be
more usable. This functionality is covered in the config file in `NUMBER MANIPULATION SETTINGS`
and the code in the m`ain.JsonParser.manipulate_number_values` function. This functionality works for his needs, but
is not well-validated or well-tested for other circumstances. TODO notes have been added to the code.

