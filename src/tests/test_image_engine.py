#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 15:30:57 2026

@author: kasteivanauskaite
"""
from knitting_pattern.math_engine import (
    generate_panel_grid,
    apply_back_short_rows_to_grid
)

# ==========================================
# 1. GRID GENERATION TESTS
# ==========================================
def test_generate_panel_grid():
    # Create a small 10 stitch wide by 5 row tall test grid
    grid = generate_panel_grid(width_sts=10, length_rows=5)
    
    # Check that it generated exactly 5 rows (Y-axis)
    assert len(grid) == 5
    # Check that the first row is exactly 10 stitches wide (X-axis)
    assert len(grid[0]) == 10
    # Check that it is initialized with zeroes
    assert grid[0][0] == 0


# ==========================================
# 2. SHAPING MATRIX MANIPULATION TESTS
# ==========================================
def test_apply_back_short_rows_to_grid():
    # Create a clean 20x10 test grid
    grid = generate_panel_grid(width_sts=20, length_rows=10)
    
    # We will pass in 'mock' shaping data so we know exactly what to expect
    mock_shaping = {
        "total_short_row_steps": 2,
        "middle_stitch": 10,
        "neck_half_width": 2,
        "sts_per_step": 2
    }
    
    carved_grid = apply_back_short_rows_to_grid(grid, mock_shaping)
    
    # THE TEST: The outer corners should now be 'dead' canvas space (-1)
    assert carved_grid[0][0] == -1
    assert carved_grid[0][-1] == -1
    
    # THE TEST: The active center neck stitches should remain untouched (0)
    assert carved_grid[0][10] == 0