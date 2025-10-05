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
    retriever_obj = Retriever()
    user_query = "What is the price of Apple iPhone 15 Pro Max?"
    results = retriever_obj.call_retriever(user_query)
    
    for idx, doc in enumerate(results):
        print(f"Results{idx}: {doc.page_content}\n Metadata: {doc.metadata}\n")