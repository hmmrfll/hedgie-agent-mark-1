# src/tools/ollama_handler.py

import logging
import subprocess
import json
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class OllamaHandler:
    """Обработчик запросов к локальной модели Ollama"""
    
    def __init__(self, model_name: str = "llama3"):
        """
        Инициализация обработчика
        
        Args:
            model_name (str): Название модели Ollama для использования
        """
        self.model_name = model_name
        self.base_url = "http://localhost:11434/api"
        
        # Проверяем, запущен ли Ollama
        self._check_ollama_running()
        
    def _check_ollama_running(self) -> bool:
        """Проверяет, запущен ли сервер Ollama"""
        try:
            response = requests.get(f"{self.base_url}/tags")
            if response.status_code == 200:
                # Проверяем, есть ли нужная модель
                models = response.json().get("models", [])
                model_exists = any(self.model_name in model.get("name", "") for model in models)
                
                if not model_exists:
                    logger.warning(f"Модель {self.model_name} не найдена в Ollama. Попытка загрузить...")
                    self._pull_model()
                
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке Ollama: {e}")
            return False
    
    def _pull_model(self) -> bool:
        """Загружает модель, если её нет"""
        try:
            logger.info(f"Загрузка модели {self.model_name}...")
            subprocess.run(["ollama", "pull", self.model_name], check=True)
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {e}")
            return False
    
    def is_available(self) -> bool:
        """Проверка доступности Ollama"""
        try:
            response = requests.get(f"{self.base_url}/tags")
            return response.status_code == 200
        except:
            return False
    
    def get_answer(self, question: str, analysis_data: Dict[str, Any]) -> str:
        """
        Получить ответ от локальной модели на вопрос по аналитике
        
        Args:
            question (str): Вопрос пользователя
            analysis_data (Dict[str, Any]): Данные анализа
            
        Returns:
            str: Ответ от модели или сообщение об ошибке
        """
        if not self.is_available():
            return "❌ Локальная модель недоступна. Убедитесь, что Ollama запущен командой 'ollama serve'."
            
        try:
            # Формируем контекст с данными анализа
            context = self._format_analysis_context(analysis_data)
            
            # Формируем запрос к модели
            prompt = (
                "Ты - ассистент по криптовалютной аналитике. Давай подробные и понятные ответы "
                "на вопросы, основываясь только на предоставленных данных анализа. "
                f"\n\nВот результаты анализа:\n{context}\n\nВопрос: {question}\n\n"
                "Дай детальный и точный ответ на вопрос, используя только информацию из предоставленного анализа."
            )
            
            # Отправляем запрос к Ollama API
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1000
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Не удалось получить ответ от модели")
            else:
                return f"❌ Ошибка при запросе к модели: {response.status_code} - {response.text}"
                
        except Exception as e:
            logger.error(f"Ошибка при запросе к Ollama: {e}")
            return f"❌ Произошла ошибка при обработке вопроса: {str(e)}"
    
    def _format_analysis_context(self, analysis_data: Dict[str, Any]) -> str:
        """
        Форматирование данных анализа в текстовый контекст для модели
        
        Args:
            analysis_data (Dict[str, Any]): Данные анализа
            
        Returns:
            str: Форматированный контекст
        """
        currency = analysis_data.get('currency', 'Криптовалюта')
        current_price = analysis_data.get('current_price', 'Н/Д')
        
        context = f"АНАЛИЗ {currency} (текущая цена: ${current_price})\n\n"
        
        # Опционный анализ
        context += "ОПЦИОННЫЙ АНАЛИЗ:\n"
        context += f"- CALL/PUT соотношение: {analysis_data.get('call_put_ratio', 'Н/Д')}\n"
        context += f"- Общая дельта: {analysis_data.get('total_delta', 'Н/Д')}\n"
        context += f"- Опционное настроение: {analysis_data.get('option_sentiment', 'Н/Д')}\n"
        
        # Основные стратегии
        strategies_data = analysis_data.get('strategies_data', {})
        if strategies_data:
            context += "- Основные стратегии: "
            strategies_summary = []
            for strategy, volume in sorted(strategies_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                strategies_summary.append(f"{strategy} ({volume:.1f})")
            context += ", ".join(strategies_summary) + "\n"
        
        # Технический анализ
        context += "\nТЕХНИЧЕСКИЙ АНАЛИЗ:\n"
        context += f"- Тренд: {analysis_data.get('trend', 'Н/Д')}\n"
        context += f"- RSI: {analysis_data.get('rsi_value', 'Н/Д')} ({analysis_data.get('rsi_signal', 'Н/Д')})\n"
        context += f"- MACD: {analysis_data.get('macd_signal', 'Н/Д')}\n"
        context += f"- Общий технический сигнал: {analysis_data.get('technical_signal', 'Н/Д')}\n"
        
        # Риск-менеджмент
        context += "\nРИСК-МЕНЕДЖМЕНТ:\n"
        context += f"- VaR (95%): {analysis_data.get('var_value', 'Н/Д')}%\n"
        context += f"- Волатильность: {analysis_data.get('volatility', 'Н/Д')}%\n"
        context += f"- Уровень риска: {analysis_data.get('risk_level', 'Н/Д')}\n"
        context += f"- Рекомендуемый стоп-лосс: ${analysis_data.get('stop_loss_price', 'Н/Д')}\n"
        context += f"- Рекомендуемый тейк-профит: ${analysis_data.get('take_profit_price', 'Н/Д')}\n"
        
        # Рекомендация
        context += "\nРЕКОМЕНДАЦИЯ:\n"
        context += f"- {analysis_data.get('recommendation', 'Н/Д')}\n"
        
        # Заключение (если есть)
        conclusion = analysis_data.get('conclusion', '')
        if conclusion:
            context += "\nЗАКЛЮЧЕНИЕ:\n"
            context += conclusion
        
        return context