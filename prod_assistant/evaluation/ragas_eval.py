
from prod_assistant.utils.model_loader import ModelLoader
from ragas import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingWrapper
from ragas.metrics import LLMContextPrecisionWithoutReference, ResponseRelevancy
import grpc.experimental.aio as grpc_aio
grpc_aio.init_grpc_aio()
model_loader  = ModelLoader()

def evaluate_context_precision():
    """
    Evaluate LLM's ability to utilize provided context without hallucinating.
    """
    pass

def evaluate_response_relevancy(query: str):
    """
    Evaluate LLM's ability to provide accurate and relevant responses.
    """
    pass