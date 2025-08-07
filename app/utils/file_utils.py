import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def read_mapping_file(file_path: str) -> List[Dict]:
    """
    Safely reads a JSON mapping file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        List[Dict]: The loaded mapping data as a list of dictionaries.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Mapping file not found at path: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from mapping file: {file_path}")
        raise

def create_random_to_original_filename_lookup(mapping_data: List[Dict]) -> Dict:
    """
    Creates a lookup dictionary from randomized filenames to original filenames.

    Args:
        mapping_data (list): A list of dictionaries from the mapping file.

    Returns:
        dict: A dictionary where keys are random filenames and values are original filenames.
    """
    lookup = {}
    for item in mapping_data:
        random_name = item.get("random_filename")
        original_name = item.get("original_filename")
        if random_name and original_name:
            lookup[random_name] = original_name
    return lookup