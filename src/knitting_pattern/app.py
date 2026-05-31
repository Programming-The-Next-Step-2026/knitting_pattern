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
import json

# ==========================================
# IMPORTING BACKEND ENGINES
# ==========================================
from knitting_pattern.math_engine import (
    calculate_stitches, calculate_rows, calculate_garment_dimensions,
    calculate_top_down_shoulder_shaping, generate_panel_grid, 
    apply_top_down_mountains_to_grid, calculate_back_neck_shaping, 
    apply_back_short_rows_to_grid, calculate_sleeve_dimensions, 
    generate_sleeve_grid
)
from knitting_pattern.image_engine import (
    get_hardcoded_heart, scale_pattern_matrix_integer, overlay_stamps_on_grid, 
    generate_multipage_pdf_figs, process_uploaded_image, get_matrix_dimensions,
    rotate_matrix, apply_transforms, generate_cropped_canvas_png_bytes, 
    merge_stamps, crop_matrix_to_bounding_box, serialize_project_state,
    deserialize_project_state
)

# ==========================================
# INITIALIZE PROJECT STATE (MULTI-PANEL)
# ==========================================
if "panels" not in st.session_state:
    # Our new "Folder System" for the garment!
    st.session_state.panels = {
        "Front Panel": {"stamps": []},
        "Back Panel": {"stamps": []},
        "Sleeve": {"stamps": []}
    }
if "active_panel" not in st.session_state: st.session_state.active_panel = "Front Panel"
if "active_stamp_idx" not in st.session_state: st.session_state.active_stamp_idx = 0
if "proj_id" not in st.session_state: st.session_state.proj_id = 0 

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Knit App", page_icon="🧶", layout="wide")
st.title("Knitting Chart Maker")
st.markdown("Transform any alpha pattern into a knittable chart with instructions for a drop-shoulder sweater")

