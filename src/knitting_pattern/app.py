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
import io
import copy
import pandas as pd

# ==========================================
# INITIALIZE SESSION STATE
# ==========================================
if "x_pos" not in st.session_state:
    st.session_state.x_pos = 20
if "y_pos" not in st.session_state:
    st.session_state.y_pos = 15
if "scale" not in st.session_state:
    st.session_state.scale = 2

# ==========================================
# IMPORTING BACKEND ENGINES
# ==========================================
from knitting_pattern.math_engine import (
    calculate_stitches, calculate_rows, calculate_garment_dimensions,
    calculate_top_down_shoulder_shaping, generate_panel_grid, 
    apply_top_down_mountains_to_grid, calculate_back_neck_shaping, 
    apply_back_short_rows_to_grid
)
from knitting_pattern.image_engine import (
    get_hardcoded_heart, scale_pattern_matrix_integer, overlay_stamps_on_grid, 
    generate_multipage_pdf_figs, process_uploaded_image, get_matrix_dimensions,
    generate_cropped_canvas_png_bytes, apply_transforms, rotate_matrix,
    merge_stamps
)

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
    with col1: gauge_sts = st.number_input("Stitches / 10cm", min_value=5.0, max_value=40.0, value=18.0, step=0.5)
    with col2: gauge_rows = st.number_input("Rows / 10cm", min_value=5.0, max_value=50.0, value=24.0, step=0.5)

    st.divider()
    st.header("2. Sizing & Fit")
    size_mode = st.radio("Sizing Method", ["Standard Sizing", "Advanced (Made-to-Measure)"])
    
    if size_mode == "Standard Sizing":
        target_size = st.selectbox("Select Size", ["XS", "S", "M", "L", "XL", "2XL"], index=2)
        dimensions = calculate_garment_dimensions(target_size, "drop_shoulder")
        chest_cm = dimensions["body_chest_circ"] + dimensions["ease_added"]
        garment_length_cm = dimensions.get("body_length_cm", 60.0) 
        st.info(f"Panel Width: {dimensions['panel_width_cm']} cm\nLength: {garment_length_cm} cm")
    else:
        target_size = "M" 
        st.markdown("**Enter your exact measurements:**")
        chest_cm = st.number_input("Full Chest Circumference (cm)", min_value=50.0, max_value=160.0, value=96.0)
        ease_cm = st.slider("Positive Ease (cm)", min_value=-5.0, max_value=30.0, value=15.0)
        chest_cm += ease_cm
        garment_length_cm = st.number_input("Desired Length (Hem to Shoulder in cm)", min_value=30.0, max_value=120.0, value=60.0, step=1.0)
        
    st.divider()
    st.header("3. Shaping & Pattern")
    panel_type = st.radio("Sweater Panel", ["Front Panel", "Back Panel"], horizontal=True)
    
    if panel_type == "Front Panel": use_shaping = st.toggle("Enable Front Shoulder Shaping", value=True)
    else: use_shaping = st.toggle("Enable Back German Short Rows", value=True)

    st.divider()
    include_pattern = st.toggle("Include Alpha Pattern", value=True)
    
# ==========================================
# CORE MATH: DYNAMIC GRID DIMENSIONS
# ==========================================
panel_width_cm = chest_cm / 2
total_sts = calculate_stitches(panel_width_cm, gauge_sts)
total_rows = calculate_rows(garment_length_cm, gauge_rows)

sweater_grid = generate_panel_grid(total_sts, total_rows)

if panel_type == "Front Panel":
    shaping = calculate_top_down_shoulder_shaping(total_sts, target_size, gauge_rows)
    if use_shaping:
        sweater_grid = apply_top_down_mountains_to_grid(sweater_grid, shaping)
        safe_y_start = shaping["mountain_rows"] + 1
    else: safe_y_start = 0

