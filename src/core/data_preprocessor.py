# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 12:33:53 2022

Data Preprocessing Module for LSH-based Entity Resolution

This module handles the preprocessing of product data for LSH-based matching.
It includes functionality for:
- Loading and transforming JSON product data
- Cleaning and standardizing product information
- Extracting model words using regex patterns
- Identifying and managing duplicate products
- Brand extraction and validation

@author: Niels
"""
import json
from src.datasketch_custom_implementation import datasketch
from tomlkit import load as toml_load
import re
import logging
import sys
import numpy as np
import pandas as pd
from scipy.sparse import lil_matrix
import matplotlib.pyplot as plt
import uuid
from collections import defaultdict
from itertools import combinations

log_format = "%(levelname)s %(asctime)s - %(message)s"

logging.basicConfig(stream=sys.stdout, filemode="w", format=log_format, level=logging.INFO)
logger = logging.getLogger("minhash")


def load_data(file_loc):
    """
    Load product data from a JSON file.

    Args:
        file_loc (str): Path to the JSON file

    Returns:
        dict: Loaded JSON data
    """
    with open(file_loc, "r") as file_:
        data = json.load(file_)
    return data


def transform_data(data):
    """
    Transform product data by adding UUIDs and creating both list and dictionary outputs.

    This function processes the input data by:
    1. Generating unique IDs for each product
    2. Creating a list representation for iteration
    3. Creating a dictionary representation for quick lookups

    Args:
        data (dict): Input data with model IDs as keys and product lists as values

    Returns:
        tuple: (list of products, dictionary of products by UUID)
    """
    list_output = []
    dict_output = {}
    for model_id in data:
        for product in data[model_id]:
            # generate uuid
            unique_id = uuid.uuid4()
            product["uuid"] = unique_id
            list_output.append(product)
            dict_output[unique_id] = product
    return list_output, dict_output


def clean_data(data, matches):
    """
    Clean product data by standardizing text formats.

    Performs text cleaning on both product titles and feature maps using
    a dictionary of correct forms and their alternatives.

    Args:
        data (dict): Dictionary of products indexed by UUID
        matches (dict): Dictionary mapping correct forms to lists of alternatives

    Returns:
        dict: Cleaned product data
    """
    logger.info("cleaning data inputs")
    return_dict = {}
    for uuid, product in data.items():
        # clean titles
        for correct_form in matches:
            for alternative in matches[correct_form]:
                product["title"] = product["title"].replace(alternative, correct_form)

        # clean feature maps
        for feature, value in product["featuresMap"].items():
            for correct_form in matches:
                for alternative in matches[correct_form]:
                    product["featuresMap"][feature] = product["featuresMap"][feature].replace(alternative, correct_form)
        return_dict[uuid] = product
    return return_dict


def tuple_model_words_to_list(model_words_regex_result):
    """
    Convert regex match tuples to list of model words.

    Args:
        model_words_regex_result (list): List of regex match tuples

    Returns:
        list: Extracted model words
    """
    result = [x[0] for x in model_words_regex_result]
    return result


def extract_model_words(data):
    """
    Extract model words from product titles and feature maps.

    Uses regex patterns to identify model identifiers in product information:
    - Words containing both letters and numbers
    - Numeric values with optional units
    - Filtered to remove the actual model ID

    Args:
        data (dict): Dictionary of products

    Returns:
        dict: Products with added model_words sets
    """
    logger.info("extracting model words using regex expressions")
    # Find all model words
    regex_title = re.compile(r"([a-zA-Z0-9]*(([0-9]+[^0-9, ]+)|([^0-9, ]+[0-9]+))[a-zA-Z0-9]*)")
    regex_KVP = re.compile(r"(^\d+(\.\d+)?[a-zA-Z]+$|^\d+(\.\d+)?$)")
    return_dict = {}
    for uuid, product in data.items():
        try:
            model_id = product["modelID"]
            model_words = tuple_model_words_to_list(regex_title.findall(product["title"]))
            for key, value in product["featuresMap"].items():
                model_words_values = tuple_model_words_to_list(regex_KVP.findall(value))

                # Extract non-numerical part of model word
                model_words_numerical = [re.sub(pattern=r"[a-zA-Z]+", repl="", string=x) for x in model_words_values]

                model_words.extend(model_words_numerical)

            model_words_filtered = [mw for mw in model_words if mw != model_id]
            product["model_words"] = set(model_words_filtered)
            return_dict[uuid] = product
        except Exception as e:
            print(f"exception: {e}")
            print(regex_title.findall(product["title"]))
    return return_dict


def extract_tv_brands(data, tv_brands):
    """
    Extract TV brands from product information.

    Attempts to identify brands through:
    1. Title matching using regex
    2. Feature map value matching
    Tracks brand statistics and potential misidentifications

    Args:
        data (dict): Dictionary of products
        tv_brands (list): List of valid TV brand names

    Returns:
        tuple: (products with brands, unbranded products, brand statistics, misidentified pairs)
    """
    logger.info("extracting tv brand from product information")
    total_products = len(data)
    count = 0
    title_no_brands = {}
    brands_in_data = {}
    dict_to_return = {}
    for uuid, product in data.items():
        # first check title
        for brand in tv_brands:
            brand_lower = brand.lower()
            # Regex covers both cases where it is actually part of a longer word and when there is not a space after the brand
            if (
                "(" not in brand
                and ")" not in brand
                and re.search(rf"\b({brand_lower})\b", product["title"].lower(), re.IGNORECASE)
            ):
                # if brand.lower() in product['title'].lower():
                product["brand"] = str(brand)
                count += 1
                if brand not in brands_in_data:
                    brands_in_data[brand] = 1
                else:
                    brands_in_data[brand] += 1
                break
        else:
            for brand in tv_brands:
                # check key-value pairs
                for key, value in product["featuresMap"].items():
                    if brand.lower() in value.lower():
                        product["brand"] = str(brand)
                        count += 1
                        if brand not in brands_in_data:
                            brands_in_data[brand] = 1
                        else:
                            brands_in_data[brand] += 1
                        break
                else:
                    continue
                break
            else:
                product["brand"] = "Unknown"
                title_no_brands[product["title"]] = product["featuresMap"]
        dict_to_return[uuid] = product
    misidentified = [
        (str(product_x["brand"]), str(product_y["brand"]), product_x, product_y)
        for uuid, product_x in data.items()
        for uuid, product_y in data.items()
        if product_x["brand"] != product_y["brand"] and product_x["modelID"] == product_y["modelID"]
    ]
    logger.info("identified {}% of brands".format(str(count / total_products * 100)))
    return data, title_no_brands, brands_in_data, misidentified


def get_model_id_to_uuid(data):
    """
    Create mapping from model IDs to product UUIDs.

    Args:
        data (list): List of products

    Returns:
        defaultdict: Dictionary mapping model IDs to sets of product UUIDs
    """
    duplicates_dict = defaultdict(set)
    for product in data:
        duplicates_dict[product["modelID"]].add(product["uuid"])
    return duplicates_dict


def data_cleaning_pipeline(file_loc):
    """
    Complete data preprocessing pipeline.

    This function orchestrates the entire preprocessing workflow:
    1. Load raw data
    2. Transform data structure
    3. Identify duplicates
    4. Clean text data
    5. Extract brands
    6. Extract model words

    Args:
        file_loc (str): Path to input JSON file

    Returns:
        tuple: (preprocessed product data, list of duplicate pairs)
    """
    data = load_data(file_loc)

    # load config
    with open("config.toml") as file_:
        config = toml_load(file_)

    data_transformed, dict_data_transformed = transform_data(data)

    # extract duplicates
    model_id_to_uuid = get_model_id_to_uuid(data_transformed)
    model_id_to_uuid_duplicates = {x: model_id_to_uuid[x] for x in model_id_to_uuid if len(model_id_to_uuid[x]) > 1}
    duplicates = [model_id_to_uuid[x] for x in model_id_to_uuid_duplicates]
    duplicates_summary = {2: 0, 3: 0, 4: 0}
    for el in duplicates:
        duplicates_summary[len(el)] += 1
    duplicates_no_triples_quadruples = []
    for el in duplicates:
        if len(el) == 2:
            duplicates_no_triples_quadruples.append(el)
        else:
            duplicates_no_triples_quadruples.extend([set(x) for x in combinations(el, r=2)])

    # data cleaning
    data_cleaned = clean_data(data=dict_data_transformed, matches=config["datacleaning"])

    # extract tv brands
    data_with_tv_brands, title_no_brands, brands_in_data, misidentified = extract_tv_brands(
        data=data_cleaned, tv_brands=config["brands"]["brand_names"]
    )

    # extract model words
    data_with_model_words = extract_model_words(data_with_tv_brands)
    return data_with_model_words, duplicates_no_triples_quadruples