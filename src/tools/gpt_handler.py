# src/tools/gpt_handler.py

import os
import logging
from typing import Dict, Any, List
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class GPTHandler:
    """Обработчик запросов к OpenAI GPT API"""
    
    def __init__(self, api_key: str = None):
        """
        Инициализация обработчика
        
        Args:
            api_key (str, optional): API ключ OpenAI, если не указан, берется из переменной среды OPENAI_API_KEY
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("API ключ OpenAI не указан, GPT функциональность будет недоступна")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
            
    def is_available(self) -> bool:
        """Проверка доступности GPT"""
        return self.client is not None
    
    def get_answer(self, question: str, analysis_data: Dict[str, Any]) -> str:
        """
        Получить ответ от GPT на вопрос по аналитике
        
        Args:
            question (str): Вопрос пользователя
            analysis_data (Dict[str, Any]): Данные анализа
            
        Returns:
            str: Ответ от GPT или сообщение об ошибке
        """
        if not self.is_available():
            return "❌ Интеграция с GPT недоступна. Обратитесь к администратору бота."
            
        try:
            # Формируем контекст с данными анализа
            context = self._format_analysis_context(analysis_data)
            
            # Формируем запрос к GPT
            messages = [
                {"role": "system", "content": (
                    "Ты - ассистент по криптовалютной аналитике. Тебе предоставлены результаты "
                    "комплексного анализа, включающего опционный анализ, технический анализ, "
                    "фундаментальный анализ и риск-менеджмент. Давай подробные и понятные ответы "
                    "на вопросы пользователя, основываясь только на предоставленных данных."
                )},
                {"role": "user", "content": f"Вот результаты анализа:\n\n{context}\n\nВопрос: {question}"}
            ]
            
            # Делаем запрос к API
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Используем новейшую модель, можно заменить на gpt-3.5-turbo для экономии
                messages=messages,
                max_tokens=1000,
                temperature=0.3  # Небольшая температура для более детерминированных ответов
            )
            
            # Возвращаем ответ
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка при запросе к GPT: {e}")
            return f"❌ Произошла ошибка при обработке вопроса: {str(e)}"
    
    def _format_analysis_context(self, analysis_data: Dict[str, Any]) -> str:
        """
        Форматирование данных анализа в текстовый контекст для GPT
        
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
        
        # Заключение
        conclusion = analysis_data.get('conclusion', '')
        if conclusion:
            context += "\nЗАКЛЮЧЕНИЕ:\n"
            context += conclusion
        
        return context