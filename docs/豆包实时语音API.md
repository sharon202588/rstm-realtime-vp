<span id="5cee3196"></span>
# 1 接口功能
豆包端到端实时语音大模型API即RealtimeAPI支持低延迟、多模式交互，可用于构建语音到语音的对话工具。该API支持中文和英语两大语种，目前只支持WebSocket协议连接到此API，同时支持客户边发送数据边接收数据的流式交互方式。
<span id="db7e1fd6"></span>
## 1.1 产品约束

1. 不同端到端模型版本的功能差异如下所示，其中未特别标注的功能，均为所有版本通用支持


| | | | \
|功能 |O版本 |SC版本 |
|---|---|---|
| | | | \
|精品音色（vv、xiaohe、yunzhou、xiaotian） |✅ |❌ |
| | | | \
|System Prompt开放配置 |✅ |✅ |
| | | | \
|克隆音色（ICL_或者S_开头的音色名称） |❌ |✅ |


   * O版本和SC版本都支持客户配置System Prompt，但是具体的配置字段会存在差异：
      * O版本可以配置bot_name、system_role、speaking_style字段，参考人设部分
      * SC版本可以配置character_manifest字段，参考角色描述部分
2. 客户端上传音频格式要求PCM（脉冲编码调制，未经压缩的的音频格式）、单声道、采样率16000、每个采样点用`int16`表示、字节序为小端序。
3. 服务端默认返回的是 OGG 封装的 Opus 音频，兼顾压缩效率与传输性能。
4. 若客户端在 StartSession事件中增加TTS配置，服务端可返回 PCM 格式的音频流。具体请求参数如下所示：
   * 单声道、24000Hz 采样率、32bit位深、字节序为小端序；

```JSON
{
    "tts" : {
        "audio_config": {
            "channel": 1,
            "format": "pcm",
            "sample_rate": 24000
        }
    }
}
```


   * 单声道、24000Hz 采样率、16bit位深、字节序为小端序；

```JSON
{
    "tts" : {
        "audio_config": {
            "channel": 1,
            "format": "pcm_s16le",
            "sample_rate": 24000
        }
    }
}
```


5. 端到端模型O版本服务端已新增 4 个音色，客户端需在 StartSession事件中的TTS 配置指定对应的发音人，默认为vv音色。
   1. zh_female_vv_jupiter_bigtts：对应vv音色，活泼灵动的女声，有很强的分享欲
   2. zh_female_xiaohe_jupiter_bigtts：对应xiaohe音色，甜美活泼的女声，有明显的台湾口音
   3. zh_male_yunzhou_jupiter_bigtts：对应yunzhou音色，清爽沉稳的男声
   4. zh_male_xiaotian_jupiter_bigtts：对应xiaotian音色，清爽磁性的男声

```JSON
{
    "tts": {
        "speaker": {{STRING}}
    }
}
```


6. 端到端模型SC版本服务端新增21个官方克隆音色，客户端在使用这些音色时候需要在StartSession事件中的TTS 配置指定对应的克隆音色。同时，角色描述在服务端已经配置好了，客户端在请求API时候无需配置character_manifest字段。
   1. ICL_zh_female_aojiaonvyou_tob
   2. ICL_zh_female_bingjiaojiejie_tob
   3. ICL_zh_female_chengshujiejie_tob
   4. ICL_zh_female_keainvsheng_tob
   5. ICL_zh_female_nuanxinxuejie_tob
   6. ICL_zh_female_tiexinnvyou_tob
   7. ICL_zh_female_wenrouwenya_tob
   8. ICL_zh_female_wumeiyujie_tob
   9. ICL_zh_female_xingganyujie_tob
   10. ICL_zh_male_aiqilingren_tob
   11. ICL_zh_male_aojiaogongzi_tob
   12. ICL_zh_male_aojiaojingying_tob
   13. ICL_zh_male_aomanshaoye_tob
   14. ICL_zh_male_badaoshaoye_tob
   15. ICL_zh_male_bingjiaobailian_tob
   16. ICL_zh_male_bujiqingnian_tob
   17. ICL_zh_male_chengshuzongcai_tob
   18. ICL_zh_male_cixingnansang_tob
   19. ICL_zh_male_cujingnanyou_tob
   20. ICL_zh_male_fengfashaonian_tob
   21. ICL_zh_male_fuheigongzi_tob
7. 除了官方克隆音色之外，客户还可以在火山豆包语音控制台开通、上传音频训练自定义克隆音色等功能。
   1. 购买入口在豆包端到端实时语音大模型商品里面，需要注意的是：购买克隆音色之后目前是分钟级生效，即2分钟之后才可以发起音色注册请求

