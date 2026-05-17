#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 21:38:58 2026

@author: kasteivanauskaite
"""

# knitting_pattern/image_engine.py
import copy

def get_hardcoded_heart():
    """
    Returns a small 2D matrix representing a heart.
    0 = Background yarn
    1 = Contrast color yarn
    """
    return [
        [0, 1, 1, 0, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 0, 0]
    ]
def scale_pattern_matrix(original_matrix, target_width_sts, target_height_rows):
    """
    Stretches or shrinks a 2D array (alpha pattern) to match the required 
    number of stitches and rows. Uses nearest-neighbor interpolation.
    """
    orig_height = len(original_matrix)
    orig_width = len(original_matrix[0])
    
    scaled_matrix = []
    
    for y in range(target_height_rows):
        new_row = []
        for x in range(target_width_sts):
            # Find the corresponding pixel in the original tiny image
            orig_y = int((y / target_height_rows) * orig_height)
            orig_x = int((x / target_width_sts) * orig_width)
            
            # Copy that pixel's color
            new_row.append(original_matrix[orig_y][orig_x])
            
        scaled_matrix.append(new_row)
        
    return scaled_matrix

def overlay_pattern_on_grid(sweater_grid, alpha_matrix, start_x, start_y):
    """
    Places the alpha pattern onto the main sweater grid.
    Prevents the pattern from printing onto carved short-row areas (-1).
    """
    # Create a copy so we don't accidentally ruin our blank canvas
    result_grid = copy.deepcopy(sweater_grid)
    
    pattern_height = len(alpha_matrix)
    pattern_width = len(alpha_matrix[0])
    
    sweater_height = len(result_grid)
    sweater_width = len(result_grid[0])

    # Loop through every pixel in our little heart graphic
    for p_y in range(pattern_height):
        for p_x in range(pattern_width):
            
            # Calculate exactly where this pixel lands on the giant sweater grid
            target_x = start_x + p_x
            target_y = start_y + p_y
            
            # 1. BOUNDARY CHECK: Does it fall off the right or bottom edges?
            if target_x < sweater_width and target_y < sweater_height:
                
                # 2. CARVING CHECK: Is this stitch a physical part of the sweater?
                if result_grid[target_y][target_x] != -1:
                    
                    # 3. COLOR CHECK: Only print the contrast color (1), ignore the graphic's background (0)
                    if alpha_matrix[p_y][p_x] != 0:
                        result_grid[target_y][target_x] = alpha_matrix[p_y][p_x]
                        
    return result_grid

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def generate_chart_image(matrix, shaping_data, filename="knitting_chart.png"):
    # 1. INJECT THE CAST-ON EDGE
    # We change every physical stitch in Row 0 to a '2' so we can color it differently
    for x in range(len(matrix[0])):
        if matrix[0][x] != -1: # As long as it's a real stitch
            matrix[0][x] = 2

    # 2. SET UP THE COLORS
    # -1: White (Empty Space)
    #  0: Light Gray (Main Yarn)
    #  1: Red (Heart/Contrast Yarn)
    #  2: Gold (The Cast-On Swoop!)
    data = np.array(matrix)
    cmap = ListedColormap(['white', '#E0E0E0', '#FF4B4B', '#FFB000'])
    
    fig, ax = plt.subplots(figsize=(14, 10))
    cax = ax.imshow(data, cmap=cmap, vmin=-1, vmax=2)
    
    # 3. DRAW THE GRID
    total_rows = len(matrix)
    total_sts = len(matrix[0])
    
    ax.set_xticks(np.arange(-.5, total_sts, 1), minor=True)
    ax.set_yticks(np.arange(-.5, total_rows, 1), minor=True)
    ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)
    ax.tick_params(which="minor", size=0) 
    
    # Hide the standard math axes
    ax.set_xticks([])
    ax.set_yticks([])
    
    # ==========================================
    # 4. PROFESSIONAL RS/WS CHART NUMBERING
    # ==========================================
    
    # We loop through every row. Odd rows get RS labels on the right. Even rows get WS labels on the left.
    for y in range(total_rows):
        # Only label every other row or specific intervals to avoid clutter, 
        # but let's do the first few specifically for the short rows!
        if y == 0:
            ax.text(total_sts, y, "CO (WS)", va='center', ha='left', fontsize=9, fontweight='bold', color='#FFB000')
        elif y % 2 != 0: # Odd rows (Right Side)
            ax.text(total_sts, y, f"Row {y} (RS)", va='center', ha='left', fontsize=8, color='black')
        else:            # Even rows (Wrong Side)
            ax.text(-0.5, y, f"(WS) Row {y}", va='center', ha='right', fontsize=8, color='black')

    # ==========================================
    # 5. ANNOTATING THE ASYMMETRIC TIMELINE
    # ==========================================
    mountain_rows = shaping_data["mountain_rows"]
    total_sts = len(matrix[0])
    midpoint = total_sts // 2
    
    # 1. REMOVED the heavy black hlines/vlines!
    # Instead, we just draw a very subtle dashed line to show the physical boundary 
    # without making it look like a brick wall.
    ax.hlines(y=mountain_rows + 0.5, xmin=midpoint, xmax=total_sts - 0.5, color='gray', linewidth=1, linestyle=':')
    ax.hlines(y=mountain_rows + 1.5, xmin=-0.5, xmax=midpoint, color='gray', linewidth=1, linestyle=':')

    # 2. Add a VERTICAL ARROW to guide the eye straight up to Row 1
    # First, we draw just the arrow itself (no text attached) so it perfectly traces the midpoint
    ax.annotate('', 
                xy=(midpoint, 1), xycoords='data', 
                xytext=(midpoint, mountain_rows - 0.5), textcoords='data', 
                arrowprops=dict(arrowstyle="->,head_length=0.8,head_width=0.4", 
                                color="blue", lw=2.5, ls="--"))
                                
    # Second, we place the text box slightly to the RIGHT of the arrow shaft (midpoint + 1.5)
    ax.text(midpoint + 1.5, mountain_rows / 2, 
            'Yarn continues\nto Row 1', 
            ha='left', va='center', color='blue', fontsize=10, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='blue', boxstyle='round,pad=0.3'))
    
    # Point out the Right Shoulder
    ax.text(total_sts - (shaping_data["first_turn_stitch"] / 2), mountain_rows / 2, 
            "Right Shoulder\n(Starts Row 1)", 
            ha="center", va="center", color="black", fontweight="bold", 
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.5'))

    # Point out the Left Shoulder
    ax.text(shaping_data["first_turn_stitch"] / 2, (mountain_rows / 2) + 0.5, 
            "Left Shoulder\n(Starts Row 2)", 
            ha="center", va="center", color="black", fontweight="bold", 
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.5'))

    ax.set_title("Advanced Top-Down Panel: Asymmetrical Short Row Chart", pad=20, fontsize=16, fontweight='bold')
    
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Professional chart successfully saved as {filename}!")

#%%
# --- TESTING BLOCK ---
if __name__ == "__main__":
    from knitting_pattern.math_engine import (
        calculate_stitches, calculate_rows, calculate_garment_dimensions, 
        calculate_top_down_shoulder_shaping, generate_panel_grid, apply_top_down_mountains_to_grid
    )

    my_gauge_sts = 18
    my_gauge_rows = 24
    
    dimensions = calculate_garment_dimensions("M", "drop_shoulder")
    total_sweater_sts = calculate_stitches(dimensions["panel_width_cm"], my_gauge_sts)
    sweater_grid = generate_panel_grid(total_sweater_sts, 50) 
    
    shaping = calculate_top_down_shoulder_shaping(total_sweater_sts, "M", my_gauge_rows)
    carved_grid = apply_top_down_mountains_to_grid(sweater_grid, shaping)

    tiny_heart = get_hardcoded_heart()
    heart_sts = calculate_stitches(15.0, my_gauge_sts)
    heart_rows = calculate_rows(15.0, my_gauge_rows)   

    giant_heart = scale_pattern_matrix(tiny_heart, heart_sts, heart_rows)

    start_x = (total_sweater_sts - heart_sts) // 2
    start_y = 12 
    
    final_chart = overlay_pattern_on_grid(carved_grid, giant_heart, start_x, start_y)
    
    # INSTEAD OF PRINTING TO TERMINAL, WE GENERATE THE IMAGE!
    # Update this line at the bottom of your test block!
    generate_chart_image(final_chart, shaping, "my_first_sweater_chart.png")
    