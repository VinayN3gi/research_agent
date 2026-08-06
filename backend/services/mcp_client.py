import uuid
import json
from typing import Dict, Any, List
from models import Document
from utils.logger import get_logger

logger = get_logger("mcp_client")

class MCPClientMock:
    def __init__(self):
        # Mock discovering tools
        self.available_tools = {
            "github_search": "Search github repositories and issues",
            "sqlite_query": "Run SQL query on local sqlite database",
            "confluence_search": "Search corporate wiki"
        }

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> List[Document]:
        """
        Simulates sending a tool_call via Model Context Protocol to an external server.
        Returns a list of parsed Documents.
        """
        logger.info(f"MCP Client: Executing {tool_name} with args {args}")
        
        # In a real MCP client, this would connect over stdio or SSE to an MCP server,
        # send the JSON-RPC tool_call, and await the response.
        
        # We will mock the response based on the tool
        mock_text = f"Mocked MCP output from external server for tool {tool_name}. "
        if "query" in args:
            mock_text += f"Query was: {args['query']}. "
            
        if tool_name == "github_search":
            mock_text += "Found 3 relevant PRs discussing this architecture."
        elif tool_name == "confluence_search":
            mock_text += "Found a Confluence page detailing the internal design."
        elif tool_name == "sqlite_query":
            mock_text += "Returned 5 rows from the user_metrics table."
        else:
            mock_text += "Generic external tool response."
            
        doc = Document(
            id=f"mcp://{tool_name}/{uuid.uuid4().hex[:8]}",
            title=f"MCP Integration: {tool_name}",
            source_type="mcp_tool",
            text=mock_text,
            metadata={"args": args}
        )
        return [doc]

# Singleton instance
mcp_client = MCPClientMock()
