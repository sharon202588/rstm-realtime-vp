"""
豆包API客户端封装模块

本模块封装了豆包（Doubao）模型的所有API调用，包括：
- REST API：用于文本生成和评分判断
- WebSocket API：用于实时语音交互

所有API调用都使用原生接口，不使用OpenAI兼容SDK。
"""

from .rest_client import DoubaoRESTClient
from .websocket_client import DoubaoWebSocketClient

__all__ = ['DoubaoRESTClient', 'DoubaoWebSocketClient']

