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
        
    Example:
        >>> calculate_stitches(50.0, 20.0)
        100
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
        
    Example:
        >>> calculate_rows(40.0, 25.0)
        100
    """
    rows_per_cm = gauge_rows_per_10cm / 10.0
    return math.ceil(length_cm * rows_per_cm)

# ==========================================
# 2. SIZING & EASE
# ==========================================

def get_standard_body_measurements(size_string):
    """
    Retrieves standard human body circumferences based on sizing.

    Args:
        size_string (str): The desired size (e.g., 'S', 'M', 'XL').

    Returns:
        dict: Measurements for chest, back, arm length, bicep, and wrist.
        
    Example:
        >>> measurements = get_standard_body_measurements("S")
        >>> measurements["chest_circ_cm"]
        86.0
    """
    body_sizes = {
        "XS": {"chest_circ_cm": 76.0, "cross_back_cm": 36.0, "arm_length_cm": 43.0, "bicep_circ_cm": 26.0, "wrist_circ_cm": 15.0},
        "S": {"chest_circ_cm": 86.0, "cross_back_cm": 38.0, "arm_length_cm": 44.0, "bicep_circ_cm": 28.0, "wrist_circ_cm": 16.0},
        "M": {"chest_circ_cm": 96.0, "cross_back_cm": 40.0, "arm_length_cm": 45.0, "bicep_circ_cm": 30.0, "wrist_circ_cm": 17.0},
        "L": {"chest_circ_cm": 106.0, "cross_back_cm": 42.0, "arm_length_cm": 46.0, "bicep_circ_cm": 34.0, "wrist_circ_cm": 18.0},
        "XL": {"chest_circ_cm": 117.0, "cross_back_cm": 44.0, "arm_length_cm": 47.0, "bicep_circ_cm": 38.0, "wrist_circ_cm": 19.0},
        "2XL": {"chest_circ_cm": 127.0, "cross_back_cm": 46.0, "arm_length_cm": 48.0, "bicep_circ_cm": 42.0, "wrist_circ_cm": 20.0}
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
              
    Example:
        >>> get_style_ease("fitted_set_in")
        {'ease_cm': 2.5, 'description': 'Tailored, close to body'}
    """
    ease_dict = {
        "drop_shoulder": {"ease_cm": 15.0, "description": "Loose, oversized fit"},
        "raglan": {"ease_cm": 7.5, "description": "Classic, comfortable fit"},
        "fitted_set_in": {"ease_cm": 2.5, "description": "Tailored, close to body"},
        "negative_ease_ribbed": {"ease_cm": -5.0, "description": "Stretches to hug the body"}
    }
    return ease_dict.get(garment_type.lower(), ease_dict["drop_shoulder"])

def calculate_garment_dimensions(size_string, garment_type, custom_ease=None):
    """
    Calculates final flat panel measurements by combining body size and ease.

    Args:
        size_string (str): The desired body size (e.g., 'M').
        garment_type (str): The style of the garment (e.g., "drop_shoulder").
        custom_ease (float, optional): User-defined ease override in cm. Defaults to None.

    Returns:
        dict: Final calculated measurements for knitting the panel.
        
    Example:
        >>> calculate_garment_dimensions("M", "drop_shoulder")
        {'body_chest_circ': 96.0, 'ease_added': 15.0, 'total_garment_circ': 111.0, 'panel_width_cm': 55.5, 'arm_length_cm': 45.0, 'style_description': 'Loose, oversized fit'}
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
# 3. TOP-DOWN SHORT ROW & SHAPING
# ==========================================

def get_shaping_guidelines(size_string):
    """
    Returns the graded centimeter drops for shoulder and back shaping.

    Args:
        size_string (str): The desired standard size (e.g., "M").

    Returns:
        dict: Contains 'shoulder_drop_cm' and 'back_neck_raise_cm'.
        
    Example:
        >>> get_shaping_guidelines("M")
        {'shoulder_drop_cm': 4.5, 'back_neck_raise_cm': 3.5}
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

