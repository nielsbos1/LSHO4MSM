"""
LSH Utilities Module

This module provides utility functions for Locality Sensitive Hashing (LSH) operations,
including sketch generation, candidate pair filtering, and performance metric calculations.

The module implements both MinHash and Fill Sketch Scheme (FSS) functionality, with
support for both standard and amplified LSH schemes.

Functions:
    add_sketches: Generate MinHash and FSS sketches for product data
    get_pair_quality: Calculate pair quality metrics for candidate pairs
    apply_lsh_generate_candidate_pairs: Generate candidate pairs using LSH
    filter_candidate_pairs_brands_and_shops: Filter candidate pairs based on brand and shop
    get_duplicates_found: Find actual duplicates among candidate pairs
    get_duplicates_found_pairwise: Find pairwise duplicates in candidate pairs
    get_total_possible_comparisions: Calculate total possible comparisons
    extract_all_model_words: Extract unique model words from data
    add_error_info_to_param_list: Add error metrics to parameter configurations

"""
from src.datasketch_custom_implementation import datasketch
import copy
from optimize_parameters import compute_weighted_average_error
import pandas as pd


def add_sketches(data, seed_gen, num_perm=256, mixed_tab=False):
    """
    Generate MinHash and Fill Sketch Scheme (FSS) sketches for product data.

    Args:
        data (dict): Dictionary of products with model words
        seed_gen: Seed generator object for reproducible results
        num_perm (int, optional): Number of permutations. Defaults to 256.
        mixed_tab (bool, optional): Whether to use mixed tabulation. Defaults to False.

    Returns:
        dict: Products with added MinHash and FSS sketches
    """
    return_dict = dict()
    # generate MinHash
    count = 0
    # generate mixedtab_objects
    # mixedtab_objects = datasketch.FillSketch.create_mixedtab_objects(sketch_length=num_perm, seed_gen=seed_gen)
    seed_minhash = seed_gen.get_single_seed()
    seed_mixed_tab_1 = seed_gen.get_single_seed()
    seed_mixed_tab_2 = seed_gen.get_single_seed()
    seeds_mixedtab = [seed_mixed_tab_1, seed_mixed_tab_2]
    for uuid, product in data.items():
        # minhash
        minhash = datasketch.MinHash(num_perm=num_perm, seed=seed_minhash)
        for model_word in product["model_words"]:
            minhash.update(model_word.encode("utf-8"))
        product["minhash"] = minhash

        # fill sketch
        # mixedtab_objects = mixedtab_objects if mixed_tab else None

        fill_sketch = datasketch.FillSketch(
            input=product["model_words"], seeds=seeds_mixedtab, sketch_length=num_perm, mixed_tab=True
        )
        product["fss"] = fill_sketch
        return_dict[uuid] = product
        count += 1

    # generate in bulk
    # data_only_model_words = [[y.encode('utf-8') for y in product['model_words']] for uuid, product in data.items()]
    # minhashes = datasketch.MinHash.bulk(data_only_model_words, num_perm=num_perm, seed=1)

    return return_dict

def get_pair_quality(candidate_pairs, data):
    """
    Calculate the pair quality metric for candidate pairs.
    
    Pair quality is defined as the percentage of candidate pairs that are actual duplicates.

    Args:
        candidate_pairs (set): Set of candidate duplicate pairs
        data (dict): Dictionary of product data

    Returns:
        float: Pair quality percentage (0-100)
    """
    duplicates = []

    for cp in candidate_pairs:
        list_cp = list(cp)
        product_1 = data[list_cp[0]]
        product_2 = data[list_cp[1]]
        if product_1["modelID"] == product_2["modelID"]:
            duplicates.append(cp)
    try:
        pair_quality = len(duplicates) / len(candidate_pairs) * 100
    except ZeroDivisionError:
        pair_quality = 0
    return pair_quality


def apply_lsh_generate_candidate_pairs(
    data_with_sketches,
    threshold,
    params=None,
    num_perm=None,
    amplified=None,
    sketch_type=None,
    parameter_config_list=None,
    minimum_r1=1,
):
    """
    Generate candidate pairs using LSH with specified parameters.

    Args:
        data_with_sketches (dict): Product data with LSH sketches
        threshold (float): LSH threshold value
        params (tuple, optional): LSH parameters (b, r)
        num_perm (int, optional): Number of permutations
        amplified (bool, optional): Whether to use amplification
        sketch_type (str, optional): Type of sketch to use ('minhash' or 'fss')
        parameter_config_list (list, optional): List of parameter configurations
        minimum_r1 (int, optional): Minimum r1 value. Defaults to 1.

    Returns:
        set: Set of candidate pairs
    """
    lsh = datasketch.MinHashLSHAmplified(
        threshold=threshold,
        num_perm=num_perm,
        amplified=amplified,
        parameter_config_list=parameter_config_list,
        params=params,
        minimum_r1=minimum_r1,
    )
    for uuid, product in data_with_sketches.items():
        lsh.insert(key=uuid, minhash=product[sketch_type])
    return lsh.get_candidate_pairs()


