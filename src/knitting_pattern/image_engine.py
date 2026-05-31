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
    """
    Returns a predefined 2D matrix representing an 8-bit heart graphic.
    
    Returns:
        list[list[int]]: A 2D array (matrix) of 1s and 0s.
        
    Example:
        >>> matrix = get_hardcoded_heart()
        >>> matrix[0]
        [0, 1, 1, 0, 1, 1, 0]
    """
    return [[0, 1, 1, 0, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]]

def scale_pattern_matrix_integer(matrix, scale_factor):
    """
    Scales a 2D matrix by an integer factor without altering original memory references.
    Each pixel becomes a block of scale_factor x scale_factor pixels.
    
    Args:
        matrix (list[list[int]]): The original graphic matrix.
        scale_factor (int): The integer multiplier to enlarge the matrix.
        
    Returns:
        list[list[int]]: A newly instanced, scaled-up matrix.
        
    Example:
        >>> matrix = [[1, 0], [0, 1]]
        >>> scale_pattern_matrix_integer(matrix, 2)
        [[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1]]
    """
    if scale_factor <= 1:
        # Return a safe copy of the original matrix
        return [row[:] for row in matrix]

    scaled_matrix = []
    for row in matrix:
        # 1. Stretch the row horizontally
        new_row = []
        for pixel in row:
            new_row.extend([pixel] * scale_factor)
        
        # 2. Stretch the row vertically (using .copy() to prevent memory smearing!)
        for _ in range(scale_factor):
            scaled_matrix.append(new_row.copy())
            
    return scaled_matrix

def rotate_matrix(matrix, degrees):
    """
    Rotates a 2D matrix mathematically by 90, 180, or 270 degrees.
    
    Args:
        matrix (list[list[int]]): The matrix to rotate.
        degrees (int): Rotation in degrees (0, 90, 180, 270).
        
    Returns:
        list[list[int]]: The mathematically rotated matrix.
        
    Example:
        >>> m = [[1, 2], [3, 4]]
        >>> rotate_matrix(m, 90)
        [[3, 1], [4, 2]]
    """
    if degrees == 0 or not matrix: return matrix
    arr = np.array(matrix)
    k_map = {90: -1, 180: 2, 270: 1}
    return np.rot90(arr, k=k_map.get(degrees, 0)).tolist()

def get_matrix_dimensions(matrix, t_type, axis, spacing_h=0, spacing_v=0):
    """
    Calculates the final width and height of a matrix after transforms are applied,
    accounting for structural gaps or overlaps.
    
    Args:
        matrix (list[list[int]]): The base matrix.
        t_type (str): The transform type (e.g., 'Mirror', 'Flip').
        axis (str): The transformation axis ('Horizontal', 'Vertical', 'Quadratic').
        spacing_h (int, optional): Horizontal gap or overlap. Defaults to 0.
        spacing_v (int, optional): Vertical gap or overlap. Defaults to 0.
        
    Returns:
        tuple: (new_width, new_height)
        
    Example:
        >>> m = [[1, 1]]
        >>> get_matrix_dimensions(m, "Mirror", "Horizontal", spacing_h=1)
        (5, 1)
    """
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
    """
    Applies symmetry, flipping, and gap spacing to a graphical matrix.
    
    Args:
        matrix (list[list[int]]): The base matrix to transform.
        t_type (str): The transform type ('None', 'Flip', 'Mirror').
        axis (str): The axis of transformation.
        spacing_h (int, optional): Horizontal pixel distance. Defaults to 0.
        spacing_v (int, optional): Vertical pixel distance. Defaults to 0.
        
    Returns:
        list[list[int]]: The transformed matrix.
        
    Example:
        >>> m = [[1, 0]]
        >>> apply_transforms(m, "Flip", "Horizontal")
        [[0, 1]]
    """
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
    """
    Overlays a stack of graphical stamps onto a base sweater grid using absolute coordinates.
    
    Args:
        sweater_grid (list[list[int]]): The mathematical grid of the garment panel.
        stamps (list[dict]): A list of state dictionaries containing stamp parameters.
        
    Returns:
        list[list[int]]: A unified matrix containing the garment shaping and layered graphics.
        
    Example:
        >>> grid = [[0, 0], [0, 0]]
        >>> stamps = [{"matrix": [[1]], "x": 0, "y": 0, "visible": True}]
        >>> overlay_stamps_on_grid(grid, stamps)
        [[1, 0], [0, 0]]
    """
    res = np.array(copy.deepcopy(sweater_grid))
    grid_h, grid_w = res.shape

    for stamp in stamps:
        if not stamp.get("visible", True): continue
    
        base_matrix = stamp.get("matrix")
        if not base_matrix: continue
        
        final_stamp = rotate_matrix(base_matrix, stamp.get("rotation", 0))
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

