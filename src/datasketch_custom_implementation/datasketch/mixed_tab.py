"""
Mixed tabulation hashing implementation to provide faster hashing compared to
traditional methods. This extends the hashing options available in datasketch.

Mixed tabulation provides fast hashing while maintaining good theoretical
properties for LSH applications.
"""

import os

os.add_dll_directory("C:\\msys64\\mingw64\\bin")
from . import pyMixedTabulation


class MixedTabulation(object):
    """
    Mixed tabulation hashing implementation.
    
    Args:
        seed (int, optional): Seed for random number generation. Defaults to 1.
        
    Attributes:
        mixed_tab_object: The underlying mixed tabulation implementation
    """
    def __init__(self, seed=1):
        self.mixed_tab_object = pyMixedTabulation.PyMixTab(seed)

    def _create_64_bit_from_x_and_i(self, x, i):
        """
        Create 64-bit integer by combining two 32-bit values.
        
        Args:
            x (int): First 32-bit value
            i (int): Second 32-bit value
            
        Returns:
            int: Combined 64-bit value
        """
        bin_x = bin(x)
        bin_i = bin(i)

        bin_x_part = bin_x.split("b")[1]
        zeros_to_add_x = 32 - len(bin_x_part)
        zeros_x = zeros_to_add_x * "0"
        bin_x_32_bit = zeros_x + bin_x_part

        bin_i_part = bin_i.split("b")[1]
        zeros_to_add_i = 32 - len(bin_i_part)
        zeros_i = zeros_to_add_i * "0"
        bin_i_32_bit = zeros_i + bin_i_part
        total_64_bit = "0b" + bin_x_32_bit + bin_i_32_bit

        total = int(total_64_bit, 2)
        return total

    def get_hash(self, x, i):
        """
        Get hash value using mixed tabulation.
        
        Args:
            x (int): Value to hash (must be 32-bit)
            i (int): Index for hash function (must be 32-bit)
            
        Returns:
            int: Hash value
        """
        key_64_bit = self._create_64_bit_from_x_and_i(x, i)
        hash = self.mixed_tab_object.getHash(key_64_bit)
        return hash
