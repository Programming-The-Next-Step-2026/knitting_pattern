
# 🧶 Knit App

## About This Project
Knit App is a comprehensive Streamlit-based application designed for knitters and compatible with crocheters and other textile makers. It bridges the gap between digital pixel art and physical garment construction. Users can upload images to generate alpha patterns, calculate garment shaping (Front, Back, and Sleeves) based on gauge and sizing, and edit multiple graphics on a digital canvas. 

---

## Key Features
* **Pattern Digitization:** Upload any PNG/JPG and use dynamic thresholding and resampling to convert it into a pixel matrix that you can layer onto a sweater canvas.
  
* **Multi-Panel Garment IDE:** Switch between Front Panel, Back Panel, and Sleeves canvases that make up a drop shoulder sweater. The app dynamically calculates dimensions and short-row shaping based on user measurements and gauge.
  
* **Layer Design Studio:** Add, duplicate, merge, and transform (rotate, flip, mirror, scale) multiple graphics on a single canvas.
  
* **Fine-Tune Pixel Editor:** A built-in, manual spreadsheet-style editor to fine-tune individual stitches or draw custom motifs from scratch on blank 25x25 or 50x50 canvases.
  
* **Alpha JSON Exporter:** Export your custom design to a JSON file to reuse in future projects.
  
* **Master PDF Compiler:** Automatically chunks your digital canvas into a printable PDF pattern complete with cast-on counts, row instructions, and sweater specs.
  
* **Project Saving:** Serialize your entire workspace (including layers, settings, and math grids) into a JSON file to resume your work later.

For more in depth documentation of the features check out docs/report.ipynb
---

## Prerequisites
Before installing, ensure you have **Python 3.9 or newer** installed on your system.

---

## Installation 

### Option A: Using GitHub Desktop
1. Download and install [GitHub Desktop](https://desktop.github.com/).
2. Open GitHub Desktop and go to **File > Clone repository**.
3. Select the **URL** tab and paste: 
   ```text
   [https://github.com/Programming-The-Next-Step-2026/knitting_pattern.git](https://github.com/Programming-The-Next-Step-2026/knitting_pattern.git)



4. Choose a local path on your computer and click **Clone**.
5. Open your preferred terminal (or Anaconda Prompt) and navigate to the folder you just cloned.
6. Run the following command to install the package and its dependencies:
```bash
pip install -e .

```



### Option B: Command Line (Windows / Mac / Linux)

1. Open your Terminal, Command Prompt, or PowerShell.
2. Clone the repository:
```bash
git clone [https://github.com/Programming-The-Next-Step-2026/knitting_pattern.git](https://github.com/Programming-The-Next-Step-2026/knitting_pattern.git)

```


3. Navigate into the directory:
```bash
cd knitting_pattern

```


4. Install the package:
```bash
pip install -e .

```



---

## Usage

Once installed, make sure you are in the `knitting_pattern` root directory, then launch the application locally:

```bash
streamlit run src/knitting_pattern/app.py

```

This will automatically open the Knit App dashboard in your default web browser.

---

## Project Architecture

The software is cleanly modularized into separated layers of concern:

* **`app.py`:** The Streamlit UI layer acting as the primary hub for state management, reactive canvas rendering, and user interaction.
* **`math_engine.py`:** Governs physical measurements, gauge conversions, and garment topography calculations (including dynamic short-row geometry and sleeve tapers).
* **`image_engine.py`:** Handles spatial canvas manipulation, utilizing Pillow and NumPy for image resampling, bounding box cropping, and Matplotlib for dynamic multi-page PDF generation.

---

## License

Distributed under the MIT License. Built as a final capstone project for the university course *Programming: The Next Step (2026)*.

```

```
