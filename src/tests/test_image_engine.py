#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 15:30:57 2026

@author: kasteivanauskaite
"""
import pytest
import numpy as np
from PIL import Image
from knitting_pattern.image_engine import (
    scale_pattern_matrix_integer,
    rotate_matrix,
    apply_transforms,
    merge_stamps,
    crop_matrix_to_bounding_box,
    serialize_project_state,
    deserialize_project_state,
    process_uploaded_image
)

# ==========================================
# 1. MATRIX MANIPULATION TESTS
# ==========================================

def test_scale_pattern_matrix_integer():
    # Test that 1s and 0s scale up correctly and maintain independence (no smearing)
    matrix = [[1, 0]]
    scaled = scale_pattern_matrix_integer(matrix, 2)
    assert scaled == [[1, 1, 0, 0], [1, 1, 0, 0]]

def test_rotate_matrix():
    # Test 90-degree rotation logic
    matrix = [[1, 2], [3, 4]]
    rotated = rotate_matrix(matrix, 90)
    assert rotated == [[3, 1], [4, 2]]

def test_apply_transforms():
    # Test Horizontal Flip
    matrix = [[1, 0]]
    flipped = apply_transforms(matrix, "Flip", "Horizontal")
    assert flipped == [[0, 1]]

def test_merge_stamps():
    # Test that two stamps merge correctly without overwriting each other
    # Stamp 1 at 0,0 and Stamp 2 at 1,1
    stamps = [
        {"matrix": [[1]], "x": 0, "y": 0, "visible": True},
        {"matrix": [[1]], "x": 1, "y": 1, "visible": True}
    ]
    sweater_grid = [[0, 0], [0, 0]]
    merged = merge_stamps(stamps)
    # merged returns: canvas, min_x, min_y
    assert merged[0] == [[1, 0], [0, 1]]

# ==========================================
# 2. IMAGE PROCESSING & CROPPING TESTS
# ==========================================

def test_crop_matrix_to_bounding_box():
    # Slices away empty space
    matrix = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    cropped = crop_matrix_to_bounding_box(matrix)
    assert cropped == [[1]]

def test_process_uploaded_image():
    # Create a simple 10x10 black image and check if it converts to a 10x10 matrix
    img = Image.new('RGB', (10, 10), color='black')
    matrix, preview = process_uploaded_image(img, 10, 128)
    assert len(matrix) == 10
    assert len(matrix[0]) == 10
    assert matrix[0][0] == 1 # Black pixels become 1

# ==========================================
# 3. PROJECT STATE (JSON) TESTS
# ==========================================

def test_serialize_deserialize():
    # Test JSON state saving with NumPy array conversion
    mock_state = {
        "settings": {"size": "M"},
        "stamps": [{"name": "Test", "matrix": np.array([[1, 0], [0, 1]])}]
    }
    
    # Check serialization
    payload = serialize_project_state(mock_state)
    assert isinstance(payload, str)
    
    # Check deserialization
    recovered = deserialize_project_state(payload)
    assert recovered["settings"]["size"] == "M"
    assert recovered["stamps"][0]["matrix"] == [[1, 0], [0, 1]]