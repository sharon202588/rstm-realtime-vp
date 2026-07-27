"""
豆包REST API客户端

用于调用豆包文本生成模型，主要用于评分器的CPAS评分判断。
使用原生REST API，遵循官方示例代码模式。

API文档参考：
- https://www.volcengine.com/docs/6561/1594356?lang=zh
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any
from enum import Enum


class ReasoningEffort(str, Enum):
    """推理努力程度配置"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MINIMAL = "minimal"


class DoubaoRESTClient:
    """
    豆包REST API客户端
    
    用于调用豆包文本生成模型进行评分判断。
    支持 doubao-seed-2-0-lite-260428 模型。
    """
    
    # API端点配置
    DEFAULT_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    
    # 默认模型配置
    DEFAULT_MODEL = "doubao-seed-2-0-lite-260428"
    DEFAULT_MAX_TOKENS = 65535
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60
    ):
        """
        初始化豆包REST客户端
        
        Args:
            api_key: 豆包API密钥，如果为None则从环境变量 ARK_API_KEY 读取
            endpoint: API端点URL，默认使用官方端点
            model: 模型名称，默认使用 doubao-seed-2-0-lite-260428
            timeout: 请求超时时间（秒），默认60秒
        """
        self.api_key = api_key or os.getenv("ARK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. "
                "Please provide it as parameter or set ARK_API_KEY environment variable."
            )
        
        self.endpoint = endpoint or self.DEFAULT_ENDPOINT
        self.model = model or os.getenv("DOUBAO_GRADER_MODEL") or self.DEFAULT_MODEL
        self.timeout = timeout
        
        # 请求头配置
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        max_completion_tokens: Optional[int] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用聊天完成API
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            max_completion_tokens: 最大完成token数，默认65535
            reasoning_effort: 推理努力程度（low/medium/high），默认medium
            temperature: 温度参数，控制输出随机性
            **kwargs: 其他API参数
        
        Returns:
            API响应字典，包含模型生成的文本
        
        Raises:
            requests.RequestException: 当API请求失败时抛出
        """
        # 构建请求体
        payload = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": max_completion_tokens or self.DEFAULT_MAX_TOKENS
        }
        
        # 添加可选参数
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort.value if isinstance(reasoning_effort, ReasoningEffort) else reasoning_effort
        
        if temperature is not None:
            payload["temperature"] = temperature
        
        # 添加其他自定义参数
        payload.update(kwargs)
        
        # 发送请求
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            # 错误处理和日志记录
            error_msg = f"Doubao API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" | Response: {json.dumps(error_detail, ensure_ascii=False)}"
                except:
                    error_msg += f" | Response: {e.response.text}"
            raise requests.exceptions.RequestException(error_msg) from e
    
    def grade_dialogue(
        self,
        dialogue_history: str,
        grader_prompt: str,
        reasoning_effort: ReasoningEffort = ReasoningEffort.MEDIUM
    ) -> Dict[str, Any]:
        """
        对医患对话进行CPAS评分
        
        这是一个便捷方法，专门用于调用评分器。
        会自动构建符合grader_prompt.md规范的提示词。
        
        Args:
            dialogue_history: 对话历史记录（文本格式）
            grader_prompt: 评分器提示词模板（从grader_prompt.md读取）
            reasoning_effort: 推理努力程度，默认medium
        
        Returns:
            包含CPAS评分结果的字典，格式应符合grader_prompt.md的输出规范
        """
        # 替换提示词中的变量
        prompt = grader_prompt.replace("{{PRECEDING_DIALOGUE_HISTORY}}", dialogue_history)
        
        # 构建消息
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # 调用API
        response = self.chat_completion(
            messages=messages,
            reasoning_effort=reasoning_effort
        )
        
        # 提取生成的文本
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0].get("message", {}).get("content", "")
            
            # 尝试解析JSON格式的评分结果
            try:
                # 如果返回的是JSON字符串，解析它
                if content.strip().startswith("{"):
                    return json.loads(content)
                else:
                    # 如果不是JSON，返回原始文本
                    return {"raw_response": content, "full_response": response}
            except json.JSONDecodeError:
                # JSON解析失败，返回原始内容
                return {"raw_response": content, "full_response": response}
        else:
            # 没有choices字段，返回完整响应
            return {"full_response": response}
    
    def grade_prompt(
        self,
        prompt: str,
        reasoning_effort: ReasoningEffort = ReasoningEffort.MINIMAL,
    ) -> Dict[str, Any]:
        """Grade one pre-rendered CPAS prompt and parse its JSON response."""

        response = self.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            reasoning_effort=reasoning_effort,
        )
        choices = response.get("choices") or []
        if not choices:
            return {"full_response": response}

        content = str(choices[0].get("message", {}).get("content", "")).strip()
        candidate = content
        if candidate.startswith("```"):
            lines = candidate.splitlines()
            if lines and lines[0].strip().lower() in ("```", "```json"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            candidate = "\n".join(lines).strip()

        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else {"raw_response": content}
        except json.JSONDecodeError:
            return {"raw_response": content, "full_response": response}
    def simple_chat(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        简单的聊天接口
        
        Args:
            user_message: 用户消息
            system_message: 可选的系统消息
            **kwargs: 其他API参数
        
        Returns:
            模型生成的回复文本
        """
        messages = []
        
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        response = self.chat_completion(messages=messages, **kwargs)
        
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0].get("message", {}).get("content", "")
        else:
            raise ValueError(f"Unexpected API response format: {response}")

