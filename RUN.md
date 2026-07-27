# 项目运行指南

How to Run the Project

## 📋 运行前准备

### 1. 检查Python版本

```bash
python --version
# 或
python3 --version
```

**要求**：Python 3.8 或更高版本

### 2. 安装依赖包

```bash
# 在项目根目录执行
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install requests>=2.31.0 websockets>=12.0 python-dotenv>=1.0.0
```

### 3. 配置API密钥

#### 方法1：使用 .env 文件（推荐）

1. **复制环境变量模板**：
```bash
# Windows
copy env.example .env

# macOS / Linux
cp env.example .env
```

2. **编辑 .env 文件**，填入你的API密钥：

```bash
# 豆包评分器API配置（REST API）
ARK_API_KEY=your_ark_api_key_here

# 豆包语音模型API配置（WebSocket API）
DOUBAO_REALTIME_APP_ID=your_app_id_here
DOUBAO_REALTIME_ACCESS_KEY=your_realtime_access_key_here
```

3. **验证配置**：
```bash
python test_credentials.py
```

如果看到所有密钥都已配置（✅），说明配置成功！

#### 方法2：设置系统环境变量

**Windows PowerShell:**
```powershell
$env:ARK_API_KEY = "your_ark_api_key_here"
$env:DOUBAO_REALTIME_APP_ID = "your_app_id_here"
$env:DOUBAO_REALTIME_ACCESS_KEY = "your_realtime_access_key_here"
```

**Windows CMD:**
```cmd
setx ARK_API_KEY "your_ark_api_key_here"
setx DOUBAO_REALTIME_APP_ID "your_app_id_here"
setx DOUBAO_REALTIME_ACCESS_KEY "your_realtime_access_key_here"
```

**macOS / Linux:**
```bash
export ARK_API_KEY="your_ark_api_key_here"
export DOUBAO_REALTIME_APP_ID="your_app_id_here"
export DOUBAO_REALTIME_ACCESS_KEY="your_realtime_access_key_here"
```

---

## 🚀 运行方式

### 方式1：交互式对话（推荐新手）

这是最简单的方式，适合快速体验系统功能。

```bash
python main.py
```

**运行后**：
1. 系统会显示欢迎信息和当前状态
2. 提示你输入医生的发言
3. 输入后按回车，系统会自动：
   - 生成虚拟患者回应
   - 进行CPAS评分
   - 更新关系状态
   - 显示结果
4. 输入 `quit` 或 `exit` 退出

**示例交互**：
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
```

### 方式2：运行完整对话流程示例

这个示例演示了完整的 Phase A → D 流程。

```bash
python examples/dialogue_example.py
```

**特点**：
- 预定义的对话轮次
- 完整的流程演示
- 详细的状态变化显示
- 适合理解系统工作原理

### 方式3：运行CPAS评分器示例

单独测试评分功能。

```bash
python examples/grade_example.py
```

**特点**：
- 演示CPAS评分功能
- 显示评分结果JSON
- 适合测试评分器

### 方式4：测试风格映射器

测试7-level风格映射功能。

```bash
python tests/test_style_mapper.py
```

**特点**：
- 测试边界值映射
- 测试范围内值映射
- 验证映射逻辑正确性

---

## 📝 运行示例

### 示例1：交互式对话完整流程

```bash
$ python main.py

✅ 已加载 .env 文件

============================================================
RSTM-SP: 自适应实时语音虚拟患者系统
============================================================

系统说明：
  - 输入医生的发言（文本）
  - 系统将生成虚拟患者的回应
  - 后台自动进行CPAS评分和状态更新
  - 输入 'quit' 或 'exit' 退出

============================================================

初始化对话管理器...
✅ 对话管理器初始化成功

初始状态: S(t)=0.000
初始风格: Neutral (Level 4)

============================================================
开始对话...
============================================================

[Turn 1] 请输入医生的发言:
> 张老师，您好。请坐。今天我们来聊聊您的检查结果。

[患者回应]
风格: Neutral (Level 4)
交互风格: Flat
------------------------------------------------------------
（患者回应内容）
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

[Turn 2] 请输入医生的发言:
> quit

对话结束。
```

### 示例2：程序化使用

创建你自己的脚本 `my_dialogue.py`：

```python
import asyncio
import os
from dotenv import load_dotenv
from core.dialogue_manager import DialogueManager

# 加载环境变量
load_dotenv()

async def main():
    # 初始化对话管理器
    manager = DialogueManager(
        ark_api_key=os.getenv("ARK_API_KEY"),
        doubao_realtime_app_id=os.getenv("DOUBAO_REALTIME_APP_ID"),
        doubao_realtime_access_key=os.getenv("DOUBAO_REALTIME_ACCESS_KEY"),
        initial_cci=0.0
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

if __name__ == "__main__":
    asyncio.run(main())
```

运行：
```bash
python my_dialogue.py
```

---

## 🔧 故障排查

### 问题1：找不到模块

**错误**：`ModuleNotFoundError: No module named 'doubao'`

**解决方案**：
1. 确认在项目根目录运行
2. 确认已安装依赖：`pip install -r requirements.txt`
3. 检查Python路径是否正确

### 问题2：找不到环境变量

**错误**：`ValueError: API key is required`

**解决方案**：
1. 确认 `.env` 文件在项目根目录
2. 确认已安装 `python-dotenv`：`pip install python-dotenv`
3. 运行 `python test_credentials.py` 检查配置

### 问题3：API调用失败

**错误**：`401 Unauthorized` 或 `403 Forbidden`

**解决方案**：
1. 检查密钥是否正确
2. 检查密钥是否过期
3. 确认API服务已开通
4. 参考 `docs/api_credentials_setup.md`

### 问题4：WebSocket连接失败

**错误**：连接被拒绝或认证失败

**解决方案**：
1. 确认 `DOUBAO_REALTIME_APP_ID` 和 `DOUBAO_REALTIME_ACCESS_KEY` 都正确配置
2. 确认使用新开通模型对应的接入 Key（不是 Secret Key）
3. 检查网络连接和防火墙设置

---

## ✅ 运行检查清单

在运行前，确认：

- [ ] Python 3.8+ 已安装
- [ ] 依赖包已安装（`pip install -r requirements.txt`）
- [ ] API密钥已配置（`.env` 文件或环境变量）
- [ ] 密钥验证通过（`python test_credentials.py`）
- [ ] 在项目根目录运行命令

---

## 📚 更多帮助

- **快速启动**：查看 `QUICKSTART.md`
- **API配置**：查看 `docs/api_credentials_setup.md`
- **项目架构**：查看 `README.md`
- **系统规范**：查看 `specs/vibe_coding_guide.md`

---

## 🎯 推荐运行顺序

1. **首次运行**：
   ```bash
   python test_credentials.py  # 验证配置
   python tests/test_style_mapper.py  # 测试映射器
   python examples/grade_example.py  # 测试评分器
   python examples/dialogue_example.py  # 完整流程示例
   ```

2. **交互式使用**：
   ```bash
   python main.py  # 开始交互式对话
   ```

3. **集成开发**：
   - 参考 `examples/dialogue_example.py`
   - 查看 `core/dialogue_manager.py` 的API

---

**现在就可以开始运行了！** 🚀
