import argparse
import json
import xml.etree.ElementTree as ET
import yaml
import logging
import os
import jsonschema
from jsonschema import validate
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def setup_argparse():
    """
    Sets up the command-line argument parser.

    Returns:
        argparse.ArgumentParser: The argument parser object.
    """
    parser = argparse.ArgumentParser(description="Validates structured data files against a schema.")
    parser.add_argument("file_path", help="Path to the data file.")
    parser.add_argument("schema_path", help="Path to the schema file.")
    parser.add_argument("--file_type", choices=['json', 'xml', 'yaml'], required=True, help="Type of the data file (json, xml, yaml).")
    return parser


def load_data(file_path, file_type):
    """
    Loads data from the specified file based on its type.

    Args:
        file_path (str): Path to the data file.
        file_type (str): Type of the data file (json, xml, yaml).

    Returns:
        dict or ET.Element: The loaded data as a dictionary (JSON, YAML) or an ElementTree (XML).
        None: If an error occurs during loading.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file type is unsupported.
        Exception: For other errors during file reading or parsing.
    """
    try:
        with open(file_path, 'r') as f:
            if file_type == 'json':
                data = json.load(f)
            elif file_type == 'yaml':
                data = yaml.safe_load(f)  # Use safe_load to prevent arbitrary code execution
            elif file_type == 'xml':
                tree = ET.parse(f)
                data = tree.getroot()
            else:
                raise ValueError("Unsupported file type.")
            return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except ValueError as e:
        logging.error(f"Error loading data: {e}")
        raise
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")  # Log the full traceback
        raise


def load_schema(schema_path, file_type):
    """
    Loads the schema from the specified file.

    Args:
        schema_path (str): Path to the schema file.
        file_type (str): The file type to determine the loader method

    Returns:
        dict: The loaded schema as a dictionary (JSON, YAML).  For XML, returns the schema file path as string
            None: if schema loading fails

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the schema file type is unsupported.
        Exception: For other errors during schema file reading or parsing.
    """
    try:
        with open(schema_path, 'r') as f:
            if file_type == 'json':
                schema = json.load(f)
            elif file_type == 'yaml':
                schema = yaml.safe_load(f)
            elif file_type == 'xml':
                schema = schema_path  # returns the xsd path as a string
            else:
                raise ValueError("Unsupported schema file type.")
            return schema
    except FileNotFoundError:
        logging.error(f"Schema file not found: {schema_path}")
        raise
    except ValueError as e:
        logging.error(f"Error loading schema: {e}")
        raise
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        raise


def validate_data(data, schema, file_type):
    """
    Validates the data against the provided schema.

    Args:
        data (dict or ET.Element): The data to validate.
        schema (dict or str): The schema to validate against. If XML file type, schema will be a string representing the xsd file path
        file_type (str): Type of the data file (json, xml, yaml).

    Returns:
        bool: True if the data is valid, False otherwise.

    Raises:
        jsonschema.exceptions.ValidationError: If the data does not conform to the schema (for JSON and YAML).
        ET.ParseError: If the XML validation fails.
        ValueError: If the file_type is not supported.
        Exception: For unexpected validation errors.
    """
    try:
        if file_type == 'json':
            validate(instance=data, schema=schema)
            return True
        elif file_type == 'yaml':
            validate(instance=data, schema=schema)
            return True
        elif file_type == 'xml':
            try:
                # XML validation against XSD is a complex topic that requires additional libraries and careful implementation
                # This part of the script can be extended to perform more robust XML validation with XSD.
                import lxml.etree as lxml_ET
                xmlschema_doc = lxml_ET.parse(schema)
                xmlschema = lxml_ET.XMLSchema(xmlschema_doc)
                xml_string = ET.tostring(data)
                xml_doc = lxml_ET.fromstring(xml_string)

                xmlschema.assertValid(xml_doc)
                return True

            except lxml.etree.XMLSchemaError as e:
                logging.error(f"XML Schema validation error: {e}")
                return False
            except lxml.etree.XMLSyntaxError as e:
                logging.error(f"XML Syntax Error: {e}")
                return False
            except Exception as e:
                logging.exception(f"An unexpected error occurred: {e}")
                return False
        else:
            raise ValueError("Unsupported file type.")
    except jsonschema.exceptions.ValidationError as e:
        logging.error(f"Validation error: {e}")
        return False
    except jsonschema.exceptions.SchemaError as e:
        logging.error(f"Schema error: {e}")
        return False
    except ValueError as e:
        logging.error(f"Error during validation: {e}")
        return False
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        return False


def is_valid_file_path(file_path):
    """
    Check if a file path is valid.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file path is valid, False otherwise.
    """
    try:
        # Check if the file exists and is a file
        if not Path(file_path).is_file():
            logging.warning(f"File does not exist or is not a file: {file_path}")
            return False
        # Check if the file is readable
        if not os.access(file_path, os.R_OK):
            logging.warning(f"File is not readable: {file_path}")
            return False
        return True
    except Exception as e:
        logging.error(f"Error checking file path: {e}")
        return False


def main():
    """
    Main function to parse arguments, load data and schema, and validate the data.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Input validation: Check if the file paths are valid
    if not is_valid_file_path(args.file_path):
        print("Invalid file path. Exiting.")
        return
    if not is_valid_file_path(args.schema_path):
        print("Invalid schema path. Exiting.")
        return

    try:
        data = load_data(args.file_path, args.file_type)
        schema = load_schema(args.schema_path, args.file_type)

        if data is not None and schema is not None:
            if validate_data(data, schema, args.file_type):
                print("Data validation successful.")
            else:
                print("Data validation failed.")
        else:
            print("Failed to load data or schema.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Example usage (for development and testing):
    # Create dummy files if they don't exist
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({"name": "John Doe", "age": 30}, f)
    if not os.path.exists("schema.json"):
        with open("schema.json", "w") as f:
            json.dump({"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}, "required": ["name", "age"]}, f)

    # Example command-line usage:
    # python main.py data.json schema.json --file_type json
    main()