<div style="text-align: center"><img src="https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/0ea61da842ff445097d978cd77f034d7~tplv-goo7wpa0wc-image.image" width="2788px" /></div>


   2. 注册克隆音色[参考文档](https://www.volcengine.com/docs/6561/1305191)，和传统的声音复刻相比有如下注意事项：
      1. 端到端模型仅对中文有较好支持，其他语种效果暂时还不能保证
      2. 在端到端模型里注册克隆音色时候，强烈推荐带上对应的音频文本，保证模型克隆效果
      3. 注册端到端模型的复刻音色请求所需参数，未提及参数对端到端链路不生效无需填写

```JSON
curl -L -X POST 'https://openspeech.bytedance.com/api/v1/mega_tts/audio/upload' \
-H 'Authorization: Bearer; your-access-key' \
-H 'Resource-Id: volc.megatts.voiceclone' \
-H 'Content-Type: application/json' \
-d '{
    "speaker_id": "S_123456",
    "appid": "12345678",
    "audios": [
        {
            "audio_bytes": "必填，二进制音频字节，需对二进制音频进行base64编码",
            "text":"必填，音频所对应的文本，可以让用户按照该文本念诵，服务会对比音频与该文本的差异。若差异过大会返回1109 WERError",
            "audio_format": "wav"
        }
    ],
    "source": 2
}'
```


8. 限流条件分为QPM和TPM，QPM全称query per minute，这里的query对应StartSession事件，即在一个AppID下面每分钟的StartSession事件不能超过配额值（默认60QPM）。TPM全称tokens per minute，即一分钟所消耗的全部token不能超过对应的配额值（默认10000TPM）。

<span id="0337adc7"></span>
## 1.2 最佳实践

1. 系统最初仅支持麦克风输入，现已逐步扩展，支持文本和录音文件作为输入源。具体说明如下：
   1. **麦克风输入**
      1. 采用流式输入输出架构，音频会实时上传。
      2. 客户端无需额外发送静音片段。
   2. **纯文本输入**
      1. 支持直接以文本形式发起对话。
      2. 服务端会自动补充静音片段，保证流式链路的完整性。

```JSON
{
    "dialog": {
        "extra": {
            "input_mod": "text"
        }
    }
}
```


   3. **录音文件输入**
         1. 支持将录音文件作为输入源，但是需要将录音文件改为流式发送，即发送20ms的音频包休眠20ms。
         2. 对于采样率 16k、位深 int16 的pcm音频而言，20ms 的音频包大小为 640 字节。
         3. 服务端同样会自动补充静音片段，保持与麦克风实时流式输入一致的处理逻辑。

```JSON
{
    "dialog": {
        "extra": {
            "input_mod": "audio_file"
        }
    }
}
```


2. 在客户端发送 FinishSession 事件后，系统将不再返回任何事件。但客户端仍可复用与火山语音网关之间的 WebSocket 连接。若需发起新的会话，客户端需重新从 StartSession 事件开始。


![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/7fbb240f4a9749899fe78a4bfd4bdd5c~tplv-goo7wpa0wc-image.image =1962x)

3. 在没有对话需求时候，可以发送FinishSession事件结束会话。如果不想复用websocket连接，可以继续发送FinishConnection事件，释放对应的websocket连接。
4. 推荐客户端在事件的 optional 字段中携带 event 和 session ID，以降低开发成本，并将事件处理的复杂性交由火山语音服务端负责。
5. 客户在集成端到端语音合成模型过程中，使用 ChatTTSText 进行音频合成请求的最佳实践方法，其中黄色部分需要客户实现：

![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/762ca135f7a34d198e015e43fcc2a720~tplv-goo7wpa0wc-image.image =3674x)

<span id="f62fb160"></span>
# 2 接口说明
WebSocket是一种广泛支持的实时数据传输API，也是服务器应用程序中连接到豆包端到端实时语音大模型API的最佳选择。在客户服务器上集成此API时候，可以通过WebSocket直接连接到实时语音大模型API，具体鉴权参数可以在火山控制台获取。
<span id="e157f85e"></span>
## 2.1 ws连接详细信息

* 通过WebSocket建立连接需要以下连接信息：


| | |||| \
|URL |wss://openspeech.bytedance.com/api/v3/realtime/dialogue | | | |
|---|---|---|---|---|
| | | | | | \
|Request Headers |\
| |Key |说明 |是否必须 |Value示例 |
|^^| | | | | \
| |X-Api-App-ID |\
| | |使用火山引擎控制台获取的APP ID，可参考 [控制台使用FAQ-Q1](https://www.volcengine.com/docs/6561/196768#q1%EF%BC%9A%E5%93%AA%E9%87%8C%E5%8F%AF%E4%BB%A5%E8%8E%B7%E5%8F%96%E5%88%B0%E4%BB%A5%E4%B8%8B%E5%8F%82%E6%95%B0appid%EF%BC%8Ccluster%EF%BC%8Ctoken%EF%BC%8Cauthorization-type%EF%BC%8Csecret-key-%EF%BC%9F) |是 |\
| | | | |123456789 |
|^^| | | | | \
| |X-Api-Access-Key |\
| | |使用火山引擎控制台获取的Access Token，可参考 [控制台使用FAQ-Q1](https://www.volcengine.com/docs/6561/196768#q1%EF%BC%9A%E5%93%AA%E9%87%8C%E5%8F%AF%E4%BB%A5%E8%8E%B7%E5%8F%96%E5%88%B0%E4%BB%A5%E4%B8%8B%E5%8F%82%E6%95%B0appid%EF%BC%8Ccluster%EF%BC%8Ctoken%EF%BC%8Cauthorization-type%EF%BC%8Csecret-key-%EF%BC%9F) |是 |\
| | | | |your-access-key |\
| | | | | |
|^^| | | | | \
| |X-Api-Resource-Id |\
| | |表示调用服务的资源信息 ID |\
| | |固定值：volc.speech.dialog |是 |\
| | | | |volc.speech.dialog |\
| | | | | |
|^^| | | | | \
| |X-Api-App-Key |固定值 |是 |PlgvMymc7f3tQnJ6 |
|^^| | | | | \
| |X-Api-Connect-Id |\
| | |用于追踪当前连接情况的标志 ID |\
| | |建议用户传递，便于排查连接情况 |否 |d1dcd999-9a9e-4ed6-b227-8649e946f6c4 |


* 在 websocket 握手成功后，会返回如下Response header


| | | | \
|Key |说明 |Value示例 |
|---|---|---|
| | | | \
|X-Tt-Logid |服务端返回的 logid，建议用户获取和打印方便定位问题 |20250506234111719BC62BBA7C4C0C635A |

<span id="8c513a38"></span>
## 2.2 WebSocket二进制协议
豆包端到端实时语音大模型API使用二进制协议传输数据，协议由4字节的header、optioanl、payload size和payload三部分组成，其中：

* header用于描述消息类型、序列化方式以及压缩格式等信息
* optional可选字段
   * sequence字段
   * event字段，用于描述链接过程中状态管理的预定义事件
   * connect id size/ connect id字段，用于描述连接类事件的标识
   * session id size/ session id 字段，用于描述会话类事件的标识
   * error code: 仅用于错误数据包，描述错误信息
* payload size代表payload的长度
* payload是具体负载的内容，依据不同的消息类型装载不同的内容

<span id="14a3f1a3"></span>
### header二进制数据

| | | | | \
|Byte |Left-4bit |Right-4bit |说明 |
|---|---|---|---|
| | | | | \
|0 |Protocol Version | |目前只有v1，固定0b0001 |
|^^| | | | \
| | |Header Size |目前只有4字节固定0b0001 |
| | | | | \
|1 |Message Type |Message type specific flags |详细见下面消息说明 |
| | | | | \
|2 |Serialization method | |* 0b0000：Raw（无特殊序列化，主要针对二进制音频数据） |\
| | | |* 0b0001：JSON（主要针对文本类型消息） |
|^^| | | | \
| | |Compression method |\
| | | |* 0b0000：无压缩（**推荐**） |\
| | | |* 0b0001：gzip |
| | || | \
|3 |0x00 | |Reserved |

<span id="065ab2ba"></span>
#### Mesage Type

| | | | \
|Message Type |含义 |说明 |
|---|---|---|
| | | | \
|0b0001 |Full-client request |客户端发送文本事件的消息类型 |
| | | | \
|0b1001 |Full-server response |服务器返回的文本事件的消息类型 |
| | | | \
|0b0010 |Audio-only request |客户端发送音频数据的消息类型 |
| | | | \
|0b1011 |Audio-only response |服务器返回音频数据的消息类型 |
| | | | \
|0b1111 |Error information |服务器返回的错误事件的消息类型 |

<span id="a1967b21"></span>
### Message type specific flags
Optional可选字段code、sequence、event取决于Message type specific flags，而connect id和session id取决于事件类型。如果设置对应flag请**按照表格顺序**进行二进制组装。目前支持的全集如下所示：

| | | | | \
|字段 |长度（Byte） |说明 |Message type specific flags |
|---|---|---|---|
| | | | | \
|code |4 |【可选】错误码code |* 0b1111：错误数据包 |
| | | | | \
|sequence |\
| |4 |\
| | |【可选】描述客户端的事件序号 |\
| | | |* 0b0000：没有sequence字段 |\
| | | |* 0b0001：序号大于 0 的非终端数据包 |\
| | | |* 0b0010：最后一个无序号的数据包 |\
| | | |* 0b0011：最后一个序号小于 0 的数据包，一般用-1表示 |
| | | | | \
|event |4 |【必须】描述连接过程中状态管理的预定义事件，详细参考[实时对话事件](https://bytedance.larkoffice.com/docx/JwKydEGDkojKxHxOrzNcYeewnyd#share-NceddeBUkot54QxBOemcYsKknFe)中的事件ID |* 0b0100：携带事件ID |\
| | | | |\
| | | | |
| | | | | \
|connect id size |4 |【可选】客户事件携带的connect id对应的长度，只有Connect事件才能携带此字段 |—— |\
| | | | |
| | | |^^| \
|connect id |取决于connect id size |【可选】客户生成的connect id | |
| | | |^^| \
|session id size |4 |【必须】客户事件携带的session id对应的长度，只有Session级别的事件携带此字段 | |
| | | |^^| \
|session id |取决于session id size |【必须】客户事件携带的session id | |

<span id="524c5654"></span>
### 具体的payload size和payload
payload可以放音频二进制数据，也可以放类似StartSession事件中的json数据。

| | | | \
|字段 |长度（Byte） |说明 |
|---|---|---|
| | | | \
|payload size |4 |paylaod长度 |
| | | | \
|payload |长度取决于payload size |payload内容，可以是二进制音频数据，也可以是json字符串 |

<span id="b52b5df8"></span>
#### 错误帧payload
```Plain Text
{
    "error": {{STRING}}
}
```

<span id="62b7be6c"></span>
## 2.3 实时对话事件
通过WebSocket连接到豆包端到端实时语音大模型API之后，可以调用`S2S模型`进行语音到语音的对话。需要**发送客户端事件**来启动操作，并**监听服务器事件**以采取对应的操作。
<span id="2e9c0e94"></span>
### 客户端事件

| | | | | | \
|事件ID |事件定义 |事件类型 |说明 |示例 |
|---|---|---|---|---|
| | | | | | \
|1 |StartConnection |Connect类事件 |\
| | | |Websocket 阶段声明创建连接 |```JSON |\
| | | | |{} |\
| | | | |``` |\
| | | | | |
| | |^^| |^^| \
|2 |FinishConnection | |断开websocket连接，后面需要重新发起websocket连接 | |
| | | | | | \
|100 |\
| |StartSession |\
| | |Session类事件 |\
| | | |Websocket 阶段声明创建会话，其中： |\
| | | | |\
| | | |* end_smooth_window_ms字段用于客户调整判断用户停止说话的时间，默认1500ms，取值范围[500ms, 50s] |\
| | | |* enable_custom_vad字段用于标识是否开启自定义判断用户说话停止的参数，true代表开启，默认为false |\
| | | |* enable_asr_twopass字段用于标识是否开启非流式模型识别能力，true代表开启，默认为false |\
| | | |* bot_name字段用于修改基础人设信息，例如人名、来源等，默认为豆包，只针对**O版本**生效 |\
| | | |* system_role字段用于配置背景人设信息，描述角色的来源、设定等，例如“你是大灰狼、用户是小红帽，用户逃跑时你会威胁吃掉他。”，只针对**O版本**生效 |\
| | | |* speaking_style字段用于配置模型对话风格，例如“你说话偏向林黛玉。”、“你口吻拽拽的。”等，只针对**O版本**生效 |\
| | | |* 长度限制：bot_name 最长不超过 20 个字符 |\
| | | |* dialog_id字段用于加载相同dialog id的对话记录，进而提升模型上下文记忆能力，目前服务端仅支持最近20轮QA对 |\
| | | |* character_manifest字段用于填充模型所扮演角色的描述信息，只针对**SC版本**生效 |\
| | | |* location字段用于客户端传入用户位置信息，以提升联网搜索结果的精准度，关闭内置联网时候无需此字段 |\
| | | |   * country：默认中国 |\
| | | |   * country_code：默认CN |\
| | | |* strict_audit字段用于声明安全审核等级，true代表严格审核、false代表普通审核，默认为true |\
| | | |* audit_response字段用于指定用户query命中安全审核之后的自定义回复话术 |\
| | | |* enable_volc_websearch字段用于开关内置联网功能，开启内置联网参考火山引擎控制台[融合信息搜索API](https://www.volcengine.com/docs/85508/1650263) |\
| | | |* volc_websearch_type字段用于指定搜索服务类型 |\
| | | |   * web_summary代表总结版，不传此参数默认为总结版 |\
| | | |   * web代表普通版，需要客户指定才能生效 |\
| | | |* volc_websearch_api_key字段用于指定客户开通的融合信息搜索API服务访问密钥 |\
| | | |* volc_websearch_result_count字段用于指定搜索结果条数，最多10条，默认10条 |\
| | | |* volc_websearch_no_result_message字段用于指定没有搜索结果时候的回复话术 |\
| | | |* input_mod使用text(纯文本)或者audio_file(录音文件)模式时，服务端会自动补充静音数据保证输入效果对齐麦克风模式 |\
| | | |* 【**必传参数**】model字段用于区分端到端模型版本，其中**O版本**特点支持内置联网和外部RAG输入能力，**SC版本**特点支持声音复刻，取值字段枚举：O、SC，默认为O |```JSON |\
| | | | |{ |\
| | | | |    "asr": { |\
| | | | |        "extra": { |\
| | | | |            "end_smooth_window_ms": {{INT}}, |\
| | | | |            "enable_custom_vad": {{BOOLEAN}}, |\
| | | | |            "enable_asr_twopass": {{BOOLEAN}}, |\
| | | | |        } |\
| | | | |    }, |\
| | | | |    "dialog": { |\
| | | | |        "bot_name": {{STRING}}, |\
| | | | |        "system_role": {{STRING}}, |\
| | | | |        "speaking_style": {{STRING}}, |\
| | | | |        "dialog_id": {{STRING}}, |\
| | | | |        "character_manifest": {{STRING}}, |\
| | | | |        "location": { |\
| | | | |            "longitude": {{Float64}}, |\
| | | | |            "latitude": {{Float64}}, |\
| | | | |            "city": {{STRING}}, |\
| | | | |            "country": {{STRING}}, |\
| | | | |            "province": {{STRING}}, |\
| | | | |            "district": {{STRING}}, |\
| | | | |            "town": {{STRING}}, |\
| | | | |            "country_code": {{STRING}}, |\
| | | | |            "address": {{STRING}} |\
| | | | |        }, |\
| | | | |        "extra" : { |\
| | | | |            "strict_audit": {{BOOLEAN}}, |\
| | | | |            "audit_response": {{STRING}}, |\
| | | | |            "enable_volc_websearch": {{BOOLEAN}}, |\
| | | | |            "volc_websearch_type": {{STRING}}, |\
| | | | |            "volc_websearch_api_key": {{STRING}}, |\
| | | | |            "volc_websearch_result_count": {{INT}}, |\
| | | | |            "volc_websearch_no_result_message": {{STRING}}, |\
| | | | |            "input_mod": {{STRING}}, |\
| | | | |            "model": {{STRING}} |\
| | | | |        } |\
| | | | |    } |\
| | | | |} |\
| | | | |``` |\
| | | | | |\
| | | | | |
| | |^^| | | \
|102 |FinishSession |\
| | | |客户端声明结束会话，后面可以复用websocket连接 |\
| | | | |```JSON |\
| | | | |{} |\
| | | | |``` |\
| | | | | |
| | |^^| | | \
|200 |TaskRequest | |客户端上传音频 |音频二进制数据 |
| | |^^| | | \
|300 |SayHello |\
| | | |客户端提交打招呼文本 |\
| | | | |```JSON |\
| | | | |{ |\
| | | | |    "content": {{STRING}} |\
| | | | |} |\
| | | | |``` |\
| | | | | |
| | |^^| | | \
|500 |ChatTTSText |\
| | | |用户query之后，模型会生成闲聊结果。如果客户判断用户query不需要闲聊结果，可以指定文本合成音频 |\
| | | | |```Plain Text |\
| | | | |{ |\
| | | | |    "start": {{BOOLEAN}}, |\
| | | | |    "content": {{STRING}}, |\
| | | | |    "end": {{BOOLEAN}} |\
| | | | |} |\
| | | | |``` |\
| | | | | |
| | |^^| | | \
|501 |\
| |ChatTextQuery |\
| | | |用户输入文本query，模型输出闲聊结果。若用户判断不采用音频输入进行query，可使用该事件输入文本进行query |\
| | | | |```JSON |\
| | | | |{ |\
| | | | |    "content": {{STRING}} |\
| | | | |} |\
| | | | |``` |\
| | | | | |
| | |^^| | | \
|502 |\
| |ChatRAGText |\
| | | |用户query之后，模型会生成闲聊结果。如果客户判断用户query不需要闲聊结果，可以输入外部RAG知识，通过模型的总结和口语化改写之后输出对应音频。外部RAG输入整体长度不超过4K个字符。 |\
| | | | |```JSON |\
| | | | |{ |\
| | | | |    "external_rag": {{STRING}} |\
| | | | |} |\
| | | | |``` |\
| | | | | |
#{.custom-md-table}# 
<style> 
	.custom-md-table th:nth-of-type(1){min-width:100px;} 
	.custom-md-table th:nth-of-type(2){min-width:100px;} 
	.custom-md-table th:nth-of-type(3){min-width:100px;} 
	.custom-md-table th:nth-of-type(4){min-width:400px;} 
	.custom-md-table th:nth-of-type(5){min-width:100px;} 
</style>
<span id="57205643"></span>
备注：

* Websocket阶段：在 HTTP 建立连接之后Upgrade 
* 客户端在发送FinishSession事件之后，websocket连接不会断开，客户端可以继续复用，复用时候需要再发送一次StartSession事件，即重新初始化会话
* Message Type = 0b0001，Message type specific flags = 0b0100，StartConnection事件二进制帧对应的字节数组示例：
   * [17 20 16 0 0 0 0 1 0 0 0 2 123 125]
* Message Type = 0b0001，Message type specific flags = 0b0100，SessionID = 75a6126e-427f-49a1-a2c1-621143cb9db3，jsonPayload = {"dialog":{"bot_name":"豆包","dialog_id":"","extra":null}}，StartSession事件二进制帧对应的字节数组示例：

```Plain Text
 [17 20 16 0 0 0 0 100 0 0 0 36 55 53 97 54 49 50 54 101 45 52 50 55 102 45 52 57 97 49 45 97 50 99 49 45 54 50 49 49 52 51 99 98 57 100 98 51 0 0 0 60 123 34 100 105 97 108 111 103 34 58 123 34 98 111 116 95 110 97 109 101 34 58 34 232 177 134 229 140 133 34 44 34 100 105 97 108 111 103 95 105 100 34 58 34 34 44 34 101 120 116 114 97 34 58 110 117 108 108 125 125]
```


* ChatTTSText事件请求示例：
   * 第一包json示例

```Plain Text
{
    "start": true,
    "content": "今天是",
    "end": false
}
```


   * 中间包，用于流式上传待合成音频的文本

```Plain Text
{
    "start": false,
    "content": "星期二。",
    "end": false
}
```


   * 最后一包，若用户在音频播报过程中发起新的 query 导致中断，且合成音频的 end 包尚未发送，此时无需再下发该 end 包，以避免多余流程或状态异常。

```JSON
{
    "start": false,
    "content": "",
    "end": true
}
```


* ChatRAGText事件请求中的external_rag是一个json数组字符串，对应的json描述：

```JSON
{
    "title": {{STRING}},
    "content": {{STRING}},
}
```

### 服务端事件

| 事件ID | 事件定义 | 事件类型 | 说明 | 示例 |
| --- | --- | --- | --- | --- |
| 50 | ConnectionStarted | Connect类 | 成功建立连接 | ```json |\
||||| {} |\
||||| ``` |
| 51 | ConnectionFailed | ^^ | 建立连接失败 | ```json |\
||||| { |\
|||||     "error": {{STRING}} |\
||||| } |\
||||| ``` |
| 52 | ConnectionFinished | ^^ | 连接结束 | ```json |\
||||| {} |\
||||| ``` |
| 150 | SessionStarted | Session类 | 成功启动会话，返回的dialog id用于接续最近的对话内容，增加模型智能度 | ```json |\
||||| { |\
|||||     "dialog_id": {{STRING}} |\
||||| } |\
||||| ``` |
| 152 | SessionFinished | ^^ | 会话已结束 | ```json |\
||||| {} |\
||||| ``` |
| 153 | SessionFailed | ^^ | 会话失败 | ```json |\
||||| { |\
|||||     "error": {{STRING}} |\
||||| } |\
||||| ``` |
| 154 | UsageResponse | ^^ | 每一轮交互对应的用量信息 | ```json |\
||||| { |\
|||||     "usage": { |\
|||||         "input_text_tokens": {{INT}}, |\
|||||         "input_audio_tokens": {{INT}}, |\
|||||         "cached_text_tokens": {{INT}}, |\
|||||         "cached_audio_tokens": {{INT}}, |\
|||||         "output_text_tokens": {{INT}}, |\
|||||         "output_audio_tokens": {{INT}}, |\
|||||     } |\
||||| } |\
||||| ``` |
| 350 | TTSSentenceStart | ^^ | 合成音频的起始事件，tts\_type取值类型有： | ```json |\
||||| { |\
|||| - audit\_content\_risky（命中安全审核音频） |     "tts_type": {{STRING}}, |\
|||| 	 |     "text" : {{STRING}}, |\
|||| - chat\_tts\_text（客户文本合成音频） |     "question_id": {{STRING}}, |\
|||| 	 |     "reply_id": {{STRING}}, |\
|||| - network（内置联网音频） | } |\
|||| 	 | ``` |\
|||| - external\_rag（外部RAG总结音频） |\
|||| 	 |\
|||| - default（闲聊音频） |
| 351 | TTSSentenceEnd | ^^ | 合成音频的分句结束事件 | ```json |\
||||| {} |\
||||| ``` |
| 352 | TTSResponse | ^^ | 返回模型生成的音频数据 | payload装载二进制音频数据 |
| 359 | TTSEnded | ^^ | 模型一轮音频合成结束事件 | ```json |\
||||| {} |\
||||| ``` |
| 450 | ASRInfo | ^^ | 模型识别出音频流中的首字返回的事件，用于打断客户端的播报 | ```json |\
||||| { |\
|||||     "question_id": {{STRING}} |\
||||| } |\
||||| ``` |
| 451 | ASRResponse | ^^ | 模型识别出用户说话的文本内容 | ```json |\
||||| { |\
|||||     "results": [ |\
|||||       { |\
|||||         "text": {{STRING}}, |\
|||||         "is_interim": {{BOOLEAN}} |\
|||||       } |\
|||||     ] |\
||||| } |\
||||| ``` |
| 459 | ASREnded | ^^ | 模型认为用户说话结束的事件 | ```json |\
||||| {} |\
||||| ``` |
| 550 | ChatResponse | ^^ | 模型回复的文本内容 | ```json |\
||||| { |\
|||||   "content": {{STRING}}, |\
||||| } |\
||||| ``` |
| 553 | ChatTextQueryConfirmed | ^^ | ChatTextQuery请求对应的ack | ```json |\
||||| { |\
|||||   "question_id": {{STRING}}, |\
||||| } |\
||||| ``` |
| 559 | ChatEnded | ^^ | 模型回复文本结束事件 | ```json |\
||||| {} |\
||||| ``` |
#{.custom-md-table}# 
<style> 
	.custom-md-table th:nth-of-type(1){min-width:100px;} 
	.custom-md-table th:nth-of-type(2){min-width:100px;} 
	.custom-md-table th:nth-of-type(3){min-width:100px;} 
	.custom-md-table th:nth-of-type(4){min-width:400px;} 
	.custom-md-table th:nth-of-type(5){min-width:100px;} 
</style>
备注：

* 服务器事件中json paylod可能会多返回一些字段，客户端无需关心
* Message type specific flags = 0b0100，session id =3c791a7d-227a-4446-993b-24f9e302cc98，TTSResponse事件示例：
   * [17 180 0 0 0 0 1 96 0 0 0 36 51 99 55 57 49 97 55 100 45 50 50 55 97 45 52 52 52 54 45 57 57 51 98 45 50 52 102 57 101 51 48 50 99 99 57 56 0 0 7 252 79 103 103 83 0 0 64 129 32 0 0 0 0 0 132 149 185 182 172 8 0 0 169 57 249 174 1 71 104 139 98 229 167 232 122 108 0 183 60 54 43 137 197 126 20 248 201 174]

<span id="67102c8e"></span>
# 3 快速开始
<span id="980108d4"></span>
## Python示例
<Attachment link="https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_afd6058d244c0dc6f6e1b08c5cbb34b7.zip" name="realtime_dialog.zip.zip" size="220.33KB"></Attachment>
<span id="a5b89380"></span>
## Go示例

<Attachment link="https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/4674d51c2bf841089595e3e4830a7511~tplv-goo7wpa0wc-image.image" name="realtime_dialog.zip" ></Attachment>
## Java示例

<Attachment link="https://portal.volccdn.com/obj/volcfe/cloud-universal-doc/upload_2a10579e3e9b8ac9a9041bcc1b70eb23.zip" name="realtime_dialog.zip" size="124.83KB"></Attachment>
暂时无法在飞书文档外展示此内容

您可以通过以下步骤，快速体验与 Realtime 模型API实时对话的功能。

1. 下载realtime_dialog.zip文件到本地，依据操作系统类型对`gordonklaus/portaudio`依赖进行安装：
   1. macOS：

```Bash
brew install portaudio
```


   2. CentOS：

```Bash
sudo yum install -y portaudio portaudio-devel
```


   3. Debian/Ubuntu：

```Shell
sudo apt-get install portaudio19-dev
```


2. 安装后在项目下运行：

```Shell
go执行命令：go run . -v=0
python执行命令：python main.py
```

4 交互示例
RealtimeAPI的交互流程目前只支持server_vad模式，该模式的交互流程如下：

1. 客户端发送StartSession事件初始化会话
2. 客户端可以随时通过TaskRequest事件将音频发送到服务端
3. 服务端在检测到用户说话的时候，会返回ASRInfo和ASRResponse事件，同时在检测到用户说话结束之后返回ASREnded事件
4. 服务端合成的音频通过TTSResponse事件将音频返回给客户端

![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/4ded1f3496b6435d972a37525c993717~tplv-goo7wpa0wc-image.image =283x)
<span id="882ba1ba"></span>
## 4.1 文本输入
![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/46ee6f916ef84be2861eecc4932a51e9~tplv-goo7wpa0wc-image.image =244x)

<span id="511d1d9b"></span>
## 4.2 合成音频
当客户判定不使用模型生成闲聊内容时，系统允许客户多次上传文本执行音频合成，以满足多样化需求。整体交互示例如下所示：
![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/0fb49295389e4dc491be4cd67ebeb2ba~tplv-goo7wpa0wc-image.image =277x)
<span id="3b7a0bae"></span>
## 4.3 外部RAG输入
![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/fc4233a293a645a3897269f1b279eee8~tplv-goo7wpa0wc-image.image =321x)
<span id="9b537d22"></span>
# 5 错误码

| | | | | \
|类型 |错误码 |错误定义 |说明 |
|---|---|---|---|
| | | | | \
|客户端 |\
| |45000002 |Empty audio |客户上传空的音频包，即TaskRequest事件中的音频长度为0 |
|^^| | | | \
| |45000003 |Abnormal silence audio |10分钟静音释放链接 |
| | | | | \
|服务端 |\
| |55000001 |Server processing error |\
| | | |服务端超过10秒没有收到query音频（客户端想要保持链接需要一直发送静音音频） |
|^^|^^|^^| | \
| | | |下游服务超过35秒没有收到tts回复 |
|^^|^^|^^| | \
| | | |服务端处理错误（通用型错误，需要借助logid进行深入排查） |
|^^| | | | \
| |55000030 |Service unavailable |下游模块建立连接失败 |
|^^| | | | \
| |55002070 |AudioFlow error |下游返回错误信息，统一对外的错误码 |

<span id="c1288469"></span>
| 日期 | update |
| --- | --- |
| 25.11.24 | 提供java示例 |
| 25.10.28 | 服务端事件ASRInfo增加返回question\_id字段；TTSSentenceStart事件增加返回question\_id和reply\_id字段；客户端增加麦克风静音模式保活机制；ChatTextQuery增加ack事件553； |
| 25.10.10 | 支持按需开启流式和非流式二遍识别模式，即在一次语音请求中先使用流式实时返回逐字文本，再使用非流式提升最终的识别准确率； |
| 25.09.23 | 放开和prompt相关的长度限制，丰富客户接入场景； |
| 25.09.22 | 支持自定义配置判断用户说话停止的参数；**s2s****模型-SC版本**开放支持内置联网和外部RAG输入能力； |
| 25.09.11 | **s2s****模型****\-O版本**支持外部RAG输入；客户在使用录音文件或者文本输入时候，客户端不需要补充发送静音，只需指定对应的模式参数即可，同时无需配置recv\_timeout参数； |
| 25.09.09 | **s2s****模型****\-SC版本**支持角色扮演、声音复刻能力；在使用此能力时候，需要传入对应的克隆音色以及角色描述，之前的bot\_name、system\_role、speaking\_style参数不会生效； |
| 25.09.05 | 支持纯文本模式demo，t2s模式可以使用recv\_timeout参数扩大超时时间避免还需要发送静音的问题； |
| 25.08.27 | 支持文本query和端到端模型进行交互，需要注意的是，再使用文本query进行交互时候，静音音频还是要发送的； |
| 25.08.20 | demo示例放开用户说话停止时间参数；system\_role和speaking\_style总长放开到4000； |
| 25.08.13 | Go demo修复并发写websocket的问题；支持内置联网开关，默认关闭；支持用户自己开通火山融合搜索服务；支持返回用量信息到客户端；支持system\_role和speaking\_style传入带转义字符的文本； |
| 25.08.06 | demo示例新增代码：支持传入录音文件；支持多音色；支持两种pcm位深； |
| 25.08.01 | 文档更新功能：支持两种pcm位深；支持多发音人；支持内置联网； |
| 25.07.14 | 支持客户自定义用户query命中安全审核时候的回复话术，新增audit\_response字段 |
| 25.07.09 | go示例修复一个tts音色配置bug |
| 25.07.03 | python示例开放模型人设区域，提升端到端模型自定义能力；增加SayHello、ChatTTSText事件发送示例； |
| 25.07.01 | 客户端在发送ChatTTSText事件时候一定要在收到ASREnded事件之后；增加一些报错处理，例如appkey错误、sp配置长度超过限制； |
| 25.06.25 | Go示例开放模型人设区域，提升端到端模型自定义能力；增加SayHello、ChatTTSText事件发送示例； |
| 25.06.10 | 更新realtime\_dialog示例，用户query打断本地播放音频 |
| 25.06.05 | 更新realtime\_dialog 示例，ctrl+c之后发送FinishSession、FinishConnection事件之后，再调用close断开websocket连接 |
| 25.06.05 | 补充客户接入ChatTTSText的最佳实践 |
| 25.06.04 | 删除服务端返回的UsageResponse事件，客户可以在火山控制台查看用量 |
| 25.06.04 | 更新realtime\_dialog Go示例demo，新增sayHello、chatTTSTesxt数据构造示例 |
| 25.06.03 | 新增realtime\_dialog Python示例demo |
| 25.05.30 | 更新realtime\_dialog示例，新增pcm保存到文件代码示例 |
| 25.05.30 | 更新Message type specific flags说明，注明必须传的字段 |
| 25.05.28 | 更新realtime\_dialog Go示例demo，修复录音上传慢问题 |


