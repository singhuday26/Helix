# Helix Quick Setup Guide 🧬

Follow these steps to get the Helix inference engine up and running on your machine.

## Prerequisites

- **Windows 10/11** (Project is optimized for DirectML on Windows)
- **Python 3.10+** installed and added to PATH.
- **Git** installed.

## 🚀 One-Click Setup (Recommended)

1.  Open the `Helix` folder in File Explorer.
2.  Double-click **`setup.bat`**.

This script will automatically:
- Create a Python virtual environment (`venv`).
- Install PyTorch, DirectML, and all other dependencies in the correct order.
- Verify the installation.

## 🛠️ Manual Setup

If you prefer to set it up yourself, run these commands in a terminal (PowerShell or Command Prompt):

```powershell
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the environment
.\venv\Scripts\activate

# 3. Install dependencies (Order is important!)
pip install torch torchvision torchaudio
pip install torch-directml
pip install -r requirements.txt
```

## 🏃‍♂️ Running the Engine

Once setup is complete, you can start the server:

```powershell
# Make sure your virtual environment is activated
.\venv\Scripts\activate

# Run the server
python run.py
```

The server will start at `http://localhost:8000`.
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🧪 Verify Installation

To check if everything is working correctly, you can run the model load test:

```powershell
python test_model_load.py
```
