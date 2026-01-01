import os

from langchain_community.agent_toolkits.load_tools import load_tools
from smolagents import (LiteLLMModel, CodeAgent, Tool, DuckDuckGoSearchTool, ToolCollection, GradioUI)

model = LiteLLMModel(model_id=os.getenv("OLLAMA_MODEL", "ollama_chat/llama3.2"),
                     api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), api_key="", )

search_tool = DuckDuckGoSearchTool(5)
searx_tool = Tool.from_langchain(
    load_tools(["searx-search"], searx_host="http://192.168.213.60:8180", num_results=5)[0]
)

with ToolCollection.from_mcp({"url": "http://192.168.213.60:3333/mcp", "transport": "streamable-http"},
                             trust_remote_code=True, structured_output=True) as gitlab_tools:

    agent = CodeAgent(tools=[*gitlab_tools.tools], model=model, planning_interval=3,
                      use_structured_outputs_internally=True)

    gradio_ui = GradioUI(agent)
    gradio_ui.launch(False)
