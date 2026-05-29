#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 15:14:10 2026

@author: kasteivanauskaite
"""
import pytest

from knitting_pattern.math_engine import (
    calculate_stitches, calculate_rows, get_standard_body_measurements,
    get_style_ease, calculate_garment_dimensions, get_shaping_guidelines,
    calculate_top_down_shoulder_shaping, calculate_back_neck_shaping,
    generate_panel_grid, apply_top_down_mountains_to_grid,
    apply_back_short_rows_to_grid, calculate_sleeve_dimensions,
    generate_sleeve_grid
)

# ==========================================
# 1. GAUGE CALCULATORS TESTS
# ==========================================

def test_calculate_stitches():
    # 20 sts per 10cm = 2.0 sts/cm. 50cm width -> 100 sts.
    assert calculate_stitches(50, 20) == 100
    # Test decimal ceiling behavior: 10.5cm * 2.0 sts/cm = 21 sts.
    assert calculate_stitches(10.5, 20) == 21
    # Test rounding up: 10cm * 1.8 sts/cm = 18 sts.
    assert calculate_stitches(10.0, 18) == 18

def test_calculate_rows():
    # 24 rows per 10cm = 2.4 rows/cm. 20cm length -> 48 rows.
    assert calculate_rows(20, 24) == 48
    # Test ceiling behavior: 10.1cm * 2.5 rows/cm = 25.25 -> 26 rows.
    assert calculate_rows(10.1, 25) == 26

# ==========================================
# 2. SIZING & EASE TESTS
# ==========================================

def test_get_standard_body_measurements():
    # Test exact match
    size_m = get_standard_body_measurements("M")
    assert size_m["chest_circ_cm"] == 96.0
    assert size_m["bicep_circ_cm"] == 30.0
    
    # Test case insensitivity
    size_s = get_standard_body_measurements("s")
    assert size_s["chest_circ_cm"] == 86.0
    
    # Test fallback for invalid string (should default to M)
    size_invalid = get_standard_body_measurements("INVALID_SIZE")
    assert size_invalid["chest_circ_cm"] == 96.0

def test_get_style_ease():
    # Test known style
    raglan = get_style_ease("raglan")
    assert raglan["ease_cm"] == 7.5
    
    # Test case insensitivity
    ribbed = get_style_ease("NEGATIVE_EASE_RIBBED")
    assert ribbed["ease_cm"] == -5.0
    
    # Test fallback
    unknown = get_style_ease("not_a_style")
    assert unknown["ease_cm"] == 15.0  # Defaults to drop_shoulder

def test_calculate_garment_dimensions():
    # Standard sizing: Size M (96cm) + Drop Shoulder (15cm) = 111cm total / 2 = 55.5cm panel
    dims = calculate_garment_dimensions("M", "drop_shoulder")
    assert dims["body_chest_circ"] == 96.0
    assert dims["ease_added"] == 15.0
    assert dims["total_garment_circ"] == 111.0
    assert dims["panel_width_cm"] == 55.5
    
    # Custom ease override: Size S (86cm) + 10cm custom ease = 96cm total / 2 = 48cm panel
    custom_dims = calculate_garment_dimensions("S", "drop_shoulder", custom_ease=10.0)
    assert custom_dims["ease_added"] == 10.0
    assert custom_dims["panel_width_cm"] == 48.0

# ==========================================
# 3. TOP-DOWN SHORT ROW & SHAPING TESTS
# ==========================================

def test_get_shaping_guidelines():
    guidelines = get_shaping_guidelines("L")
    assert guidelines["shoulder_drop_cm"] == 5.5
    assert guidelines["back_neck_raise_cm"] == 4.0
    
    fallback = get_shaping_guidelines("UNKNOWN")
    assert fallback["shoulder_drop_cm"] == 4.5  # Defaults to M

def test_calculate_top_down_shoulder_shaping():
    # Size M (drop 4.5cm). Gauge: 20 rows/10cm (2 rows/cm).
    # Mountain rows = 4.5 * 2 = 9. Steps = 9 // 2 = 4.
    # Total sts = 100. Quarter = 25. Middle = 50.
    shaping = calculate_top_down_shoulder_shaping(100, "M", 20)
    assert shaping["mountain_rows"] == 9
    assert shaping["total_short_row_steps"] == 4
    assert shaping["first_turn_stitch"] == 25
    assert shaping["middle_stitch"] == 50
    assert shaping["sts_per_step"] == 25 // 4 # 6

def test_calculate_back_neck_shaping():
    # Size M (raise 3.5cm). Gauge: 20 rows/10cm (2 rows/cm).
    # Mountain rows = 3.5 * 2 = 7. Steps = 7 // 2 = 3.
    shaping = calculate_back_neck_shaping(120, "M", 20)
    assert shaping["mountain_rows"] == 7
    assert shaping["total_short_row_steps"] == 3
    assert shaping["middle_stitch"] == 60
    assert shaping["neck_half_width"] == 20

# ==========================================
# 4. GRID GENERATION & MODIFICATION TESTS
# ==========================================

def test_generate_panel_grid():
    grid = generate_panel_grid(10, 5)
    assert len(grid) == 5  # 5 rows
    assert len(grid[0]) == 10  # 10 columns
    assert grid[0][0] == 0
    assert grid[4][9] == 0

def test_apply_top_down_mountains_to_grid():
    grid = generate_panel_grid(20, 10)
    shaping_data = {
        "total_short_row_steps": 2,
        "first_turn_stitch": 5,
        "sts_per_step": 2
    }
    carved_grid = apply_top_down_mountains_to_grid(grid, shaping_data)
    
    # Verify the grid retains dimensions
    assert len(carved_grid) == 10
    assert len(carved_grid[0]) == 20
    
    # Row 0 is the Cast-On (should remain untouched 0s)
    assert all(st == 0 for st in carved_grid[0])
    
    # Verify that shaping created empty space (-1) at the neck edges
    # On row 1 (right shoulder step 1), stitches from midpoint (10) to right inner edge should be carved.
    # right_inner_edge = 20 - (5 + 0) = 15. So cols 10 to 14 are -1.
    assert carved_grid[1][12] == -1 

def test_apply_back_short_rows_to_grid():
    grid = generate_panel_grid(20, 10)
    shaping_data = {
        "total_short_row_steps": 2,
        "middle_stitch": 10,
        "neck_half_width": 2,
        "sts_per_step": 2
    }
    carved_grid = apply_back_short_rows_to_grid(grid, shaping_data)
    
    # Outer edges on row 0 should be -1, inner neck should be 0
    assert carved_grid[0][0] == -1  # Edge carved out
    assert carved_grid[0][10] == 0  # Neck remains intact

# ==========================================
# 5. SLEEVE CALCULATION & GRID TESTS
# ==========================================

def test_calculate_sleeve_dimensions():
    # Test Size M with 20 sts and 30 rows per 10cm. 
    # Bicep = 30+5 = 35cm -> 70 sts
    # Wrist = 17+2 = 19cm -> 38 sts
    # Length = 45cm -> 135 rows
    # Straight length = 15cm -> 45 rows
    sleeve = calculate_sleeve_dimensions("M", 20, 30, straight_length_cm=15.0)
    
    assert sleeve["bicep_sts"] >= sleeve["wrist_sts"]
    assert sleeve["total_rows"] == 135
    assert sleeve["straight_rows"] == 45
    assert sleeve["total_dec_rounds"] > 0
    assert sleeve["dec_rate"] > 0

def test_generate_sleeve_grid():
    # Use a small mock sleeve for easy matrix validation
    sleeve_data = {
        "bicep_sts": 10,
        "wrist_sts": 6,
        "total_rows": 10,
        "straight_rows": 2,
        "dec_rate": 2,
        "total_dec_rounds": 2
    }
    grid = generate_sleeve_grid(sleeve_data)
    
    # 1. Total dimensions should match bicep x rows
    assert len(grid) == 10
    assert len(grid[0]) == 10
    
    # 2. Zone 1 (Straight): Top row should be fully knittable
    assert all(st == 0 for st in grid[0])
    assert all(st == 0 for st in grid[2])
    
    # 3. Zone 3 (Tapered Bottom): Bottom row should have -1 on the outer edges
    # Bicep is 10, wrist is 6. Difference is 4. So 2 empty stitches on each side.
    assert grid[9][0] == -1
    assert grid[9][1] == -1
    assert grid[9][2] == 0  # Start of wrist
    assert grid[9][8] == -1
    assert grid[9][9] == -1