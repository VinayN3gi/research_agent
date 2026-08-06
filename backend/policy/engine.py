from utils.logger import get_logger

logger = get_logger("policy")

class PolicyEngine:
    def __init__(self):
        # Extremely basic static ruleset for MVP
        self.allowed_tools = ["web_search", "github", "reddit", "arxiv"]
        self.blocked_queries = ["confidential", "internal", "secret", "password", "api_key"]

    def evaluate_tool_call(self, tool_name: str, query: str) -> bool:
        """
        Intercepts a tool call and evaluates if it violates system policy.
        Returns True if allowed, False if blocked.
        """
        logger.info(f"Policy Engine evaluating: {tool_name} -> {query}")
        
        # 1. Check Tool Allowlist
        if tool_name not in self.allowed_tools:
            logger.warning(f"Policy Engine BLOCKED tool '{tool_name}' (not in allowlist).")
            return False
            
        # 2. Check Query for Sensitive Data
        query_lower = query.lower()
        for blocked_word in self.blocked_queries:
            if blocked_word in query_lower:
                logger.warning(f"Policy Engine BLOCKED query (contains sensitive word: '{blocked_word}').")
                return False
                
        logger.info("Policy Engine ALLOWED execution.")
        return True

# Global singleton
engine = PolicyEngine()
