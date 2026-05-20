#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 23:04:52 2026

@author: kasteivanauskaite
run: streamlit run src/knitting_pattern/app.py
"""
import os
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw

# ==========================================
# INITIALIZE SESSION STATE (For Centering Buttons)
# ==========================================
if "x_pos" not in st.session_state:
    st.session_state.x_pos = 20
if "y_pos" not in st.session_state:
    st.session_state.y_pos = 15
if "scale" not in st.session_state:
    st.session_state.scale = 2

# ==========================================
# IMPORTING YOUR BACKEND ENGINES
# ==========================================
from knitting_pattern.math_engine import (
    calculate_stitches, calculate_rows, calculate_garment_dimensions,
    calculate_top_down_shoulder_shaping, generate_panel_grid, apply_top_down_mountains_to_grid,
    calculate_back_neck_shaping, apply_back_short_rows_to_grid 
)
from knitting_pattern.image_engine import (
    get_hardcoded_heart, scale_pattern_matrix_integer, overlay_pattern_on_grid, generate_chart_image
)

# ==========================================
# HELPER: PROCESS UPLOADED IMAGES
# ==========================================

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

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Knit & Pixel", page_icon="🧶", layout="wide")

st.title("🧶 Knit & Pixel: Colorwork Generator")
st.markdown("Transform any alpha pattern into a perfectly scaled, knittable chart.")

# ==========================================
# SIDEBAR: SETTINGS & MEASUREMENTS
# ==========================================
with st.sidebar:
    st.header("1. Yarn & Gauge")
    col1, col2 = st.columns(2)
    with col1:
        gauge_sts = st.number_input("Stitches / 10cm", min_value=5.0, max_value=40.0, value=18.0, step=0.5)
    with col2:
        gauge_rows = st.number_input("Rows / 10cm", min_value=5.0, max_value=50.0, value=24.0, step=0.5)

    st.divider()

    st.header("2. Sizing & Fit")
    size_mode = st.radio("Sizing Method", ["Standard Sizing", "Advanced (Made-to-Measure)"])
    
    if size_mode == "Standard Sizing":
        target_size = st.selectbox("Select Size", ["XS", "S", "M", "L", "XL", "2XL"], index=2)
        dimensions = calculate_garment_dimensions(target_size, "drop_shoulder")
        chest_cm = dimensions["body_chest_circ"] + dimensions["ease_added"]
        # Standard sizes usually have a graded length, we'll default to 60cm if not in your dictionary
        garment_length_cm = dimensions.get("body_length_cm", 60.0) 
        st.info(f"Panel Width: {dimensions['panel_width_cm']} cm\nLength: {garment_length_cm} cm")
    else:
        target_size = "M" 
        st.markdown("**Enter your exact measurements:**")
        chest_cm = st.number_input("Full Chest Circumference (cm)", min_value=50.0, max_value=160.0, value=96.0)
        ease_cm = st.slider("Positive Ease (cm)", min_value=-5.0, max_value=30.0, value=15.0, help="Added to the chest circumference.")
        chest_cm += ease_cm
        
        garment_length_cm = st.number_input("Desired Length (Hem to Shoulder in cm)", min_value=30.0, max_value=120.0, value=60.0, step=1.0)
        
    st.divider()

    st.header("3. Shaping & Pattern")
    panel_type = st.radio("Sweater Panel", ["Front Panel", "Back Panel"], horizontal=True)
    
    if panel_type == "Front Panel":
        use_shaping = st.toggle("Enable Front Shoulder Shaping", value=True)
    else:
        use_shaping = st.toggle("Enable Back German Short Rows", value=True)

    st.divider()
    include_pattern = st.toggle("Include Alpha Pattern", value=True)
    
# ==========================================
# CORE MATH: DYNAMIC GRID DIMENSIONS
# ==========================================
panel_width_cm = chest_cm / 2
total_sts = calculate_stitches(panel_width_cm, gauge_sts)

# This physically translates the length cm into exact matrix rows!
total_rows = calculate_rows(garment_length_cm, gauge_rows)

sweater_grid = generate_panel_grid(total_sts, total_rows)

if panel_type == "Front Panel":
    shaping = calculate_top_down_shoulder_shaping(total_sts, target_size, gauge_rows)
    if use_shaping:
        sweater_grid = apply_top_down_mountains_to_grid(sweater_grid, shaping)
        safe_y_start = shaping["mountain_rows"] + 1
    else:
        safe_y_start = 0

elif panel_type == "Back Panel":
    shaping = calculate_back_neck_shaping(total_sts, target_size, gauge_rows)
    if use_shaping:
        sweater_grid = apply_back_short_rows_to_grid(sweater_grid, shaping)
        safe_y_start = shaping["mountain_rows"] + 1
    else:
        safe_y_start = 0

# ==========================================
# MAIN PAGE: PATTERN SELECTION 
# ==========================================
st.header("4. Select Alpha Pattern")

tab1, tab2 = st.tabs(["Upload Image", "Use Preset Pattern"])

base_pattern_matrix = None

with tab1:
    uploaded_file = st.file_uploader("Upload a pixel graphic (.png, .jpg)", type=['png', 'jpg', 'jpeg'])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        # 1. Sliders Side-by-Side (Making them smaller and neater)
        st.markdown("**Image Settings:**")
        col_w, col_t = st.columns(2)
        with col_w:
            target_width = st.slider("Target Width (Stitches)", min_value=5, max_value=total_sts, value=25, step=1)
        with col_t:
            threshold = st.slider("Darkness Threshold", min_value=1, max_value=255, value=128, step=1, 
                                  help="Slide to dial in the perfect outline.")
        
        # Pass the sliders into the function and get BOTH the matrix and the preview image back!
        base_pattern_matrix, processed_preview = process_uploaded_image(image, target_width, threshold)
        
        # 2. Images Side-by-Side for Easy Comparison
        st.markdown("**Comparison Preview:**")
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.image(image, caption="Original Image", use_container_width=True)
        with col_img2:
            st.image(processed_preview, caption="Knitting Matrix Vision", use_container_width=True)

with tab2:
    preset = st.selectbox("Choose a preset", ["8-Bit Heart"])
    if uploaded_file is None:
        base_pattern_matrix = get_hardcoded_heart()
        st.info("Using the default heart. Try uploading your own above!")

# ==========================================
# NEW SECTION: REAL-TIME PLACEMENT
# ==========================================
st.divider()
st.header("5. Real-Time Placement")

sweater_grid = generate_panel_grid(total_sts, total_rows)

# THE NEW ROUTING LOGIC: Checks the sidebar toggle before doing the math!
if panel_type == "Front Panel":
    shaping = calculate_top_down_shoulder_shaping(total_sts, target_size, gauge_rows, panel_type)
    if use_shaping:
        sweater_grid = apply_top_down_mountains_to_grid(sweater_grid, shaping)
        safe_y_start = shaping["mountain_rows"] + 1
    else:
        safe_y_start = 0

elif panel_type == "Back Panel":
    shaping = calculate_back_neck_shaping(total_sts, target_size, gauge_rows)
    if use_shaping:
        sweater_grid = apply_back_short_rows_to_grid(sweater_grid, shaping)
        # The back is a dome, so the top-center row is at 0!
        safe_y_start = 0
    else:
        safe_y_start = 0


# Safety checks to prevent app crashes if the canvas resizes out from under the sliders!
if st.session_state.y_pos < safe_y_start:
    st.session_state.y_pos = int(safe_y_start)
if st.session_state.x_pos > total_sts:
    st.session_state.x_pos = total_sts // 2

col_controls, col_preview = st.columns([1, 1.5])

with col_controls:
    st.markdown("Use the sliders to lock your alpha pattern to the grid.")
    pattern_scale = st.slider("Scale Multiplier", min_value=1, max_value=10, key="scale")
    
    # Calculate physical width/height of the pattern right now
    p_w = len(base_pattern_matrix[0]) * pattern_scale
    p_h = len(base_pattern_matrix) * pattern_scale

    # ==========================================
    # CALLBACK FUNCTIONS FOR BUTTONS
    # These run *before* the UI renders!
    # ==========================================
    def center_x_callback(t_sts, p_width):
        st.session_state.x_pos = max(0, (t_sts - p_width) // 2)

    def center_y_callback(t_rows, s_y_start, p_height):
        space = t_rows - s_y_start
        st.session_state.y_pos = int(s_y_start + (space - p_height) // 2)

    # X-Axis Controls
    st.markdown("##### Horizontal Placement")
    col_x_slider, col_x_btn = st.columns([3, 1])
    with col_x_slider:
        st.slider("X Position", min_value=0, max_value=total_sts, key="x_pos", label_visibility="collapsed")
    with col_x_btn:
        # We attach the callback to the on_click parameter!
        st.button("Center ↔", on_click=center_x_callback, args=(total_sts, p_w), use_container_width=True)

    # Y-Axis Controls
    st.markdown("##### Vertical Placement")
    col_y_slider, col_y_btn = st.columns([3, 1])
    with col_y_slider:
        st.slider("Y Position", min_value=int(safe_y_start), max_value=total_rows, key="y_pos", label_visibility="collapsed")
    with col_y_btn:
        st.button("Center ↕", on_click=center_y_callback, args=(total_rows, safe_y_start, p_h), use_container_width=True)

with col_preview:
    scaled_pattern = scale_pattern_matrix_integer(base_pattern_matrix, pattern_scale)
    
    # 1. Base Canvas (White for the empty space around the sweater)
    preview_canvas = np.full((total_rows, total_sts, 3), 255, dtype=np.uint8)
    
    # 2. Solid Sweater Base (No more checkerboard!)
    for r in range(total_rows):
        for c in range(total_sts):
            if sweater_grid[r][c] != -1: 
                # Just a clean, solid light gray for the sweater panel
                preview_canvas[r, c] = [190, 190, 190]

    # 3. Pattern Placement
    if include_pattern and base_pattern_matrix is not None:
        scaled_pattern = scale_pattern_matrix_integer(base_pattern_matrix, pattern_scale)
        for r in range(len(scaled_pattern)):
            for c in range(len(scaled_pattern[0])):
                if scaled_pattern[r][c] == 1:
                    y = st.session_state.y_pos + r
                    x = st.session_state.x_pos + c
                    if 0 <= y < total_rows and 0 <= x < total_sts:
                        preview_canvas[y, x] = [220, 50, 50]

    preview_img = Image.fromarray(preview_canvas)
    
    # 4. Chunkier Upscaling
    cell_size = 10
    preview_img = preview_img.resize((total_sts * cell_size, total_rows * cell_size), Image.NEAREST)
    
    # 5. Crisp Graph Paper Lines over the solid background
    draw = ImageDraw.Draw(preview_img)
    grid_color = (130, 130, 130) # Dark slate gray
    
    # Draw vertical grid lines
    for x in range(0, preview_img.width, cell_size):
        draw.line([(x, 0), (x, preview_img.height)], fill=grid_color, width=1)
    # Draw horizontal grid lines
    for y in range(0, preview_img.height, cell_size):
        draw.line([(0, y), (preview_img.width, y)], fill=grid_color, width=1)
        
    # Draw a thick bounding box around the whole preview
    draw.rectangle([(0, 0), (preview_img.width-1, preview_img.height-1)], outline=grid_color, width=2)
        
    st.image(preview_img, caption=f"Real-Time Placement ({total_sts} sts x {total_rows} rows)", use_container_width=True)
    st.divider()
    
# ==========================================
# THE MAGIC BUTTON (Final Export)
# ==========================================
st.markdown("### Happy with your placement?")
if st.button("✨ Generate Final Printable Chart", type="primary", use_container_width=True):
    with st.spinner("Generating high-res Matplotlib chart..."):
        
        if include_pattern and base_pattern_matrix is not None:
            scaled_pattern = scale_pattern_matrix_integer(base_pattern_matrix, pattern_scale)
            final_chart = overlay_pattern_on_grid(sweater_grid, scaled_pattern, st.session_state.x_pos, st.session_state.y_pos)
        else:
            final_chart = sweater_grid
            
        image_filename = "app_generated_chart.png"
        generate_chart_image(final_chart, shaping, image_filename)
        
        st.success("Chart generated successfully!")
        
'''
import os
import streamlit as st
import numpy as np
from PIL import Image

# ==========================================
# IMPORTING YOUR BACKEND ENGINES
# ==========================================
from knitting_pattern.math_engine import (
    calculate_stitches, calculate_rows, calculate_garment_dimensions,
    calculate_top_down_shoulder_shaping, generate_panel_grid, apply_top_down_mountains_to_grid
)
from knitting_pattern.image_engine import (
    get_hardcoded_heart, scale_pattern_matrix_integer, overlay_pattern_on_grid, generate_chart_image
)

# ==========================================
# HELPER: PROCESS UPLOADED IMAGES
# ==========================================
def process_uploaded_image(pil_image):
    """Converts a user's uploaded image into a binary 1/0 matrix for knitting."""
    # Shrink it so massive photos don't crash the grid
    pil_image.thumbnail((50, 50)) 
    # Convert to grayscale
    gray = pil_image.convert('L')
    arr = np.array(gray)
    # Threshold: dark pixels become 1 (the pattern), light pixels become 0 (empty)
    matrix = [[1 if val < 128 else 0 for val in row] for row in arr]
    return matrix

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Knit & Pixel", page_icon="🧶", layout="wide")

