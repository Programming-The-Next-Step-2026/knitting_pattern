#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 20:22:07 2026

@author: kasteivanauskaite
"""

from .example import add, calculate_mean

# engine/__init__.py

# This exposes these specific functions to the rest of your app
from .math_engine import (
    calculate_stitches, calculate_rows, calculate_garment_dimensions,
    calculate_top_down_shoulder_shaping, generate_panel_grid, apply_top_down_mountains_to_grid,
    calculate_back_neck_shaping, apply_back_short_rows_to_grid 
)

# Expose Image Engine Functions
from .image_engine import (
    get_hardcoded_heart,
    scale_pattern_matrix_integer,
    overlay_pattern_on_grid,
    generate_chart_image
)