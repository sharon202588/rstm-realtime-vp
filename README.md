# RSTM-SP: 自适应实时语音虚拟患者系统

## 项目简介

本项目是一个**研究导向的实时语音虚拟患者系统**，用于模拟医患沟通中**关系与情绪随沟通行为演化的过程**。系统基于 **SPIKES** 和 **VR-CoDES** 两个国际公认的临床沟通框架，通过 **CPAS (Clinical Performance Assessment Score)** 评分体系，结合 **RSTM (Relationship State Trajectory Model)** 关系状态轨迹模型，实现动态的、自适应的虚拟患者交互。

### 核心特性

- **实时语音交互**：使用豆包端到端实时语音大模型，实现低延迟、自然的语音对话
- **动态关系演化**：通过RSTM模型，根据医生沟通质量动态调整虚拟患者的关系状态和回应风格
- **结构化评分**：使用CPAS评分系统，客观评估医生沟通表现
- **7级风格映射**：将连续关系状态映射到7-level affective–interaction style，确保回应风格一致性

## 核心概念

### SPIKES 框架
SPIKES 是告知坏消息的标准流程，包含六个阶段：

- **S (Setting)** - 环境准备：确保私密、安静的环境
- **P (Perception)** - 感知评估：了解患者对病情的认知程度
- **I (Invitation)** - 邀请：询问患者希望如何接收信息
- **K (Knowledge)** - 知识传递：告知坏消息
- **E (Emotions)** - 情绪处理：识别并回应患者的情绪反应
- **S (Strategy/Summary)** - 策略总结：制定后续计划并总结

### VR-CoDES 框架
VR-CoDES (Verona Coding Definitions of Emotional Sequences) 用于评估医生对患者情绪的识别和回应能力，重点关注：
- **空间构建 (Space-Building)**：积极回应情绪，给予支持
- **中性/被动 (Neutral/Passive)**：机械式回应，缺乏情感共鸣
- **空间压缩 (Space-Reducing)**：忽视或阻断情绪表达

### CPAS 评分系统
CPAS 采用"安全优先、双轨评分"算法：

1. **Track A (任务完成度)**：评估医生是否有效完成 SPIKES 的相应阶段
   - 评分范围：-5 到 +2
   - 如果违反 P-I-K 安全协议，直接锁定为 -5

2. **Track B (共情能力)**：评估医生对患者情绪的处理质量
   - 评分范围：-3 到 +3
   - 基于 VR-CoDES 框架评估

3. **最终 CPAS 分数** = Track A + Track B

## 安全协议：P-I-K 规则

**核心原则**：在告知坏消息（K 阶段）之前，医生必须先完成：
- **P (Perception)**：了解患者的认知
- **I (Invitation)**：获得患者的同意

如果医生跳过 P 或 I 阶段直接告知坏消息，将被判定为 **PIK_Violation**，Track A 分数直接锁定为 -5。

## 技术架构

### 豆包模型API

本项目使用**豆包（Doubao）模型API**实现两个核心功能：

1. **评分判断**：使用 `doubao-seed-2-0-lite-260428` 模型进行CPAS评分
2. **语音交互**：使用端到端实时语音大模型API实现虚拟患者与医生的实时语音对话

### 豆包文本生成模型（评分器）

#### 模型信息

- **模型名称**：`doubao-seed-2-0-lite-260428`
- **用途**：CPAS评分判断，分析医生沟通质量
- **API端点**：`https://ark.cn-beijing.volces.com/api/v3/chat/completions`
- **协议**：REST API
- **认证方式**：Bearer Token（ARK_API_KEY）

#### 模型特性

- **高精度推理**：支持 reasoning_effort 参数（minimal/low/medium/high），确保评分准确性
- **长文本支持**：最大完成token数可达65535，适合处理完整对话历史
- **JSON输出**：支持结构化输出，直接返回符合CPAS评分规范的JSON结果

#### API调用示例

```python
from doubao.rest_client import DoubaoRESTClient, ReasoningEffort

# 初始化客户端
client = DoubaoRESTClient(api_key="your_ark_api_key")

# 调用评分接口
result = client.grade_dialogue(
    dialogue_history="对话历史文本...",
    grader_prompt="评分器提示词...",
    reasoning_effort=ReasoningEffort.MINIMAL
)
```

### 豆包端到端实时语音大模型

