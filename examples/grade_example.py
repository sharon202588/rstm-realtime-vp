"""
CPAS评分器使用示例

演示如何使用豆包REST API客户端对医患对话进行CPAS评分。
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from doubao.rest_client import DoubaoRESTClient, ReasoningEffort


def load_grader_prompt():
    """加载评分器提示词模板"""
    prompt_path = project_root / "specs" / "grader_prompt.md"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def format_dialogue_history(dialogue_turns):
    """
    格式化对话历史
    
    Args:
        dialogue_turns: 对话轮次列表，格式为 [{"role": "Doctor/Patient", "content": "..."}, ...]
    
    Returns:
        格式化后的对话历史字符串
    """
    formatted = []
    for i, turn in enumerate(dialogue_turns, 1):
        role = turn.get("role", "Unknown")
        content = turn.get("content", "")
        formatted.append(f"Turn {i}: {role}: {content}")
    return "\n".join(formatted)


def main():
    """主函数：执行CPAS评分示例"""
    
    # 检查环境变量
    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        print("错误：请设置环境变量 ARK_API_KEY")
        print("示例：export ARK_API_KEY=your_api_key")
        return
    
    # 示例对话历史（模拟医患沟通场景）
    example_dialogue = [
        {
            "role": "Doctor",
            "content": "张老师，您好。请坐。今天我们来聊聊您的检查结果。"
        },
        {
            "role": "Patient",
            "content": "医生，我有点紧张。两周前体检说肺部有问题，让我来复查。"
        },
        {
            "role": "Doctor",
            "content": "我理解您的担心。在告诉您具体结果之前，我想先了解一下，您对目前的情况有什么了解吗？"
        }
    ]
    
    print("=" * 60)
    print("CPAS评分器示例")
    print("=" * 60)
    print("\n对话历史：")
    print(format_dialogue_history(example_dialogue))
    print("\n" + "=" * 60)
    
    try:
        # 加载评分器提示词
        print("\n加载评分器提示词模板...")
        grader_prompt = load_grader_prompt()
        
        # 格式化对话历史
        dialogue_history = format_dialogue_history(example_dialogue)
        
        # 初始化客户端
        print("初始化豆包REST客户端...")
        client = DoubaoRESTClient(api_key=api_key)
        
        # 执行评分
        print("正在调用评分API（这可能需要几秒钟）...")
        result = client.grade_dialogue(
            dialogue_history=dialogue_history,
            grader_prompt=grader_prompt,
            reasoning_effort=ReasoningEffort.MEDIUM
        )
        
        # 显示结果
        print("\n" + "=" * 60)
        print("评分结果：")
        print("=" * 60)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 提取关键信息
        if isinstance(result, dict):
            cpas_score = result.get("final_cpas_score")
            if cpas_score is not None:
                print("\n" + "=" * 60)
                print(f"最终CPAS分数：{cpas_score}")
                
                scoring = result.get("scoring_breakdown", {})
                track_a = scoring.get("track_a_task")
                track_b = scoring.get("track_b_empathy")
                
                if track_a is not None and track_b is not None:
                    print(f"  - Track A (任务完成度)：{track_a}")
                    print(f"  - Track B (共情能力)：{track_b}")
                
                safety = result.get("safety_check", {})
                safety_status = safety.get("status")
                if safety_status:
                    print(f"  - 安全状态：{safety_status}")
        
        print("\n" + "=" * 60)
        print("评分完成！")
        
    except Exception as e:
        print(f"\n错误：{str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

