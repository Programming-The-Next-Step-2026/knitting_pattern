#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May  9 00:18:15 2026

@author: kasteivanauskaite
"""
import math

# ==========================================
# 1. GAUGE CALCULATORS
# ==========================================

def calculate_stitches(width_cm, gauge_sts_per_10cm):
    """
    Calculates the total number of stitches required for a specific width.

    Args:
        width_cm (float): The desired width of the fabric in centimeters.
        gauge_sts_per_10cm (float): The knitter's stitch gauge over 10 cm.

    Returns:
        int: Total stitches needed, rounded up to the nearest whole integer.
    """
    sts_per_cm = gauge_sts_per_10cm / 10.0
    return math.ceil(width_cm * sts_per_cm)

def calculate_rows(length_cm, gauge_rows_per_10cm):
    """
    Calculates the total number of rows required for a specific length.

    Args:
        length_cm (float): The desired length of the fabric in centimeters.
        gauge_rows_per_10cm (float): The knitter's row gauge over 10 cm.

    Returns:
        int: Total rows needed, rounded up to the nearest whole integer.
    """
    rows_per_cm = gauge_rows_per_10cm / 10.0
    return math.ceil(length_cm * rows_per_cm)

# ==========================================
# 2. SIZING & EASE ENGINE
# ==========================================

def get_standard_body_measurements(size_string):
    """
    Retrieves standard human body circumferences based on sizing.

    Args:
        size_string (str): The desired size (e.g., 'S', 'M', 'XL').

    Returns:
        dict: A dictionary containing 'chest_circ_cm', 'cross_back_cm', 
              and 'arm_length_cm' as floats.
    """
    body_sizes = {
        "XS": {"chest_circ_cm": 76.0, "cross_back_cm": 36.0, "arm_length_cm": 43.0},
        "S": {"chest_circ_cm": 86.0, "cross_back_cm": 38.0, "arm_length_cm": 44.0},
        "M": {"chest_circ_cm": 96.0, "cross_back_cm": 40.0, "arm_length_cm": 45.0},
        "L": {"chest_circ_cm": 106.0, "cross_back_cm": 42.0, "arm_length_cm": 46.0},
        "XL": {"chest_circ_cm": 117.0, "cross_back_cm": 44.0, "arm_length_cm": 47.0},
        "2XL": {"chest_circ_cm": 127.0, "cross_back_cm": 46.0, "arm_length_cm": 48.0}
    }
    return body_sizes.get(size_string.upper(), body_sizes["M"])

def get_style_ease(garment_type):
    """
    Retrieves the standard ease allowance for a specific garment construction.

    Args:
        garment_type (str): Type of garment (e.g., 'drop_shoulder', 'raglan').

    Returns:
        dict: Contains 'ease_cm' (float) to be added to the body circumference, 
              and a 'description' (str) of the fit.
    """
    ease_dict = {
        "drop_shoulder": {"ease_cm": 15.0, "description": "Loose, oversized fit"},
        "raglan": {"ease_cm": 7.5, "description": "Classic, comfortable fit"},
        "fitted_set_in": {"ease_cm": 2.5, "description": "Tailored, close to body"},
        "negative_ease_ribbed": {"ease_cm": -5.0, "description": "Stretches to fit tightly"}
    }
    return ease_dict.get(garment_type.lower(), ease_dict["drop_shoulder"])

def calculate_garment_dimensions(size_string, garment_type, custom_ease=None):
    """
    Calculates final flat panel measurements by combining body size and ease.

    Args:
        size_string (str): The desired body size (e.g., 'M').
        garment_type (str): The style of the garment.
        custom_ease (float, optional): User-defined ease override in cm. Defaults to None.

    Returns:
        dict: Final calculated measurements for knitting the panel.
    """
    body = get_standard_body_measurements(size_string)
    style = get_style_ease(garment_type)

    ease_to_add = custom_ease if custom_ease is not None else style["ease_cm"]
    total_garment_circ = body["chest_circ_cm"] + ease_to_add
    panel_width_cm = total_garment_circ / 2

    return {
        "body_chest_circ": body["chest_circ_cm"],
        "ease_added": ease_to_add,
        "total_garment_circ": total_garment_circ,
        "panel_width_cm": panel_width_cm,
        "arm_length_cm": body["arm_length_cm"],
        "style_description": style["description"]
    }

# ==========================================
# 3. TOP-DOWN SHORT ROW & SHAPING ENGINE
# ==========================================

def get_shaping_guidelines(size_string):
    """
    Returns the graded centimeter drops for shoulder shaping.
    Updated with deeper slopes for a highly tailored, less 'boxy' fit.

    Args:
        size_string (str): The desired body size.

    Returns:
        dict: Contains 'shoulder_drop_cm' and 'back_neck_raise_cm'.
    """
    guidelines = {
        "XS": {"shoulder_drop_cm": 3.5, "back_neck_raise_cm": 2.5},
        "S": {"shoulder_drop_cm": 4.0, "back_neck_raise_cm": 3.0},
        "M": {"shoulder_drop_cm": 4.5, "back_neck_raise_cm": 3.5},
        "L": {"shoulder_drop_cm": 5.5, "back_neck_raise_cm": 4.0},
        "XL": {"shoulder_drop_cm": 6.5, "back_neck_raise_cm": 4.5},
        "2XL": {"shoulder_drop_cm": 7.5, "back_neck_raise_cm": 5.0}
    }
    return guidelines.get(size_string.upper(), guidelines["M"])

def calculate_top_down_shoulder_shaping(total_chest_sts, size_string, gauge_rows_per_10cm, panel_type="Front Panel"):
    """
    Calculates the short row intervals for top-down 'two mountain' shoulder shaping.

    Args:
        total_chest_sts (int): The total cast-on width for the panel.
        size_string (str): The body size, used to pull dynamic drop guidelines.
        gauge_rows_per_10cm (float): The knitter's row gauge.
        panel_type (str): "Front Panel" or "Back Panel".
    """
    shaping_rules = get_shaping_guidelines(size_string)
    
    if panel_type == "Front Panel":
        slope_drop_cm = shaping_rules["shoulder_drop_cm"]
    else:
        slope_drop_cm = shaping_rules["back_neck_raise_cm"]

    quarter_mark = total_chest_sts // 4
    middle_mark = total_chest_sts // 2
    
    rows_per_cm = gauge_rows_per_10cm / 10.0
    mountain_rows = math.ceil(slope_drop_cm * rows_per_cm)
    steps = max(1, mountain_rows // 2)
    
    distance_to_cover = middle_mark - quarter_mark
    sts_per_step = distance_to_cover // steps
    
    return {
        "mountain_rows": mountain_rows,
        "total_short_row_steps": steps,
        "first_turn_stitch": quarter_mark,
        "middle_stitch": middle_mark,
        "sts_per_step": sts_per_step
    }
def calculate_back_neck_shaping(total_chest_sts, size_string, gauge_rows_per_10cm):
    shaping_rules = get_shaping_guidelines(size_string)
    raise_cm = shaping_rules["back_neck_raise_cm"]
    
    rows_per_cm = gauge_rows_per_10cm / 10.0
    mountain_rows = math.ceil(raise_cm * rows_per_cm)
    steps = max(1, mountain_rows // 2)
    
    middle_mark = total_chest_sts // 2
    neck_half_width = total_chest_sts // 6 
    
    shoulder_sts = (total_chest_sts // 2) - neck_half_width
    sts_per_step = max(1, shoulder_sts // steps)
    
    return {
        "mountain_rows": mountain_rows,
        "total_short_row_steps": steps,
        "middle_stitch": middle_mark,
        "neck_half_width": neck_half_width,
        "sts_per_step": sts_per_step,
        "first_turn_stitch": middle_mark + neck_half_width
    }

def apply_back_short_rows_to_grid(grid, shaping_data):
    steps = shaping_data["total_short_row_steps"]
    middle = shaping_data["middle_stitch"]
    neck_half_width = shaping_data["neck_half_width"]
    sts_per_step = shaping_data["sts_per_step"]
    total_sts = len(grid[0])
    
    for step in range(steps):
        live_left_edge = middle - neck_half_width - (step * sts_per_step)
        live_right_edge = middle + neck_half_width + (step * sts_per_step)
        
        r1 = step * 2
        r2 = step * 2 + 1
        
        if r1 < len(grid):
            for col in range(0, live_left_edge): grid[r1][col] = -1
            for col in range(live_right_edge, total_sts): grid[r1][col] = -1
            
        if r2 < len(grid):
            for col in range(0, live_left_edge): grid[r2][col] = -1
            for col in range(live_right_edge, total_sts): grid[r2][col] = -1

    return grid
# ==========================================
# 4. GRID GENERATION (THE CANVAS)
# ==========================================

def generate_panel_grid(width_sts, length_rows):
    """
    Creates a 2D matrix representing a blank, flat garment panel.

    Args:
        width_sts (int): Total stitches (X-axis).
        length_rows (int): Total rows (Y-axis).

    Returns:
        list of lists: A 2D array filled with 0s.
    """
    return [[0 for _ in range(width_sts)] for _ in range(length_rows)]

def apply_top_down_mountains_to_grid(grid, shaping_data):
    """
    Modifies the digital grid with ASYMMETRICAL top-down short row shaping.
    The left shoulder shaping is delayed by 1 row compared to the right.
    """
    steps = shaping_data["total_short_row_steps"]
    quarter = shaping_data["first_turn_stitch"]
    sts_per_step = shaping_data["sts_per_step"]
    
    total_sts = len(grid[0])
    midpoint = total_sts // 2
    
    # Row 0 is the full Cast-On sweep. Shaping starts on Row 1.

    for step in range(steps):
        # RIGHT SHOULDER (Starts immediately on Row 1)
        rs_row_1 = 1 + (step * 2)
        rs_row_2 = 2 + (step * 2)
        
        # LEFT SHOULDER (Delayed by 1 row, starts Row 2)
        ls_row_1 = 2 + (step * 2)
        ls_row_2 = 3 + (step * 2)
        
        left_inner_edge = quarter + (step * sts_per_step)
        right_inner_edge = total_sts - left_inner_edge
        
        # Carve RIGHT side of the neck (columns from midpoint to the right)
        if rs_row_1 < len(grid):
            for col in range(midpoint, right_inner_edge):
                grid[rs_row_1][col] = -1
        if rs_row_2 < len(grid):
            for col in range(midpoint, right_inner_edge):
                grid[rs_row_2][col] = -1

        # Carve LEFT side of the neck (columns from the left to midpoint)
        if ls_row_1 < len(grid):
            for col in range(left_inner_edge, midpoint):
                grid[ls_row_1][col] = -1
        if ls_row_2 < len(grid):
            for col in range(left_inner_edge, midpoint):
                grid[ls_row_2][col] = -1

    return grid

# ==========================================
# TESTING BLOCK
# ==========================================
if __name__ == "__main__":
    def print_grid_visually(grid, title="Grid"):
        print(f"\n--- {title} ---")
        for row in grid: 
            row_string = "".join(["██" if stitch == 0 else "  " for stitch in row])
            print(row_string)

    print("Testing Math Engine with updated Top-Down logic...\n")
    
    # 40 stitches wide, 14 rows tall (just to see the top section)
    test_grid = [[0 for _ in range(40)] for _ in range(14)]
    
    # Mock parameters for testing the new deeper slopes
    test_shaping = {
        "total_short_row_steps": 6,          # Deeper slope requires more steps
        "first_turn_stitch": 10,             # 1/4 of 40
        "sts_to_knit_past_double_stitch": 1  # Slower progression towards center
    }
    
    carved_grid = apply_top_down_mountains_to_grid(test_grid, test_shaping)
    print_grid_visually(carved_grid, "Top-Down Mountains (Row 0 is Cast-On)")
    
    