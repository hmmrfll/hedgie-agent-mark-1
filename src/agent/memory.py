# src/agent/memory.py

from typing import Dict, Any, List
from datetime import datetime

class Memory:
    def __init__(self):
        self.short_term = {}  # Текущая сессия
        self.context = {}     # Текущий контекст
        self.history = []     # История действий

    def update_context(self, data: Dict[str, Any]):
        """Обновление текущего контекста"""
        self.context.update(data)
        self._add_to_history("context_update", data)

    def get_context(self) -> Dict[str, Any]:
        """Получение текущего контекста"""
        return self.context

    def _add_to_history(self, action: str, data: Any):
        """Добавление действия в историю"""
        self.history.append({
            'timestamp': datetime.now(),
            'action': action,
            'data': data
        })

    def get_history(self) -> List[Dict]:
        """Получение истории действий"""
        return self.history

    def clear_session(self):
        """Очистка данных текущей сессии"""
        self.short_term.clear()