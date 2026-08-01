from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import torch

def setup_embeddings():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5", 
        device=device
    )
