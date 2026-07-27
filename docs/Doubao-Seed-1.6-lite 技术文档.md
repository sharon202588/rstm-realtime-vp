<span id="4715c5ff"></span>
# 进入体验中心
可从以下位置进入体验中心：

* 在控制台左侧导航栏中，点击 [体验中心](https://console.volcengine.com/ark/region:ark+cn-beijing/experience/chat)。
* 在 **模型广场** 中打开模型详情页，点击 **立即体验** 进入体验中心。

<span id="d0853a4f"></span>
# 选择模型并配置参数

1. 在体验中心界面左上方展开模型列表，选择需要试用的模型、模型版本/推理接入点。可以通过以下方式调用模型：
   * 在 **语言** 标签页中选择一个模型，在模型详情页上选择模型版本，也可使用已创建的推理接入点或新建接入点。
      <div style="text-align: center"><img src="https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/50b7c59549ce45e894cb143dc6655317~tplv-goo7wpa0wc-image.image" width="843px" />      </div>

   * 在 **我的** 标签页中选择已完成精调并导出至模型仓库的精调模型。
   * 在 **智能路由** 标签页选择已有智能路由接入点或新建智能路由。智能路由可根据每次请求的 Prompt 动态匹配最适合的模型完成任务。有关智能路由的更多信息，请参考[智能模型路由](/docs/82379/1828788)。
      :::tip
       智能路由为邀测能力，如需使用，请提交[测试申请工单](https://console.volcengine.com/auth/login?redirectURI=%2Fworkorder%2Fcreate%3Fstep%3D2%26SubProductID%3DP00001166)。
      :::
2. 点击模型列表右侧的 **模型参数** 配置模型参数，将鼠标悬停在参数右侧的 **?** 图标查看参数说明。可结合下表的效果说明调整参数。
   
   | | | \
   |**参数名** |**效果说明** |
   |---|---|
   | | | \
   |Temperature |* Temperature 越低，生成内容通常越严谨和保守，适合有标准答案的任务，如事实问答、代码生成、逻辑推理等。 |\
   | |* Temperature 越高，输出内容更随机，更具创意性，适合创造性任务，如写诗歌、写故事等。 |
   | | | \
   |TopP |\
   | |TopP 可实现的效果与 Temperature 相似： |\
   | | |\
   | |* TopP 越低，生成的内容更严谨、一致，但也更循规蹈矩，适用于对准确性要求较高的场景，比如知识问答或代码补全。 |\
   | |* TopP 越高，生成内容更丰富，适合开放式对话、故事创作等场景。 |
   | | | \
   |max_tokens |输出文本的最大 token 限制。如需限制模型输出的长度，可通过此参数进行设置。 |\
   | |1 个中文字符或英文单词通常计为 1 token，可以使用 [Token 计算器](/docs/82379/1749096)计算 token 消耗量。 |\
   | |**注**：模型可输入和输出的 token 总和还受到模型上下文长度上限的限制。 |
   | | | \
   |frequency_penalty |* frequency_penalty 越高，对重复内容的惩罚越大，可用于需要降低重复内容、丰富措辞的场景。 |\
   | |* frequency_penalty 越低，模型会倾向于输出重复的内容，适用于需要突出重点、允许重复的场景。 |\
   | |* 当将该值设为 0 时，将不对模型自然的用词分布进行干预。 |\
   | | |\
   | |取值范围：-2.0 - 2.0 |
   | | | \
   |System Prompt |用于设定模型的行为偏好，告知其需要扮演的角色，或提供背景信息。System Prompt 优先级高于对话中输入的指令。 |\
   | |例如，如果希望模型精简输出，System Prompt 中可填写：“所有回复控制在 3 句话内，只给核心结论，不展开解释。” |\
   | |**注**：点击右侧的 **铅笔** 图标可进入 Prompt 优化界面，对系统指令进行优化。 |


<span id="21ec743d"></span>
# 与模型对话
在对话框中输入指令或问题，点击右下角的 **发送** 图标，即可开始与模型对话。
根据所选模型，您可以使用以下功能：

* 上传附件：上传图片、视频或其他文件。
* 联网：允许模型调用互联网检索工具；如关闭则仅使用模型自身知识生成内容。
* 思考深度：控制推理步数与生成时长。深度越高，生成质量通常越好，但用时更长。
* MCP：选择要调用的外部工具，如文件检索、数据库、企业内部服务等，执行记录将展示在对话细节中。关于 MCP 的具体信息请参考 [MCP 简介](/docs/82379/1539085)。
   <div style="text-align: center"><img src="https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/57388c4c47a54adb8c6c33a63385f39a~tplv-goo7wpa0wc-image.image" width="917px" />   </div>

* Canvas：将模型返回的内容输出为可编辑的文档或代码文件，并在画布上展示代码执行的效果，便于修改和导出生成的内容。关于 Canvas 的具体信息请参考 [Canvas 简介](/docs/82379/1581314)。
      <div style="text-align: center"><img src="https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/13f4a4cdac95499fb1e40cd95be1bb1d~tplv-goo7wpa0wc-image.image" width="819px" />      </div>

* 知识库：关联知识库中的文档，让模型在对话过程中基于文档内容进行推理和生成。可以免费体验方舟示例知识库中的内容，如需创建和管理知识库，请参考[文档知识问答核心流程](/docs/82379/1261883)。

完成对话后，您可以：

* 在对话框中继续发送内容，每次发送的内容会自动带入此前的信息。
* 重新生成、复制已生成内容或对内容进行评价。
* 创建新对话或清空本次对话中的上下文。

您还可以在左侧的 **最近对话** 列表中切换至历史对话，重命名对话，或将其删除。
<div style="text-align: center"><img src="https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/5ca03e49f14f49e99542c58654557c40~tplv-goo7wpa0wc-image.image" width="1579px" /></div>

<span id="a7df72ce"></span>
# 对比模型效果
 点击模型列表右侧的 **模型对比** 对比不同模型生成内容的效果，可同时对比三个模型的效果。
<div style="text-align: center"><img src="https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/789e4d9be2034de7b10e0258cbb577d9~tplv-goo7wpa0wc-image.image" width="1285px" /></div>

<span id="c551e2b0"></span>
# 快速接入 API
点击右上方的 **API 接入** 可复制 API key 和示例代码，快速测试 API 请求并创建应用。
<div style="text-align: center"><img src="https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/b91564d9ddc34cca9cac33b2e5ca74ed~tplv-goo7wpa0wc-image.image" width="2528px" /></div>


