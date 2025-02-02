"""
LSH Parameter Optimization Module

This module provides tools for optimizing LSH parameters based on
false positive and false negative probability calculations.
Features include:
- Optimal parameter computation for MinHashLSH
- Error probability calculations
- Parameter space exploration
- Performance metric optimization

Mathematical Framework:
- Uses integration-based probability calculations
- Implements both amplified and non-amplified schemes
- Supports multiple optimization criteria

"""
import numpy as np
from scipy.integrate import quad as integrate
import json
import time
from sympy.ntheory import factorint
import itertools
import math
import pandas as pd


def _false_positive_probability(threshold, b_1, b_2, r_1, r_2):
    """
    Calculate false positive probability for given LSH parameters.
    
    Computes the probability that a pair of items with similarity less than
    the threshold is incorrectly identified as a candidate pair.

    Args:
        threshold (float): LSH similarity threshold
        b_1 (int): First-level number of bands
        b_2 (int): Second-level number of bands
        r_1 (int): First-level rows per band
        r_2 (int): Second-level rows per band

    Returns:
        float: False positive probability
    """
    _probability = lambda s: 1 - (1 - (1 - (1 - s ** float(r_1)) ** float(b_1)) ** float(r_2)) ** float(b_2)
    a, err = integrate(_probability, 0.0, threshold)
    return a


def _false_negative_probability(threshold, b_1, b_2, r_1, r_2):
    """
    Calculate false negative probability for given LSH parameters.
    
    Computes the probability that a pair of items with similarity greater than
    the threshold is not identified as a candidate pair.

    Args:
        threshold (float): LSH similarity threshold
        b_1 (int): First-level number of bands
        b_2 (int): Second-level number of bands
        r_1 (int): First-level rows per band
        r_2 (int): Second-level rows per band

    Returns:
        float: False negative probability
    """
    _probability = lambda s: 1 - (1 - (1 - (1 - (1 - s ** float(r_1)) ** float(b_1)) ** float(r_2)) ** float(b_2))
    a, err = integrate(_probability, threshold, 1.0)
    return a


def compute_weighted_average_error(threshold, b_1, b_2, r_1, r_2, false_positive_weight=0.5, false_negative_weight=0.5):
    """
    Compute weighted average of false positive and false negative errors.

    Args:
        threshold (float): LSH similarity threshold
        b_1 (int): First-level number of bands
        b_2 (int): Second-level number of bands
        r_1 (int): First-level rows per band
        r_2 (int): Second-level rows per band
        false_positive_weight (float, optional): Weight for false positives. Defaults to 0.5.
        false_negative_weight (float, optional): Weight for false negatives. Defaults to 0.5.

    Returns:
        tuple: (weighted error, false positive rate, false negative rate)
    """
    fp = _false_positive_probability(threshold, b_1, b_2, r_1, r_2)
    fn = _false_negative_probability(threshold, b_1, b_2, r_1, r_2)
    error = fp * false_positive_weight + fn * false_negative_weight
    return error, fp, fn

def _get_divisors(number):
    """
    Get all divisors of a number using prime factorization.
    
    This function uses sympy's factorint to get prime factors and
    generates all possible divisors using combinations of these factors.

    Args:
        number (int): Number to find divisors for

    Returns:
        set: Set of all divisors
    """
    factors = factorint(number)
    list_factors = [key for key, value in factors.items() for i in range(1, value + 1)]
    return_set = {1, number}
    for i in range(len(list_factors)):
        combis = itertools.combinations(list_factors, i)
        for com in combis:
            return_set.add(math.prod(com))
    return return_set

def optimal_param(threshold, num_perm, false_positive_weight, false_negative_weight, amplified, minimum_r1=1):
    """
    Find optimal LSH parameters using an improved search algorithm.
    
    This function explores the parameter space efficiently by using divisor-based
    search and early stopping. It supports both amplified and non-amplified LSH schemes.

    Args:
        threshold (float): Target similarity threshold
        num_perm (int): Number of permutations
        false_positive_weight (float): Weight for false positives in error calculation
        false_negative_weight (float): Weight for false negatives in error calculation
        amplified (bool): Whether to use amplification
        minimum_r1 (int, optional): Minimum value for r1. Defaults to 1.

    Returns:
        tuple: ((b1, b2), (r1, r2)) optimal parameters and minimum error
    """
    start_time = time.time()
    min_error = float("inf")
    opt = ((), ())
    # all_outcomes = []
    count = 0
    for r_1 in range(minimum_r1, num_perm + 1):
        max_b_0 = int(num_perm / r_1)
        # min_error_b_0 = {}
        for b_0 in range(max_b_0, 0, -1):
            b_1_options = _get_divisors(b_0) if amplified else {b_0}
            for b_1 in b_1_options:
                n_2 = int(b_0 / b_1)
                b_2_options = _get_divisors(n_2) if amplified else {1}
                for b_2 in b_2_options:
                    count += 1
                    r_2 = int(n_2 / b_2)
                    fp = _false_positive_probability(threshold, b_1, b_2, r_1, r_2)
                    fn = _false_negative_probability(threshold, b_1, b_2, r_1, r_2)
                    error = fp * false_positive_weight + fn * false_negative_weight
                    if error < min_error:
                        min_error = error
                        b = (b_1, b_2)
                        r = (r_1, r_2)
                        opt = (b, r)
    print(f"optimal_parameters: {opt}")
    print(f"evaluation took {time.time() - start_time} seconds")
    print(f"threshold estimated: {threshold_comp(r[0],b[0])}")
    return opt, min_error


def threshold_comp(r, b):
    """
    Compute the theoretical threshold for given r and b values.
    
    This function calculates the threshold at which the s-curve has
    its steepest slope for the given parameters.

    Args:
        r (int): Rows per band
        b (int): Number of bands

    Returns:
        float: Computed threshold value
    """
    if  r * b - 1 != 0 :
        return ((r - 1) / (r * b - 1)) ** (1 / r)
    else:
        return 0


if __name__ == "__main__":
    thresholds = list(np.arange(start=0.05, stop=1, step=0.05))
    num_perms = [16, 32, 64, 128, 256, 512, 1024]
    amplified_list = [True, False]

    list_configurations = [
        {"threshold": threshold, "num_perm": num_perm, "amplified": amplified}
        for threshold in thresholds
        for num_perm in num_perms
        for amplified in amplified_list
    ]

    with open("./results/parameter_config.json", "r") as file_:
        existing_config = json.load(file_)

    # uncomment this line if you want to recalculate the optimal parameters
    # existing_config = []

    print(f"num configs: {len(list_configurations)}")

    for index, config in enumerate(list_configurations):
        # search in existing config
        params = next(
            (
                x["params"]
                for x in existing_config
                if (
                    abs(x["threshold"] - config["threshold"]) < 0.01
                    and x["num_perm"] == config["num_perm"]
                    and x["amplified"] is config["amplified"]
                )
            ),
            "not_found",
        )
        print(config)
        print(params)
        if params == "not_found":

            # optimize parmameters
            params, error = optimal_param(
                threshold=config["threshold"],
                num_perm=config["num_perm"],
                false_positive_weight=0.5,
                false_negative_weight=0.5,
                amplified=config["amplified"],
            )

        config["params"] = params
        config["threshold"] = round(config["threshold"], 2)
        list_configurations[index] = config
        print(config)

    with open("./results/parameter_config.json", "w") as file_:
        json.dump(list_configurations, file_)