st.title("🧶 Knit & Pixel: Colorwork Generator")
st.markdown("Transform any alpha pattern into a perfectly scaled, knittable chart.")

# ==========================================
# SIDEBAR: SETTINGS & MEASUREMENTS
# ==========================================
with st.sidebar:
    st.header("1. Yarn & Gauge")
    col1, col2 = st.columns(2)
    with col1:
        gauge_sts = st.number_input("Stitches / 10cm", min_value=5.0, max_value=40.0, value=18.0, step=0.5)
    with col2:
        gauge_rows = st.number_input("Rows / 10cm", min_value=5.0, max_value=50.0, value=24.0, step=0.5)

    st.divider()

    st.header("2. Sizing")
    size_mode = st.radio("Sizing Method", ["Standard Sizing", "Advanced (Made-to-Measure)"])
    
    if size_mode == "Standard Sizing":
        target_size = st.selectbox("Select Size", ["XS", "S", "M", "L", "XL", "2XL"], index=2)
        dimensions = calculate_garment_dimensions(target_size, "drop_shoulder")
        chest_cm = dimensions["body_chest_circ"] + dimensions["ease_added"]
        st.info(f"Panel Width: {dimensions['panel_width_cm']} cm")
    else:
        target_size = "M" 
        st.markdown("**Enter your exact body measurements:**")
        chest_cm = st.number_input("Full Chest Circumference (cm)", min_value=50.0, max_value=160.0, value=96.0)
        ease_cm = st.slider("Positive Ease (cm)", min_value=-5.0, max_value=30.0, value=15.0)
        chest_cm += ease_cm

    st.divider()

    st.header("3. Shaping")
    use_shoulder_shaping = st.toggle("Enable Shoulder Short Rows", value=True)