# ==========================================
# SIDEBAR: SETTINGS & MEASUREMENTS
# ==========================================
with st.sidebar:
    st.header("1. Yarn Gauge")
    col1, col2 = st.columns(2)
    with col1: gauge_sts = st.number_input("Stitches / 10cm", min_value=5.0, max_value=40.0, value=18.0, step=0.5, key="gauge_sts")
    with col2: gauge_rows = st.number_input("Rows / 10cm", min_value=5.0, max_value=50.0, value=24.0, step=0.5, key="gauge_rows")

    st.divider()
    st.header("2. Sizing & Fit")
    size_mode = st.radio("Sizing Method", ["Standard Sizing", "Advanced (Made-to-Measure)"], key="size_mode")
    
    if size_mode == "Standard Sizing":
        target_size = st.selectbox("Select Size", ["XS", "S", "M", "L", "XL", "2XL"], index=2, key="target_size")
        dimensions = calculate_garment_dimensions(target_size, "drop_shoulder")
        chest_cm = dimensions["body_chest_circ"] + dimensions["ease_added"]
        garment_length_cm = dimensions.get("body_length_cm", 60.0) 
        st.info(f"Panel Width: {dimensions['panel_width_cm']} cm\nLength: {garment_length_cm} cm")
    else:
        target_size = "M" 
        st.markdown("**Enter your exact measurements:**")
        chest_cm = st.number_input("Full Chest Circumference (cm)", min_value=50.0, max_value=160.0, value=96.0, key="chest_cm")
        ease_cm = st.slider("Positive Ease (cm)", min_value=-5.0, max_value=30.0, value=15.0, key="ease_cm")
        chest_cm += ease_cm
        garment_length_cm = st.number_input("Desired Length (Hem to Shoulder in cm)", min_value=30.0, max_value=120.0, value=60.0, step=1.0, key="garment_length_cm")
        
    st.divider()
    
    # --- ACTIVE CANVAS ROUTER ---
    st.header("3. Active Canvas")
    active_panel = st.radio("Editing Panel:", ["Front Panel", "Back Panel", "Sleeve"], key="active_panel")
    
    # Reset layer selection index if we switch panels to avoid out-of-bounds errors
    if "last_panel" not in st.session_state or st.session_state.last_panel != active_panel:
        st.session_state.active_stamp_idx = 0
        st.session_state.last_panel = active_panel
    
    # Shaping rules based on the active panel
    if active_panel == "Front Panel": use_shaping = st.toggle("Enable Front Shoulder Shaping", value=True, key="use_shaping_front")
    elif active_panel == "Back Panel": use_shaping = st.toggle("Enable Back German Short Rows", value=True, key="use_shaping_back")
    else: use_shaping = False # Sleeves have built-in taper shaping, no toggle needed

    st.divider()
    include_pattern = st.toggle("Include Alpha Pattern", value=True, key="include_pattern")

    st.divider()
    st.header("💾 Project File")
    st.caption("Save or restore your project.")
    
    st.text_input("Project Name", value="my_knit_project", key="project_name")

    def get_project_json():
        # Package the multi-panel state along with settings
        project_data = {
            "settings": {
                "project_name": st.session_state.get("project_name", "my_knit_project"),
                "gauge_sts": st.session_state.get("gauge_sts", 18.0),
                "gauge_rows": st.session_state.get("gauge_rows", 24.0),
                "size_mode": st.session_state.get("size_mode", "Standard Sizing"),
                "target_size": st.session_state.get("target_size", "M"),
                "chest_cm": st.session_state.get("chest_cm", 96.0),
                "ease_cm": st.session_state.get("ease_cm", 15.0),
                "garment_length_cm": st.session_state.get("garment_length_cm", 60.0),
                "active_panel": st.session_state.get("active_panel", "Front Panel"),
                "use_shaping_front": st.session_state.get("use_shaping_front", True),
                "use_shaping_back": st.session_state.get("use_shaping_back", True),
                "include_pattern": st.session_state.get("include_pattern", True)
            },
            "panels": st.session_state.panels
        }
        # Safe JSON dump for the deep dictionary
        return json.dumps(project_data)

    raw_name = st.session_state.get("project_name", "my_knit_project").strip()
    safe_name = raw_name.replace(" ", "_") if raw_name else "untitled_project"

    st.download_button("📥 Download Full Project", data=get_project_json(), file_name=f"{safe_name}.json", mime="application/json", use_container_width=True)
    
    st.file_uploader("Upload Project", type="json", label_visibility="collapsed", key="project_file_upload")
    
    # --- CALLBACK FUNCTION ---
    def restore_project_callback():
        if st.session_state.project_file_upload is not None:
            json_string = st.session_state.project_file_upload.getvalue().decode("utf-8")
            raw_data = json.loads(json_string)
            
            # 1. Backwards Compatibility Safety Net!
            if isinstance(raw_data, list):
                # If it's an old save file (just a list), wrap it in our new format
                loaded_data = {
                    "settings": {},
                    "panels": {
                        "Front Panel": {"stamps": raw_data},
                        "Back Panel": {"stamps": []},
                        "Sleeve": {"stamps": []}
                    }
                }
            else:
                loaded_data = raw_data
            
            # 2. Inject saved settings into widgets
            for k, v in loaded_data.get("settings", {}).items(): 
                st.session_state[k] = v
                
            # 3. Inject saved multi-panel layers
            if "panels" in loaded_data: 
                st.session_state.panels = loaded_data["panels"]
            elif "stamps" in loaded_data: # Intermediate save files
                st.session_state.panels = {"Front Panel": {"stamps": loaded_data["stamps"]}, "Back Panel": {"stamps": []}, "Sleeve": {"stamps": []}}
                
            st.session_state.active_stamp_idx = 0
            st.session_state.proj_id += 1

    st.button("⚠️ Restore Project (Overwrites current)", type="primary", on_click=restore_project_callback, use_container_width=True)

# ==========================================
# CORE MATH: MULTI-CANVAS ROUTER
# ==========================================
panel_width_cm = chest_cm / 2

