# Wechat

Wechat 是一个开源的微信客户端实现接口，使用 python 完成微信的登录和消息收发功能

当前支持的功能相对简单，下面有详细介绍，后续会继续添加功能并优化实现

## 基本使用示例

```python
import Wechat

weChat = Wechat.Wechat()
weChat.login()
weChat.run()
```
该示例实现微信二维码扫码登录，然后处理接收的消息，默认不做任何处理，可以通过自定义函数替换默认处理

## 自定义消息处理

```python
import Wechat

def processMsg(self, msg):
    print(msg)

weChat = Wechat.Wechat()
weChat.registerProcessMsgFunc(processMsg)
weChat.login()
weChat.run()
```

自定义一个消息处理函数，调用 registerProcessMsgFunc 函数来替换默认处理函数

msg 是个字典类型，有些字段是必有的，有些是可有的，不同的消息类型所包含的字段不同：

必有字段：

    'fromUserName': 字符串类型，表示发送方的身份，登陆后由系统分配

    'fromUserNickName': 字符串类型，表示发送方的昵称，暂未实现

    'fromUserRemarkName': 字符串类型，表示发送方的备注名，暂未实现

    'fromUserType': 字符串类型，取值 "GROUP/PUBLIC/CONTACT", 表示消息来源于群组/公众号/联系人

    'msgType': 字符串类型，取值 "TEXT/POSITION/IMAGE/VOICE/VIDEO/CARD/ANIMATION/FILE/UNSUPPORTED", 表示消息类型是文本/位置/图片/语音/视频/名片/表情/文件/不支持

可有字段：

msgType = TEXT:

    'content': 字符串类型，表示接收到的消息内容


msgType = POSITION:

    'x': 字符串类型，浮点数，表示纬度

    'y': 字符串类型，浮点数，表示经度

    'scale': 字符串类型，整数，表示缩放比例

    'label': 字符串类型，表示位置的标签名称

    'poiname': 字符串类型，表示位置的具体名称


msgType = IMAGE:

    'imgHeight': 整数类型，表示图片高度

    'imgWidth': 整数类型，表示图片宽度

    'msgId': 字符串类型，表示图片在服务器的资源id，由系统分配，用于下载使用

    'downloadFunc': 函数类型，表示下载图片的函数，有一个输入参数 msgId

msg['downloadFunc'](msg['msgId']) 将下载图片到当前目录，保存文件名为 img_(msgId).jpg


msgType = VOICE:

    'voiceLength': 整数类型，表示语音时长，单位毫秒

    'msgId': 字符串类型，表示图片在服务器的资源id，由系统分配，用于下载使用

    'downloadFunc': 函数类型，表示下载语音的函数，有一个输入参数 msgId

msg['downloadFunc'](msg['msgId'])，将下载语音到当前目录，保存文件名为 voice_xxx.mp3


msgType = VIDEO:

    'imgHeight': 整数类型，表示视频高度

    'imgWidth': 整数类型，表示视频宽度

    'playLength': 整数类型，表示视频时长，单位秒

    'msgId': 字符串类型，表示视频在服务器的资源id，由系统分配，用于下载使用

    'downloadFunc': 函数类型，表示下载视频的函数，有一个输入参数 msgId

msg['downloadFunc'](msg['msgId']) 将下载视频到当前目录，保存文件名为 video_(msgId).mp4


msgType = CARD:

    'username': 字符串类型，表示微信号

    'nickname': 字符串类型，表示昵称

    'alias': 字符串类型，表示别名

    'province': 字符串类型，表示省

    'city': 字符串类型，表示城市

    'sex': 字符串类型，表示性别，0-未知 1-男 2-女

    'regionCode': 字符串类型，表示注册地

    'msgId': 字符串类型，表示视频在服务器的资源id，由系统分配，未使用


msgType = ANIMATION:

    'imgHeight': 整数类型，表示表情高度

    'imgWidth': 整数类型，表示表情宽度

    'msgId': 字符串类型，表示表情在服务器的资源id，由系统分配，未使用


msgType = FILE:

    'fileName': 字符串类型，表示文件名

    'fileSize': 字符串类型，表示文件大小，单位字节

    'mediaId': 字符串类型，表示视频多媒体id，由系统分配，用于下载使用

    'msgId': 字符串类型，表示视频在服务器的资源id，由系统分配

    'downloadFunc': 函数类型，表示下载文件的函数，未实现


msgType = UNSUPPORTED:

    没有可有字段，只有上述的必有字段


## 进阶应用

### 使用代理

在 Wechat 的构造函数中传入代理，就可以使用代理完成各种 request 消息处理

```python
proxies = { 'http':'http://ip:port', 'https':'https://ip:port' }
weChat = Wechat.Wechat(proxies=proxies)
```