# Calculate Core Dimensions early so the UI can use them!
panel_width_cm = chest_cm / 2
total_sts = calculate_stitches(panel_width_cm, gauge_sts)
total_rows = 70 # The height of the preview canvas

# ==========================================
# MAIN PAGE: PATTERN SELECTION 
# ==========================================
st.header("4. Select Alpha Pattern")

tab1, tab2 = st.tabs(["Upload Image", "Use Preset Pattern"])

base_pattern_matrix = None

with tab1:
    uploaded_file = st.file_uploader("Upload a pixel graphic (.png, .jpg)", type=['png', 'jpg', 'jpeg'])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Graphic", width=150)
        base_pattern_matrix = process_uploaded_image(image)

with tab2:
    preset = st.selectbox("Choose a preset", ["8-Bit Heart"])
    if uploaded_file is None:
        base_pattern_matrix = get_hardcoded_heart()
        st.info("Using the default heart. Try uploading your own above!")

# ==========================================
# NEW SECTION: REAL-TIME PLACEMENT
# ==========================================
st.divider()
st.header("5. Real-Time Placement")

# 1. CALCULATE SHAPING EARLY FOR THE PREVIEW
sweater_grid = generate_panel_grid(total_sts, total_rows)
shaping = calculate_top_down_shoulder_shaping(total_sts, target_size, gauge_rows)