# We dynamically generate the specific math grid based on what tab you are on!
if active_panel in ["Front Panel", "Back Panel"]:
    total_sts = calculate_stitches(panel_width_cm, gauge_sts)
    total_rows = calculate_rows(garment_length_cm, gauge_rows)
    sweater_grid = generate_panel_grid(total_sts, total_rows)
    
    if active_panel == "Front Panel":
        shaping = calculate_top_down_shoulder_shaping(total_sts, target_size, gauge_rows)
        if use_shaping:
            sweater_grid = apply_top_down_mountains_to_grid(sweater_grid, shaping)
            safe_y_start = shaping["mountain_rows"] + 1
        else: safe_y_start = 0
        
    elif active_panel == "Back Panel":
        shaping = calculate_back_neck_shaping(total_sts, target_size, gauge_rows)
        if use_shaping:
            sweater_grid = apply_back_short_rows_to_grid(sweater_grid, shaping)
            safe_y_start = shaping["mountain_rows"] + 1
        else: safe_y_start = 0

elif active_panel == "Sleeve":
    # Hook up the new Sleeve Trapezoid math!
    shaping = calculate_sleeve_dimensions(target_size, gauge_sts, gauge_rows)
    sweater_grid = generate_sleeve_grid(shaping)
    total_sts = shaping["bicep_sts"]
    total_rows = shaping["total_rows"]
    safe_y_start = 0

# Extract the specific layer stack for our active panel
active_stamps = st.session_state.panels[active_panel]["stamps"]

# ==========================================
# MAIN PAGE: PATTERN SELECTION 
# ==========================================
st.header("4. Select Alpha Pattern")
tab1, tab2, tab3 = st.tabs(["Upload Image (PNG/JPG)", "Upload Alpha JSON", "Use Preset Pattern"])
base_pattern_matrix = None
current_graphic_name = "Graphic"

with tab1:
    uploaded_file = st.file_uploader("Upload a pixel graphic (.png, .jpg)", type=['png', 'jpg', 'jpeg'])
    if uploaded_file is not None:
        current_graphic_name = os.path.splitext(uploaded_file.name)[0]
        image = Image.open(uploaded_file)
        st.markdown("**Image Settings:**")
        col_w, col_t = st.columns(2)
        with col_w: target_width = st.slider("Target Width (Stitches)", min_value=5, max_value=total_sts, value=25, step=1)
        with col_t: threshold = st.slider("Darkness Threshold", min_value=1, max_value=255, value=128, step=1)
        
        base_pattern_matrix, processed_preview = process_uploaded_image(image, target_width, threshold)
        
        col_img1, col_img2 = st.columns(2)
        with col_img1: st.image(image, caption="Original Image", use_container_width=True)
        with col_img2: st.image(processed_preview, caption="Knitting Matrix Vision", use_container_width=True)

with tab2:
    st.markdown("Upload a pure pixel matrix generated by this app for 100% lossless quality.")
    alpha_file = st.file_uploader("Upload Alpha Pattern (.json)", type=["json"])
    if alpha_file:
        current_graphic_name = os.path.splitext(alpha_file.name)[0]
        base_pattern_matrix = json.load(alpha_file)
        st.success("Alpha pattern loaded successfully!")
        preview_arr = np.array([[0 if val == 1 else 255 for val in row] for row in base_pattern_matrix], dtype=np.uint8)
        st.image(Image.fromarray(preview_arr).resize((len(base_pattern_matrix[0])*10, len(base_pattern_matrix)*10), Image.NEAREST), caption="Lossless JSON Preview")

