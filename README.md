# wechat

wechat 是一个开源的微信客户端实现接口，使用 python 完成微信的登录和消息收发功能

当前支持的功能相对简单，后续会持续添加功能并优化

## 基本使用示例

```python
import wechat

weChat = wechat.wechat()
weChat.login()
weChat.run()
```
该示例实现最基础功能：微信二维码扫码登录，接收消息，默认接收的消息不做任何处理

## 自定义消息处理

```python
import wechat

# 自定义消息处理函数
def process_msg(self, msg):
    print(msg)

weChat = wechat.wechat()
weChat.register_process_msg_func(process_msg)
weChat.login()
weChat.run()
```

首先自定义消息处理函数，然后调用 register_process_msg_func 替换默认处理函数

msg 是字典类型，消息类型不同所包含的字段也不同，有些字段是必有的，有些是可选的

### 必有字段：

    'senderType': 字符串类型，取值 "GROUP/SUBSCRIPTION/CONTACT/MYSELF/UNSUPPORTED", 表示消息来源于群组/公众号/联系人/自己/不支持

    'senderName': 字符串类型，表示发送者的身份，由系统分配，@@开头表示群组，@开头表示联系人或者公众号

    'msgType': 字符串类型，取值 "TEXT/POSITION/IMAGE/VOICE/VIDEO/CARD/ANIMATION/FILE/UNSUPPORTED", 表示消息类型是文本/位置/图片/语音/视频/名片/表情/文件/不支持

### 可选字段：

```python
senderType = GROUP

    'groupNickName': 字符串类型，表示发送者所在的群组昵称


senderType = SUBSCRIPTION

    'subscriptionNickName': 字符串类型，表示发送者公众号昵称


senderType = CONTACT

    'contactNickName':   字符串类型，表示发送者昵称
    'contactRemarkName': 字符串类型，表示发送者备注名


senderType = MYSELF

    'myNickName': 字符串类型，表示自己的昵称


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

    调用 msg['downloadFunc'](msg['msgId'])，将下载图片到当前目录，保存文件名为 img_(msgId).jpg


msgType = VOICE:

    'voiceLength': 整数类型，表示语音时长，单位毫秒

    'msgId': 字符串类型，表示图片在服务器的资源id，由系统分配，用于下载使用

    'downloadFunc': 函数类型，表示下载语音的函数，有一个输入参数 msgId

    调用 msg['downloadFunc'](msg['msgId'])，将下载语音到当前目录，保存文件名为 voice_xxx.mp3


msgType = VIDEO:

    'imgHeight': 整数类型，表示视频高度

    'imgWidth': 整数类型，表示视频宽度

    'playLength': 整数类型，表示视频时长，单位秒

    'msgId': 字符串类型，表示视频在服务器的资源id，由系统分配，用于下载使用

    'downloadFunc': 函数类型，表示下载视频的函数，有一个输入参数 msgId

    调用 msg['downloadFunc'](msg['msgId'])，将下载视频到当前目录，保存文件名为 video_(msgId).mp4


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

    没有可选字段
```

## 进阶应用

### 使用代理

在 wechat 的构造函数中传入代理，就可以使用代理完成各种 requests 消息处理

```python
proxies = { 'http':'http://ip:port', 'https':'https://ip:port' }
weChat = wechat.wechat(proxies=proxies)
```

## 待实现功能

1. 增加图片显示登陆二维码方式
2. 保存登陆缓存信息，避免每次都要扫码登录
3. 解决 emoji 表情信息过滤
4. 解析群组消息是否包含@信息
5. 增加文件下载功能
6. 增加发送视频，普通文件功能
7. 增加系统异常处理
