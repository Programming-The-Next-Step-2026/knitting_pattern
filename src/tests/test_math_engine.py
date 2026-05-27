#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 15:14:10 2026

@author: kasteivanauskaite
"""
from knitting_pattern.math_engine import (
    calculate_stitches, 
    calculate_rows, 
    get_standard_body_measurements
)

# ==========================================
# 1. GAUGE CALCULATOR TESTS
# ==========================================
def test_calculate_stitches():
    # If a fabric is 10cm wide, and gauge is 20 sts per 10cm, we expect 20 stitches.
    assert calculate_stitches(10.0, 20.0) == 20
    
    # If fabric is 15cm wide, and gauge is 22 sts per 10cm (2.2 sts/cm)
    # 15 * 2.2 = 33 stitches
    assert calculate_stitches(15.0, 22.0) == 33
    
    # Testing rounding: 10.5cm * 2.2 = 23.1. Should round up to 24.
    assert calculate_stitches(10.5, 22.0) == 24

def test_calculate_rows():
    # 10cm length at 30 rows/10cm should equal 30 rows
    assert calculate_rows(10.0, 30.0) == 30

# ==========================================
# 2. SIZING DATA TESTS
# ==========================================
def test_get_standard_body_measurements():
    # Test that size Medium returns the correct dictionary
    m_size = get_standard_body_measurements("M")
    assert m_size["chest_circ_cm"] == 96.0
    
    # Test that lowercase inputs are handled properly
    s_size = get_standard_body_measurements("s")
    assert s_size["chest_circ_cm"] == 86.0
    
    # Test fallback: an invalid size should default to Medium (96.0)
    invalid_size = get_standard_body_measurements("NONEXISTENT")
    assert invalid_size["chest_circ_cm"] == 96.0