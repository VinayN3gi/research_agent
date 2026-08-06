import os
import json
from typing import Dict, List
from utils.logger import get_logger

logger = get_logger("memory")

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "data", "tool_performance.json")

class AgentMemory:
    def __init__(self):
        self.performance: Dict[str, Dict[str, float]] = {}
        self._load()

    def _load(self):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    self.performance = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load agent memory: {e}")

    def _save(self):
        try:
            with open(MEMORY_FILE, "w") as f:
                json.dump(self.performance, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save agent memory: {e}")

    def record_tool_success(self, topic: str, tool: str, score: float):
        """
        Record how well a specific tool performed for a given topic.
        score: 0.0 to 1.0
        """
        topic = topic.lower()
        if topic not in self.performance:
            self.performance[topic] = {}
        
        # Exponential moving average for score
        current_score = self.performance[topic].get(tool, 0.5)
        new_score = (current_score * 0.7) + (score * 0.3)
        self.performance[topic][tool] = new_score
        self._save()
        logger.info(f"Memory updated: {topic} -> {tool} ({new_score:.2f})")

    def get_recommended_tools(self, topic: str) -> List[str]:
        """
        Return a list of recommended tools for a topic, sorted by performance.
        """
        topic = topic.lower()
        if topic not in self.performance:
            return ["web_search"] # Default fallback
            
        tools = self.performance[topic]
        # Sort tools by descending score
        sorted_tools = sorted(tools.items(), key=lambda item: item[1], reverse=True)
        return [t[0] for t in sorted_tools]

# Global singleton
memory = AgentMemory()
