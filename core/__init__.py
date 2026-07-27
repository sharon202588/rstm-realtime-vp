"""
系统核心模块

实现完整的对话轮次运行逻辑：
- Phase A: 实时语音回应
- Phase B: 后台评分
- Phase C: 关系状态更新
- Phase D: 状态→风格映射
"""

from .dialogue_manager import DialogueManager

__all__ = ['DialogueManager']

