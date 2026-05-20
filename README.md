# SynthBlend  
### A Blender-based Synthetic Data Generation Add-on for Computer Vision Defect Detection

Synthetic dataset generation framework for procedural defect creation, automatic ground truth mask generation, and YOLOv8 segmentation training using Blender and Python.

---
# Inspiration & Credits

Special thanks to:

## Inspiration

- [uvHolographics by rvorias](https://github.com/rvorias/uvHolographics)

This project was heavily inspired by the concepts, experimentation workflow, procedural rendering ideas, and Blender-based shader experimentation demonstrated in **uvHolographics**.

Huge credit and appreciation to the original creator for the inspiration and motivation behind this project.

## Overview

SynthBlend is a custom Blender add-on developed for generating synthetic datasets for computer vision and machine learning applications, especially industrial defect detection and segmentation.

The system automates:

- Procedural defect generation
- Ground truth mask creation
- YOLO-ready annotation generation
- Domain randomization
- Dataset export
- Segmentation model training workflows

The project was developed as part of a Bachelor of Technology (B.Tech) final year project in Information Technology at Manipal University Jaipur.

---

# Motivation

Creating real-world defect datasets is difficult because:

- Manual annotation is time-consuming
- Industrial datasets are limited
- Rare defects are hard to capture
- Pixel-level segmentation requires extensive effort
- Real data collection is expensive

SynthBlend addresses these issues by generating realistic synthetic datasets automatically using Blender-based procedural rendering and shader systems.

---

# Features

- Blender Add-on for automated dataset generation
- Procedural scratches, cracks, and surface damage generation
- Automatic Ground Truth (GT) mask rendering
- YOLOv8-compatible dataset export
- Domain randomization
- Random camera and lighting generation
- Realistic rendering pipeline
- Segmentation dataset creation
- Dataset statistics logging

### Supported Objects

- Helmets
- Cars
- Mobile phones
- Glass surfaces

---

# Technologies Used

- Blender
- Python
- YOLOv8 (Ultralytics)
- OpenCV
- NumPy
- Google Colab

---

# System Architecture

```text
1. 3D Object Import
2. Procedural Defect Generation
3. Domain Randomization
4. Realistic Rendering
5. Ground Truth Mask Generation
6. Dataset Export
7. YOLOv8 Segmentation Training
8. Prediction & Evaluation
```

---

# Procedural Defect Generation

SynthBlend uses Blender shader nodes to generate procedural defects such as:

- Scratches
- Cracks
- Surface damage
- Reflection distortions

### Shader Nodes Used

- Noise Texture
- Voronoi Texture
- ColorRamp
- Mapping Nodes
- Mix Nodes
- Bump Nodes

### Randomized Parameters

- Position
- Rotation
- Scale
- Intensity
- Reflection variation

---

# Ground Truth Mask Generation

Ground truth masks are generated automatically during rendering.

## Color Segmentation System

| Class | Color |
|------|------|
| Scratch / Defect | Pink |
| Glass Region | Cyan |
| Background | Black |

This enables automatic segmentation annotation generation for YOLOv8 segmentation training.

---

# Dataset Structure

```text
dataset/
│
├── images/
│   ├── train/
│   └── val/
│
├── labels/
│   ├── train/
│   └── val/
│
├── masks/
│
└── data.yaml
```

---

# YOLOv8 Training

The generated datasets were used to train YOLOv8 segmentation models.

## Training Includes

- Dataset preprocessing
- Data augmentation
- Segmentation training
- Validation and testing

## Performance Metrics

| Metric | Value |
|------|------|
| Precision | 0.91 |
| Recall | 0.88 |
| mAP50 | 0.93 |
| mAP50-95 | 0.79 |

---

# Results

The system successfully:

- Generated realistic synthetic datasets
- Created automatic segmentation masks
- Reduced manual annotation effort
- Trained YOLOv8 segmentation models effectively
- Achieved strong segmentation performance on defect datasets

---

# Limitations

Current challenges include:

- Realistic dent generation
- Reflection artifacts on shiny surfaces
- Thin crack visibility under poor lighting
- Synthetic-to-real domain gap

---

# Future Scope

Planned improvements:

- GAN-based defect generation
- Physics-based dent simulation
- Real-time rendering pipeline
- Detectron2 / SAM support
- Additional industrial defect categories

---

# Installation

## Requirements

- Blender 4.x or newer
- Python 3.x
- Ultralytics YOLOv8
- OpenCV
- NumPy

## Blender Add-on Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/SynthBlend.git
```

### Install Add-on

1. Open Blender
2. Go to:

```text
Edit → Preferences → Add-ons → Install
```

3. Select the SynthBlend add-on `.zip` or `.py`
4. Enable the add-on

---

# Usage

1. Import 3D object
2. Configure materials and defects
3. Enable procedural generation
4. Switch between:
   - Real Render Mode
   - GT Mask Mode
5. Generate dataset
6. Export YOLO-ready structure
7. Train YOLOv8 model

---

# Research / Academic Context

This project was developed as:

> **“SynthBlend: A Blender-based Synthetic Data Generation Addon for Computer Vision Defect Detection”**

The project focuses on reducing manual dataset annotation effort using procedural synthetic data generation and automatic segmentation pipelines.

---



# Author

## Rohit Koshy

B.Tech Information Technology  
Manipal University Jaipur

---

# License

This project is intended for educational and research purposes.