本项目使用**豆包端到端实时语音大模型API（RealtimeAPI）**来实现虚拟患者与医生的实时语音对话交互。

#### 为什么选择豆包语音模型？

1. **低延迟实时交互**：支持WebSocket协议，实现语音到语音的实时对话，满足医患沟通培训的真实场景需求
2. **多模式支持**：支持语音输入、文本输入等多种交互方式，灵活适配不同培训场景
3. **中文优化**：针对中文语音识别和合成进行了深度优化，确保医患沟通的准确性和自然度
4. **流式处理**：支持边发送边接收的流式交互方式，提供流畅的对话体验

#### 技术规格

**API协议**：
- **文本处理**：REST API（用于评分器文本生成，使用 doubao-seed-2-0-lite-260428 模型）
- **语音交互**：WebSocket API（用于实时语音对话）

**音频格式要求**：
- **客户端上传**：
  - 格式：PCM（脉冲编码调制，未压缩音频）
  - 声道：单声道
  - 采样率：16000 Hz
  - 采样点：int16
  - 字节序：小端序

- **服务端返回**：
  - 默认：OGG封装的Opus音频（兼顾压缩效率与传输性能）
  - 可选：PCM格式（需在StartSession事件中配置TTS参数）
    - 单声道、24000Hz采样率、32bit位深或16bit位深、小端序

**支持语言**：
- 中文（主要）
- 英语

**功能特性**：
- 支持自定义System Prompt（人设配置）
- 支持多种音色选择（包括精品音色和克隆音色）
- 支持流式和非流式二遍识别模式（提升识别准确率）
- 支持内置联网和外部RAG输入能力
- 支持角色扮演和声音复刻

#### 官方文档

