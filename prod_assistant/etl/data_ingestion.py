import os
import pandas as pd
from dotenv import load_dotenv
from typing import List
from langchain_core.documents import Document
from langchain_astradb import AstraDBVectorStore
from prod_assistant.utils.model_loader import ModelLoader
from prod_assistant.utils.config_loader import load_config


class DataIngestion:
    """
    Class to handle data ingestion into AstraDB vector database.
    """

    def __init__(self):
        """
        Initialize the DataIngestion class.
        """
        pass

    def _load_env_variables(self):
        """
        Load environment variables
        """
        pass

    def _get_csv_path(self):
        """
        Get the CSV file path from configuration.
        """
        pass

    def _load_csv(self):
        """
        Load data from CSV file.
        """
        pass

    def transform_data(self):
        """
        Transform the loaded data.
        """
        pass

    def store_in_vector_db(self):
        """
        Store the transformed data in the vector database.
        """
        pass

    def run_pipeline(self):
        pass
    