with tab3:
    preset = st.selectbox(
        "Choose a preset", 
        ["8-Bit Heart", "Blank Canvas (25x25)", "Blank Canvas (50x50)"]
    )
    
    if uploaded_file is None and alpha_file is None:
        current_graphic_name = preset
        
        if preset == "8-Bit Heart":
            base_pattern_matrix = get_hardcoded_heart()
            st.info("Using the default heart. Try uploading your own above!")
            
        elif preset == "Blank Canvas (25x25)":
            # Generate a 25x25 matrix filled with 0s (empty knittable space)
            base_pattern_matrix = [[0 for _ in range(25)] for _ in range(25)]
            st.info("Using a blank 25x25 canvas. Add it as a layer, then use the Micro-Grid Editor to draw!")
            
        elif preset == "Blank Canvas (50x50)":
            # Generate a 50x50 matrix filled with 0s
            base_pattern_matrix = [[0 for _ in range(50)] for _ in range(50)]
            st.warning("50x50 is quite wide! You will need to scroll horizontally in the Micro-Grid Editor to draw on the edges.")
            
# ==========================================
# DESIGN STUDIO
# ==========================================
st.divider()
st.header(f"5. Design Studio: {active_panel}") # Header dynamically updates!

current_graphic_name = "Graphic"
if include_pattern and base_pattern_matrix is not None:
    if uploaded_file is not None: current_graphic_name = os.path.splitext(uploaded_file.name)[0]
    else: current_graphic_name = preset

    st.markdown("### ➕ Add Current Graphic to Canvas")
    if st.button(f"Add as New Layer to {active_panel}", type="primary"):
        new_stamp = {
            "name": f"{current_graphic_name} ({len(active_stamps) + 1})",
            "matrix": base_pattern_matrix,
            "x": total_sts // 2,
            "y": int(safe_y_start) + 10,
            "scale": 1, "symmetry": "None", "axis": "Horizontal",
            "rotation": 0, "spacing_h": 0, "spacing_v": 0, "visible": True  
        }
        active_stamps.append(new_stamp)
        st.session_state.active_stamp_idx = len(active_stamps) - 1
        st.rerun()
            
st.markdown("---")

if not active_stamps:
    st.info(f"Your {active_panel} is currently blank. Click 'Add as New Layer' to start designing!")
    col_controls, col_preview = st.columns([1, 1.5])