def calculate_top_down_shoulder_shaping(total_chest_sts, size_string, gauge_rows_per_10cm):
    """
    Calculates the short row intervals for top-down 'two mountain' shoulder shaping.

    Args:
        total_chest_sts (int): The total cast-on width for the panel.
        size_string (str): The body size, used to pull dynamic drop guidelines.
        gauge_rows_per_10cm (float): The knitter's row gauge.
        
    Returns:
        dict: Calculations for shoulder short row shaping based on sizing.
        
    Example:
        >>> calculate_top_down_shoulder_shaping(100, "M", 20.0)
        {'mountain_rows': 9, 'total_short_row_steps': 4, 'first_turn_stitch': 25, 'middle_stitch': 50, 'sts_per_step': 6}
    """
    shaping_rules = get_shaping_guidelines(size_string)

    slope_drop_cm = shaping_rules["shoulder_drop_cm"]

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
    """
    Calculates the short row intervals for top-down back short-row shaping.

    Args:
        total_chest_sts (int): The total cast-on width for the panel.
        size_string (str): The body size, used to pull dynamic drop guidelines.
        gauge_rows_per_10cm (float): The knitter's row gauge.
        
    Returns:
        dict: Calculations for raising the back with short-row shaping.
        
    Example:
        >>> calculate_back_neck_shaping(100, "M", 20.0)
        {'mountain_rows': 7, 'total_short_row_steps': 3, 'middle_stitch': 50, 'neck_half_width': 16, 'sts_per_step': 11, 'first_turn_stitch': 66, 'purl_distance': 32}
    """
    shaping_rules = get_shaping_guidelines(size_string)
    raise_cm = shaping_rules["back_neck_raise_cm"]
    
    rows_per_cm = gauge_rows_per_10cm / 10.0
    mountain_rows = math.ceil(raise_cm * rows_per_cm)
    steps = max(1, mountain_rows // 2)
    
    middle_mark = total_chest_sts // 2
    neck_half_width = total_chest_sts // 6 
    
    shoulder_sts = (total_chest_sts // 2) - neck_half_width
    sts_per_step = max(1, shoulder_sts // steps)
    
    # Exact turn counts for the instructions 
    left_turn = middle_mark - neck_half_width
    right_turn = middle_mark + neck_half_width
    
    # Row 1 (RS): Start at the edge, knit across to the left turn
    first_rs_knit = total_chest_sts - left_turn
    # Row 2 (WS): Purl from the left turn back to the right turn
    ws_purl = right_turn - left_turn
    
    return {
        "mountain_rows": mountain_rows,
        "total_short_row_steps": steps,
        "middle_stitch": middle_mark,
        "neck_half_width": neck_half_width,
        "sts_per_step": sts_per_step,
        "first_turn_stitch": first_rs_knit, 
        "purl_distance": ws_purl            
    }

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
        list[list[int]]: A 2D array filled with 0s.
        
    Example:
        >>> generate_panel_grid(3, 2)
        [[0, 0, 0], [0, 0, 0]]
    """
    return [[0 for _ in range(width_sts)] for _ in range(length_rows)]

def apply_top_down_mountains_to_grid(grid, shaping_data):
    """
    Modifies the panel grid with asymmetrical top-down short-row shaping.
    The left shoulder shaping is delayed by 1 row compared to the right.
    
    Args: 
        grid (list[list[int]]): Empty grid based on sizing.
        shaping_data (dict): Shoulder drop calculations from the math engine.
        
    Returns: 
        list[list[int]]: Grid with -1s indicating unworked space.
        
    Example:
        >>> grid = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        >>> shaping = {"total_short_row_steps": 1, "first_turn_stitch": 1, "sts_per_step": 1}
        >>> apply_top_down_mountains_to_grid(grid, shaping)
        [[0, 0, 0, 0], [0, 0, -1, 0], [0, -1, -1, 0], [0, -1, 0, 0]]
    """
    steps = shaping_data["total_short_row_steps"]
    quarter = shaping_data["first_turn_stitch"]
    sts_per_step = shaping_data["sts_per_step"]
    
    total_sts = len(grid[0])
    midpoint = total_sts // 2
    
    # Row 0 is the full Cast-On. Shaping starts on Row 1.
    for step in range(steps):
        rs_row_1 = 1 + (step * 2)
        rs_row_2 = 2 + (step * 2)
        
        ls_row_1 = 2 + (step * 2)
        ls_row_2 = 3 + (step * 2)
        
        left_inner_edge = quarter + (step * sts_per_step)
        right_inner_edge = total_sts - left_inner_edge
        
        # Carve RIGHT side of the neck
        if rs_row_1 < len(grid):
            for col in range(midpoint, right_inner_edge): grid[rs_row_1][col] = -1
        if rs_row_2 < len(grid):
            for col in range(midpoint, right_inner_edge): grid[rs_row_2][col] = -1

        # Carve LEFT side of the neck
        if ls_row_1 < len(grid):
            for col in range(left_inner_edge, midpoint): grid[ls_row_1][col] = -1
        if ls_row_2 < len(grid):
            for col in range(left_inner_edge, midpoint): grid[ls_row_2][col] = -1

    return grid

def apply_back_short_rows_to_grid(grid, shaping_data):
    """ 
    Applies back neck short-row shaping to a garment panel grid. 
    
    Args: 
        grid (list[list[int]]): A 2D garment grid representing stitches and rows.
        shaping_data (dict): Dictionary containing calculated short-row shaping.
        
    Returns: 
        list[list[int]]: Updated grid containing back neck short-row shaping. 
        
    Example:
        >>> grid = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        >>> shaping = {"total_short_row_steps": 1, "middle_stitch": 2, "neck_half_width": 1, "sts_per_step": 1}
        >>> apply_back_short_rows_to_grid(grid, shaping)
        [[0, 0, 0, 0], [-1, 0, 0, -1], [-1, 0, 0, -1]]
    """
    steps = shaping_data["total_short_row_steps"]
    middle = shaping_data["middle_stitch"]
    neck_half_width = shaping_data["neck_half_width"]
    sts_per_step = shaping_data["sts_per_step"]
    total_sts = len(grid[0])
    
    for step in range(steps):
        left_turn = middle - neck_half_width - (step * sts_per_step)
        right_turn = middle + neck_half_width + (step * sts_per_step)
        
        prev_right_turn = total_sts - 1 if step == 0 else middle + neck_half_width + ((step - 1) * sts_per_step)
        
        rs_row = 1 + (step * 2)
        ws_row = 2 + (step * 2)
        
        # Row 1 (RS)
        if rs_row < len(grid):
            for col in range(0, left_turn): grid[rs_row][col] = -1
            for col in range(prev_right_turn + 1, total_sts): grid[rs_row][col] = -1
            
        # Row 2 (WS)
        if ws_row < len(grid):
            for col in range(0, left_turn): grid[ws_row][col] = -1
            for col in range(right_turn + 1, total_sts): grid[ws_row][col] = -1

    return grid

def calculate_sleeve_dimensions(size_string, gauge_sts_per_10cm, gauge_rows_per_10cm, 
                                custom_bicep=None, custom_wrist=None, custom_length=None,
                                straight_length_cm=15.0):
    """ 
    Calculates sleeve shaping dimensions for a tapered top-down sleeve.
    
    Args: 
        size_string (str): Standard body size used for baseline measurements. 
        gauge_sts_per_10cm (float): Stitch gauge measured over 10 cm. 
        gauge_rows_per_10cm (float): Row gauge measured over 10 cm. 
        custom_bicep (float, optional): Custom bicep circumference. Defaults to None. 
        custom_wrist (float, optional): Custom wrist circumference. Defaults to None. 
        custom_length (float, optional): Custom sleeve length. Defaults to None. 
        straight_length_cm (float, optional): Length of upper arm before taper. Defaults to 15.0 cm. 
        
    Returns: 
        dict: Calculated sleeve shaping data.
        
    Example:
        >>> calculate_sleeve_dimensions("M", 20.0, 20.0, custom_bicep=30.0, custom_wrist=20.0, custom_length=45.0, straight_length_cm=10.0)
        {'bicep_sts': 60, 'wrist_sts': 40, 'total_rows': 90, 'straight_rows': 20, 'dec_rate': 7, 'total_dec_rounds': 10}
    """
    body = get_standard_body_measurements(size_string)
    
    bicep_sts = calculate_stitches(custom_bicep or body["bicep_circ_cm"] + 5.0, gauge_sts_per_10cm)
    wrist_sts = calculate_stitches(custom_wrist or body["wrist_circ_cm"] + 2.0, gauge_sts_per_10cm)
    total_rows = calculate_rows(custom_length or body["arm_length_cm"], gauge_rows_per_10cm)
    
    straight_rows = calculate_rows(straight_length_cm, gauge_rows_per_10cm)
    taper_rows = total_rows - straight_rows
    
    total_sts_to_decrease = bicep_sts - wrist_sts
    decrease_rounds = total_sts_to_decrease // 2
    
    dec_rate = taper_rows // decrease_rounds if decrease_rounds > 0 else 0
    
    return {
        "bicep_sts": bicep_sts,
        "wrist_sts": wrist_sts,
        "total_rows": total_rows,
        "straight_rows": straight_rows,
        "dec_rate": dec_rate,
        "total_dec_rounds": decrease_rounds
    }

def generate_sleeve_grid(sleeve_data):
    """ 
    Generates a 2D sleeve shaping grid for a tapered sleeve. 
    
    Args: 
        sleeve_data (dict): Sleeve shaping calculations containing stitch counts.
        
    Returns: 
        list[list[int]]: A 2D grid representing the sleeve layout with -1s for tapers. 
        
    Example:
        >>> sleeve_data = {'bicep_sts': 4, 'wrist_sts': 2, 'total_rows': 3, 'straight_rows': 1, 'dec_rate': 1, 'total_dec_rounds': 1}
        >>> generate_sleeve_grid(sleeve_data)
        [[0, 0, 0, 0], [0, 0, 0, 0], [-1, 0, 0, -1]]
    """
    bicep = sleeve_data["bicep_sts"]
    rows = sleeve_data["total_rows"]
    straight_rows = sleeve_data["straight_rows"]
    dec_rate = sleeve_data["dec_rate"]
    
    grid = [[0 for _ in range(bicep)] for _ in range(rows)]
    
    current_width = bicep
    
    for r in range(rows):
        if r > straight_rows and dec_rate > 0 and (r - straight_rows) % dec_rate == 0:
            if current_width > sleeve_data["wrist_sts"]:
                current_width -= 2
        
        removed_total = bicep - current_width
        empty_on_each_side = removed_total // 2
        
        for c in range(empty_on_each_side):
            grid[r][c] = -1 
            grid[r][(bicep - 1) - c] = -1 
            
    return grid