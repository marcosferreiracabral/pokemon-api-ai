from abc import ABC, abstractmethod
from typing import List, Optional, Any

class BaseRepository(ABC):
    """
    Interface base para repositórios.
    Define contratos genéricos para operações de dados.
    """
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def get_all(self, limit: int = 10, offset: int = 0) -> List[Any]:
        pass
