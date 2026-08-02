from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings

def setup_splitter():
    Settings.text_splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
