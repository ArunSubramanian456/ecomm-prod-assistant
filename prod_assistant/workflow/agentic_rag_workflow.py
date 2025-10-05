from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from prod_assistant.prompt_library.prompts import PROMPT_REGISTRY, PromptType
from prod_assistant.retriever.retrieval import Retriever
from prod_assistant.utils.model_loader import ModelLoader


class AgenticRAG:
    """Proper Agentic RAG using LangGraph's ToolNode and tools_condition."""

    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]

    def __init__(self):
        self.retriever = Retriever().load_retriever()  # Initialize once
        self.model_loader = ModelLoader()
        self.llm = self.model_loader.load_llm()
        self.checkpointer = MemorySaver()
        self.tools = self._create_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)

    def _create_tools(self):
        @tool
        def retrieve_product_info(query: str) -> str:
            """Retrieve product information including prices, reviews, and details."""
            docs = self.retriever.invoke(query)
            return self._format_docs(docs)
        
        return [retrieve_product_info]

    
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
    def _assistant(self, state: AgentState):
        print("--- ASSISTANT ---")
        messages = state["messages"]
        
        system_prompt = """You are a helpful e-commerce assistant. 
        Use the retrieve_product_info tool when users ask about products, prices, or reviews.
        Otherwise, respond directly to general questions."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{messages}")
        ])
        
        chain = prompt | self.llm_with_tools
        response = chain.invoke({"messages": messages})
        return {"messages": [response]}

    def _generate_response(self, state: AgentState):
        print("--- GENERATE ---")
        messages = state["messages"]
        context = messages[-1].content
        
        question = messages[0].content
        prompt = ChatPromptTemplate.from_template(
            PROMPT_REGISTRY[PromptType.PRODUCT_BOT].template
        )
        
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({"context": context, "question": question})
        return {"messages": [AIMessage(content=response)]}
    
    def _grade_documents(self, state: AgentState) -> Literal["generator", "rewriter"]:
        print("--- GRADER ---")
        question = state["messages"][0].content
        docs = state["messages"][-1].content

        prompt = PromptTemplate(
            template="""You are a grader. Question: {question}\nDocs: {docs}\n
            Are docs relevant to the question? Answer yes or no.""",
            input_variables=["question", "docs"],
        )
        chain = prompt | self.llm | StrOutputParser()
        score = chain.invoke({"question": question, "docs": docs})
        return "generator" if "yes" in score.lower() else "rewriter"
    
    def _rewrite(self, state: AgentState):
        print("--- REWRITE ---")
        question = state["messages"][0].content
        new_q = self.llm.invoke(
            [HumanMessage(content=f"Rewrite the query to be clearer: {question}")]
        )
        return {"messages": [AIMessage(content=new_q.content)]}

    # ---------- Build Workflow ----------
    def _build_workflow(self):
        workflow = StateGraph(self.AgentState)
        
        # Add nodes
        workflow.add_node("assistant", self._assistant)
        workflow.add_node("tools", ToolNode(self.tools))
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
            # Assess agent decision
            self._grade_documents,
            {"generator": "generate", "rewriter": "rewrite"},
        )
        
        workflow.add_edge("rewrite", "assistant")
        workflow.add_edge("generate", END)
        
        return workflow

    # ---------- Public Run ----------
    def run(self, query: str, thread_id : str = "default_thread") -> str:
        """Run the workflow for a given query."""
        result = self.app.invoke({"messages": [HumanMessage(content=query)]},
                                 config = {"configurable": {"thread_id" : thread_id}})  # Pass thread_id for checkpointing
        return result["messages"][-1].content


if __name__ == "__main__":
    rag_agent = AgenticRAG()
    answer = rag_agent.run("What is the price of Vivo T4?")
    print("\nFinal Answer:\n", answer)