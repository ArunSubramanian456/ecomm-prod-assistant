import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

async def main():
    
    # client_config_for_stdio = {
    #     "hybrid_search": {
    #         "command": "python",
    #         "args": [r"C:\Users\aruns\Documents\Learning\LLMOps\ecomm-prod-assistant\prod_assistant\mcp_servers\product_search_server.py"],
    #         "transport": "stdio"
    #     }
    # }
    
    client_config_for_http = {
        "hybrid_search": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp/"
        }
    }
            
    client = MultiServerMCPClient(client_config_for_http)

    tools = await client.get_tools()
    print("Available tools:", [t.name for t in tools])

    # Pick tools by name
    retriever_tool = next(t for t in tools if t.name == "get_product_info")
    web_tool = next(t for t in tools if t.name == "web_search")

    # --- Step 1: Try retriever first ---
    query = "What is the price and rating of Apple iPhone 17?"
    # query = "What is the price and rating of Apple iPhone 17?"
        
    retriever_result = await retriever_tool.ainvoke({"query": query})
    print("\nRetriever Result:\n", retriever_result)

    # --- Step 2: Fallback to web search if retriever fails ---
    if not retriever_result.strip() or "No local results found." in retriever_result:
        print("\n No local results, falling back to web search...\n")
        web_result = await web_tool.ainvoke({"query": query})
        print("Web Search Result:\n", web_result)
    

if __name__ == "__main__":
    asyncio.run(main())