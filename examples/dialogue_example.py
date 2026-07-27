"""
完整对话流程示例

演示如何使用DialogueManager实现完整的医患对话流程（Phase A → D）
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dialogue_manager import DialogueManager


async def on_patient_response(response: str, style_info: dict):
    """患者回应回调"""
    print(f"\n[患者回应] (风格: {style_info['name']}, Level {style_info['level']})")
    print(f"{response}\n")


async def on_grade_complete(grade_result: dict):
    """评分完成回调"""
    cpas_score = grade_result.get("final_cpas_score", "N/A")
    print(f"[后台评分] CPAS分数: {cpas_score}")


async def on_state_update(state_update: dict):
    """状态更新回调"""
    state = state_update.get("state", 0.0)
    cci = state_update.get("cci", 0.0)
    turn = state_update.get("turn", 0)
    print(f"[状态更新] Turn {turn}: CCI={cci:.3f}, S(t)={state:.3f}")


async def main():
    """主函数：演示完整对话流程"""
    
    # 检查环境变量
    ark_api_key = os.getenv("ARK_API_KEY")
    doubao_realtime_app_id = os.getenv("DOUBAO_REALTIME_APP_ID")
    doubao_realtime_access_key = os.getenv("DOUBAO_REALTIME_ACCESS_KEY")
    
    if not ark_api_key:
        print("错误：请设置环境变量 ARK_API_KEY")
        return
    
    print("=" * 60)
    print("RSTM-SP 完整对话流程示例")
    print("=" * 60)
    print("\n系统将演示：")
    print("  Phase A: 实时语音回应（不等待评分）")
    print("  Phase B: 后台评分（异步执行）")
    print("  Phase C: 关系状态更新（确定性）")
    print("  Phase D: 状态→风格映射")
    print("\n" + "=" * 60)
    
    # 初始化对话管理器
    print("\n初始化对话管理器...")
    manager = DialogueManager(
        ark_api_key=ark_api_key,
        doubao_realtime_app_id=doubao_realtime_app_id,
        doubao_realtime_access_key=doubao_realtime_access_key,
        initial_cci=0.0,  # 初始中性状态
        state_file="dialogue_state.json"  # 状态持久化文件
    )
    
    # 注册回调函数
    manager.on_patient_response = on_patient_response
    manager.on_grade_complete = on_grade_complete
    manager.on_state_update = on_state_update
    
    # 示例对话轮次
    doctor_turns = [
        "张老师，您好。请坐。今天我们来聊聊您的检查结果。",
        "我理解您的担心。在告诉您具体结果之前，我想先了解一下，您对目前的情况有什么了解吗？",
        "好的，我明白了。那么，您希望我如何向您说明检查结果呢？是详细说明，还是先给您一个大概的情况？"
    ]
    
    print("\n开始对话...")
    print("=" * 60)
    
    # 处理每一轮对话
    for i, doctor_message in enumerate(doctor_turns, 1):
        print(f"\n[Turn {i}] 医生发言：")
        print(f"{doctor_message}")
        
        try:
            # 处理医生发言（完整流程 Phase A → D）
            result = await manager.process_doctor_turn(
                doctor_message=doctor_message,
                use_voice=False  # 使用文本模式（测试）
            )
            
            # 显示当前状态信息
            state_info = manager.get_current_state_info()
            print(f"\n[当前状态] S(t)={state_info['current_state']:.3f}, "
                  f"风格: {state_info['current_style']['name']} (Level {state_info['current_style']['level']})")
            
        except Exception as e:
            print(f"\n错误：{str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-" * 60)
    
    # 显示最终状态摘要
    print("\n" + "=" * 60)
    print("对话结束 - 最终状态摘要")
    print("=" * 60)
    
    final_state = manager.get_current_state_info()
    print(f"总轮次: {final_state['dialogue_turns']}")
    print(f"最终CCI: {final_state['current_cci']:.3f}")
    print(f"最终状态 S(t): {final_state['current_state']:.3f}")
    print(f"最终风格: {final_state['current_style']['name']} (Level {final_state['current_style']['level']})")
    print(f"状态历史记录数: {final_state['history_length']}")
    
    # 显示状态历史（最近5轮）
    history = manager.state_manager.get_history(last_n=5)
    if history:
        print("\n最近5轮状态变化：")
        for entry in history:
            print(f"  Turn {entry['turn']}: CPAS={entry['cpas_score']:.1f}, "
                  f"CCI {entry['cci_before']:.2f}→{entry['cci_after']:.2f}, "
                  f"S(t) {entry['state_before']:.3f}→{entry['state_after']:.3f}")


if __name__ == "__main__":
    asyncio.run(main())

