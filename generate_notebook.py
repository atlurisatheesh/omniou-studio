import nbformat as nbf
from pathlib import Path

def create_notebook():
    nb = nbf.v4.new_notebook()

    # Introduction
    nb['cells'].append(nbf.v4.new_markdown_cell("""# 🚀 CloneAI Pro - Cloud GPU Render Engine (Phase 1)
Welcome to the Cloud GPU development environment for CloneAI.
This notebook will allow you to generate identity-locked videos using free T4/P100 GPUs on Kaggle or Google Colab.

**Setup Instructions:**
1. Upload this notebook to Google Colab (`colab.research.google.com`) or Kaggle.
2. In Colab, go to `Runtime` -> `Change runtime type` -> Select `T4 GPU`.
3. Run the cells below!"""))

    # Step 1: System Specs
    nb['cells'].append(nbf.v4.new_code_cell("""# 1. Verify GPU Allocation
!nvidia-smi"""))

    # Step 2: Install Base Dependencies
    nb['cells'].append(nbf.v4.new_markdown_cell("""### 🛠️ Step 2: Install ML Dependencies
Installs Torch (CUDA 12.1), InsightFace, and video processing tools. (~3 minutes)"""))
    
    nb['cells'].append(nbf.v4.new_code_cell("""# Install PyTorch for CUDA
!pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install heavy ML packages
!pip install insightface onnxruntime-gpu basicsr facexlib realesrgan gfpgan librosa soundfile imageio imageio-ffmpeg structlog fastapi uvicorn pydantic

# Install system dependencies (ffmpeg for video compiling)
!apt-get update && apt-get install -y ffmpeg"""))

    # Step 3: Download Models
    nb['cells'].append(nbf.v4.new_markdown_cell("""### 📥 Step 3: Download AI Models
This downloads all the necessary model weights (~5GB) for GFPGAN, LivePortrait, and MuseTalk."""))
    
    nb['cells'].append(nbf.v4.new_code_cell("""import os

# Create models directory
os.makedirs("models/insightface", exist_ok=True)
os.makedirs("models/gfpgan", exist_ok=True)

print("Downloading GFPGAN...")
!wget -nc -O models/gfpgan/GFPGANv1.4.pth https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth

# Note: Insightface models usually download automatically on first run, 
# but we ensure the environment variable points to our cache dir.
os.environ["INSIGHTFACE_HOME"] = os.path.abspath("models/insightface")
print("Models directory prepared.")"""))

    # Step 4: Clone the Backend Logic
    nb['cells'].append(nbf.v4.new_markdown_cell("""### 📂 Step 4: Upload Your Local Workspace
To use your custom exact logic, zip up your `backend/app` folder from your local PC and upload it here using the Colab file explorer, OR run the cell below to upload it via UI constraint."""))
    
    nb['cells'].append(nbf.v4.new_code_cell("""from google.colab import files
import zipfile
import os

print("Please zip your 'backend' folder and upload it here:")
uploaded = files.upload()

for filename in uploaded.keys():
    if filename.endswith('.zip'):
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall("cloneai_backend")
        print(f"Extracted {filename} to cloneai_backend/")
"""))

    # Step 5: Test Generation
    nb['cells'].append(nbf.v4.new_markdown_cell("""### 🎬 Step 5: Direct Generation Test
We will test the absolute raw pipeline by passing a dummy image and audio to verify GPU rendering works."""))
    
    nb['cells'].append(nbf.v4.new_code_cell("""import sys
sys.path.append("cloneai_backend")

# Try to import pipeline orchestrator
try:
    from app.services.pipeline import PipelineOrchestrator
    print("✅ Successfully loaded CloneAI Pipeline!")
    
    # Initialize Pipeline
    pipeline = PipelineOrchestrator(device="cuda", model_cache_dir="models")
    
    # NOTE: You need to upload a 'test_photo.jpg' and 'test_voice.wav' to colab first!
    print("\\nReady to render! Make sure 'test_photo.jpg' and 'test_voice.wav' are in the files tab.")
    
except ImportError as e:
    print(f"❌ Failed to import your backend code: {e}")
    print("Ensure you uploaded the zip file and it extracts to have 'app/services/pipeline.py'")"""))

    # Write notebook
    notebook_dir = Path("notebooks")
    notebook_dir.mkdir(exist_ok=True)
    out_path = notebook_dir / "CloneAI_Cloud_Dev.ipynb"
    
    with open(out_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
        
    print(f"Notebook successfully created at {out_path}")

if __name__ == "__main__":
    create_notebook()
