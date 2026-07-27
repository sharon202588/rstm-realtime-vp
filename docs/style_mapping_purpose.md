# 状态→风格映射：确定实时语音模型输出风格

## 核心说明

**状态→风格映射（Phase D）的作用是确定实时语音模型的输出风格。**

## 映射流程

1. **状态更新**：根据CPAS评分更新关系状态 S(t)
2. **风格映射**：将连续状态 S(t) 映射到 7-level affective–interaction style
3. **生成约束**：生成风格约束提示词
4. **注入模型**：风格约束提示词直接注入到豆包端到端实时语音模型的系统提示词中
5. **控制输出**：实时语音模型根据风格约束生成符合当前关系状态的语音回应

## 实现位置

- **风格映射器**：`rstm/style_mapper.py`
  - `map_state_to_style()`: 将 S(t) 映射到 7-level 风格
  - `get_style_prompt()`: 生成风格约束提示词

- **应用位置**：`core/dialogue_manager.py`
  - Phase A: 使用当前状态映射的风格约束生成语音回应
  - Phase D: 计算下一轮使用的风格约束

## 关键代码

```python
# Phase A: 使用当前状态确定输出风格
current_state = self.state_manager.get_current_state()
style_prompt = StyleMapper.get_style_prompt(current_state)  # 确定输出风格
patient_response = await self._generate_voice_response(
    doctor_message,
    style_prompt  # 风格约束注入到实时语音模型
)

# Phase D: 计算下一轮的风格约束
new_state = state_update["state"]
new_style = StyleMapper.map_state_to_style(new_state)
style_prompt_for_next_turn = StyleMapper.get_style_prompt(new_state)  # 用于下一轮
```

## 7-Level 风格映射表

| Level | 名称 | 状态范围 | 用于确定语音输出风格 |
|-------|------|---------|---------------------|
| 1 | Highly Defensive | (-1.0, -0.71) | 高度防御性、不信任的语音风格 |
| 2 | Defensive | (-0.71, -0.43) | 防御性、谨慎的语音风格 |
| 3 | Neutral-Negative | (-0.43, -0.14) | 中性偏负面、被动的语音风格 |
| 4 | Neutral | (-0.14, 0.14) | 中性、开放的语音风格 |
| 5 | Neutral-Positive | (0.14, 0.43) | 中性偏正面、积极的语音风格 |
| 6 | Positive | (0.43, 0.71) | 正面、开放的语音风格 |
| 7 | Highly Positive | (0.71, 1.0) | 高度正面、完全信任的语音风格 |

## 重要说明

1. **直接控制输出**：风格映射不是"建议"，而是直接确定实时语音模型的输出风格
2. **系统提示词注入**：风格约束通过系统提示词注入到豆包端到端实时语音模型
3. **动态适应**：随着关系状态 S(t) 的变化，语音输出风格自动调整
4. **一致性保证**：确保虚拟患者的语音回应与当前关系状态保持一致