def get_panel_instructions(panel_type, shaping, co_sts="?"):
    """
    Generates the text instruction block for the PDF based on the specific panel type.
    
    Args:
        panel_type (str): The garment panel (e.g., 'Front Panel', 'Sleeve').
        shaping (dict): Calculations generated by the math engine.
        co_sts (int, optional): Total cast-on stitches. Defaults to "?".
        
    Returns:
        str: A formatted multi-line string with human-readable knitting instructions.
        
    Example:
        >>> shaping = {"first_turn_stitch": 5, "total_short_row_steps": 2, "sts_per_step": 3}
        >>> text = get_panel_instructions("Front Panel", shaping, 50)
        >>> "FRONT PANEL SHAPING" in text
        True
    """
    if not shaping: shaping = {}
        
    if panel_type == "Front Panel":
        first_turn = shaping.get("first_turn_stitch", "?")
        steps = shaping.get("total_short_row_steps", 1)
        sts_per_step = shaping.get("sts_per_step", "?")
        next_turns = max(0, steps - 1)
        
        return (
            "FRONT PANEL SHAPING (German Short Rows):\n"
            f"Cast on {co_sts} stitches.\n"
            "Work left and right shoulder short rows simultaneously.\n\n"
            
            "RIGHT SHOULDER (Row 1):\n"
            f"• Work {first_turn} sts, turn.\n"
            f"• Next {next_turns} turns: Work {sts_per_step} sts past last turn.\n\n"
            
            "LEFT SHOULDER (Row 2):\n"
            f"• Work {first_turn} sts, turn.\n"
            f"• Next {next_turns} turns: Work {sts_per_step} sts past last turn.\n\n"
            
            "BODY PANEL:\n"
            "• Work even in pattern until desired length."
        )

    elif panel_type == "Back Panel":
        sts_per_step = shaping.get("sts_per_step", "?")
        first_knit = shaping.get("first_turn_stitch", "?")
        purl_dist = shaping.get("purl_distance", "?")
        
        return (
            "BACK PANEL SHAPING (German Short Rows):\n"
            f"Row 0: Cast on {co_sts} stitches.\n\n"
            f"Row 1 (RS): Knit {first_knit} sts. Make a double stitch and turn.\n"
            f"Row 2 (WS): Purl {purl_dist} sts. Make a double stitch and turn.\n\n"
            "Continue working back and forth. Each time you reach a double stitch,\n"
            f"knit (or purl) it together as one stitch, then work {sts_per_step} more\n"
            "stitches past it before turning.\n\n"
            "Repeat this process until you reach the outer edges of the garment."
        )
        
    elif panel_type == "Sleeve":
        straight = shaping.get("straight_rows", "?")
        dec_rate = shaping.get("dec_rate", "?")
        
        return (
            "SLEEVE CONSTRUCTION:\n"
            f"Pick up {co_sts} stitches evenly around the armhole.\n"
            "Place a stitch marker (PM) at the center underarm to signify the\n"
            "Beginning of Round (BOR).\n\n"
            f"Knit {straight} rounds straight.\n\n"
            "Decrease Round: Knit to 3 sts before SM, ssk, k1, SM, k1, k2tog.\n"
            "(If knitting flat: Apply the same decreases 3 sts from the edges).\n\n"
            f"Work a decrease round every {dec_rate} rounds until desired length."
        )
        
    return ""

