#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 21:38:58 2026

@author: kasteivanauskaite
"""
import copy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from PIL import Image, ImageDraw
import io
import json

def get_hardcoded_heart():
    return [[0, 1, 1, 0, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]]

def scale_pattern_matrix_integer(original_matrix, multiplier):
    if multiplier <= 1: return original_matrix
    scaled_matrix = []
    for row in original_matrix:
        scaled_row = []
        for pixel in row: scaled_row.extend([pixel] * int(multiplier))
        for _ in range(int(multiplier)): scaled_matrix.append(scaled_row.copy()) 
    return scaled_matrix

def rotate_matrix(matrix, degrees):
    if degrees == 0 or not matrix: return matrix
    arr = np.array(matrix)
    k_map = {90: -1, 180: 2, 270: 1}
    return np.rot90(arr, k=k_map.get(degrees, 0)).tolist()

def get_matrix_dimensions(matrix, t_type, axis, spacing_h=0, spacing_v=0):
    if t_type == "None" or not matrix: return len(matrix[0]), len(matrix)
    h, w = len(matrix), len(matrix[0])
    m = 2 if t_type == "Mirror" else 1
    
    new_w = w
    if axis in ["Horizontal", "Quadratic"]:
        overlap_w = min(abs(spacing_h), w) if spacing_h < 0 else 0
        gap_w = spacing_h if spacing_h > 0 else 0
        new_w = (w * m) + gap_w - overlap_w
        
    new_h = h
    if axis in ["Vertical", "Quadratic"]:
        overlap_h = min(abs(spacing_v), h) if spacing_v < 0 else 0
        gap_h = spacing_v if spacing_v > 0 else 0
        new_h = (h * m) + gap_h - overlap_h
        
    return new_w, new_h

def apply_transforms(matrix, t_type, axis, spacing_h=0, spacing_v=0):
    t_type = t_type.capitalize()
    if t_type == "None" or not matrix: return matrix
    arr = np.array(matrix)
    
    if t_type == "Flip":
        if axis == "Horizontal": return arr[:, ::-1].tolist()
        if axis == "Vertical": return arr[::-1, :].tolist()
        if axis == "Quadratic": return arr[::-1, ::-1].tolist()
        
    if t_type == "Mirror":
        def add_gap(m, ax, s):
            side2 = m[:, ::-1] if ax == 1 else m[::-1, :]
            
            if s >= 0:
                gap = np.zeros((len(m), s), dtype=int) if ax == 1 else np.zeros((s, len(m[0])), dtype=int)
                return np.concatenate((m, gap, side2), axis=ax)
            else:
                overlap = min(abs(s), m.shape[1] if ax == 1 else m.shape[0])
                if ax == 1: 
                    w = m.shape[1]
                    new_w = (2 * w) - overlap
                    canvas = np.zeros((m.shape[0], new_w), dtype=int)
                    canvas[:, :w] = np.maximum(canvas[:, :w], m)
                    canvas[:, new_w-w:] = np.maximum(canvas[:, new_w-w:], side2)
                    return canvas
                else: 
                    h = m.shape[0]
                    new_h = (2 * h) - overlap
                    canvas = np.zeros((new_h, m.shape[1]), dtype=int)
                    canvas[:h, :] = np.maximum(canvas[:h, :], m)
                    canvas[new_h-h:, :] = np.maximum(canvas[new_h-h:, :], side2)
                    return canvas

        if axis == "Horizontal": return add_gap(arr, 1, spacing_h).tolist()
        if axis == "Vertical": return add_gap(arr, 0, spacing_v).tolist()
        if axis == "Quadratic": return add_gap(np.array(add_gap(arr, 1, spacing_h)), 0, spacing_v).tolist()
        
    return matrix.tolist()

def overlay_stamps_on_grid(sweater_grid, stamps):
    res = np.array(copy.deepcopy(sweater_grid))
    grid_h, grid_w = res.shape

    for stamp in stamps:
        if not stamp.get("visible", True): continue
    
        base_matrix = stamp.get("matrix")
        if not base_matrix: continue
        
        final_stamp = rotate_matrix(base_matrix, stamp.get("rotation", 0))
        # Pass both spacing_h and spacing_v
        final_stamp = apply_transforms(final_stamp, stamp.get("symmetry", "None"), stamp.get("axis", "Horizontal"), stamp.get("spacing_h", 0), stamp.get("spacing_v", 0))
        final_stamp = scale_pattern_matrix_integer(final_stamp, stamp.get("scale", 1))
        
        final_arr = np.array(final_stamp)
        start_x, start_y = stamp.get("x", 0), stamp.get("y", 0)
        h, w = final_arr.shape
        
        y_min, y_max = max(0, start_y), min(grid_h, start_y + h)
        x_min, x_max = max(0, start_x), min(grid_w, start_x + w)
        
        if y_min >= y_max or x_min >= x_max: continue
        
        stamp_y_min, stamp_x_min = y_min - start_y, x_min - start_x
        stamp_y_max, stamp_x_max = stamp_y_min + (y_max - y_min), stamp_x_min + (x_max - x_min)
        
        stamp_crop = final_arr[stamp_y_min:stamp_y_max, stamp_x_min:stamp_x_max]
        grid_crop = res[y_min:y_max, x_min:x_max]
        
        mask = (grid_crop != -1) & (stamp_crop != 0)
        grid_crop[mask] = stamp_crop[mask]
        
    return res.tolist()

# ... (Keep your generate_multipage_pdf_figs and process_uploaded_image exactly as they were below this)
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

def generate_cropped_canvas_png_bytes(math_grid):
    """Crops the composed canvas tightly around the pattern, adding a white background and grid."""
    arr = np.array(math_grid)
    # Find all coordinates where the pattern exists (1)
    coords = np.argwhere(arr == 1)

    if coords.size == 0:
        # Fallback if canvas is empty
        img = Image.new('RGB', (100, 100), (255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    # Get the bounding box of the combined pattern
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    cropped = arr[y_min:y_max+1, x_min:x_max+1]

    # Render: 255 (White) for background, Red for pattern
    img_arr = np.full((cropped.shape[0], cropped.shape[1], 3), 255, dtype=np.uint8)
    img_arr[cropped == 1] = [220, 50, 50]

    img = Image.fromarray(img_arr)
    
    # Scale up by 10x and draw grid
    cell_size = 10
    img = img.resize((cropped.shape[1] * cell_size, cropped.shape[0] * cell_size), Image.NEAREST)
    draw = ImageDraw.Draw(img)
    grid_color = (130, 130, 130)

    for x in range(0, img.width, cell_size):
        draw.line([(x, 0), (x, img.height)], fill=grid_color, width=1)
    for y in range(0, img.height, cell_size):
        draw.line([(0, y), (img.width, y)], fill=grid_color, width=1)
    draw.rectangle([(0, 0), (img.width-1, img.height-1)], outline=grid_color, width=2)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def merge_stamps(stamps_to_merge):
    """Combines multiple stamps into a single matrix and calculates the new bounding box origin."""
    if not stamps_to_merge:
        return None, 0, 0
        
    stamp_data = []
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for stamp in stamps_to_merge:
        if not stamp.get("visible", True): continue
    
        base_matrix = stamp.get("matrix")
        if not base_matrix: continue
        
        # Bake all transformations into the layer
        t_mat = rotate_matrix(base_matrix, stamp.get("rotation", 0))
        t_mat = apply_transforms(t_mat, stamp.get("symmetry", "None"), stamp.get("axis", "Horizontal"), stamp.get("spacing_h", 0), stamp.get("spacing_v", 0))
        t_mat = scale_pattern_matrix_integer(t_mat, stamp.get("scale", 1))
        
        arr = np.array(t_mat)
        h, w = arr.shape
        sx, sy = stamp.get("x", 0), stamp.get("y", 0)
        
        stamp_data.append((arr, sx, sy, h, w))
        
        # Find the absolute edges of the combined graphic
        min_x = min(min_x, sx)
        min_y = min(min_y, sy)
        max_x = max(max_x, sx + w)
        max_y = max(max_y, sy + h)
        
    if not stamp_data: return None, 0, 0
    
    # Create a blank local canvas just big enough to hold everything
    combined_h = max_y - min_y
    combined_w = max_x - min_x
    combined_canvas = np.zeros((combined_h, combined_w), dtype=int)
    
    # Paste everything onto the local canvas using the calculated offsets
    for arr, sx, sy, h, w in stamp_data:
        local_y = sy - min_y
        local_x = sx - min_x
        # Mask out transparent pixels so layers blend naturally
        mask = arr != 0
        combined_canvas[local_y:local_y+h, local_x:local_x+w][mask] = arr[mask]
        
    return combined_canvas.tolist(), min_x, min_y

def crop_matrix_to_bounding_box(matrix):
    """Crops a matrix to its tightest bounding box of 1s (for Alpha JSON exports)."""
    if not matrix: return []
    arr = np.array(matrix)
    coords = np.argwhere(arr != 0)
    
    if coords.size == 0:
        return arr.tolist()
        
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    
    return arr[y_min:y_max+1, x_min:x_max+1].tolist()

def serialize_project_state(project_data):
    """
    Pure function: Converts the entire project dictionary (settings + stamps) into JSON.
    """
    safe_data = copy.deepcopy(project_data)
    safe_stamps = []
    
    # Clean the numpy arrays out of the stamps
    for s in safe_data.get("stamps", []):
        if isinstance(s.get("matrix"), np.ndarray):
            s["matrix"] = s["matrix"].tolist()
        safe_stamps.append(s)
        
    safe_data["stamps"] = safe_stamps
    return json.dumps(safe_data)

def deserialize_project_state(json_string):
    """
    Pure function: Safely loads the project state, with backwards compatibility.
    """
    if not json_string:
        return {"settings": {}, "stamps": []}
        
    data = json.loads(json_string)
    
    # Backwards compatibility: If you load an old save that was just a list of stamps, 
    # it won't crash. It will just load the stamps and use default settings.
    if isinstance(data, list):
        return {"settings": {}, "stamps": data}
        
    return data