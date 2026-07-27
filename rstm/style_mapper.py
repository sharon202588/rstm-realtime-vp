"""
风格映射器

将连续状态 S(t) 映射到 7-level affective–interaction style
用于约束虚拟患者的语音生成风格

本实现严格遵循 specs/affective_interaction_mapping.md 规范（冻结文件）

重要说明：
- 规范基准：specs/affective_interaction_mapping.md（FROZEN）
- 验证文档：specs/implementation_verification.md（用于验证实现是否正确）
- 本文件是代码实现，必须遵循规范文件，而非验证文档
"""

from typing import Dict, List, Tuple


class StyleMapper:
    """
    7-level affective–interaction style 映射器
    
    将连续状态 S(t) ∈ (-1, 1) 映射到离散的风格级别
    
    本实现严格遵循 specs/affective_interaction_mapping.md 规范：
    - 确定性映射
    - 互斥且完备
    - Level 4 是唯一闭区间 [-0.10, +0.10]
    - 其他级别为半开区间
    """
    
    # 7-level 风格定义（遵循 affective_interaction_mapping.md 规范）
    STYLES = [
        {
            "level": 1,
            "name": "Agitated / Irritated",
            "interaction_style": "Reactive",
            "description": "激动/易怒",
            "state_range": (-1.0, -0.70),  # [-1.00, -0.70) 半开区间
            "behavioral_cues": [
                "Fast, loud, sharp articulation",
                "Tense breathing",
                "Abrupt, confrontational responses"
            ],
            "characteristics": ["快速", "大声", "尖锐", "对抗性"]
        },
        {
            "level": 2,
            "name": "Anxious / Worried",
            "interaction_style": "Anxious",
            "description": "焦虑/担忧",
            "state_range": (-0.70, -0.40),  # [-0.70, -0.40) 半开区间
            "behavioral_cues": [
                "Soft but shaky voice",
                "Uneven rhythm",
                "Nervous hesitations",
                "Uncertain phrasing"
            ],
            "characteristics": ["声音颤抖", "节奏不均", "犹豫", "不确定"]
        },
        {
            "level": 3,
            "name": "Concerned / Downcast",
            "interaction_style": "Downcast",
            "description": "担忧/低落",
            "state_range": (-0.40, -0.10),  # [-0.40, -0.10) 半开区间
            "behavioral_cues": [
                "Slow pace",
                "Low energy",
                "Muffled tone",
                "Long pauses",
                "Downward emotional weight"
            ],
            "characteristics": ["缓慢", "低能量", "低沉", "长停顿"]
        },
        {
            "level": 4,
            "name": "Neutral",
            "interaction_style": "Flat",
            "description": "中性",
            "state_range": (-0.10, 0.10),  # [-0.10, +0.10] 闭区间（唯一）
            "behavioral_cues": [
                "Even volume",
                "Steady pace",
                "No emotional coloring",
                "Purely factual delivery"
            ],
            "characteristics": ["音量均匀", "节奏稳定", "无情感色彩", "纯事实性"]
        },
        {
            "level": 5,
            "name": "Mildly Positive / Encouraging",
            "interaction_style": "Warm",
            "description": "轻度正面/鼓励",
            "state_range": (0.10, 0.40),  # (+0.10, +0.40] 半开区间
            "behavioral_cues": [
                "Light warmth",
                "Soft upward pitch",
                "Calm, encouraging phrasing"
            ],
            "characteristics": ["温和", "音调上扬", "鼓励性"]
        },
        {
            "level": 6,
            "name": "Cooperative / Engaged",
            "interaction_style": "Engaged",
            "description": "合作/参与",
            "state_range": (0.40, 0.70),  # (+0.40, +0.70] 半开区间
            "behavioral_cues": [
                "Clear, warm voice",
                "Responsive cues",
                "Active engagement",
                "Supportive interaction"
            ],
            "characteristics": ["清晰温暖", "积极响应", "主动参与", "支持性"]
        },
        {
            "level": 7,
            "name": "Trusting / Reassured",
            "interaction_style": "Reassuring",
            "description": "信任/安心",
            "state_range": (0.70, 1.0),  # (+0.70, +1.00] 半开区间
            "behavioral_cues": [
                "Soft, smooth tone",
                "Flowing delivery",
                "Comforting presence",
                "Openly trusting"
            ],
            "characteristics": ["柔和流畅", "流畅表达", "安慰性", "开放信任"]
        }
    ]
    
    @classmethod
    def map_state_to_style(cls, state: float) -> Dict:
        """
        将连续状态映射到7-level风格
        
        严格遵循 specs/affective_interaction_mapping.md 规范：
        - Level 4 是唯一闭区间 [-0.10, +0.10]
        - 其他级别为半开区间
        - 映射是确定性的、互斥的、完备的
        
        Args:
            state: 连续状态值 S(t) ∈ (-1, 1)
        
        Returns:
            风格字典，包含level、name、interaction_style、behavioral_cues等
        """
        # 确保状态在有效范围内
        state = max(-1.0, min(1.0, state))
        
        # 按照规范进行映射（遵循 affective_interaction_mapping.md）
        # Level 1-3: 左闭右开 [-1.00, -0.70), [-0.70, -0.40), [-0.40, -0.10)
        # Level 4: 闭区间 [-0.10, +0.10]
        # Level 5-7: 左开右闭 (+0.10, +0.40], (+0.40, +0.70], (+0.70, +1.00]
        
        for style in cls.STYLES:
            min_val, max_val = style["state_range"]
            level = style["level"]
            
            if level == 1:
                # Level 1: [-1.00, -0.70) 左闭右开
                if state >= min_val and state < max_val:
                    return style.copy()
            elif level == 2:
                # Level 2: [-0.70, -0.40) 左闭右开
                if state >= min_val and state < max_val:
                    return style.copy()
            elif level == 3:
                # Level 3: [-0.40, -0.10) 左闭右开
                if state >= min_val and state < max_val:
                    return style.copy()
            elif level == 4:
                # Level 4: [-0.10, +0.10] 闭区间（唯一）
                if state >= min_val and state <= max_val:
                    return style.copy()
            elif level == 5:
                # Level 5: (+0.10, +0.40] 左开右闭
                if state > min_val and state <= max_val:
                    return style.copy()
            elif level == 6:
                # Level 6: (+0.40, +0.70] 左开右闭
                if state > min_val and state <= max_val:
                    return style.copy()
            elif level == 7:
                # Level 7: (+0.70, +1.00] 左开右闭
                if state > min_val and state <= max_val:
                    return style.copy()
        
        # 边界情况处理（理论上不应该到达这里）
        if state == -1.0:
            return cls.STYLES[0].copy()  # Level 1
        if state == 1.0:
            return cls.STYLES[-1].copy()  # Level 7
        
        # 如果到达这里，说明有逻辑错误
        # 默认返回中性风格（Level 4）
        return cls.STYLES[3].copy()
    
    @classmethod
    def get_style_prompt(cls, state: float) -> str:
        """
        根据状态生成风格约束提示词
        
        用于确定实时语音模型的输出风格（7-level affective–interaction style）。
        这个提示词将直接注入到豆包端到端实时语音模型的系统提示词中，
        约束虚拟患者的语音回应风格，确保风格与当前关系状态一致。
        
        Args:
            state: 连续状态值 S(t) ∈ (-1, 1)
        
        Returns:
            风格约束提示词字符串，用于实时语音模型的输出风格确定
        """
        style = cls.map_state_to_style(state)
        
        # 构建风格约束提示词，包含行为线索（Behavioral Cues）
        interaction_style = style.get('interaction_style', style['name'])
        behavioral_cues = style.get('behavioral_cues', [])
        
        prompt = f"""当前医患关系状态：{style['name']} (Level {style['level']})
交互风格：{interaction_style}
关系描述：{style['description']}
行为线索（Behavioral Cues）：
{chr(10).join('  - ' + cue for cue in behavioral_cues)}
患者特征：{', '.join(style['characteristics'])}
状态值：{state:.3f}

请根据以上关系状态和行为线索，以符合该风格的方式回应医生。
在语音生成时，注意体现相应的语音特征（节奏、音调、语调等）。
保持自然、真实，不要过度表演。"""
        
        return prompt
    
    @classmethod
    def get_all_styles(cls) -> List[Dict]:
        """
        获取所有风格定义
        
        Returns:
            所有7-level风格的列表
        """
        return [style.copy() for style in cls.STYLES]