def generate_multipage_pdf_figs(matrix, shaping_data, title="Knitting Blueprint", rows_per_page=60, settings=None):
    """
    Slices a garment matrix into printable chart chunks and renders Matplotlib Figures.
    
    Args:
        matrix (list[list[int]]): The complete garment grid.
        shaping_data (dict): Logic used to draw custom arrows or text.
        title (str, optional): Project Title. Defaults to "Knitting Blueprint".
        rows_per_page (int, optional): Pagination break limit. Defaults to 60.
        settings (dict, optional): User metrics for the legend. Defaults to None.
        
    Returns:
        list: A list of matplotlib.figure.Figure objects ready to be saved to PDF.
        
    Example:
        >>> matrix = [[0, 0], [0, 0]]
        >>> figs = generate_multipage_pdf_figs(matrix, {})
        >>> len(figs) > 0 # Returns Title page, Instruction page, and Chart
        True
    """
    figs = []
    
    # 1. INJECT THE CAST-ON EDGE
    for x in range(len(matrix[0])):
        if matrix[0][x] != -1: 
            matrix[0][x] = 2

    total_rows = len(matrix)
    total_sts = len(matrix[0])
    co_sts = sum(1 for st in matrix[0] if st != -1) # Count cast-on stitches
    
    pattern_row = next((y for y, row in enumerate(matrix) if 1 in row), None)
    pattern_str = f"Row {pattern_row}" if pattern_row else "None included"

    panel_name = title.split(" - ")[-1] if " - " in title else title
    project_name = title.split(" - ")[0] if " - " in title else "Knitting Project"

    if settings is None: settings = {}
    gauge_sts = settings.get("gauge_sts", "?")
    gauge_rows = settings.get("gauge_rows", "?")
    size = settings.get("target_size", "?")
    chest = settings.get("chest_cm", "?")

    # ==========================================
    # PAGE 1: TITLE & LEGEND (Standalone Cover)
    # ==========================================
    fig_cover, ax_cover = plt.subplots(figsize=(11, 8.5))
    ax_cover.axis('off')
    ax_cover.set_facecolor('#F9F9F9')
    
    cover_text = (
        f"🧶 {project_name.upper()}\n"
        f"PANEL: {panel_name.upper()}\n"
        "════════════════════════════════════════\n\n"
        "PROJECT LEGEND & METRICS:\n"
        f"• Target Size: {size} (Chest: {chest} cm)\n"
        f"• Gauge: {gauge_sts} sts & {gauge_rows} rows per 10cm\n"
        f"• Panel Start Width: {co_sts} sts\n"
        f"• Panel Total Length: {total_rows} rows\n"
        f"• Colorwork Starts: {pattern_str}\n"
    )
        
    ax_cover.text(0.5, 0.6, cover_text, va='center', ha='center', 
                  fontsize=16, color='#222222', linespacing=1.8, fontfamily='sans-serif')
    figs.append(fig_cover)

    # ==========================================
    # PAGE 2: INSTRUCTIONS (Standalone Text Page)
    # ==========================================
    if not shaping_data: shaping_data = {}
    shaping_instructions = get_panel_instructions(panel_name, shaping_data, co_sts) 
    
    if not shaping_instructions:
        shaping_instructions = "• Shaping disabled or standard straight knitting."

    fig_inst, ax_inst = plt.subplots(figsize=(11, 8.5))
    ax_inst.axis('off')
    ax_inst.set_facecolor('#FFFFFF')

    inst_text = (
        f"PATTERN INSTRUCTIONS: {panel_name.upper()}\n"
        "════════════════════════════════════════\n\n"
        f"{shaping_instructions}"
    )

    ax_inst.text(0.1, 0.85, inst_text, va='top', ha='left', 
                  fontsize=13, color='#222222', linespacing=1.8, fontfamily='sans-serif')
    figs.append(fig_inst)

    # ==========================================
    # PAGES 3+: SLICING THE CHART INTO CHUNKS
    # ==========================================
    cmap = ListedColormap(['#C0C0C0', 'white', '#FF4B4B', '#FFB000'])
    
    for chunk_start in range(0, total_rows, rows_per_page):
        chunk_end = min(chunk_start + rows_per_page, total_rows)
        chunk_matrix = matrix[chunk_start:chunk_end]
        chunk_height = len(chunk_matrix)
        
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.imshow(chunk_matrix, cmap=cmap, vmin=-1, vmax=2)
        
        ax.set_xticks(np.arange(-.5, total_sts, 1), minor=True)
        ax.set_yticks(np.arange(-.5, chunk_height, 1), minor=True)
        ax.grid(which="minor", color="#B0B0B0", linestyle='-', linewidth=0.5) 
        ax.tick_params(which="minor", size=0) 
        ax.set_xticks([])
        ax.set_yticks([])
        
        sudoku_col='#595959'
        ax.axvline(-0.5, color=sudoku_col, linewidth=2)
        ax.axvline(total_sts - 0.5, color=sudoku_col, linewidth=2)
        ax.axhline(-0.5, color=sudoku_col, linewidth=2)
        ax.axhline(chunk_height - 0.5, color=sudoku_col, linewidth=2)
        
        for x in range(total_sts):
            if (x + 1) % 5 == 0 and (x + 1) < total_sts:
                ax.axvline(x + 0.5, color=sudoku_col, linewidth=1.5)
                
        for local_y in range(chunk_height):
            abs_y = chunk_start + local_y
            if abs_y % 5 == 0 and abs_y != 0:
                ax.axhline(local_y - 0.5, color=sudoku_col, linewidth=1.5)
        
        for x in range(total_sts):
            stitch_num = x + 1
            if stitch_num == 1 or stitch_num % 5 == 0:
                ax.text(x, -0.8, str(stitch_num), va='bottom', ha='center', fontsize=8, color='#444444', fontweight='bold')
                ax.text(x, chunk_height - 0.2, str(stitch_num), va='top', ha='center', fontsize=8, color='#444444', fontweight='bold')

        for local_y in range(chunk_height):
            abs_y = chunk_start + local_y
            if abs_y == 0:
                ax.text(-1.0, local_y, "CO (WS)", va='center', ha='right', fontsize=9, fontweight='bold', color='#FFB000')
            elif abs_y <= 4 or abs_y % 5 == 0: 
                if abs_y % 2 != 0: 
                    ax.text(total_sts + 0.5, local_y, f"Row {abs_y} (RS)", va='center', ha='left', fontsize=8, color='#333333', fontweight='bold')
                else:          
                    ax.text(-1.0, local_y, f"Row {abs_y} (WS)", va='center', ha='right', fontsize=8, color='#333333', fontweight='bold')

        if shaping_data and "mountain_rows" in shaping_data and "Front Panel" in panel_name:
            m_row = shaping_data["mountain_rows"]
            if chunk_start <= m_row < chunk_end:
                local_m_row = m_row - chunk_start
                midpoint = total_sts // 2
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
    """
    Converts a high-resolution PIL Image into a boolean matrix and high-contrast preview.
    
    Args:
        pil_image (PIL.Image): The user-uploaded image object.
        target_width (int): The desired width in physical stitches.
        threshold_value (int): The darkness threshold (1-255) for binarization.
        
    Returns:
        tuple: (binary matrix list, PIL.Image high-contrast grid preview)
        
    Example:
        >>> from PIL import Image
        >>> img = Image.new('RGB', (100, 100), color='black')
        >>> matrix, preview = process_uploaded_image(img, 10, 128)
        >>> len(matrix[0]) == 10
        True
    """
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
    preview_arr = np.array([[0 if val == 1 else 255 for val in row] for row in matrix], dtype=np.uint8)
    preview_img = Image.fromarray(preview_arr)
    preview_img = preview_img.convert("RGB")
    
    cell_size = 10
    preview_img = preview_img.resize((target_width * cell_size, target_height * cell_size), Image.NEAREST)
    
    # 6. DRAW THE GRAPH PAPER GRID
    draw = ImageDraw.Draw(preview_img)
    grid_color = (130, 130, 130)
    
    for x in range(0, preview_img.width, cell_size):
        draw.line([(x, 0), (x, preview_img.height)], fill=grid_color, width=1)
    for y in range(0, preview_img.height, cell_size):
        draw.line([(0, y), (preview_img.width, y)], fill=grid_color, width=1)
        
    draw.rectangle([(0, 0), (preview_img.width-1, preview_img.height-1)], outline=grid_color, width=2)
    
    return matrix, preview_img