if use_shoulder_shaping:
    sweater_grid = apply_top_down_mountains_to_grid(sweater_grid, shaping)
    # The absolute highest row they are allowed to place a pattern
    safe_y_start = shaping["mountain_rows"] + 1 
else:
    safe_y_start = 0

col_controls, col_preview = st.columns([1, 1.5])

with col_controls:
    st.markdown("Use the sliders to lock your alpha pattern to the grid.")
    pattern_scale = st.slider("Scale Multiplier", min_value=1, max_value=10, value=2, step=1)
    
    start_x_stitch = st.slider("X Position (Left to Right)", min_value=0, max_value=total_sts, value=total_sts//2 - 5, step=1)
    
    # 2. LOCK THE Y SLIDER! 
    # min_value is now safe_y_start, preventing placement in the short rows!
    start_y_row = st.slider("Y Position (Top to Bottom)", 
                            min_value=int(safe_y_start), 
                            max_value=total_rows, 
                            value=int(safe_y_start) + 5, 
                            step=1,
                            help="Pattern placement is locked below the neckline shaping.")

with col_preview:
    scaled_pattern = scale_pattern_matrix_integer(base_pattern_matrix, pattern_scale)
    
    # 3. BUILD CANVAS BASED ON ACTUAL SWEATER SHAPE
    # Start with a white background (empty space)
    preview_canvas = np.full((total_rows, total_sts, 3), 255, dtype=np.uint8)
    
    # Paint only the actual sweater stitches gray!
    for r in range(total_rows):
        for c in range(total_sts):
            if sweater_grid[r][c] != -1: # If it's a real stitch
                preview_canvas[r, c] = [235, 235, 235] if r % 2 == 0 else [245, 245, 245]

    # 4. Stamp the scaled pattern
    p_h = len(scaled_pattern)
    p_w = len(scaled_pattern[0])
    for r in range(p_h):
        for c in range(p_w):
            if scaled_pattern[r][c] == 1:
                y = start_y_row + r
                x = start_x_stitch + c
                if 0 <= y < total_rows and 0 <= x < total_sts:
                    preview_canvas[y, x] = [255, 75, 75] 

    preview_img = Image.fromarray(preview_canvas)
    preview_img = preview_img.resize((total_sts * 8, total_rows * 8), Image.NEAREST)
    
    st.image(preview_img, caption=f"Real-Time Grid Preview", use_container_width=True)

st.divider()

# ==========================================
# THE MAGIC BUTTON (Final Export)
# ==========================================
st.markdown("### Happy with your placement?")
if st.button("✨ Generate Final Printable Chart", type="primary", use_container_width=True):
    
    with st.spinner("Generating high-res Matplotlib chart..."):
        
        # We already carved the sweater_grid above, so we just overlay!
        final_chart = overlay_pattern_on_grid(sweater_grid, scaled_pattern, start_x_stitch, start_y_row)
        
        image_filename = "app_generated_chart.png"
        generate_chart_image(final_chart, shaping, image_filename)
        
        st.success("Chart generated successfully!")
        
        col_results1, col_results2 = st.columns([1, 2])
        with col_results1:
            st.subheader("Knitting Specs")
            st.metric(label="Cast On Width", value=f"{total_sts} sts")
            st.metric(label="Gauge (10cm)", value=f"{gauge_sts} sts x {gauge_rows} rows")
            if use_shoulder_shaping:
                st.metric(label="Short Row Steps", value=f"{shaping['total_short_row_steps']} steps")
                
        with col_results2:
            st.subheader("Final Printable Chart")
            if os.path.exists(image_filename):
                st.image(image_filename, use_container_width=True)
            else:
                st.error("Failed to generate image file.")
'''
