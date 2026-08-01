from llama_index.core import SimpleDirectoryReader
import os

def load_document(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return SimpleDirectoryReader(input_files=[file_path]).load_data()
