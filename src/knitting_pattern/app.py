#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 23:04:52 2026

@author: kasteivanauskaite
"""

import os
import streamlit as st
from PIL import Image

# ==========================================
# IMPORTING YOUR BACKEND ENGINES
# ==========================================
from knitting_pattern.math_engine import (
    calculate_stitches, calculate_rows, calculate_garment_dimensions,
    calculate_top_down_shoulder_shaping, generate_panel_grid, apply_top_down_mountains_to_grid
)
from knitting_pattern.image_engine import (
    get_hardcoded_heart, scale_pattern_matrix, overlay_pattern_on_grid, generate_chart_image
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
        target_size = "M" # Default for shaping math if custom size
        st.markdown("**Enter your exact body measurements:**")
        chest_cm = st.number_input("Full Chest Circumference (cm)", min_value=50.0, max_value=160.0, value=96.0)
        ease_cm = st.slider("Positive Ease (cm)", min_value=-5.0, max_value=30.0, value=15.0)
        chest_cm += ease_cm

    st.divider()

    st.header("3. Shaping")
    use_shoulder_shaping = st.toggle("Enable Shoulder Short Rows", value=True)

# ==========================================
# MAIN PAGE: PATTERN SELECTION & PREVIEW
# ==========================================
st.header("4. Select Alpha Pattern")

tab1, tab2 = st.tabs(["Upload Image", "Use Preset Pattern"])

with tab1:
    uploaded_file = st.file_uploader("Upload a pixel graphic (.png, .jpg)", type=['png', 'jpg', 'jpeg'])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Graphic", width=200)
        st.warning("Image processing engine coming soon! Defaulting to preset.")

with tab2:
    st.selectbox("Choose a preset", ["8-Bit Heart"])
    st.info("Using the hardcoded heart from your image_engine!")

st.divider()

# ==========================================
# THE MAGIC BUTTON (Now Fully Connected!)
# ==========================================
if st.button("✨ Generate Knitting Chart", type="primary", use_container_width=True):
    
    with st.spinner("Calculating stitches, shaping, and generating image..."):
        
        # 1. MATH ENGINE: Calculate grid dimensions
        panel_width_cm = chest_cm / 2
        total_sts = calculate_stitches(panel_width_cm, gauge_sts)
        total_rows = 50 # Let's show the top 50 rows of the chest
        
        sweater_grid = generate_panel_grid(total_sts, total_rows)
        
        # 2. MATH ENGINE: Apply Top-Down Shaping
        shaping = calculate_top_down_shoulder_shaping(total_sts, target_size, gauge_rows)
        if use_shoulder_shaping:
            sweater_grid = apply_top_down_mountains_to_grid(sweater_grid, shaping)

        # 3. IMAGE ENGINE: Scale the Heart Graphic
        tiny_heart = get_hardcoded_heart()
        heart_sts = calculate_stitches(15.0, gauge_sts) # 15cm wide
        heart_rows = calculate_rows(15.0, gauge_rows)   # 15cm tall
        giant_heart = scale_pattern_matrix(tiny_heart, heart_sts, heart_rows)

        # 4. IMAGE ENGINE: Overlay Graphic onto Sweater
        start_x = (total_sts - heart_sts) // 2
        start_y = shaping["mountain_rows"] + 2 # Safely below the neckline!
        
        final_chart = overlay_pattern_on_grid(sweater_grid, giant_heart, start_x, start_y)
        
        # 5. GENERATE FINAL IMAGE
        image_filename = "app_generated_chart.png"
        generate_chart_image(final_chart, shaping, image_filename)
        
        st.success("Chart generated successfully!")
        
        # Display Results Safely
        col_results1, col_results2 = st.columns([1, 2])
        
        with col_results1:
            st.subheader("Knitting Specs")
            st.metric(label="Cast On Width", value=f"{total_sts} sts")
            st.metric(label="Gauge (10cm)", value=f"{gauge_sts} sts x {gauge_rows} rows")
            if use_shoulder_shaping:
                st.metric(label="Short Row Steps", value=f"{shaping['total_short_row_steps']} steps")
                
        with col_results2:
            st.subheader("Final Chart")
            # Safely check if the image was actually created to prevent Streamlit crashes
            if os.path.exists(image_filename):
                st.image(image_filename, use_container_width=True)
            else:
                st.error("Failed to generate image file.")