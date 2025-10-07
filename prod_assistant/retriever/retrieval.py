import os
from langchain_astradb import AstraDBVectorStore
from typing import List
from langchain_core.documents import Document
from graph_retriever.strategies import Eager
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

from langchain_graph_retriever import GraphRetriever
from prod_assistant.utils.config_loader import load_config
from prod_assistant.utils.model_loader import ModelLoader
from dotenv import load_dotenv
import sys
from pathlib import Path
from prod_assistant.evaluation.ragas_eval import evaluate_context_precision, evaluate_response_relevancy
# Add the project root to the Python path for direct script execution
# project_root = Path(__file__).resolve().parents[2]
# sys.path.insert(0, str(project_root))

class Retriever:
    def __init__(self):
        """Initialize the Retriever class.
        """
        self.model_loader=ModelLoader()
        self.config=load_config()
        self.load_env_variables()
        self.vstore = None
        self.retriever = None
    
    def load_env_variables(self):
        """Load environment variables for the retriever.
        """
        load_dotenv()
         
        required_vars = ["GOOGLE_API_KEY", "ASTRA_DB_API_ENDPOINT", "ASTRA_DB_APPLICATION_TOKEN", "ASTRA_DB_KEYSPACE"]
        
        missing_vars = [var for var in required_vars if os.getenv(var) is None]
        
        if missing_vars:
            raise EnvironmentError(f"Missing environment variables: {missing_vars}")

        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.db_api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        self.db_application_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        self.db_keyspace = os.getenv("ASTRA_DB_KEYSPACE")
    
    
    def load_retriever(self):
        """Load the retriever model.
        """
        if not self.vstore:
            collection_name = self.config["astra_db"]["collection_name"]
            
            self.vstore = AstraDBVectorStore(
                embedding= self.model_loader.load_embeddings(),
                collection_name=collection_name,
                api_endpoint=self.db_api_endpoint,
                token=self.db_application_token,
                namespace=self.db_keyspace,
                )
        if not self.retriever:
            top_k = self.config["retriever"]["top_k"] if "retriever" in self.config else 3
            retriever = GraphRetriever(store=self.vstore,
                edges=[("product", "product_title"), ("price", "price"), ("rating", "rating"), ("reviews", "total_reviews")],
                strategy=Eager(k=top_k, start_k=1, max_depth=2),
            )
            # retriever=self.vstore.as_retriever(search_kwargs={"k": top_k})
            llm = self.model_loader.load_llm()
            compressor = LLMChainExtractor.from_llm(llm)
            self.retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=retriever
            )
            print("Retriever loaded successfully.")
            return self.retriever
    
    def call_retriever(self,query):
        """Call the retriever model.
        """
        retriever=self.load_retriever()
        output=retriever.invoke(query)
        return output

if __name__ == "__main__":
    user_query = "What is the price and rating of Apple iPhone 14 Pro Max?"
    
    retriever_obj = Retriever()

    retrieved_docs = retriever_obj.call_retriever(user_query)
    print(retrieved_docs)

    def _format_docs(docs) -> str:
        if not docs:
            return "No relevant documents found."
        formatted_chunks = []
        for d in docs:
            meta = d.metadata or {}
            formatted = (
                f"Title: {meta.get('product_title', 'N/A')}\n"
                f"Price: {meta.get('price', 'N/A')}\n"
                f"Rating: {meta.get('rating', 'N/A')}\n"
                f"Reviews:\n{d.page_content.strip()}"
            )
            formatted_chunks.append(formatted)
        return "\n\n---\n\n".join(formatted_chunks)
    
    retrieved_contexts = [_format_docs(retrieved_docs)]
    print(retrieved_contexts)
    
    #this is not an actual output this have been written to test the pipeline
    response="The price of Apple iPhone 14 Pro Max (Gold, 256 GB) is 144900. It has a rating of 4.6 out of 5 based on 166 reviews."
    
    context_score = evaluate_context_precision(user_query,response,retrieved_contexts)
    relevancy_score = evaluate_response_relevancy(user_query,response,retrieved_contexts)
    
    print("\n--- Evaluation Metrics ---")
    print("Context Precision Score:", context_score)
    print("Response Relevancy Score:", relevancy_score)
    