详细API文档和示例代码请参考：
- [豆包端到端实时语音大模型API接入文档](https://www.volcengine.com/docs/6561/1594356?lang=zh)

#### 实现说明

- 所有豆包API调用封装在 `/doubao` 目录下的客户端模块中
- 使用原生REST API和WebSocket API，不使用OpenAI兼容SDK
- 遵循官方示例代码模式，确保兼容性和稳定性

## 项目结构

```
RSTM-SP/
├── README.md                    # 项目说明文档（本文件）
├── specs/                       # 规范文档
│   ├── grader_prompt.md        # 评分器提示词规范（冻结文件，请勿修改）
│   ├── patient_profile.md      # 虚拟患者配置文件（冻结文件，请勿修改）
│   ├── affective_interaction_mapping.md  # 7-level风格映射规范（冻结文件，请勿修改）
│   └── vibe_coding_guide.md    # 氛围编程说明文档（核心架构参考）
├── doubao/                     # 豆包API客户端封装
│   ├── __init__.py
│   ├── rest_client.py          # REST API客户端（评分器）
│   ├── websocket_client.py     # WebSocket API客户端（实时语音）
│   └── requirements.txt        # Python依赖包列表
├── rstm/                       # 关系状态轨迹模型
│   ├── __init__.py
│   ├── state_manager.py        # RSTM状态管理器（CCI和S(t)计算）
│   └── style_mapper.py         # 7-level风格映射器
├── core/                       # 系统核心模块
│   ├── __init__.py
│   └── dialogue_manager.py     # 对话管理器（Phase A→D流程）
└── examples/                   # 使用示例
    ├── grade_example.py        # CPAS评分器使用示例
    └── dialogue_example.py     # 完整对话流程示例
```

## 虚拟患者配置文件

`specs/patient_profile.md` 文件定义了标准化虚拟患者（SP - Simulated Patient）的身份和临床背景信息。

### 重要说明
- **状态：冻结 (FROZEN)**
- **版本：1.2**
- **修改限制**：此文件不得修改，内容必须原样注入系统上下文
- **原因**：任何对患者身份、背景或性格的修改都会影响培训场景的一致性和实验可比性

### 患者信息概览

**基本身份**：
- 姓名：张老师（58岁，男性）
- 职业：高中教师
- 家庭：已婚，妻子李华（55岁），12岁女儿，82岁母亲需要照顾
- 性格：理性、克制、有责任感，不愿让他人担心

**医疗背景**：
- 既往史：轻度高血压（药物控制），无吸烟史但长期接触二手烟
- 当前状况：体检发现肺部阴影，CT提示右上肺Ⅱ期癌变可能，等待活检确认
- 症状：轻度咳嗽、活动后气短、疲倦
- 情境：两周前接到复查电话，今天第一次正式见医生了解病情

### 使用要求

1. **原样注入**：必须将文件内容完整注入到系统提示词中，不得重新解释、总结或修改
2. **角色扮演**：虚拟患者应忽略AI自我描述，仅以患者身份自然发言
3. **语言风格**：每次发言保持2-4句自然语言长度，符合真实口语交流
4. **一致性**：在整个培训过程中保持患者身份、性格和背景的一致性

## 7-Level Affective–Interaction 风格映射规范

`specs/affective_interaction_mapping.md` 文件定义了从连续关系状态 S(t) 到离散 affective–interaction styles 的确定性映射。

### 重要说明
- **状态：冻结 (FROZEN)**
- **版本：1.2**
- **修改限制**：此文件不得修改，映射规则必须在运行时保持不变
- **原因**：任何对映射规则的修改都会影响实验的可比性和一致性

### 映射特点

- **确定性**：每个 S(t) 值唯一映射到一个风格级别
- **互斥性**：不同级别之间互不重叠
- **完备性**：覆盖整个 (-1, 1) 范围
- **区间规则**：
  - Level 4 (Neutral) 是唯一闭区间 [-0.10, +0.10]
  - 其他级别为半开区间

### 7-Level 风格定义

| Level | 名称 | 交互风格 | 状态范围 |
|-------|------|---------|---------|
| 1 | Agitated / Irritated | Reactive | [-1.00, -0.70) |
| 2 | Anxious / Worried | Anxious | [-0.70, -0.40) |
| 3 | Concerned / Downcast | Downcast | [-0.40, -0.10) |
| 4 | Neutral | Flat | [-0.10, +0.10] |
| 5 | Mildly Positive / Encouraging | Warm | (+0.10, +0.40] |
| 6 | Cooperative / Engaged | Engaged | (+0.40, +0.70] |
| 7 | Trusting / Reassured | Reassuring | (+0.70, +1.00] |

每个级别都包含详细的行为线索（Behavioral Cues），用于指导实时语音模型的输出风格。

## 评分器提示词规范

`specs/grader_prompt.md` 文件包含了完整的评分逻辑和输出格式规范。

### 重要说明
- **状态：冻结 (FROZEN)**
- **版本：1.2**
- **修改限制**：此文件不得修改，仅允许替换 `{{TARGET_DOCTOR_TURN_ID}}`、`{{TARGET_DOCTOR_UTTERANCE}}` 和 `{{PRECEDING_DIALOGUE_HISTORY}}`
- **原因**：任何对逻辑、评分规则或输出格式的修改都会影响实验的可比性

### 评分流程

1. **阶段识别 (Step 0)**
   - 分析医生的最后一条回复
   - 识别为 `SETTING`、`PERCEPTION`、`INVITATION`、`KNOWLEDGE`、`EMPATHY` 或 `STRATEGY_SUMMARY`

2. **安全门检查 (Step 1)**
   - 如果识别为 K 阶段，检查是否先完成了 P 和 I
   - 如果违反，触发 PIK_Violation 并锁定 Track A = -5

3. **双轨评分 (Step 2)**
   - Track A：评估任务完成质量
   - Track B：评估共情能力

4. **最终计算 (Step 3)**
   - CPAS = Track A + Track B

### 输出格式

评分器必须返回以下 JSON 格式：

```json
{
  "doctor_turn_id": "目标医生轮次ID",
  "grading_status": "scored",
  "target_response_extraction": "医生的目标回复原文",
  "inferred_stage": "SETTING|PERCEPTION|INVITATION|KNOWLEDGE|EMPATHY|STRATEGY_SUMMARY",
  "safety_check": {
    "status": "Safe|PIK_Violation",
    "missing_elements": "None|P|I|Both"
  },
  "scoring_breakdown": {
    "track_a_task": <整数>,
    "track_b_empathy": <整数>,
    "formula": "Track A + Track B"
  },
  "final_cpas_score": <整数>,
  "reasoning": "简要说明阶段、安全门、Track A和Track B的文字证据。"
}
```

## 实时语音虚拟患者界面

本项目提供面向学习者和研究者的浏览器语音界面。界面没有医生对话文本框，医生直接使用麦克风与虚拟患者交流。Windows 下可双击 `start_ui.cmd`；脚本会启动本地服务并打开界面。

```powershell
.\.venv\Scripts\python.exe ui_server.py
# 或
.\.venv\Scripts\python.exe main.py --ui
```

启动后打开 `http://127.0.0.1:7860`，在浏览器中允许麦克风权限，然后点击“开始对话”。页面加载不会连接外部模型；只有点击开始后才会连接豆包实时语音与评分服务。当前语音断句使用 1500 ms 自定义 VAD 平滑窗口：医生连续停顿约 1.5 秒后，系统才判定本轮发言结束并让患者回答。

界面自动跟随“交流语言”切换中文或英文。患者交互模式显示为“自适应交互”和“非自适应交互”：前者允许 CPAS 驱动 RSTM 状态变化；后者仅在开场采用 Level 3 `Concerned / Downcast`，随后依据固定病例与对话上下文自然回应，不进行 CPAS 评分或 RSTM 更新。对话记录使用固定高度的内部滚动区域；CPAS 区域显示“流程完成度”和“共情与互动质量”两条评分及逐轮历史。研究者可在会话开始前通过“查看与管理患者设定”读取冻结的默认病例，或创建、修改和删除保存在应用文件夹 `data/patient_templates.json` 中的自定义患者模板；会话进行中该入口会锁定，避免影响测试。自定义模板仅要求填写“临床事实”，其他模块可空；模板名称留空时会从临床事实的第一段短句在本地生成。保存设定只保存草稿，只有点击“使用此患者并生成新会话”才会切换VP身份并生成新的研究会话。

### 复制到其他 Windows 电脑

双击项目根目录的 `build_portable.cmd` 会在项目同级的 `RealtimeVoiceVP/` 发布目录中生成一个新版本文件夹。当项目位于 `F:\RSTM-SP` 时，发布位置为 `F:\RealtimeVoiceVP\RealtimeVoiceVP V1.0.0`，后续构建自动递增为 `V1.0.1`、`V1.0.2`，且不会覆盖旧版本。`LATEST.txt` 记录最新版本文件夹名称，每个版本内的 `VERSION.txt` 记录其版本号。

向其他电脑复制时，只复制某一个完整的 `RealtimeVoiceVP Vx.y.z/` 文件夹。目标电脑无需安装 Python，双击其中的 `start_ui.cmd` 即可启动；仍需联网访问豆包服务，并允许浏览器使用麦克风。版本文件夹中的 `.env` 含有明文 API 凭证，只能复制到受信任的电脑。

也可以复制项目源码文件夹，但不要依赖原电脑生成的 `.venv`。目标电脑需安装 64 位 Python 3.10-3.14，并在首次启动时联网；双击根目录 `start_ui.cmd` 后，脚本会自动重建本地环境并安装 `requirements-runtime.txt` 中的运行依赖。

自定义患者设定保存在应用文件夹的 `data/` 下，会随文件夹迁移。会话文字、研究事件及可选音频保存在本机应用文件夹中，不会自动上传到 Git。

实时语音只读取新开通模型对应的 `DOUBAO_REALTIME_APP_ID` 与 `DOUBAO_REALTIME_ACCESS_KEY`。按官方实时对话文档，握手使用 `X-Api-App-ID`、`X-Api-Access-Key` 和固定资源 ID `volc.speech.dialog`；该端点不使用单独 `X-Api-Key`，`Secret Key` 也不写入项目。`DOUBAO_GRADER_MODEL` 必须填写当前账号已开通的评分模型或推理端点 ID。测试界面会在每次开始场次时重新读取 `.env`。

测试界面固定使用 `breaking_bad_news` 场景。自适应组从 Level 3 `Concerned / Downcast`、`S(t)=-0.25` 开始，并可由 CPAS 驱动后续状态变化。非自适应组仅将 Level 3 用作开场表现，后续不再施加 Level 约束，不提交 CPAS 评分，也不更新 RSTM。CPAS 在后台只评价最近一次医生发言，完整既往对话仅作为上下文；患者回复不会等待评分结果。
自适应组只有在 RSTM 跨越 Level 边界时才更新远端患者风格；同一 Level 内的数值变化不会操作语音会话。跨级更新会等待本轮 `TTSEnded`，随后在原 WebSocket 和原 `dialog_id` 上发送全量 `UpdateConfig`，并在收到 `ConfigUpdated` 后继续收音。若更新被拒绝或短时间内未确认，系统才重建物理连接，并把同一 `dialog_id` 传入新 Session 以恢复对话上下文。

测试数据保存在 `logs/<session_id>/`：

- `research_events.jsonl`：完整文字对话、CPAS原始输出及简短理由、RSTM轨迹和连接事件。
- `audio/clinician_session.wav`：医生麦克风输入，16 kHz、单声道、PCM16。
- `audio/patient_session.wav`：虚拟患者输出，24 kHz、单声道、PCM16。

界面只保留一个“生成新会话”入口。它会停止当前连接并保存本轮音频，清空对话、未完成评分和RSTM轨迹，恢复初始互动状态，并生成唯一的新受试者编号和会话编号。当前选择的交流语言、交互模式与患者模板会保留，便于连续测试同一研究条件。每场研究测试的日志还会保存本轮实际使用的患者设定快照，避免后续修改自定义模板影响审计。

端口可通过 `--http-port` 和 `--ws-port` 修改。若修改WebSocket端口，例如改为 `9000`，请使用 `http://127.0.0.1:7860/?wsPort=9000` 打开页面。
## 快速开始

### 🚀 5分钟快速启动

1. **安装依赖**：
```bash
pip install -r requirements.txt
```

2. **配置API密钥**：
```bash
# 复制环境变量模板
cp env.example .env

# 编辑 .env 文件，填入你的API密钥
# ARK_API_KEY=your_api_key
# DOUBAO_REALTIME_APP_ID=your_app_id
# DOUBAO_REALTIME_ACCESS_KEY=your_realtime_access_key
```

3. **验证配置**：
```bash
python test_credentials.py
```

4. **运行系统**：
```bash
python main.py
```

详细说明请参考：[QUICKSTART.md](QUICKSTART.md)

## 安装和配置

### 安装依赖

```bash
# 安装项目所有依赖
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install requests>=2.31.0 websockets>=12.0 python-dotenv>=1.0.0
```

### 豆包API配置

在使用豆包语音模型前，需要完成以下配置：

1. **获取API凭证**：
   - 在火山引擎控制台创建应用并获取 `app_id` 和 `app_key`
   - 配置API访问权限

2. **环境变量配置**：
   ```bash
   # 豆包评分器API配置（REST API）
   ARK_API_KEY=your_ark_api_key
   
   # 豆包语音模型API配置（WebSocket API）
   DOUBAO_REALTIME_APP_ID=your_app_id
   DOUBAO_REALTIME_ACCESS_KEY=your_realtime_access_key
   DOUBAO_API_ENDPOINT=wss://openspeech.bytedance.com/api/v1/realtime
   ```

3. **初始化客户端**：
   ```python
   import os
   from doubao.websocket_client import DoubaoWebSocketClient
   from doubao.rest_client import DoubaoRESTClient, ReasoningEffort
   
   # 初始化REST客户端（评分器，使用 doubao-seed-2-0-lite-260428）
   rest_client = DoubaoRESTClient(
       api_key=os.getenv("ARK_API_KEY")
   )
   
   # 初始化WebSocket客户端（语音交互）
   ws_client = DoubaoWebSocketClient(
       realtime_app_id=os.getenv("DOUBAO_REALTIME_APP_ID"),
       realtime_access_key=os.getenv("DOUBAO_REALTIME_ACCESS_KEY")
   )
   ```

### 虚拟患者语音对话

使用豆包WebSocket API实现虚拟患者的实时语音交互：

1. **建立WebSocket连接**：连接到豆包实时语音API
2. **发送StartSession事件**：配置会话参数（音色、System Prompt等）
3. **发送音频数据**：实时发送医生语音（PCM格式）
4. **接收患者回复**：接收虚拟患者的语音回复（OGG/Opus或PCM格式）
5. **处理对话事件**：处理ASR、TTS等事件，维护对话状态

### 评分器文本处理

使用豆包REST API（`doubao-seed-2-0-lite-260428` 模型）进行CPAS评分：

1. **读取提示词模板**：从 `specs/grader_prompt.md` 读取评分器提示词
2. **替换变量**：将 `{{PRECEDING_DIALOGUE_HISTORY}}` 替换为实际对话历史
3. **调用API**：使用 `DoubaoRESTClient.grade_dialogue()` 方法调用评分接口
4. **解析结果**：提取JSON格式的CPAS评分结果

**示例代码**：
```python
from doubao.rest_client import DoubaoRESTClient, ReasoningEffort

# 读取提示词模板
with open("specs/grader_prompt.md", "r", encoding="utf-8") as f:
    grader_prompt = f.read()

# 初始化客户端
client = DoubaoRESTClient(api_key=os.getenv("ARK_API_KEY"))

# 进行评分
result = client.grade_dialogue(
    dialogue_history="Turn 1: Doctor: ...\nTurn 2: Patient: ...\nTurn 3: Doctor: ...",
    grader_prompt=grader_prompt,
    reasoning_effort=ReasoningEffort.MINIMAL
)

# 解析评分结果
cpas_score = result.get("final_cpas_score")
track_a = result.get("scoring_breakdown", {}).get("track_a_task")
track_b = result.get("scoring_breakdown", {}).get("track_b_empathy")
```

### 输入数据格式

评分器需要接收对话历史记录，格式应包含：
- 对话轮次（Turn 1, Turn 2, Turn 3...）
- 说话者身份（Doctor / Patient）
- 对话内容

### 变量替换

在使用 `grader_prompt.md` 时，需要将 `{{PRECEDING_DIALOGUE_HISTORY}}` 替换为实际的对话历史。

## 评分标准详解

### Track A: 任务完成度评分

- **+1 / +2 (完成)**：
  - P 阶段：提出清晰的问题了解患者认知
  - I 阶段：获得有效的许可
  - K 阶段：清晰传递信息
  - E 阶段：使用 N.U.R.S.E. 技巧回应情绪

- **0 (不完整)**：
  - 模糊、拖延或进展甚微

- **-1 / -2 (失败)**：
  - 信息不准确
  - 语言混乱
  - 主动回避职责

- **-5 (安全违规)**：
  - 违反 P-I-K 安全协议

### Track B: 共情能力评分

- **+2 到 +3 (空间构建)**：
  - 明确验证情绪
  - 邀请患者详细说明
  - 命名感受（N.U.R.S.E.）
  - 提供积极支持

- **0 到 +1 (中性/被动)**：
  - 机械式礼貌
  - "我理解"等套话
  - 纯临床信息，缺乏情感共鸣

- **-1 到 -3 (空间压缩)**：
  - 阻断行为
  - 打断患者
  - 忽视情绪线索
  - 虚假安慰（"会好起来的"）
  - 使用术语或生硬语言

## N.U.R.S.E. 技巧

在 E (Emotions) 阶段，医生应使用 N.U.R.S.E. 技巧：

- **N (Name)** - 命名情绪："你看起来很担心"
- **U (Understand)** - 理解："我能理解这让你感到害怕"
- **R (Respect)** - 尊重："你表现得很勇敢"
- **S (Support)** - 支持："我会一直陪着你"
- **E (Explore)** - 探索："能告诉我更多你的感受吗？"

## 注意事项

1. **实验可比性**：`grader_prompt.md` 和 `patient_profile.md` 文件已被冻结，任何修改都会影响不同实验之间的可比性。

2. **评分一致性**：确保评分器严格按照规范执行，避免主观偏差。

3. **边界情况**：当医生的回复混合多个 SPIKES 阶段时，选择主导意图进行评分。

4. **安全优先**：P-I-K 安全协议是硬性要求，违反即触发严重扣分。

## 未来改进方向

1. **多语言支持**：扩展对中文、英文等多种语言的支持
2. **细粒度分析**：增加对每个 SPIKES 阶段的详细评估
3. **学习建议**：基于评分结果生成个性化的改进建议
4. **批量处理**：支持批量评估多个对话记录
5. **可视化报告**：生成直观的评分报告和趋势分析

## 版本历史

- **v1.0.0** (当前版本)
  - 初始版本
  - 实现基于 SPIKES 和 VR-CoDES 的 CPAS 评分系统
  - 建立 P-I-K 安全协议检查机制
  - 定义标准化虚拟患者配置文件（张老师案例）
  - 集成豆包端到端实时语音大模型API（RealtimeAPI）
  - 实现REST API和WebSocket API客户端封装
  - 实现RSTM关系状态轨迹模型（确定性状态管理）
  - 实现7-level affective–interaction style映射
  - 实现完整对话流程管理器（Phase A → D）
  - 建立氛围编程说明文档（vibe_coding_guide.md）

## 联系方式

如有问题或建议，请通过项目仓库提交 Issue。

---

**重要提醒**：本项目用于临床沟通培训和质量评估，评分结果仅供参考，不应作为唯一评判标准。实际临床场景复杂多样，需要结合具体情况灵活应用。
