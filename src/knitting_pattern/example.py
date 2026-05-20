#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 20:20:34 2026

@author: kasteivanauskaite
"""

import numpy as np

def add(x, y):
    """
    Adds two numbers together.

    Args:
        x: The first number.
        y: The second number.

    Returns:
        The sum of x and y.

    Example:
        >>> add(2, 3)
        5
    """
    return x + y

def calculate_mean(data):
    """
    Calculates the average of a list of numbers using NumPy.

    Args:
        data: A list or array of numbers.

    Returns:
        The arithmetic mean as a float.

    Example:
        >>> calculate_mean([1, 2, 3, 4, 5])
        3.0
    """
    return float(np.mean(data))