# 快速启动指南

Quick Start Guide

## 🚀 5分钟快速开始

### 步骤1：安装依赖

```bash
# 安装Python依赖包
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install requests>=2.31.0 websockets>=12.0 python-dotenv>=1.0.0
```

### 步骤2：配置API密钥

#### 方法1：使用 .env 文件（推荐）

1. 复制环境变量模板：
```bash
cp env.example .env
```

2. 编辑 `.env` 文件，填入你的API密钥：
```bash
ARK_API_KEY=your_ark_api_key_here
DOUBAO_REALTIME_APP_ID=your_app_id_here
DOUBAO_REALTIME_ACCESS_KEY=your_realtime_access_key_here
```

#### 方法2：设置系统环境变量

**Windows PowerShell:**
```powershell
$env:ARK_API_KEY = "your_ark_api_key_here"
$env:DOUBAO_REALTIME_APP_ID = "your_app_id_here"
$env:DOUBAO_REALTIME_ACCESS_KEY = "your_realtime_access_key_here"
```

**macOS / Linux:**
```bash
export ARK_API_KEY="your_ark_api_key_here"
export DOUBAO_REALTIME_APP_ID="your_app_id_here"
export DOUBAO_REALTIME_ACCESS_KEY="your_realtime_access_key_here"
```

### 步骤3：验证配置

```bash
python test_credentials.py
```

如果看到所有密钥都已配置，说明配置成功！

### 步骤4：运行系统

#### 方式1：交互式对话（推荐）

```bash
python main.py
```

然后输入医生的发言，系统会自动生成虚拟患者的回应。

#### 方式2：运行示例代码

**完整对话流程示例：**
```bash
python examples/dialogue_example.py
```

**CPAS评分器示例：**
```bash
python examples/grade_example.py
```

**风格映射器测试：**
```bash
python tests/test_style_mapper.py
```

## 📋 使用示例

### 交互式对话

运行 `python main.py` 后：

```
[Turn 1] 请输入医生的发言:
> 张老师，您好。请坐。今天我们来聊聊您的检查结果。

[患者回应]
风格: Neutral (Level 4)
交互风格: Flat
------------------------------------------------------------
患者回应内容...
------------------------------------------------------------

[后台评分]
CPAS分数: 2
  Track A (任务完成度): 1
  Track B (共情能力): 1
  安全状态: Safe

[状态更新] Turn 1
  CCI: 2.000
  S(t): 0.198

[当前状态] S(t)=0.198, 风格: Neutral-Positive (Level 5)
```

### 程序化使用

```python
import asyncio
import os
from dotenv import load_dotenv
from core.dialogue_manager import DialogueManager

load_dotenv()

async def main():
    # 初始化对话管理器
    manager = DialogueManager(
        ark_api_key=os.getenv("ARK_API_KEY"),
        doubao_realtime_app_id=os.getenv("DOUBAO_REALTIME_APP_ID"),
        doubao_realtime_access_key=os.getenv("DOUBAO_REALTIME_ACCESS_KEY")
    )
    
    # 处理医生发言
    result = await manager.process_doctor_turn(
        doctor_message="张老师，您好。请坐。",
        use_voice=False  # 使用文本模式
    )
    
    # 获取结果
    patient_response = result["phase_a"]["patient_response"]
    cpas_score = result["phase_b"].get("final_cpas_score", 0)
    state = result["phase_c"]["state"]
    
    print(f"患者回应: {patient_response}")
    print(f"CPAS分数: {cpas_score}")
    print(f"关系状态: {state}")

asyncio.run(main())
```

## 🔧 故障排查

### 问题1：找不到环境变量

**症状**：`ValueError: API key is required`

**解决方案**：
1. 确认 `.env` 文件在项目根目录
2. 确认已安装 `python-dotenv`：`pip install python-dotenv`
3. 运行 `python test_credentials.py` 检查配置

### 问题2：API调用失败

**症状**：401 Unauthorized 或 403 Forbidden

**解决方案**：
1. 检查密钥是否正确
2. 检查密钥是否过期
3. 确认API服务已开通
4. 参考 `docs/api_credentials_setup.md`

### 问题3：模块导入错误

**症状**：`ModuleNotFoundError`

**解决方案**：
1. 确认在项目根目录运行
2. 确认已安装所有依赖：`pip install -r requirements.txt`
3. 检查Python版本（需要3.8+）

## 📚 更多文档

- **API密钥配置**：`docs/api_credentials_setup.md`
- **项目构建清单**：`docs/project_build_checklist.md`
- **系统架构**：`specs/vibe_coding_guide.md`
- **API参考**：查看各模块的文档字符串

## ✅ 检查清单

在运行系统前，确认：

- [ ] Python 3.8+ 已安装
- [ ] 依赖包已安装（`pip install -r requirements.txt`）
- [ ] API密钥已配置（`.env` 文件或环境变量）
- [ ] 密钥验证通过（`python test_credentials.py`）
- [ ] 项目文件完整（所有模块文件存在）

## 🎯 下一步

1. **运行示例**：先运行 `examples/dialogue_example.py` 了解系统工作流程
2. **阅读文档**：查看 `README.md` 了解系统架构
3. **自定义配置**：根据需要调整RSTM参数（注意：MVP阶段参数已固定）
4. **集成开发**：参考 `core/dialogue_manager.py` 集成到你的应用中

---

**需要帮助？** 查看 `docs/` 目录下的详细文档，或检查 `specs/` 目录下的规范文档。

