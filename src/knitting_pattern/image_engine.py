#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 21:38:58 2026

@author: kasteivanauskaite
"""

# knitting_pattern/image_engine.py
import copy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from PIL import Image, ImageDraw

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
def scale_pattern_matrix_integer(original_matrix, multiplier):
    """
    Scales a 2D array by an exact integer multiplier to preserve crisp pixel art.
    A multiplier of 2 turns every 1x1 pixel into a 2x2 block of stitches.
    """
    scaled_matrix = []
    
    for row in original_matrix:
        # Step 1: Duplicate horizontally (columns)
        scaled_row = []
        for pixel in row:
            scaled_row.extend([pixel] * int(multiplier))
            
        # Step 2: Duplicate vertically (rows)
        for _ in range(int(multiplier)):
            # We append a copy() so we don't accidentally link the memory of the rows!
            scaled_matrix.append(scaled_row.copy()) 
            
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

def generate_multipage_pdf_figs(matrix, shaping_data, title="Knitting Blueprint", rows_per_page=60):
    figs = []
    
    # 1. INJECT THE CAST-ON EDGE
    for x in range(len(matrix[0])):
        if matrix[0][x] != -1: 
            matrix[0][x] = 2

    total_rows = len(matrix)
    total_sts = len(matrix[0])
    
    # ==========================================
    # PAGE 1: THE COVER & INSTRUCTION PAGE
    # ==========================================
    fig_cover, ax_cover = plt.subplots(figsize=(11, 8.5))
    ax_cover.axis('off')
    ax_cover.set_facecolor('#F9F9F9')
    
    co_sts = sum(1 for st in matrix[0] if st != -1)
    pattern_row = next((y for y, row in enumerate(matrix) if 1 in row), None)
    pattern_str = f"Row {pattern_row}" if pattern_row else "None included"

    if shaping_data and "mountain_rows" in shaping_data:
        first_turn = shaping_data.get("first_turn_stitch", "?")
        steps = shaping_data.get("total_short_row_steps", 1)
        sts_per_step = shaping_data.get("sts_per_step", "?")
        straight_rows = total_rows - shaping_data["mountain_rows"]
        
        instructions = (
            f"🧶 {title.upper()}\n"
            "════════════════════════════════════════\n\n"
            "OVERALL SPECS:\n"
            f"• Cast On: {co_sts} sts\n"
            f"• Total Length: {total_rows} rows\n"
            f"• Colorwork Starts: {pattern_str}\n\n"
            
            "⛰️ SHORT ROW SHAPING\n"
            "Grey blocks represent empty space (no stitches knitted).\n\n"
            
            "RIGHT SHOULDER (Row 1):\n"
            f"• Work {first_turn} sts, turn.\n"
            f"• Next {steps - 1} turns: Work {sts_per_step} sts past last turn.\n\n"
            
            "LEFT SHOULDER (Row 2):\n"
            f"• Work {first_turn} sts, turn.\n"
            f"• Next {steps - 1} turns: Work {sts_per_step} sts past last turn.\n\n"
            
            "BODY PANEL:\n"
            f"• Work even for {straight_rows} rows."
        )
    else:
        instructions = (
            f"🧶 {title.upper()}\n"
            "════════════════════════════════════════\n\n"
            "OVERALL SPECS:\n"
            f"• Cast On: {co_sts} sts\n"
            f"• Total Length: {total_rows} rows\n"
            f"• Colorwork Starts: {pattern_str}\n\n"
            "• Short row shaping is disabled for this panel."
        )
        
    ax_cover.text(0.5, 0.6, instructions, va='center', ha='center', 
                  fontsize=14, color='#222222', linespacing=1.8, fontfamily='sans-serif')
    
    figs.append(fig_cover)

    # ==========================================
    # PAGES 2+: SLICING THE CHART INTO CHUNKS
    # ==========================================
    cmap = ListedColormap(['#C0C0C0', 'white', '#FF4B4B', '#FFB000'])
    
    for chunk_start in range(0, total_rows, rows_per_page):
        chunk_end = min(chunk_start + rows_per_page, total_rows)
        chunk_matrix = matrix[chunk_start:chunk_end]
        chunk_height = len(chunk_matrix)
        
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.imshow(chunk_matrix, cmap=cmap, vmin=-1, vmax=2)
        
        # 1. SOFT BASE GRID (The light background cells)
        ax.set_xticks(np.arange(-.5, total_sts, 1), minor=True)
        ax.set_yticks(np.arange(-.5, chunk_height, 1), minor=True)
        ax.grid(which="minor", color="#B0B0B0", linestyle='-', linewidth=0.5) 
        ax.tick_params(which="minor", size=0) 
        ax.set_xticks([])
        ax.set_yticks([])
        
        # 2. SUDOKU BLOCKS (Heavy lines every 5 blocks)
        sudoku_col='#595959'
        # Outer Bounding Box
        ax.axvline(-0.5, color=sudoku_col, linewidth=2)
        ax.axvline(total_sts - 0.5, color=sudoku_col, linewidth=2)
        ax.axhline(-0.5, color=sudoku_col, linewidth=2)
        ax.axhline(chunk_height - 0.5, color=sudoku_col, linewidth=2)
        
        # Heavy Vertical Lines (Boxing every 5 stitches left-to-right)
        for x in range(total_sts):
            if (x + 1) % 5 == 0 and (x + 1) < total_sts:
                ax.axvline(x + 0.5, color=sudoku_col, linewidth=1.5)
                
        # Heavy Horizontal Lines (Absolute tracking across chunks)
        for local_y in range(chunk_height):
            abs_y = chunk_start + local_y
            if abs_y % 5 == 0 and abs_y != 0:
                ax.axhline(local_y - 0.5, color=sudoku_col, linewidth=1.5)
        
        # 3. STITCH NUMBERING (Now reads 1, 2, 3... from Left to Right)
        for x in range(total_sts):
            stitch_num = x + 1
            # Print the number on the 1st stitch and every 5th stitch
            if stitch_num == 1 or stitch_num % 5 == 0:
                # Top Label
                ax.text(x, -0.8, str(stitch_num), va='bottom', ha='center', fontsize=8, color='#444444', fontweight='bold')
                # Bottom Label
                ax.text(x, chunk_height - 0.2, str(stitch_num), va='top', ha='center', fontsize=8, color='#444444', fontweight='bold')

        # 4. ROW NUMBERING (With explicit RS/WS and moved Cast-On)
        for local_y in range(chunk_height):
            abs_y = chunk_start + local_y
            
            if abs_y == 0:
                # Moved to the left side (-1.0) 
                ax.text(-1.0, local_y, "CO (WS)", va='center', ha='right', fontsize=9, fontweight='bold', color='#FFB000')
            elif abs_y <= 4 or abs_y % 5 == 0: 
                if abs_y % 2 != 0: 
                    # Odd Rows are RS: Label stays on the Right
                    ax.text(total_sts + 0.5, local_y, f"Row {abs_y} (RS)", va='center', ha='left', fontsize=8, color='#333333', fontweight='bold')
                else:          
                    # Even Rows are WS: Label explicitly moved to the Left
                    ax.text(-1.0, local_y, f"Row {abs_y} (WS)", va='center', ha='right', fontsize=8, color='#333333', fontweight='bold')

        # 5. ASYMMETRICAL MOUNTAIN ARROW (If on this chunk)
        if shaping_data and "mountain_rows" in shaping_data:
            m_row = shaping_data["mountain_rows"]
            
            if chunk_start <= m_row < chunk_end:
                local_m_row = m_row - chunk_start
                midpoint = total_sts // 2
                
                # We use the bold sudoku lines now, so just draw the yarn jump arrow!
                ax.annotate('', 
                            xy=(midpoint, 1 - chunk_start), xycoords='data', 
                            xytext=(midpoint, local_m_row - 0.5), textcoords='data', 
                            arrowprops=dict(arrowstyle="->,head_length=0.8,head_width=0.4", 
                                            color="#0055A4", lw=2, ls="--"))

        ax.set_title(f"{title} — Rows {chunk_start} to {chunk_end - 1}", pad=25, fontsize=12, fontweight='bold', color='#555555')
        plt.tight_layout()
        figs.append(fig)
        
    return figs

def process_uploaded_image(pil_image, target_width, threshold_value):
    """Converts an uploaded image into a binary matrix and a visual graph-paper preview."""
    
    # 1. FIX TRANSPARENCY
    if pil_image.mode in ('RGBA', 'LA') or (pil_image.mode == 'P' and 'transparency' in pil_image.info):
        bg = Image.new('RGBA', pil_image.size, (255, 255, 255, 255))
        pil_image = Image.alpha_composite(bg, pil_image.convert('RGBA'))

    # 2. CALCULATE EXACT HEIGHT
    aspect_ratio = pil_image.height / pil_image.width
    target_height = int(target_width * aspect_ratio)
    
    # 3. BOX RESAMPLING
    if hasattr(Image, 'Resampling'):
        pil_image = pil_image.resize((target_width, target_height), Image.Resampling.BOX)
    else:
        pil_image = pil_image.resize((target_width, target_height), Image.BOX)
        
    gray = pil_image.convert('L')
    arr = np.array(gray)
    
    # 4. THRESHOLD MATH
    matrix = [[1 if val < threshold_value else 0 for val in row] for row in arr]
    
    # 5. BUILD THE HIGH-CONTRAST PREVIEW IMAGE
    # 0 = Black (Pattern), 255 = White (Background)
    preview_arr = np.array([[0 if val == 1 else 255 for val in row] for row in matrix], dtype=np.uint8)
    preview_img = Image.fromarray(preview_arr)
    
    # Convert to RGB so we can draw colored/gray grid lines on it!
    preview_img = preview_img.convert("RGB")
    
    # Scale it up by 10x
    cell_size = 10
    preview_img = preview_img.resize((target_width * cell_size, target_height * cell_size), Image.NEAREST)
    
    # 6. DRAW THE GRAPH PAPER GRID
    draw = ImageDraw.Draw(preview_img)
    grid_color = (130, 130, 130) # Matching slate gray
    
    # Draw vertical grid lines
    for x in range(0, preview_img.width, cell_size):
        draw.line([(x, 0), (x, preview_img.height)], fill=grid_color, width=1)
    # Draw horizontal grid lines
    for y in range(0, preview_img.height, cell_size):
        draw.line([(0, y), (preview_img.width, y)], fill=grid_color, width=1)
        
    # Draw a thick bounding box around the whole thing
    draw.rectangle([(0, 0), (preview_img.width-1, preview_img.height-1)], outline=grid_color, width=2)
    
    return matrix, preview_img
