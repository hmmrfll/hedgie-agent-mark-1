# src/agent/communicator.py

import sys
import time
from typing import Any

class Communicator:
    def __init__(self, delay: float = 0.5):
        self.delay = delay

    def say(self, message: str):
        """Вывод сообщения с задержкой"""
        print(f"\nАгент: {message}")
        sys.stdout.flush()
        time.sleep(self.delay)

    def ask(self, question: str) -> str:
        """Запрос ввода от пользователя"""
        print(f"\nАгент: {question}")
        return input("> ").strip()

    def show_progress(self, message: str):
        """Отображение прогресса"""
        print(f"\rАгент: {message}", end="")
        sys.stdout.flush()

    def show_warning(self, message: str):
        """Отображение предупреждения"""
        print(f"\nПредупреждение: {message}")

    def show_error(self, message: str):
        """Отображение ошибки"""
        print(f"\nОшибка: {message}")