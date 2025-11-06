from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import CachePolicy
from langgraph.cache.memory import InMemoryCache

from prod_assistant.prompt_library.prompts import PROMPT_REGISTRY, PromptType
from prod_assistant.retriever.retrieval import Retriever
from prod_assistant.utils.model_loader import ModelLoader
from prod_assistant.evaluation.ragas_eval import evaluate_context_precision, evaluate_response_relevancy
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

class AgenticRAG:
    """Proper Agentic RAG using LangGraph's ToolNode and tools_condition."""

    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        revision_count: int # To track number of rewrites
        max_revision_count: int # To limit the number of rewrites

    def __init__(self):
        self.retriever = Retriever().load_retriever()  # Initialize once
        self.model_loader = ModelLoader()
        self.llm = self.model_loader.load_llm()
        self.checkpointer = MemorySaver()
        
        # MCP Client Init
        client_config_for_stdio = {
            "hybrid_search": {
                "command": "python",
                "args": ["prod_assistant/mcp_servers/product_search_server.py"],
                "transport": "stdio"
            }
        }
        
        client_config_for_http = {
            "hybrid_search": {
                "transport": "streamable_http",
                "url": "http://localhost:8000/mcp/"
            }
        }
    
        self.mcp_client = MultiServerMCPClient(client_config_for_http)
        
        self.mcp_tools = None
        self.llm_with_tools = None
        self.workflow = None
        self.app = None
        
        
    # Add a async factory method to initialize async components
    @classmethod
    async def async_init(cls):
        instance = cls()
        instance.mcp_tools = await instance.mcp_client.get_tools()
        instance.llm_with_tools = instance.llm.bind_tools(instance.mcp_tools)
        instance.workflow = instance._build_workflow()
        instance.app = instance.workflow.compile(checkpointer=instance.checkpointer, cache=InMemoryCache())
        return instance

    
    # ---------- Helpers ----------
    def _format_docs(self, docs) -> str:
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

    # ---------- Nodes ----------
    async def _assistant(self, state: AgentState):
        print("--- ASSISTANT ---")
        messages = state["messages"]
        
        system_prompt = """You are a helpful e-commerce assistant. 
        Use the retrieve_product_info tool when users ask about products, prices, or reviews.
        Otherwise, if the user asks about billing, shipping, returns or other ecommerce related topics, respond 'I'm sorry, but I can't assist with that.'.
        For any other off topic queries, gently inform the user that you can only assist with e-commerce related questions."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{messages}")
        ])
        
        chain = prompt | self.llm_with_tools
        response = await chain.ainvoke({"messages": messages})
        print(f"Assistant Response: {response}")
        return {"messages": [response]}

    async def _generate_response(self, state: AgentState):
        print("--- GENERATE ---")
        messages = state["messages"]
        context = messages[-1].content
            
        question = messages[0].content
        prompt = ChatPromptTemplate.from_template(
            PROMPT_REGISTRY[PromptType.PRODUCT_BOT].template
        )
        
        chain = prompt | self.llm | StrOutputParser()
        response = await chain.ainvoke({"context": context, "question": question})
        print(f"Generated Response: {response}")
        return {"messages": [AIMessage(content=response)]}

    async def _grade_documents(self, state: AgentState) -> Literal["generate", "rewrite"]:
        print("--- GRADER ---")
        question = state["messages"][0].content
        docs = state["messages"][-1].content
        current_count = state.get("revision_count", 0)

        prompt = PromptTemplate(
            template="""You are a grader. Question: {question}\nDocs: {docs}\n
            Are docs relevant to the question? Answer yes or no.""",
            input_variables=["question", "docs"],
        )
        chain = prompt | self.llm | StrOutputParser()
        score = await chain.ainvoke({"question": question, "docs": docs})
        
        print(f"Revision count: {current_count}/{state.get('max_revision_count', 2)}")
        
        if "yes" in score.lower():
            print("Documents are relevant. Moving to generate.")
            return "generate"
        elif current_count >= state.get("max_revision_count", 2):
            print("Max revisions reached. Moving to generate.")
            state["messages"].append(AIMessage(content="No relevant documents found. Proceeding with best effort response."))
            return "generate"
        else:
            print("Documents not relevant. Rewriting query.")
            return "rewrite"
    
    async def _rewrite(self, state: AgentState):
        print("--- REWRITE ---")
        question = state["messages"][0].content
        current_count = state.get("revision_count", 0)
        
        new_q = await self.llm.ainvoke(
            [HumanMessage(content=f"Rewrite the query to be clearer. \
                          Specifically, include that the user is looking for information about product features, price, reviews and ratings: {question}")]
        )
        print(f"Rewritten Query: {new_q.content}")
        return {
            "messages": [HumanMessage(content=new_q.content)],
            "revision_count": current_count + 1
        }

    # ---------- Build Workflow ----------
    def _build_workflow(self):
        workflow = StateGraph(self.AgentState)
        
        # Add nodes
        workflow.add_node("assistant", self._assistant)
        workflow.add_node("tools", ToolNode(self.mcp_tools), cache_policy=CachePolicy(ttl=120),)
        workflow.add_node("generate", self._generate_response)
        workflow.add_node("rewrite", self._rewrite)
        
        # Add edges
        workflow.add_edge(START, "assistant")
        
        # Use tools_condition for automatic routing
        workflow.add_conditional_edges(
            "assistant",
            tools_condition,
            {
                "tools": "tools",
                END: END
            }
        )
        
        # Edges taken after the `action` node is called.
        workflow.add_conditional_edges(
            "tools",
            self._grade_documents,
            {"generate": "generate", "rewrite": "rewrite"},
        )
        
        workflow.add_edge("rewrite", "assistant")
        workflow.add_edge("generate", END)
        
        return workflow

    # ---------- Public Run ----------
    async def run(self, query: str, thread_id : str = "default_thread") -> str:
        """Run the workflow for a given query."""
        result = await self.app.ainvoke({"messages": [HumanMessage(content=query)]},
                                 config = {"recursion_limit": 10,"configurable": {"thread_id" : thread_id}})  # Pass thread_id for checkpointing
        return result["messages"][-1].content

        # Future enhancement:
        # function call to ragas evaluation functions
        # evaluate_context_precision(query, response, retrieved_context)
        # evaluate_response_relevancy(query, response, retrieved_context)
        # based on the score from ragas evaluation
        # if score is less than threshold
        # rewrite the query and call the retriever again
        # else
        # return the response


if __name__ == "__main__":

    async def main():
        user_query = "What is the price and rating of Apple iPhone 14 Pro Max?"
        rag_agent = await AgenticRAG.async_init()
        response = await rag_agent.run(user_query)
        return response
    
    response = asyncio.run(main())
    print(response)