elif panel_type == "Back Panel":
    shaping = calculate_back_neck_shaping(total_sts, target_size, gauge_rows)
    if use_shaping:
        sweater_grid = apply_back_short_rows_to_grid(sweater_grid, shaping)
        safe_y_start = shaping["mountain_rows"] + 1
    else: safe_y_start = 0

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
        
        st.markdown("**Image Settings:**")
        col_w, col_t = st.columns(2)
        with col_w: target_width = st.slider("Target Width (Stitches)", min_value=5, max_value=total_sts, value=25, step=1)
        with col_t: threshold = st.slider("Darkness Threshold", min_value=1, max_value=255, value=128, step=1)
        
        # 1. Base math generation
        base_pattern_matrix, processed_preview = process_uploaded_image(image, target_width, threshold)
        
        st.markdown("**Comparison Preview:**")
        col_img1, col_img2 = st.columns(2)
        with col_img1: st.image(image, caption="Original Image", use_container_width=True)
        with col_img2: st.image(processed_preview, caption="Knitting Matrix Vision", use_container_width=True)

        # 2. Advanced Editor (The Magic Checkbox Grid)
        st.write("---")
        if st.toggle("🛠️ Advanced Pixel Editing (Manual Override)"):
            st.caption("Click the checkboxes to toggle stitches. (1 = Stitched, 0 = Empty)")
            
            # Convert matrix to boolean DataFrame
            df = pd.DataFrame(base_pattern_matrix).astype(bool)
            
            # Create a configuration that forces cells to be small squares
            column_config = {
                col: st.column_config.CheckboxColumn(
                    None, # Hide column headers
                    width="small",
                ) for col in df.columns
            }
            
            # Use the editor with custom column widths
            edited_df = st.data_editor(
                df,
                column_config=column_config,
                hide_index=True,
                use_container_width=False, # Set to False to prevent stretching
                key="manual_pixel_editor"
            )
            
            base_pattern_matrix = edited_df.astype(int).values.tolist()
            
            # Add a small "Apply Edits" button to keep the UI snappy
            if st.button("Apply Pixel Edits"):
                st.rerun()
                
with tab2:
    preset = st.selectbox("Choose a preset", ["8-Bit Heart"])
    if uploaded_file is None:
        base_pattern_matrix = get_hardcoded_heart()
        st.info("Using the default heart. Try uploading your own above!")
        
# ==========================================
# INITIALIZE STAMP MANAGER STATE
# ==========================================
if "stamps" not in st.session_state: st.session_state.stamps = []
if "active_stamp_idx" not in st.session_state: st.session_state.active_stamp_idx = 0

# ==========================================
# NEW SECTION: MULTI-STAMP DESIGN STUDIO
# ==========================================
st.divider()
st.header("5. Multi-Stamp Design Studio")

current_graphic_name = "Graphic"
if include_pattern and base_pattern_matrix is not None:
    if uploaded_file is not None: current_graphic_name = os.path.splitext(uploaded_file.name)[0]
    else: current_graphic_name = preset

    st.markdown("### ➕ Add Current Graphic to Canvas")
    if st.button("Add as New Layer", type="primary"):
        new_stamp = {
            "name": f"{current_graphic_name} ({len(st.session_state.stamps) + 1})",
            "matrix": base_pattern_matrix,
            "x": total_sts // 2,
            "y": int(safe_y_start) + 10,
            "scale": 1,
            "symmetry": "None",
            "axis": "Horizontal",
            "rotation": 0,
            "spacing": 0
        }
        st.session_state.stamps.append(new_stamp)
        st.session_state.active_stamp_idx = len(st.session_state.stamps) - 1
        st.rerun()
            
st.markdown("---")

if not st.session_state.stamps:
    st.info("Your canvas is currently blank. Click 'Add as New Layer' to start designing!")
    col_controls, col_preview = st.columns([1, 1.5])
