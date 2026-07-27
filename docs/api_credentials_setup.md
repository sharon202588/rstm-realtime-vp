# API密钥配置指南

## ⚠️ 安全提醒

**重要**：API密钥是敏感信息，请务必：
- ✅ 使用环境变量存储密钥，不要硬编码到代码中
- ✅ 将 `.env` 文件添加到 `.gitignore`，不要提交到版本控制
- ✅ 定期轮换密钥
- ✅ 不要在不安全的环境中分享密钥

## 密钥映射说明

本项目只保存环境变量名和占位符，不应在文档或源码中填写真实密钥。

### 1. 豆包评分器API（REST API）

**用途**：CPAS评分判断，使用 `doubao-seed-2-0-lite-260428` 模型

**环境变量**：`ARK_API_KEY`

**你的密钥**：
```
your_ark_api_key_here
```

### 2. 豆包实时语音API（WebSocket API）

**用途**：实时语音交互，使用端到端实时语音大模型

**环境变量**：
- `DOUBAO_REALTIME_APP_ID`：新开通实时语音模型对应的 APP ID
- `DOUBAO_REALTIME_ACCESS_KEY`：同一模型对应的接入 Key

按官方实时对话文档（2026-07-10 更新），WebSocket 握手发送 `X-Api-App-ID`、`X-Api-Access-Key`、固定 `X-Api-App-Key`、`X-Api-Resource-Id: volc.speech.dialog`。该端点未列出单独 `X-Api-Key` 鉴权。`Secret Key` 不用于这个数据接口，也不写入项目。

## 配置方法

### 方法1：使用 .env 文件（推荐）

1. 在项目根目录创建 `.env` 文件：

```bash
# 豆包评分器API配置（REST API）
ARK_API_KEY=your_ark_api_key_here

# 新开通的端到端实时语音模型
DOUBAO_REALTIME_APP_ID=your_app_id_here
DOUBAO_REALTIME_ACCESS_KEY=your_realtime_access_key_here
```

2. 安装 python-dotenv（如果还没有）：

```bash
pip install python-dotenv
```

3. 在代码中加载环境变量：

```python
from dotenv import load_dotenv
import os

# 加载 .env 文件
load_dotenv()

# 现在可以使用环境变量
api_key = os.getenv("ARK_API_KEY")
realtime_app_id = os.getenv("DOUBAO_REALTIME_APP_ID")
realtime_access_key = os.getenv("DOUBAO_REALTIME_ACCESS_KEY")
```

### 方法2：系统环境变量

#### Windows PowerShell

```powershell
$env:ARK_API_KEY = "your_ark_api_key_here"
$env:DOUBAO_REALTIME_APP_ID = "your_app_id_here"
$env:DOUBAO_REALTIME_ACCESS_KEY = "your_realtime_access_key_here"
```

#### Windows CMD

```cmd
setx ARK_API_KEY "your_ark_api_key_here"
setx DOUBAO_REALTIME_APP_ID "your_app_id_here"
setx DOUBAO_REALTIME_ACCESS_KEY "your_realtime_access_key_here"
```

#### macOS / Linux

```bash
export ARK_API_KEY="your_ark_api_key_here"
export DOUBAO_REALTIME_APP_ID="your_app_id_here"
export DOUBAO_REALTIME_ACCESS_KEY="your_realtime_access_key_here"
```

要永久设置（添加到 `~/.bashrc` 或 `~/.zshrc`）：

```bash
echo 'export ARK_API_KEY="your_ark_api_key_here"' >> ~/.bashrc
echo 'export DOUBAO_REALTIME_APP_ID="your_app_id_here"' >> ~/.bashrc
echo 'export DOUBAO_REALTIME_ACCESS_KEY="your_realtime_access_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## 验证配置

创建测试脚本 `test_credentials.py`：

```python
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 检查密钥是否已配置
ark_api_key = os.getenv("ARK_API_KEY")
doubao_realtime_realtime_app_id = os.getenv("DOUBAO_REALTIME_APP_ID")
doubao_realtime_access_key = os.getenv("DOUBAO_REALTIME_ACCESS_KEY")

print("=" * 60)
print("API密钥配置检查")
print("=" * 60)

if ark_api_key:
    print(f"✅ ARK_API_KEY: {ark_api_key[:20]}...")
else:
    print("❌ ARK_API_KEY: 未配置")

if doubao_realtime_app_id:
    print(f"✅ DOUBAO_REALTIME_APP_ID: {doubao_realtime_app_id}")
else:
    print("❌ DOUBAO_REALTIME_APP_ID: 未配置")

if doubao_realtime_access_key:
    print(f"✅ DOUBAO_REALTIME_ACCESS_KEY: {doubao_realtime_access_key[:20]}...")
else:
    print("❌ DOUBAO_REALTIME_ACCESS_KEY: 未配置")

print("=" * 60)
```

运行测试：

```bash
python test_credentials.py
```

## 使用示例

### 初始化REST客户端（评分器）

```python
import os
from dotenv import load_dotenv
from doubao.rest_client import DoubaoRESTClient

load_dotenv()

# 初始化客户端
client = DoubaoRESTClient(
    api_key=os.getenv("ARK_API_KEY")
)
```

### 初始化WebSocket客户端（语音）

```python
import os
from dotenv import load_dotenv
from doubao.websocket_client import DoubaoWebSocketClient

load_dotenv()

# 初始化客户端
ws_client = DoubaoWebSocketClient(
    realtime_app_id=os.getenv("DOUBAO_REALTIME_APP_ID"),
    realtime_access_key=os.getenv("DOUBAO_REALTIME_ACCESS_KEY")
)
```

## 注意事项

1. **DOUBAO_REALTIME_ACCESS_KEY 的确认**：
   - 请查看 `docs/豆包实时语音API.md` 文档
   - 使用新开通模型页面显示的接入 Key，不使用已失效的试用凭证
   - 根据API文档中的认证方式选择正确的密钥

2. **密钥轮换**：
   - 定期检查密钥是否过期
   - 如果密钥泄露，立即在控制台重置

3. **生产环境**：
   - 使用密钥管理服务（如 AWS Secrets Manager、Azure Key Vault）
   - 不要将密钥存储在代码仓库中
   - 使用不同的密钥用于开发和生产环境

## 故障排查

### 问题1：找不到环境变量

**症状**：`ValueError: API key is required`

**解决方案**：
1. 确认 `.env` 文件在项目根目录
2. 确认已安装 `python-dotenv`：`pip install python-dotenv`
3. 确认代码中调用了 `load_dotenv()`

### 问题2：API调用失败

**症状**：401 Unauthorized 或 403 Forbidden

**解决方案**：
1. 检查密钥是否正确
2. 检查密钥是否过期
3. 检查API服务是否已开通
4. 查看API文档确认认证方式

### 问题3：WebSocket连接失败

**症状**：连接被拒绝或认证失败

**解决方案**：
1. 确认 `DOUBAO_REALTIME_APP_ID` 和 `DOUBAO_REALTIME_ACCESS_KEY` 都正确配置
2. 确认 APP ID 与接入 Key 属于同一个已开通的实时语音模型
3. 检查网络连接和防火墙设置