else:
    st.markdown("###  Layer Manager")
    col_manage, col_merge = st.columns([1.2, 1])

    with col_manage:
        layer_names = [stamp["name"] for stamp in active_stamps]
        # Safety catch if layers were deleted
        idx = st.session_state.active_stamp_idx
        if idx >= len(layer_names): idx = max(0, len(layer_names) - 1)
        
        selected_name = st.selectbox("Select Layer to Edit:", layer_names, index=idx)
        st.session_state.active_stamp_idx = layer_names.index(selected_name)
        active_stamp = active_stamps[st.session_state.active_stamp_idx]

        c_ren_input, c_ren_btn, c_vis = st.columns([2.5, 1, 1.2])
        with c_ren_input: new_name = st.text_input("Rename Layer", value=active_stamp["name"], label_visibility="collapsed")
        with c_ren_btn:
            if st.button("✏️ Rename", use_container_width=True):
                if new_name and new_name != active_stamp["name"]:
                    active_stamp["name"] = new_name
                    st.rerun()
        with c_vis:
            is_vis = active_stamp.get("visible", True)
            if st.button("👁️ Visible" if is_vis else "🚫 Hidden", use_container_width=True):
                active_stamp["visible"] = not is_vis
                st.rerun()

    with col_merge:
        with st.expander("🔗 Merge Layers Together"):
            merge_candidates = st.multiselect("Select layers:", layer_names, label_visibility="collapsed")
            if st.button("Merge Selected", type="primary", use_container_width=True):
                if len(merge_candidates) > 1:
                    stamps_to_merge = [s for s in active_stamps if s["name"] in merge_candidates]
                    merged_matrix, new_x, new_y = merge_stamps(stamps_to_merge)
                    if merged_matrix:
                        new_stamp = {
                            "name": f"Merged Layer ({len(active_stamps) + 1})",
                            "matrix": merged_matrix,
                            "x": new_x, "y": new_y,
                            "scale": 1, "symmetry": "None", "axis": "Horizontal",
                            "rotation": 0, "spacing_h": 0, "spacing_v": 0, "visible": True
                        }
                        # Remove merged, append new
                        st.session_state.panels[active_panel]["stamps"] = [s for s in active_stamps if s["name"] not in merge_candidates]
                        st.session_state.panels[active_panel]["stamps"].append(new_stamp)
                        st.session_state.active_stamp_idx = len(st.session_state.panels[active_panel]["stamps"]) - 1
                        st.rerun()
                else: st.warning("Select at least 2 layers.")

    st.write("---")

    c_dup, c_del, c_exp = st.columns(3)
    with c_dup:
        if st.button("📑 Duplicate Layer", use_container_width=True):
            cloned = copy.deepcopy(active_stamp)
            cloned["name"] = f"{active_stamp['name']} (Copy)"
            active_stamps.append(cloned)
            st.session_state.active_stamp_idx = len(active_stamps) - 1
            st.rerun()
    with c_del:
        if st.button("🗑️ Delete Layer", type="secondary", use_container_width=True):
            active_stamps.pop(st.session_state.active_stamp_idx)
            st.session_state.active_stamp_idx = max(0, len(active_stamps) - 1)
            st.rerun()
    with c_exp:
        with st.expander("💾 Export JSON", expanded=False):
            export_scaled = st.checkbox("Include Scale Multiplier?", value=False, help="Check this to download the physically enlarged matrix instead of the original size.")
            
            t_mat = rotate_matrix(active_stamp["matrix"], active_stamp.get("rotation", 0))
            t_mat = apply_transforms(t_mat, active_stamp.get("symmetry", "None"), active_stamp.get("axis", "Horizontal"), active_stamp.get("spacing_h", 0), active_stamp.get("spacing_v", 0))
            
            # If the user checked the box, mathematically scale the matrix before saving it
            if export_scaled and active_stamp.get("scale", 1) > 1:
                t_mat = scale_pattern_matrix_integer(t_mat, active_stamp.get("scale", 1))
                
            cropped_mat = crop_matrix_to_bounding_box(t_mat)
            st.download_button(
                label="📥 Download JSON", 
                data=json.dumps(cropped_mat), 
                file_name=f"{active_stamp['name'].replace(' ', '_')}_alpha.json", 
                mime="application/json", 
                use_container_width=True
            )
    st.write("---")
    
    # 3. MANUAL PIXEL EDITOR (The "Tweezers")
    with st.expander("🖌️ Fine-Tune Pixels", expanded=False):
        st.markdown("### Grid Editor")
        st.caption("Check/uncheck boxes to edit pixels. Columns are kept narrow so you can see more of your pattern at once.")
        
        # Grab identifiers
        pk = st.session_state.proj_id
        idx = st.session_state.active_stamp_idx

        # --- CSS  ---
        st.markdown("""
            <style>
            [data-testid="stDataEditor"] div {
                font-size: 10px !important;
            }
            /* Make the checkboxes fill the cell more efficiently */
            [data-testid="stDataEditor"] input[type="checkbox"] {
                transform: scale(0.8);
            }
            </style>
        """, unsafe_allow_html=True)

        import pandas as pd
        bool_matrix = [[bool(val) for val in row] for row in active_stamp["matrix"]]
        df = pd.DataFrame(bool_matrix)
        
        # NEW: Force every column to be exactly 30 pixels wide (the smallest reliable checkbox size)
        # We also use the index as a 'Row Number'
        col_config = {
            column: st.column_config.CheckboxColumn(label="", width=20) 
            for column in df.columns
        }
        
        with st.form(key=f"pixel_form_{idx}_{pk}_{active_panel}"):
            # We enable the index here so you can see Row 0, Row 1, etc. to stay oriented
            edited_df = st.data_editor(
                df,
                column_config=col_config,
                hide_index=False, 
                use_container_width=False, 
                height=450, # Increased height slightly since cells are now smaller
                key=f"pixel_edit_{idx}_{pk}_{active_panel}"
            )
            
            if st.form_submit_button("✅ Apply Pixel Edits", type="primary", use_container_width=True):
                new_matrix = [[1 if val else 0 for val in row] for row in edited_df.values.tolist()]
                if new_matrix != active_stamp["matrix"]:
                    active_stamp["matrix"] = new_matrix
                    st.rerun()

    col_controls, col_preview = st.columns([1, 1.5])
    
    with col_controls:
        # Wrap Transform in a border
        with st.container(border=True):
            st.markdown("#### Transform")
            pk = st.session_state.proj_id
            idx = st.session_state.active_stamp_idx
            
            sym_opts = ["None", "Flip", "Mirror"]
            curr_sym = str(active_stamp.get("symmetry", "None")).capitalize()
            t_type = st.radio("Type", sym_opts, index=sym_opts.index(curr_sym) if curr_sym in sym_opts else 0, horizontal=True, key=f"sym_{idx}_{pk}_{active_panel}")
            
            axis_opts = ["Horizontal", "Vertical"]
            if t_type == "Mirror": axis_opts.append("Quadratic")
            curr_axis = str(active_stamp.get("axis", "Horizontal")).capitalize()
            axis = st.radio("Axis", axis_opts, index=axis_opts.index(curr_axis) if curr_axis in axis_opts else 0, horizontal=True, key=f"ax_{idx}_{pk}_{active_panel}")
            
            curr_rot = active_stamp.get("rotation", 0)
            rot = st.radio("Rotate", [0, 90, 180, 270], index=[0, 90, 180, 270].index(curr_rot) if curr_rot in [0,90,180,270] else 0, horizontal=True, key=f"rot_{idx}_{pk}_{active_panel}")
            
            active_stamp["symmetry"], active_stamp["axis"], active_stamp["rotation"] = t_type, axis, rot
            
            active_stamp["spacing_h"] = st.slider("Horizontal Spacing", -30, 30, int(active_stamp.get("spacing_h", 0)), key=f"sh_{idx}_{pk}_{active_panel}")
            active_stamp["spacing_v"] = st.slider("Vertical Spacing", -30, 30, int(active_stamp.get("spacing_v", 0)), key=f"sv_{idx}_{pk}_{active_panel}")
            # --- BAKING SCALE SLIDER ---
            col_sc_slide, col_sc_bake = st.columns([2.5, 1])
            
            with col_sc_slide:
                active_stamp["scale"] = st.slider("Scale", 1, 10, int(active_stamp.get("scale", 1)), key=f"sc_{idx}_{pk}_{active_panel}")
                
            with col_sc_bake:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) # Pushes the button down to align with the slider
                if st.button("🔨 Bake", use_container_width=True, help="Permanently enlarge the pixel matrix so you can edit the scaled pixels individually.", key=f"bake_{idx}_{pk}_{active_panel}"):
                    if active_stamp["scale"] > 1:
                        # Mathematically enlarge the matrix
                        active_stamp["matrix"] = scale_pattern_matrix_integer(active_stamp["matrix"], active_stamp["scale"])
                        # Reset the slider back to 1
                        active_stamp["scale"] = 1
                        st.rerun()
        # Wrap Position in a border
        with st.container(border=True):
            st.markdown("#### Position")
            p_w_raw, p_h_raw = get_matrix_dimensions(active_stamp["matrix"], t_type, axis, active_stamp["spacing_h"], active_stamp["spacing_v"])
            if active_stamp.get("rotation", 0) in [90, 270]: p_w_raw, p_h_raw = p_h_raw, p_w_raw
            p_w, p_h = p_w_raw * active_stamp["scale"], p_h_raw * active_stamp["scale"]
            
            def center_h(key, width, tot_w): st.session_state[key] = max(0, (tot_w - width) // 2)
            def center_v(key, height, tot_h, safe_y): st.session_state[key] = int(safe_y + (tot_h - safe_y - height) // 2)
                
            active_stamp["x"] = st.slider("X Position", -total_sts, total_sts, int(active_stamp.get("x", 0)), key=f"x_{idx}_{pk}_{active_panel}")
            st.button("Center Horizontally ↔", on_click=center_h, args=(f"x_{idx}_{pk}_{active_panel}", p_w, total_sts), use_container_width=True)
                
            active_stamp["y"] = st.slider("Y Position", -total_rows, total_rows, int(active_stamp.get("y", 0)), key=f"y_{idx}_{pk}_{active_panel}")
            st.button("Center Vertically ↕", on_click=center_v, args=(f"y_{idx}_{pk}_{active_panel}", p_h, total_rows, safe_y_start), use_container_width=True)
            
# --- REAL-TIME CANVAS RENDERING ---
with col_preview:
    if "preview_canvas" not in locals():
        preview_canvas = np.full((total_rows, total_sts, 3), 255, dtype=np.uint8)
        
        for r in range(total_rows):
            for c in range(total_sts):
                if sweater_grid[r][c] != -1: 
                    preview_canvas[r, c] = [190, 190, 190]

        preview_math_grid = overlay_stamps_on_grid(sweater_grid, active_stamps)
        
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

        st.image(preview_img, caption=f"{active_panel} Canvas ({total_sts} sts x {total_rows} rows)", use_container_width=True)
        
        cropped_bytes = generate_cropped_canvas_png_bytes(preview_math_grid)
        st.download_button(label="Download Graphic as PNG", data=cropped_bytes, file_name=f"cropped_{active_panel.replace(' ', '_')}.png", mime="image/png", use_container_width=True)

# ==========================================
# 6. EXPORT & PRINT STUDIO
# ==========================================
st.divider()
st.header("6. Export & Print Studio")

# The slider is brought back out to the top so it updates dynamically!
st.markdown("### 📄 Print Settings")
rows_per_page = st.slider("Rows per printed page", min_value=30, max_value=120, value=60, step=10)

tab_preview, tab_master = st.tabs(["Preview Active Panel", "Compile Master Pattern PDF"])


# --- TAB 1: REAL-TIME PREVIEW ---
with tab_preview:
    st.markdown(f"Previewing pages for: **{active_panel}**")
    
    
    col_prev_btn, col_png = st.columns([1.5, 1])
    with col_prev_btn:
        if st.button(f"Generate {active_panel} Preview", type="primary", use_container_width=True):
            with st.spinner("Generating visual preview..."):
                st.session_state.preview_grid = overlay_stamps_on_grid(sweater_grid, active_stamps)
                st.session_state.preview_shaping = shaping
                st.session_state.preview_panel = active_panel

    with col_png:
        if "preview_img" in locals():
            buf_img = io.BytesIO()
            preview_img.save(buf_img, format="PNG")
            st.download_button(label=f"🖼️ Download {active_panel} Graphic (PNG)", data=buf_img.getvalue(), file_name=f"{active_panel.replace(' ', '_')}_canvas.png", mime="image/png", use_container_width=True)

    # If a preview exists for the CURRENT panel, render it live!
    if "preview_grid" in st.session_state and st.session_state.get("preview_panel") == active_panel:
        st.success("Preview generated! Adjust the slider above to see the pages update in real-time.")
        # Package settings for the legend
        project_metrics = {
            "gauge_sts": gauge_sts,
            "gauge_rows": gauge_rows,
            "target_size": target_size,
            "chest_cm": chest_cm
        }
        
        figs = generate_multipage_pdf_figs(
            st.session_state.preview_grid, 
            st.session_state.preview_shaping, 
            title=f"{st.session_state.get('project_name', 'My Project').replace('_', ' ')} - {active_panel}", 
            rows_per_page=rows_per_page,
            settings=project_metrics  # <--- NEW
        )
        for fig in figs: 
            st.pyplot(fig)


# --- TAB 2: MASTER GARMENT COMPILER ---
with tab_master:
    st.markdown("Select which panels to bundle into a single PDF document:")
    export_options = st.columns(3)
    with export_options[0]: export_front = st.checkbox("Front Panel", value=True)
    with export_options[1]: export_back = st.checkbox("Back Panel", value=True)
    with export_options[2]: export_sleeve = st.checkbox("Sleeve", value=True)

    panels_to_export = []
    if export_front: panels_to_export.append("Front Panel")
    if export_back: panels_to_export.append("Back Panel")
    if export_sleeve: panels_to_export.append("Sleeve")

    if st.button("Compile Master Pattern PDF", type="primary", use_container_width=True):
        if not panels_to_export:
            st.warning("Please select at least one panel to export.")
        else:
            with st.spinner("Compiling high-res master PDF... This might take a moment."):
                from matplotlib.backends.backend_pdf import PdfPages
                buf = io.BytesIO()
                
                with PdfPages(buf) as pdf:
                    for p_name in panels_to_export:
                        # 1. Recalculate base math for this specific panel in the background
                        p_width_cm = chest_cm / 2
                        if p_name in ["Front Panel", "Back Panel"]:
                            p_sts = calculate_stitches(p_width_cm, gauge_sts)
                            p_rows = calculate_rows(garment_length_cm, gauge_rows)
                            p_grid = generate_panel_grid(p_sts, p_rows)
                            
                            if p_name == "Front Panel":
                                p_shaping = calculate_top_down_shoulder_shaping(p_sts, target_size, gauge_rows)
                                if st.session_state.get("use_shaping_front", True):
                                    p_grid = apply_top_down_mountains_to_grid(p_grid, p_shaping)
                            elif p_name == "Back Panel":
                                p_shaping = calculate_back_neck_shaping(p_sts, target_size, gauge_rows)
                                if st.session_state.get("use_shaping_back", True):
                                    p_grid = apply_back_short_rows_to_grid(p_grid, p_shaping)
                                    
                        elif p_name == "Sleeve":
                            p_shaping = calculate_sleeve_dimensions(target_size, gauge_sts, gauge_rows)
                            p_grid = generate_sleeve_grid(p_shaping)
                            
                        # 2. Overlay that panel's specific stamps
                        p_stamps = st.session_state.panels[p_name]["stamps"]
                        final_p_grid = overlay_stamps_on_grid(p_grid, p_stamps)
                        
                        # 3. Generate figures and append to the Master PDF
                        title = f"{st.session_state.get('project_name', 'My Project').replace('_', ' ')} - {p_name}"
                        # Package settings for the legend
                        project_metrics = {
                            "gauge_sts": gauge_sts,
                            "gauge_rows": gauge_rows,
                            "target_size": target_size,
                            "chest_cm": chest_cm
                        }
                        
                        # 3. Generate figures and append to the Master PDF
                        title = f"{st.session_state.get('project_name', 'My Project').replace('_', ' ')} - {p_name}"
                        figs = generate_multipage_pdf_figs(
                            final_p_grid, 
                            p_shaping, 
                            title=title, 
                            rows_per_page=rows_per_page,
                            settings=project_metrics # <--- NEW
                        )
                        for fig in figs:
                            pdf.savefig(fig, bbox_inches='tight')

                buf.seek(0)
                st.session_state.master_pdf_buf = buf
                
                #celebration baloons
                st.session_state.show_balloons = True 
                st.rerun()

    # DISPLAY MASTER DOWNLOAD
    if "master_pdf_buf" in st.session_state:
        st.success("Master Pattern PDF generated successfully!")
        
        # NEW: Check the flag, launch balloons, and immediately turn the flag off!
        if st.session_state.get("show_balloons"):
            st.balloons()
            st.session_state.show_balloons = False 
            
        st.download_button(
            label="📥 Download Master PDF",
            data=st.session_state.master_pdf_buf,
            file_name=f"{safe_name}_master_pattern.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )