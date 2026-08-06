from abc import ABC, abstractmethod
from typing import Dict, List, Any
from models import Document
from utils.logger import get_logger

logger = get_logger("plugins")

class Connector(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the connector, e.g., 'github' or 'google_drive'."""
        pass

    @abstractmethod
    def capabilities(self) -> List[str]:
        """List of capabilities, e.g., ['search', 'fetch', 'execute']."""
        pass

    @abstractmethod
    async def search(self, query: str) -> List[str]:
        """Search the external system and return a list of Document IDs or URLs."""
        pass

    @abstractmethod
    async def fetch(self, doc_id: str) -> Document:
        """Fetch a specific document from the external system."""
        pass

    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """Execute a specific action, e.g., 'clone' repo."""
        pass

    @abstractmethod
    async def health(self) -> bool:
        """Check if the connector is healthy and authenticated."""
        pass

class ConnectorRegistry:
    def __init__(self):
        self._connectors: Dict[str, Connector] = {}
        
    def register(self, connector: Connector):
        logger.info(f"Registering Connector: {connector.name}")
        self._connectors[connector.name] = connector
        
    def get(self, name: str) -> Connector:
        if name not in self._connectors:
            raise ValueError(f"Connector {name} not found in registry.")
        return self._connectors[name]
        
    def list_connectors(self) -> List[str]:
        return list(self._connectors.keys())

# Global registry instance
registry = ConnectorRegistry()
