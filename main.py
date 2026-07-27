"""
RSTM-SP 主入口文件

自适应实时语音虚拟患者系统的主程序入口
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path
from typing import Optional

# 将项目根目录加入路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from core.dialogue_manager import DialogueManager
from core.session_logger import SessionLogger


def _get_arg_value(args: list[str], name: str, default: str) -> str:
    prefix = f"{name}="
    for index, arg in enumerate(args):
        if arg == name and index + 1 < len(args):
            return args[index + 1]
        if arg.startswith(prefix):
            return arg[len(prefix):]
    return default


def _default_initial_state_for_scenario(scenario: str) -> float:
    if scenario == "breaking_bad_news":
        return -0.25
    return 0.0


def _load_optional_text_file(path: str) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8").strip()


async def on_patient_response(response: str, style_info: dict):
    """患者回应回调"""
    print(f"\n{'='*60}")
    print("[患者回应]")
    print(f"风格: {style_info['name']} (Level {style_info['level']})")
    print(f"交互风格: {style_info.get('interaction_style', 'N/A')}")
    print("-" * 60)
    print(response)
    print(f"{'='*60}\n")


async def on_grade_complete(grade_result: dict):
    """评分完成回调"""
    print("\n[后台评分]")
    print(f"CPAS分数: {grade_result.get('final_cpas_score', 'N/A')}")

    scoring = grade_result.get("scoring_breakdown", {})
    if scoring:
        print(f"  Track A (任务完成度): {scoring.get('track_a_task', 'N/A')}")
        print(f"  Track B (共情能力): {scoring.get('track_b_empathy', 'N/A')}")

    safety = grade_result.get("safety_check", {})
    if safety:
        print(f"  安全状态: {safety.get('status', 'N/A')}")


async def on_state_update(state_update: dict):
    """状态更新回调"""
    state = state_update.get("state", 0.0)
    cci = state_update.get("cci", 0.0)
    turn = state_update.get("turn", 0)
    print(f"\n[状态更新] Turn {turn}")
    print(f"  CCI: {cci:.3f}")
    print(f"  S(t): {state:.3f}")


async def interactive_dialogue(
    adaptive_enabled: bool = True,
    fixed_style_state: Optional[float] = None,
    participant_id: str = "anonymous",
    session_id: str = "",
    language: str = "zh",
    scenario: str = "breaking_bad_news",
    case_context: str = "",
    initial_state: float = -0.25,
    retain_audio: bool = False,
    vp_opens: bool = False,
):
    """文本模式交互"""
    print("\n" + "=" * 60)
    print("RSTM-SP: 自适应实时语音虚拟患者系统（文本模式）")
    print("=" * 60)
    print("\n系统说明：")
    print("  - 输入医生的发言（文本）")
    print("  - 系统生成虚拟患者的回应")
    print("  - 后台自动进行 CPAS 评分和状态更新")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("\n" + "=" * 60)

    ark_api_key = os.getenv("ARK_API_KEY")
    doubao_realtime_app_id = os.getenv("DOUBAO_REALTIME_APP_ID")
    doubao_realtime_access_key = os.getenv("DOUBAO_REALTIME_ACCESS_KEY")
    session_id = session_id or f"{participant_id}-{uuid.uuid4().hex[:8]}"
    condition = "adaptive" if adaptive_enabled else "non_adaptive"
    session_logger = SessionLogger(
        session_id=session_id,
        participant_id=participant_id,
        condition=condition,
        language=language,
        scenario=scenario,
        retain_audio=retain_audio,
        initial_state=initial_state,
        case_context=case_context,
    )
    state_file = session_logger.session_dir / "rstm_state.json"
    if state_file.exists():
        state_file.unlink()

    if not ark_api_key:
        print("\n[ERROR] 错误：未设置环境变量 ARK_API_KEY")
        print("   请参考 docs/api_credentials_setup.md 配置 API 密钥")
        return

    print("\n初始化对话管理器...")
    try:
        manager = DialogueManager(
            ark_api_key=ark_api_key,
            doubao_realtime_app_id=doubao_realtime_app_id,
            doubao_realtime_access_key=doubao_realtime_access_key,
            initial_cci=0.0,
            initial_state=initial_state,
            state_file=str(state_file),
            adaptive_enabled=adaptive_enabled,
            fixed_style_state=fixed_style_state if fixed_style_state is not None else initial_state,
            language=language,
            scenario=scenario,
            case_context=case_context,
            session_logger=session_logger,
        )

        manager.on_patient_response = on_patient_response
        manager.on_grade_complete = on_grade_complete
        manager.on_state_update = on_state_update

        print("[OK] 对话管理器初始化成功")

        state_info = manager.get_current_state_info()
        print(f"\n初始状态 S(t)={state_info['current_state']:.3f}")
        print(
            f"初始风格: {state_info['current_style']['name']} "
            f"(Level {state_info['current_style']['level']})"
        )

        if vp_opens:
            opening = manager.start_with_opening()
            if opening:
                await on_patient_response(opening, state_info["current_style"])

        print("\n" + "=" * 60)
        print("开始对话...")
        print("=" * 60)

        turn = 1
        while True:
            print(f"\n[Turn {turn}] 请输入医生的发言:")
            doctor_message = input("> ").strip()

            if not doctor_message:
                continue

            if doctor_message.lower() in ["quit", "exit", "q"]:
                print("\n对话结束。")
                break

            try:
                await manager.process_doctor_turn(
                    doctor_message=doctor_message,
                    use_voice=False,  # 文本模式
                )

                state_info = manager.get_current_state_info()
                print(
                    f"\n[当前状态] S(t)={state_info['current_state']:.3f}, "
                    f"风格: {state_info['current_style']['name']} "
                    f"(Level {state_info['current_style']['level']})"
                )

                turn += 1

            except Exception as e:
                print(f"\n[ERROR] 错误: {str(e)}")
                import traceback

                traceback.print_exc()

        print("\n" + "=" * 60)
        print("对话结束 - 最终状态摘要")
        print("=" * 60)

        final_state = manager.get_current_state_info()
        print(f"总轮次: {final_state['dialogue_turns']}")
        print(f"最终CCI: {final_state['current_cci']:.3f}")
        print(f"最终状态S(t): {final_state['current_state']:.3f}")
        print(
            f"最终风格: {final_state['current_style']['name']} "
            f"(Level {final_state['current_style']['level']})"
        )

        history = manager.state_manager.get_history(last_n=5)
        if history:
            print("\n最近轮次状态变化：")
            for entry in history:
                print(
                    f"  Turn {entry['turn']}: CPAS={entry['cpas_score']:.1f}, "
                    f"CCI {entry['cci_before']:.2f}→{entry['cci_after']:.2f}, "
                    f"S(t) {entry['state_before']:.3f}→{entry['state_after']:.3f}"
                )

    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {str(e)}")
        import traceback

        traceback.print_exc()


def _load_env():
    if load_dotenv:
        load_dotenv()
        print("[OK] 已加载 .env 文件")
    else:
        print("[WARN]  python-dotenv 未安装，仅读取系统环境变量")
        print("   建议安装: pip install python-dotenv")


def main():
    _load_env()
    args = sys.argv[1:]
    if "--ui" in args:
        from ui.server import LocalVoiceUIServer

        http_port = int(_get_arg_value(args, "--http-port", "7860"))
        ws_port = int(_get_arg_value(args, "--ws-port", "8765"))
        server = LocalVoiceUIServer(http_port=http_port, ws_port=ws_port)
        try:
            asyncio.run(server.serve())
        except KeyboardInterrupt:
            pass
        return
    adaptive_enabled = "--non-adaptive" not in args
    participant_id = _get_arg_value(args, "--participant-id", "anonymous")
    session_id = _get_arg_value(args, "--session-id", "")
    language = _get_arg_value(args, "--language", _get_arg_value(args, "--lang", "zh")).lower()
    if language not in ("zh", "en"):
        language = "zh"
    scenario = _get_arg_value(args, "--scenario", "breaking_bad_news")
    case_text = _get_arg_value(args, "--case-text", "")
    case_file = _get_arg_value(args, "--case-file", "")
    case_context = "\n\n".join(
        part for part in [case_text.strip(), _load_optional_text_file(case_file)] if part
    )
    initial_state = float(
        _get_arg_value(args, "--initial-state", str(_default_initial_state_for_scenario(scenario)))
    )
    fixed_style_state_arg = _get_arg_value(args, "--fixed-style-state", "")
    fixed_style_state = (
        float(fixed_style_state_arg)
        if fixed_style_state_arg
        else (
            float(os.getenv("RSTM_FIXED_STYLE_STATE"))
            if os.getenv("RSTM_FIXED_STYLE_STATE")
            else None
        )
    )
    retain_audio = "--retain-audio" in args
    vp_opens = "--vp-opens" in args

    if "--text" in args:
        mode = "text"
    elif "--voice" in args:
        mode = "voice"
    else:
        mode = os.getenv("RSTM_MODE", "voice").lower()
        if mode not in ("voice", "text"):
            mode = "voice"

    if mode == "voice":
        print("启动实时语音交互模式...")
        try:
            from examples.realtime_voice_conductor import RealtimeVoiceConductor
        except ModuleNotFoundError as exc:
            if exc.name == "sounddevice":
                print("[ERROR] 未安装 sounddevice，请先执行: pip install sounddevice")
                return
            raise

        conductor = RealtimeVoiceConductor()
        try:
            asyncio.run(conductor.run())
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
    else:
        print("启动文字交互模式...")
        try:
            asyncio.run(
                interactive_dialogue(
                    adaptive_enabled=adaptive_enabled,
                    fixed_style_state=fixed_style_state,
                    participant_id=participant_id,
                    session_id=session_id,
                    language=language,
                    scenario=scenario,
                    case_context=case_context,
                    initial_state=initial_state,
                    retain_audio=retain_audio,
                    vp_opens=vp_opens,
                )
            )
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
        except Exception as e:
            print(f"\n[ERROR] 程序错误: {str(e)}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
