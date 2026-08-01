from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.llms.mock import MockLLM
from llama_index.core import Settings
from .vectorstore import get_vector_store
from .utils import enrich_metadata, build_memory_block

class RAGRetriever:
    def __init__(self):
        # We don't need a real LLM since Engineer 1 only extracts chunks
        Settings.llm = MockLLM()
        self.vector_store = None
        self.storage_context = None
        self.index = None

    def load_index(self):
        if not self.vector_store:
            self.vector_store = get_vector_store()
            self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        if not self.index:
            self.index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)

    def retrieve_context(self, query_string: str, domain_filters: list = None) -> dict:
        try:
            self.load_index()
            retriever = self.index.as_retriever(similarity_top_k=5)
            nodes = retriever.retrieve(query_string)
            
            results = []
            for node in nodes:
                results.append({
                    "text": node.node.text,
                    "score": float(node.score) if node.score else 0.0,
                    "source": node.node.metadata.get("file_name", "unknown")
                })
                
            formatted_knowledge = {
                "total_chunks_retrieved": len(results),
                "chunks": results
            }
        except Exception as e:
            formatted_knowledge = {"error": f"Index error: {str(e)}"}
            
        return {
            "original_prompt": query_string,
            "retrieved_knowledge": formatted_knowledge,
            "metadata": enrich_metadata(domain_filters),
            "memory": build_memory_block()
        }

rag_retriever = RAGRetriever()
