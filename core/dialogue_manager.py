"""
对话管理器

实现一次完整对话轮次的运行逻辑（Phase A → D）
遵循 vibe_coding_guide.md 中定义的执行顺序
"""

import asyncio
from typing import Optional, Dict, Any, Callable
from pathlib import Path

# 导入各模块
from doubao.rest_client import DoubaoRESTClient, ReasoningEffort
from doubao.websocket_client import DoubaoWebSocketClient
from rstm.state_manager import RSTMStateManager
from rstm.style_mapper import StyleMapper
from core.session_logger import SessionLogger


LANGUAGE_INSTRUCTIONS = {
    "zh": "请全程使用中文与学习者交流。",
    "en": "Use English throughout the interaction.",
}

SCENARIO_OPENINGS = {
    "breaking_bad_news": {
        "zh": "医生，我这次检查结果是不是不太好？我这几天一直有点担心。",
        "en": "Doctor, are my test results not good? I have been worried about them these past few days.",
    }
}


class DialogueManager:
    """
    对话管理器
    
    协调三大模块：
    1. 虚拟患者生成（实时语音）
    2. 评分判别器（CPAS Grader）
    3. 关系状态轨迹模型（RSTM）
    
    实现 Phase A → D 的完整流程
    """
    
    def __init__(
        self,
        # 豆包API配置
        ark_api_key: Optional[str] = None,
        doubao_realtime_app_id: Optional[str] = None,
        doubao_realtime_access_key: Optional[str] = None,
        # RSTM配置
        initial_cci: float = 0.0,
        initial_state: Optional[float] = None,
        state_file: Optional[str] = None,
        adaptive_enabled: bool = True,
        fixed_style_state: float = 0.0,
        language: str = "zh",
        scenario: str = "breaking_bad_news",
        case_context: str = "",
        session_logger: Optional[SessionLogger] = None,
        # 提示词文件路径
        grader_prompt_path: Optional[str] = None,
        patient_profile_path: Optional[str] = None
    ):
        """
        初始化对话管理器
        
        Args:
            ark_api_key: 豆包文本模型API密钥
            doubao_realtime_app_id: 豆包语音模型应用ID
            doubao_realtime_access_key: 豆包语音模型应用密钥
            initial_cci: 初始CCI值
            state_file: RSTM状态持久化文件路径
            grader_prompt_path: 评分器提示词文件路径
            patient_profile_path: 患者配置文件路径
        """
        # 初始化REST客户端（评分器）
        self.rest_client = DoubaoRESTClient(api_key=ark_api_key) if ark_api_key else None
        
        # 初始化WebSocket客户端（语音交互）
        self.ws_client = DoubaoWebSocketClient(
            realtime_app_id=doubao_realtime_app_id,
            realtime_access_key=doubao_realtime_access_key
        ) if (doubao_realtime_app_id and doubao_realtime_access_key) else None
        
        # 初始化RSTM状态管理器
        self.state_manager = RSTMStateManager(
            initial_cci=initial_cci,
            initial_state=initial_state,
            state_file=state_file
        )
        self.adaptive_enabled = adaptive_enabled
        self.fixed_style_state = max(-1.0, min(1.0, float(fixed_style_state)))
        self.language = language if language in LANGUAGE_INSTRUCTIONS else "zh"
        self.scenario = scenario
        self.case_context = case_context.strip()
        self.session_logger = session_logger
        
        # 加载提示词文件
        project_root = Path(__file__).parent.parent
        self.grader_prompt_path = grader_prompt_path or (project_root / "specs" / "grader_prompt.md")
        self.patient_profile_path = patient_profile_path or (project_root / "specs" / "patient_profile.md")
        
        self.grader_prompt = self._load_file(self.grader_prompt_path)
        self.patient_profile = self._load_file(self.patient_profile_path)
        
        # 对话历史
        self.dialogue_history: list = []
        
        # 回调函数
        self.on_patient_response: Optional[Callable] = None
        self.on_grade_complete: Optional[Callable] = None
        self.on_state_update: Optional[Callable] = None

    def _runtime_prompt_suffix(self) -> str:
        scenario_label = {
            "breaking_bad_news": "breaking bad news communication",
        }.get(self.scenario, self.scenario)
        condition = "RSTM-enabled adaptive" if self.adaptive_enabled else "non-adaptive neutral"
        return (
            "\n\nRuntime configuration:\n"
            f"- Scenario: {scenario_label}\n"
            f"- Language: {self.language}\n"
            f"- Language instruction: {LANGUAGE_INSTRUCTIONS[self.language]}\n"
            f"- Condition: {condition}"
            + (
                "\n\nSession-specific case context:\n"
                f"{self.case_context}"
                if self.case_context
                else ""
            )
        )
    
    def _load_file(self, file_path: str) -> str:
        """加载文件内容"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {file_path}")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def add_dialogue_turn(self, role: str, content: str):
        """
        添加对话轮次
        
        Args:
            role: 说话者角色（"Doctor" 或 "Patient"）
            content: 对话内容
        """
        self.dialogue_history.append({
            "role": role,
            "content": content,
            "turn": len(self.dialogue_history) + 1
        })
    
    def format_dialogue_history(self) -> str:
        """格式化对话历史为字符串"""
        formatted = []
        for turn in self.dialogue_history:
            role = turn.get("role", "Unknown")
            content = turn.get("content", "")
            turn_num = turn.get("turn", 0)
            formatted.append(f"Turn {turn_num}: {role}: {content}")
        return "\n".join(formatted)

    def get_opening_utterance(self) -> str:
        return SCENARIO_OPENINGS.get(self.scenario, {}).get(self.language, "")

    def start_with_opening(self) -> Optional[str]:
        opening = self.get_opening_utterance()
        if opening and not self.dialogue_history:
            self.add_dialogue_turn("Patient", opening)
            return opening
        return None
    
    async def process_doctor_turn(
        self,
        doctor_message: str,
        use_voice: bool = True
    ) -> Dict[str, Any]:
        """
        处理医生的一轮发言（完整流程 Phase A → D）
        
        执行顺序：
        Phase A: 实时语音回应（最高优先级，不等待评分）
        Phase B: 后台评分（异步执行）
        Phase C: 关系状态更新（确定性）
        Phase D: 状态→风格映射
        
        Args:
            doctor_message: 医生的发言内容
            use_voice: 是否使用语音交互（True）或文本交互（False）
        
        Returns:
            包含处理结果的字典
        """
        # 添加医生发言到历史
        self.add_dialogue_turn("Doctor", doctor_message)
        
        result = {
            "phase_a": None,  # 患者回应
            "phase_b": None,  # CPAS评分
            "phase_c": None,  # 状态更新
            "phase_d": None   # 风格映射
        }
        
        # ============================================
        # Phase A: 实时语音回应（最高优先级）
        # ============================================
        # 获取当前状态和风格约束
        # 使用当前S(t)映射到7-level风格，确定实时语音模型的输出风格
        current_state = (
            self.state_manager.get_current_state()
            if self.adaptive_enabled
            else self.fixed_style_state
        )
        style_info = StyleMapper.map_state_to_style(current_state)
        style_prompt = (
            StyleMapper.get_style_prompt(current_state)
            if self.adaptive_enabled
            else ""
        )  # 用于约束实时语音模型输出
        
        # 生成患者回应（不等待评分）
        if use_voice and self.ws_client:
            # 使用WebSocket语音交互
            patient_response = await self._generate_voice_response(
                doctor_message,
                style_prompt
            )
        else:
            # 使用文本交互（用于测试）
            patient_response = await self._generate_text_response(
                doctor_message,
                style_prompt
            )
        
        result["phase_a"] = {
            "patient_response": patient_response,
            "current_state": current_state,
            "style_level": style_info["level"],
            "style_name": style_info["name"]
        }
        
        # 添加患者回应到历史
        self.add_dialogue_turn("Patient", patient_response)
        result["transcript"] = self.dialogue_history.copy()
        
        # 触发回调
        if self.on_patient_response:
            await self.on_patient_response(patient_response, style_info)
        
        # ============================================
        # Phase B: 后台评分（异步执行）
        # ============================================
        if self.rest_client:
            try:
                dialogue_text = self.format_dialogue_history()
                grade_result = self.rest_client.grade_dialogue(
                    dialogue_history=dialogue_text,
                    grader_prompt=self.grader_prompt,
                    reasoning_effort=ReasoningEffort.MEDIUM
                )
                
                result["phase_b"] = grade_result
                
                # 提取CPAS分数
                cpas_score = grade_result.get("final_cpas_score", 0.0)
                if not isinstance(cpas_score, (int, float)):
                    cpas_score = 0.0
                
                # 触发回调
                if self.on_grade_complete:
                    await self.on_grade_complete(grade_result)
                
                # ============================================
                # Phase C: 关系状态更新（确定性）
                # ============================================
                if self.adaptive_enabled:
                    state_update = self.state_manager.update_state(cpas_score)
                    result["phase_c"] = state_update
                else:
                    state_update = {
                        "adaptive_enabled": False,
                        "state": self.fixed_style_state,
                        "cci": None,
                        "turn": self.state_manager.turn_count,
                        "skipped": "non-adaptive condition",
                    }
                    result["phase_c"] = state_update
                
                # 触发回调
                if self.adaptive_enabled and self.on_state_update:
                    await self.on_state_update(state_update)
                
                # ============================================
                # Phase D: 状态→风格映射（确定实时语音模型输出风格）
                # ============================================
                # 将更新后的状态映射到7-level affective–interaction style
                # 这个映射用于确定下一轮实时语音模型的输出风格
                new_state = state_update["state"]
                new_style = StyleMapper.map_state_to_style(new_state)
                style_prompt_for_next_turn = StyleMapper.get_style_prompt(new_state)
                
                result["phase_d"] = {
                    "state": new_state,
                    "style": new_style,
                    "style_prompt": style_prompt_for_next_turn,
                    "purpose": "确定下一轮实时语音模型的输出风格（7-level映射）"
                }
                
            except Exception as e:
                # 评分失败不影响对话继续
                result["phase_b"] = {"error": str(e)}
                print(f"Warning: CPAS grading failed: {e}")
        
        if self.session_logger:
            self.session_logger.log_turn(result)

        return result
    
    async def _generate_voice_response(
        self,
        doctor_message: str,
        style_prompt: str
    ) -> str:
        """
        使用WebSocket生成语音回应
        
        通过7-level风格映射确定的风格约束，直接控制实时语音模型的输出风格。
        风格提示词将注入到豆包端到端实时语音模型的系统提示词中。
        
        Args:
            doctor_message: 医生的消息
            style_prompt: 风格约束提示词（来自7-level映射，用于确定输出风格）
        
        Returns:
            患者回应的文本内容
        """
        if not self.ws_client:
            raise RuntimeError("WebSocket client not initialized")
        
        # 建立连接
        await self.ws_client.connect()
        
        try:
            # 构建完整的系统提示词（患者角色 + 7-level风格约束）
            # 风格约束直接确定实时语音模型的输出风格
            full_prompt = f"{self.patient_profile}{self._runtime_prompt_suffix()}\n\n{style_prompt}"
            
            # 启动会话，将风格约束注入到实时语音模型
            await self.ws_client.start_session(
                system_prompt=full_prompt  # 包含7-level风格映射的约束
            )
            
            # 发送文本查询（如果医生使用文本输入）
            await self.ws_client.send_text_query(doctor_message)
            
            # 监听响应（简化版本，实际需要处理音频流）
            # 这里返回占位文本，实际实现需要处理WebSocket消息流
            response_text = "患者回应（语音转文本）"
            
            return response_text
        
        finally:
            await self.ws_client.disconnect()
    
    async def _generate_text_response(
        self,
        doctor_message: str,
        style_prompt: str
    ) -> str:
        """
        使用REST API生成文本回应（用于测试）
        
        Args:
            doctor_message: 医生的消息
            style_prompt: 风格约束提示词
        
        Returns:
            患者回应的文本内容
        """
        if not self.rest_client:
            raise RuntimeError("REST client not initialized")
        
        # 构建完整的系统提示词
        full_prompt = f"{self.patient_profile}{self._runtime_prompt_suffix()}\n\n{style_prompt}"
        
        # 构建消息
        messages = [
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": doctor_message}
        ]
        
        # 调用API（使用文本生成模型）
        response = self.rest_client.chat_completion(
            messages=messages,
            reasoning_effort=ReasoningEffort.MEDIUM
        )
        
        # 提取回复
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0].get("message", {}).get("content", "")
        else:
            return "患者回应（生成失败）"
    
    def get_current_state_info(self) -> Dict[str, Any]:
        """获取当前状态信息"""
        state = (
            self.state_manager.get_current_state()
            if self.adaptive_enabled
            else self.fixed_style_state
        )
        style = StyleMapper.map_state_to_style(state)
        summary = self.state_manager.get_state_summary()
        
        return {
            **summary,
            "current_state": state,
            "current_style": style,
            "dialogue_turns": len(self.dialogue_history)
        }