def filter_candidate_pairs_brands_and_shops(candidate_pairs, data_with_sketches):
    """
    Filter candidate pairs based on brand and shop criteria.
    
    Keeps only pairs that have the same brand but are from different shops.

    Args:
        candidate_pairs (set): Set of candidate pairs
        data_with_sketches (dict): Product data with sketches

    Returns:
        set: Filtered set of candidate pairs
    """
    # for each candidate pair, check whether they have the same brand and are from different shops
    output_set = set()
    for cp in candidate_pairs:
        list_cp = list(cp)
        product_1 = data_with_sketches[list_cp[0]]
        product_2 = data_with_sketches[list_cp[1]]
        if product_1["brand"] == product_2["brand"] and product_1["shop"] != product_2["shop"]:
            output_set.add(cp)
        else:
            pass
    return output_set


def get_duplicates_found(candidate_pairs, duplicates):
    """
    Find actual duplicates among candidate pairs, supporting multi-item duplicate sets.

    This function checks candidate pairs against known duplicate sets and identifies
    which candidate pairs are actual duplicates. It supports cases where duplicate
    sets can contain more than two items.

    Args:
        candidate_pairs (set): Set of candidate duplicate pairs
        duplicates (list): List of sets containing known duplicate groups

    Returns:
        set: Set of confirmed duplicate pairs found among candidate pairs
    """
    duplicates_found = set()
    for cp in candidate_pairs:
        duplicate = next((cp for x in duplicates if cp.issubset(x)), "not found")
        if duplicate != "not found":
            duplicates_found.add(duplicate)
    return duplicates_found


def get_duplicates_found_pairwise(candidate_pairs, duplicates_no_triples_quadruples):
    """
    Find actual duplicates among candidate pairs, for pairwise duplicates only.
    
    This function is optimized for cases where all duplicates are pairs
    (no groups of three or more duplicates). It's more efficient than get_duplicates_found
    for pairwise comparison.

    Args:
        candidate_pairs (set): Set of candidate duplicate pairs
        duplicates_no_triples_quadruples (list): List of known duplicate pairs

    Returns:
        set: Set of confirmed duplicate pairs found among candidate pairs
    """
    duplicates_found = set()
    for cp in candidate_pairs:
        if cp in duplicates_no_triples_quadruples:
            duplicates_found.add(cp)
    return duplicates_found


def get_total_possible_comparisions(data):
    """
    Calculate total possible comparisons between products.
    
    Only counts pairs from different shops with the same brand.

    Args:
        data (dict): Product data dictionary

    Returns:
        int: Total number of possible comparisons
    """
    count = 0
    for index, product in data.items():
        for index_2, product_2 in data.items():
            if index != index_2 and product["shop"] != product_2["shop"] and product["brand"] == product_2["brand"]:
                count += 1
    return count


def extract_all_model_words(data):
    """
    Extract all unique model words from product data.

    Args:
        data (dict): Product data dictionary

    Returns:
        set: Set of unique model words
    """
    model_words = set()
    for key, product in data.items():
        model_words.update(product["model_words"])
    return model_words


def add_error_info_to_param_list(param_config_list):
    """
    Add error information to parameter configurations.
    
    Calculates false positive rate, false negative rate, and weighted average error
    for each parameter configuration.

    Args:
        param_config_list (list): List of parameter configurations

    Returns:
        pandas.DataFrame: Parameter configurations with added error metrics
    """
    list_storage = []
    for element in param_config_list:
        copy_el = copy.deepcopy(element)
        copy_el["r1"] = element["params"][1][0]
        copy_el["b1"] = element["params"][0][0]
        copy_el["r2"] = element["params"][1][1]
        copy_el["b2"] = element["params"][0][1]
        error, fp, fn = compute_weighted_average_error(
            threshold=element["threshold"], b_1=copy_el["b1"], b_2=copy_el["b2"], r_1=copy_el["r1"], r_2=copy_el["r2"]
        )

        copy_el["fn"] = fn
        copy_el["fp"] = fp
        copy_el["weighted_average_error"] = 0.5 * fn + 0.5 * fp
        list_storage.append(copy_el)

    df_params = pd.DataFrame(list_storage)
    df_params["error_shift"] = df_params.groupby(["threshold", "num_perm"])["weighted_average_error"].shift()
    df_params["percentage_change"] = df_params.apply(
        lambda x: (x["error_shift"] - x["weighted_average_error"]) / x["weighted_average_error"] * 100, axis=1
    )
    return df_params
