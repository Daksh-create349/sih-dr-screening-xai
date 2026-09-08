"""Hugging Face Spaces entry point mounting FastAPI screening engine with Gradio."""

import os
import sys
from pathlib import Path

# Ensure DR workspace root in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import gradio as gr
from api.main import app as fastapi_app

# Interactive Status Page on Space Root
with gr.Blocks(title="RetinaScan AI - Tele-Screening Backend Engine") as demo:
    gr.Markdown("# 👁️ RetinaScan-AI: Clinical-Grade Tele-Screening Engine")
    gr.Markdown("### Smart India Hackathon 2026 | PS 26038 (MathWorks India)")
    gr.Markdown(
        "Autonomous Diabetic Retinopathy tele-screening engine running live.\n\n"
        "- 🩺 **Health Check:** [`/api/health`](/api/health)\n"
        "- 📄 **Swagger Interactive API Documentation:** [`/docs`](/docs)\n"
        "- 🔬 **Classifier:** EfficientNet-B3 v2 (80.3% Validated Accuracy)\n"
        "- 🧬 **Lesion Segmentation:** IDRiD Triple U-Net ResNet34\n"
        "- 💻 **PACS Frontend Workstation:** Live on Vercel"
    )

# Mount Gradio onto the existing FastAPI application
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