else:
    st.markdown("### 🎛️ Layer Studio")
    
   # 1. Layer Management (Select, Rename, Merge)
    col_manage, col_merge = st.columns([1.2, 1])

    with col_manage:
        # Layer Selection
        layer_names = [stamp["name"] for stamp in st.session_state.stamps]
        selected_name = st.selectbox("Select Layer to Edit:", layer_names, index=st.session_state.active_stamp_idx)
        st.session_state.active_stamp_idx = layer_names.index(selected_name)
        active_stamp = st.session_state.stamps[st.session_state.active_stamp_idx]

        # Rename Tool
        c_ren_input, c_ren_btn = st.columns([3, 1])
        with c_ren_input:
            new_name = st.text_input("Rename Layer", value=active_stamp["name"], label_visibility="collapsed")
        with c_ren_btn:
            if st.button("✏️ Rename", use_container_width=True):
                if new_name and new_name != active_stamp["name"]:
                    active_stamp["name"] = new_name
                    st.rerun()

    with col_merge:
        # Merge Tool (Neatly tucked into an expander next to selection)
        with st.expander("🔗 Merge Layers Together"):
            merge_candidates = st.multiselect("Select layers:", layer_names, label_visibility="collapsed")
            if st.button("Merge Selected", type="primary", use_container_width=True):
                if len(merge_candidates) > 1:
                    stamps_to_merge = [s for s in st.session_state.stamps if s["name"] in merge_candidates]
                    merged_matrix, new_x, new_y = merge_stamps(stamps_to_merge)
                    
                    if merged_matrix:
                        new_stamp = {
                            "name": f"Merged Layer ({len(st.session_state.stamps) + 1})",
                            "matrix": merged_matrix,
                            "x": new_x, "y": new_y,
                            "scale": 1, "symmetry": "None", "axis": "Horizontal",
                            "rotation": 0, "spacing_h": 0, "spacing_v": 0
                        }
                        # Swap old layers for new merged layer
                        st.session_state.stamps = [s for s in st.session_state.stamps if s["name"] not in merge_candidates]
                        st.session_state.stamps.append(new_stamp)
                        st.session_state.active_stamp_idx = len(st.session_state.stamps) - 1
                        st.rerun()
                else:
                    st.warning("Select at least 2 layers.")

    st.write("---")

    # 2. Toolbar
    c_dup, c_del = st.columns(2)
    with c_dup:
        if st.button("📑 Duplicate Layer", use_container_width=True):
            cloned = copy.deepcopy(active_stamp)
            cloned["name"] = f"{active_stamp['name']} (Copy)"
            st.session_state.stamps.append(cloned)
            st.session_state.active_stamp_idx = len(st.session_state.stamps) - 1
            st.rerun()
    with c_del:
        if st.button("🗑️ Delete Layer", type="secondary", use_container_width=True):
            st.session_state.stamps.pop(st.session_state.active_stamp_idx)
            st.session_state.active_stamp_idx = max(0, len(st.session_state.stamps) - 1)
            st.rerun()
    col_controls, col_preview = st.columns([1, 1.5])

    
    with col_controls:
        # 3. Crash-Proof Transformations
        st.markdown("#### Transform")
        
        sym_opts = ["None", "Flip", "Mirror"]
        curr_sym = str(active_stamp.get("symmetry", "None")).capitalize()
        if curr_sym not in sym_opts: curr_sym = "None"
        t_type = st.radio("Type", sym_opts, index=sym_opts.index(curr_sym), horizontal=True)
        
        axis_opts = ["Horizontal", "Vertical"]
        if t_type == "Mirror": axis_opts.append("Quadratic")
        curr_axis = str(active_stamp.get("axis", "Horizontal")).capitalize()
        if curr_axis not in axis_opts: curr_axis = "Horizontal"
        axis = st.radio("Axis", axis_opts, index=axis_opts.index(curr_axis), horizontal=True)
        
        curr_rot = active_stamp.get("rotation", 0)
        if curr_rot not in [0, 90, 180, 270]: curr_rot = 0
        rot = st.radio("Rotate", [0, 90, 180, 270], index=[0, 90, 180, 270].index(curr_rot), horizontal=True)
        
        active_stamp["symmetry"] = t_type
        active_stamp["axis"] = axis
        active_stamp["rotation"] = rot
        
        # Split into Horizontal and Vertical Sliders
        active_stamp["spacing_h"] = st.slider("Horizontal Spacing", -20, 20, int(active_stamp.get("spacing_h", 0)))
        active_stamp["spacing_v"] = st.slider("Vertical Spacing", -20, 20, int(active_stamp.get("spacing_v", 0)))
        active_stamp["scale"] = st.slider("Scale", 1, 10, int(active_stamp.get("scale", 1)))

        # 4. Placement & Centering Math
        st.markdown("#### Position")
        p_w_raw, p_h_raw = get_matrix_dimensions(active_stamp["matrix"], t_type, axis, active_stamp["spacing_h"], active_stamp["spacing_v"])
        if active_stamp.get("rotation", 0) in [90, 270]: p_w_raw, p_h_raw = p_h_raw, p_w_raw
        p_w, p_h = p_w_raw * active_stamp["scale"], p_h_raw * active_stamp["scale"]
        
        active_stamp["x"] = st.slider("X Position", -total_sts, total_sts, active_stamp["x"])
        if st.button("Center Horizontally ↔", use_container_width=True):
            active_stamp["x"] = max(0, (total_sts - p_w) // 2)
            st.rerun()
            
        active_stamp["y"] = st.slider("Y Position", -total_rows, total_rows, active_stamp["y"])
        if st.button("Center Vertically ↕", use_container_width=True):
            space = total_rows - safe_y_start
            active_stamp["y"] = int(safe_y_start + (space - p_h) // 2)
            st.rerun()
            
# --- REAL-TIME CANVAS RENDERING ---
with col_preview:
    if "preview_canvas" not in locals():
        preview_canvas = np.full((total_rows, total_sts, 3), 255, dtype=np.uint8)
        
        for r in range(total_rows):
            for c in range(total_sts):
                if sweater_grid[r][c] != -1: 
                    preview_canvas[r, c] = [190, 190, 190]

        preview_math_grid = overlay_stamps_on_grid(sweater_grid, st.session_state.stamps)
        
        for r in range(total_rows):
            for c in range(total_sts):
                if preview_math_grid[r][c] == 1:
                    preview_canvas[r, c] = [220, 50, 50]

        preview_img = Image.fromarray(preview_canvas)
        
        cell_size = 10
        preview_img = preview_img.resize((total_sts * cell_size, total_rows * cell_size), Image.NEAREST)
        draw = ImageDraw.Draw(preview_img)
        grid_color = (130, 130, 130) 
        
        for x in range(0, preview_img.width, cell_size): draw.line([(x, 0), (x, preview_img.height)], fill=grid_color, width=1)
        for y in range(0, preview_img.height, cell_size): draw.line([(0, y), (preview_img.width, y)], fill=grid_color, width=1)
        draw.rectangle([(0, 0), (preview_img.width-1, preview_img.height-1)], outline=grid_color, width=2)

        st.image(preview_img, caption=f"Multi-Stamp Canvas ({total_sts} sts x {total_rows} rows)", use_container_width=True)
        
        # --- NEW DOWNLOAD BUTTON ---
        # Pass the mathematical grid to our new auto-cropper
        cropped_bytes = generate_cropped_canvas_png_bytes(preview_math_grid)
        st.download_button(
            label="✂️ Download Cropped Graphic",
            data=cropped_bytes,
            file_name="cropped_alpha_pattern.png",
            mime="image/png",
            use_container_width=True
        )
# ==========================================
# THE MAGIC BUTTON (Final Export)
# ==========================================
st.divider()
st.markdown("### 6. Compile & Export")

col_export1, col_export2 = st.columns(2)

with col_export1:
    if st.button("✨ Compile Final Pattern", type="primary", use_container_width=True):
        with st.spinner("Compiling high-res chart..."):
            st.session_state.grid = overlay_stamps_on_grid(sweater_grid, st.session_state.stamps)
            st.rerun()

with col_export2:
    # We check if the preview_img exists from the rendering step above
    if "preview_img" in locals():
        # Convert the image to bytes so Streamlit can trigger a file download
        buf_img = io.BytesIO()
        preview_img.save(buf_img, format="PNG")
        byte_img = buf_img.getvalue()
        
        st.download_button(
            label="🖼️ Download Canvas as PNG",
            data=byte_img,
            file_name="my_knit_pixel_canvas.png",
            mime="image/png",
            use_container_width=True
        )

# ==========================================
# DISPLAY GENERATED PATTERN BLUEPRINT
# ==========================================
if "grid" in st.session_state:
    st.success("Chart compiled successfully!")
    st.subheader("Your Custom Knitting Blueprint")
    
    st.markdown("### 📄 Print Settings")
    rows_per_page = st.slider("Rows per printed page", 30, 120, 60, step=10)
    
    figs = generate_multipage_pdf_figs(st.session_state.grid, shaping, title=f"{panel_type}", rows_per_page=rows_per_page)
    
    for fig in figs: st.pyplot(fig)
    
    from matplotlib.backends.backend_pdf import PdfPages
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        for fig in figs: pdf.savefig(fig, bbox_inches='tight')
    buf.seek(0)
    
    st.download_button(
        label="📥 Download Multi-Page Pattern (PDF)",
        data=buf,
        file_name=f"knitting_pattern_{panel_type.replace(' ', '_').lower()}.pdf",
        mime="application/pdf",
        type="primary"
    )