# src/agent/states.py

from enum import Enum

class AgentState(Enum):
    IDLE = "idle"
    COLLECTING_DATA = "collecting_data"
    ANALYZING = "analyzing"
    THINKING = "thinking"
    REPORTING = "reporting"
    BLOCK_TRADES_ANALYSIS = "block_trades_analysis"  # Добавляем новое состояние
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"
    TECHNICAL_ANALYSIS = "technical_analysis"
    RISK_MANAGEMENT = "risk_management"
    RECOMMENDATIONS = "recommendations" 
