"""
关系状态轨迹模型（RSTM - Relationship State Trajectory Model）

确定性、规则驱动的状态管理模块，用于：
- 将CPAS评分映射为连续关系状态
- 维护跨轮次的情绪惯性与关系记忆
- 输出7-level affective–interaction style映射
"""

from .state_manager import RSTMStateManager
from .style_mapper import StyleMapper

__all__ = ['RSTMStateManager', 'StyleMapper']