def generate_cropped_canvas_png_bytes(math_grid):
    """
    Crops the final matrix tightly to its boundaries and exports an in-memory PNG.
    
    Args:
        math_grid (list[list[int]]): The final visual representation matrix.
        
    Returns:
        bytes: Raw image byte data for Streamlit download buttons.
        
    Example:
        >>> grid = [[0, 0], [0, 1]]
        >>> output = generate_cropped_canvas_png_bytes(grid)
        >>> isinstance(output, bytes)
        True
    """
    arr = np.array(math_grid)
    coords = np.argwhere(arr == 1)

    if coords.size == 0:
        img = Image.new('RGB', (100, 100), (255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    cropped = arr[y_min:y_max+1, x_min:x_max+1]

    img_arr = np.full((cropped.shape[0], cropped.shape[1], 3), 255, dtype=np.uint8)
    img_arr[cropped == 1] = [220, 50, 50]

    img = Image.fromarray(img_arr)
    
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
    """
    Collapses multiple graphical layers into a single combined matrix.
    
    Args:
        stamps_to_merge (list[dict]): The state dictionaries containing matrices.
        
    Returns:
        tuple: (Combined matrix list, min_x offset, min_y offset)
        
    Example:
        >>> stamps = [{"matrix": [[1]], "x": 1, "y": 1, "visible": True}]
        >>> merge_stamps(stamps)
        ([[1]], 1, 1)
    """
    if not stamps_to_merge:
        return None, 0, 0
        
    stamp_data = []
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for stamp in stamps_to_merge:
        if not stamp.get("visible", True): continue
    
        base_matrix = stamp.get("matrix")
        if not base_matrix: continue
        
        t_mat = rotate_matrix(base_matrix, stamp.get("rotation", 0))
        t_mat = apply_transforms(t_mat, stamp.get("symmetry", "None"), stamp.get("axis", "Horizontal"), stamp.get("spacing_h", 0), stamp.get("spacing_v", 0))
        t_mat = scale_pattern_matrix_integer(t_mat, stamp.get("scale", 1))
        
        arr = np.array(t_mat)
        h, w = arr.shape
        sx, sy = stamp.get("x", 0), stamp.get("y", 0)
        
        stamp_data.append((arr, sx, sy, h, w))
        
        min_x = min(min_x, sx)
        min_y = min(min_y, sy)
        max_x = max(max_x, sx + w)
        max_y = max(max_y, sy + h)
        
    if not stamp_data: return None, 0, 0
    
    combined_h = max_y - min_y
    combined_w = max_x - min_x
    combined_canvas = np.zeros((combined_h, combined_w), dtype=int)
    
    for arr, sx, sy, h, w in stamp_data:
        local_y = sy - min_y
        local_x = sx - min_x
        mask = arr != 0
        combined_canvas[local_y:local_y+h, local_x:local_x+w][mask] = arr[mask]
        
    return combined_canvas.tolist(), min_x, min_y

def crop_matrix_to_bounding_box(matrix):
    """
    Slices away empty transparent space around a graphic before JSON serialization.
    
    Args:
        matrix (list[list[int]]): The raw, uncropped matrix.
        
    Returns:
        list[list[int]]: The tightly cropped matrix.
        
    Example:
        >>> matrix = [[0, 0], [0, 1]]
        >>> crop_matrix_to_bounding_box(matrix)
        [[1]]
    """
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
    Safely converts a complex dictionary containing NumPy arrays into a pure JSON string.
    
    Args:
        project_data (dict): The complete active session state.
        
    Returns:
        str: Serialized JSON payload.
        
    Example:
        >>> state = {"settings": {}, "stamps": []}
        >>> serialize_project_state(state)
        '{"settings": {}, "stamps": []}'
    """
    safe_data = copy.deepcopy(project_data)
    safe_stamps = []
    
    for s in safe_data.get("stamps", []):
        if isinstance(s.get("matrix"), np.ndarray):
            s["matrix"] = s["matrix"].tolist()
        safe_stamps.append(s)
        
    safe_data["stamps"] = safe_stamps
    return json.dumps(safe_data)

def deserialize_project_state(json_string):
    """
    Parses a saved JSON string back into a Python dictionary, ensuring backwards compatibility.
    
    Args:
        json_string (str): The uploaded save file contents.
        
    Returns:
        dict: The structured Python dictionary payload.
        
    Example:
        >>> payload = '{"settings": {}, "stamps": []}'
        >>> type(deserialize_project_state(payload)) is dict
        True
    """
    if not json_string:
        return {"settings": {}, "stamps": []}
        
    data = json.loads(json_string)
    
    if isinstance(data, list):
        return {"settings": {}, "stamps": data}
        
    return data