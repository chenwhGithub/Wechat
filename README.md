# webwx

webwx 是一个开源的微信客户端实现接口，使用 python 完成微信的登录和消息收发功能

当前支持的功能相对简单，后续会持续添加功能并优化

具体协议分析参考博客：https://blog.csdn.net/chenwh_cn/article/details/108581139

## 基本使用示例

```python
import webwx

weChat = webwx.webwx()
weChat.login()
weChat.run()
```
该示例实现最基础功能：微信二维码扫码登录或者缓存自动登录，接收和处理消息，默认接收的消息不做任何处理

## 登录

登录方式有两种：一是不使用缓存，每次都扫码登录；二是使用缓存，每次登录成功后将信息保存到文件，如果缓存仍然有效则下次无需再扫码登录，可以直接收发消息

``` login() ``` 函数带有一个参数 ``` enable_relogin ```，默认值 ``` True ```，表示使用缓存，如果取值 ``` False ```，则不使用缓存每次扫码登录

## 二维码显示

扫码登录时，二维码的显示有两种方式：一是直接显示在屏幕上；二是通过打开图片文件的方式

``` login() ``` 函数带有一个参数 ``` enable_qrcode_cmd ```，默认值 ``` True ```，表示二维码显示在屏幕上，如果取值 ``` False ```，则打开图片文件显示二维码

## 自定义消息处理

```python
import webwx

# 自定义消息处理函数
def process_msg(self, msg):
    print(msg)

weChat = webwx.webwx()
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
    'userNickName': 字符串类型， 表示发送者的昵称
    'userDisplayName': 字符串类型，表示发送者设置的自己在该群的显示名称，没有设置为""


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

## 发送接口

支持发送 .jpg .mp4 格式的图片和视频，其它格式文件作为普通文件发送

接收者可以是: msg['senderName']，联系人的昵称，联系人的备注名，群组的昵称，按照这个优先顺序查找

```python
# 发送文本
send_text('hello world', u'张三')

# 发送图片
send_image('test.jpg', u'张三')

# 发送视频
send_video('test.mp4', u'张三')

# 发送普通文件
send_file('test.pdf', u'张三')
```

## 进阶应用

### 使用代理

在 webwx 的构造函数中传入代理，就可以使用代理完成各种 requests 消息处理

```python
proxies = { 'http':'http://ip:port', 'https':'https://ip:port' }
weChat = webwx.webwx(proxies=proxies)
```

### 下载多媒体资源

```python
# 下载所有接收到的图片/语音/视频消息，保存 jpg/mp3/mp4 文件到当前目录
def process_msg(self, msg):
    if msg['msgType'] in ["IMAGE", "VOICE", "VIDEO"]:
        msg['downloadFunc'](msg['msgId'])
```

### 发送多媒体资源

```python
# 监测群消息内容，根据内容发送图片/语音/视频消息到联系人
img_path = 'img_5100655276253422831.jpg'
video_path = 'video_1879067029541949726.mp4'
doc_path = 'pdf_3446080029541949727.pdf'

def process_msg(self, msg):
    if msg['senderType'] == 'GROUP' and msg['groupNickName'] == u'欢乐大家庭' and msg['msgType'] == 'TEXT':
        if msg['content'] == u'文本':
            self.send_text('hello world', u'张三')
        if msg['content'] == u'图片':
            self.send_image(img_path, u'张三')
        if msg['content'] == u'视频':
            self.send_video(video_path, u'张三')
        if msg['content'] == u'文件':
            self.send_file(doc_path, u'张三')
```

### 智能聊天机器人

```python
def emotibot(req_text):
    params = {
        "cmd": "chat",
        "appid": "xxx", # 申请的 emotibot 机器人id
        "userid": "xiaoming",
        "text": req_text,
        "location": "hangzhou"
    }

    resp = requests.request("post", "http://idc.emotibot.com/api/ApiKey/openapi.php", params=params)
    dic = json.loads(resp.text)
    resp_text = dic["data"][0]["value"]
    return resp_text

# 接收联系人消息，通过智能机器人获取回复消息，然后发送回联系人，实现智能聊天
def process_msg(self, msg):
    if msg['senderType'] == 'CONTACT' and msg['contactNickName'] == u'张三' and msg['msgType'] == 'TEXT':
        req_text = msg['content']
        resp_text = emotibot(req_text)
        self.send_text(resp_text, u'张三')
```

## 待实现功能

1. 解决 emoji 表情信息过滤
2. 解析群组消息是否包含@信息
3. 增加文件下载功能
4. 增加系统异常处理
