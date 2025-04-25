# src/tools/report_generator.py

import os
import datetime
from typing import Dict, Any
from jinja2 import Template
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Использовать не-интерактивный бэкенд
import matplotlib.pyplot as plt

class ReportGenerator:
    """Класс для генерации отчетов в различных форматах"""
    
    def __init__(self):
        """Инициализация генератора отчетов"""
        # Создаем директорию для отчетов, если её нет
        self.reports_dir = os.path.join(os.getcwd(), 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Каталог с шаблонами отчетов
        self.templates_dir = os.path.join(os.getcwd(), 'src', 'templates')
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Базовый шаблон LaTeX, если файл не существует
        # Исправленный default_template в src/tools/report_generator.py
        self.default_template = r"""
            \documentclass{article}
            \usepackage[utf8]{inputenc}
            \usepackage{graphicx}
            \usepackage{booktabs}
            \usepackage{hyperref}
            \usepackage{xcolor}
            \usepackage{amsmath}
            \usepackage{geometry}
            \geometry{a4paper, margin=2.5cm}

            \title{Аналитический отчет по криптовалюте <<currency>>}
            \author{Торговый агент Hedgie v1.0}
            \date{<<report_date>>}

            \begin{document}

            \maketitle

            \section{Резюме}
            \begin{itemize}
                \item Валюта: <<currency>>
                \item Анализируемый период: <<days>> дней
                \item Текущая цена: \$<<current_price>>
                \item Рекомендация: \textbf{<<recommendation>>}
                \item Уровень риска: <<risk_level>>
            \end{itemize}

            \section{Анализ опционов}
            \begin{itemize}
                \item Всего опционных сделок: <<total_trades>>
                \item CALL/PUT соотношение: <<call_put_ratio>>
                \item Общая дельта: <<total_delta>>
                \item Основные стратегии: <<main_strategies>>
            \end{itemize}

            \section{Технический анализ}
            \begin{itemize}
                \item Текущий тренд: <<trend>>
                \item RSI (индекс относительной силы): <<rsi_value>> (<<rsi_signal>>)
                \item MACD: <<macd_signal>>
                \item Общий технический сигнал: <<technical_signal>>
            \end{itemize}

            \section{Фундаментальный анализ}
            \begin{itemize}
                \item Проанализировано новостей: <<news_count>>
                \item Общий новостной фон: <<news_sentiment>>
                \item Ключевые новости: <<key_news>>
            \end{itemize}

            \section{Риск-менеджмент}
            \begin{itemize}
                \item VaR (95\%): <<var_value>>\% (максимальный ожидаемый убыток)
                \item Волатильность: <<volatility>>\%
                \item Коэффициент Шарпа: <<sharpe_ratio>>
                \item Рекомендуемый размер позиции: <<position_size>>\% от капитала
                \item Рекомендуемый стоп-лосс: \$<<stop_loss_price>> (<<stop_loss_percent>>\%)
                \item Рекомендуемый тейк-профит: \$<<take_profit_price>> (<<take_profit_percent>>\%)
            \end{itemize}

            \section{Стратегия входа и выхода}
            \begin{itemize}
                \item Точка входа: <<entry_strategy>>
                \item Уровень стоп-лосса: \$<<stop_loss_price>> (<<stop_loss_percent>>\%)
                \item Цель по прибыли: \$<<take_profit_price>> (<<take_profit_percent>>\%)
                \item Соотношение риск/доходность: 1:<<risk_reward_ratio>>
            \end{itemize}

            \section{Заключение}
            <<conclusion>>

            \vspace{1cm}
            {\small \textit{Отчет сгенерирован автоматически. Данный отчет не является финансовой рекомендацией.}}

            \end{document}
            """


    def generate_latex_report(self, data: Dict[str, Any], template_path: str = None) -> str:
        """
        Генерирует отчет в формате LaTeX
        
        Args:
            data (Dict[str, Any]): Данные для отчета
            template_path (str, optional): Путь к пользовательскому шаблону
            
        Returns:
            str: Путь к сгенерированному файлу отчета
        """
        # Загружаем шаблон
        template_content = self.default_template
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                template_content = file.read()
        
        # Создаем пользовательские разделители для Jinja2 для избежания конфликта с LaTeX
        from jinja2 import Template, Environment
        env = Environment(
            variable_start_string='<<',  # Меняем {{ на 
            variable_end_string='>>',    # Меняем }} на >>
            block_start_string='<%',     # Меняем {% на <%
            block_end_string='%>',       # Меняем %} на %>
            comment_start_string='<#',   # Меняем {# на <#
            comment_end_string='#>'      # Меняем #} на #>
        )
        template = env.from_string(template_content)
        
        # Рендерим шаблон с данными
        rendered_content = template.render(**data)
        
        # Создаем имя файла с временной меткой
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        currency = data.get('currency', 'crypto')
        filename = f"report_{currency}_{timestamp}.tex"
        filepath = os.path.join(self.reports_dir, filename)
        
        # Записываем результат в файл
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(rendered_content)
        
        return filepath
    
    def generate_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Генерирует графики для отчета
        
        Args:
            data (Dict[str, Any]): Данные для построения графиков
            
        Returns:
            Dict[str, str]: Пути к сгенерированным графикам
        """
        chart_paths = {}
        
        # Генерируем базовый путь для графиков
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        currency = data.get('currency', 'crypto')
        
        # Получаем данные о ценах
        price_data = data.get('price_data', None)
        if price_data is not None and isinstance(price_data, pd.DataFrame):
            # График цены
            plt.figure(figsize=(10, 6))
            plt.plot(price_data.index, price_data['close'], label='Цена закрытия')
            
            # Добавляем скользящие средние, если они есть
            if 'SMA_20' in price_data.columns:
                plt.plot(price_data.index, price_data['SMA_20'], label='SMA 20', linestyle='--')
            if 'SMA_50' in price_data.columns:
                plt.plot(price_data.index, price_data['SMA_50'], label='SMA 50', linestyle='-.')
            
            plt.title(f'Динамика цены {currency}')
            plt.xlabel('Дата')
            plt.ylabel('Цена (USD)')
            plt.legend()
            plt.grid(True)
            
            # Сохраняем график
            price_chart_path = os.path.join(self.reports_dir, f"price_chart_{currency}_{timestamp}.png")
            plt.savefig(price_chart_path)
            plt.close()
            
            chart_paths['price_chart'] = price_chart_path
            
            # График индикаторов
            if 'RSI' in price_data.columns:
                plt.figure(figsize=(10, 6))
                plt.plot(price_data.index, price_data['RSI'], label='RSI')
                plt.axhline(y=70, color='r', linestyle='-', alpha=0.3)
                plt.axhline(y=30, color='g', linestyle='-', alpha=0.3)
                plt.title(f'RSI {currency}')
                plt.xlabel('Дата')
                plt.ylabel('RSI')
                plt.legend()
                plt.grid(True)
                
                rsi_chart_path = os.path.join(self.reports_dir, f"rsi_chart_{currency}_{timestamp}.png")
                plt.savefig(rsi_chart_path)
                plt.close()
                
                chart_paths['rsi_chart'] = rsi_chart_path
        
        # График распределения опционных стратегий
        strategies_data = data.get('strategies_data', None)
        if strategies_data and isinstance(strategies_data, dict):
            strategies = list(strategies_data.keys())
            volumes = list(strategies_data.values())
            
            plt.figure(figsize=(10, 6))
            plt.bar(strategies, volumes)
            plt.title(f'Распределение опционных стратегий {currency}')
            plt.xlabel('Стратегия')
            plt.ylabel('Объем')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            strategies_chart_path = os.path.join(self.reports_dir, f"strategies_chart_{currency}_{timestamp}.png")
            plt.savefig(strategies_chart_path)
            plt.close()
            
            chart_paths['strategies_chart'] = strategies_chart_path
        
        return chart_paths