import os
import sys
import time
import re
import requests
import qrcode
import random
import xml.dom.minidom
import json
import html

class Wechat:

    def __init__(self, proxies={}):
        self.headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36' }
        self.proxies = proxies
        self.session = requests.Session()
        self.uuid = ''
        self.isLogin = False
        self.redirect_uri = ''
        self.skey = ''
        self.sid = ''
        self.uin = ''
        self.pass_ticket = ''
        self.device_id = 'e' + repr(random.random())[2:17]
        self.base_request = {}
        self.sync_key = {}
        self.sync_key_str = ''
        self.user = {}
        self.contact_list = []
        self.public_list = []
        self.group_list = []

    def __getTimeStamp(self):
        t = int(time.time() * 1000)
        return t

    def __getRTimeStamp(self):
        t = -int(time.time())
        return t

    def __getUuid(self):
        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'redirect_uri': 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage',
            'fun': 'new',
            'lang': 'en_US',
            '_': self.__getTimeStamp()
        }
        r = self.session.get(url, params=params, headers=self.headers, proxies=self.proxies)
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)";'
        data = re.search(regx, r.text)
        if data.group(1) == '200': # OK
            self.uuid = data.group(2)
            print("uuid: %s" %self.uuid)

    def __genQRCode(self):
        url = 'https://login.weixin.qq.com/l/' + self.uuid
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.print_ascii(invert=False)

    def __login(self):
        url = 'https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login'
        tip = 1 # 0:scaned, 1:not scaned

        while (not self.isLogin):
            localTime = int(time.time())
            params = {
                'loginicon': 'true',
                'uuid': self.uuid,
                'tip': tip,
                'r': self.__getRTimeStamp(),
                '_': self.__getTimeStamp()
            }
            r = self.session.get(url, params=params, headers=self.headers, proxies=self.proxies)
            data = re.search(r'window.code=(\d+)', r.text)
            if data.group(1) == '408': # timeout
                tip = 1
            elif data.group(1) == '201': # scaned
                tip = 0
                print("scan success")
            elif data.group(1) == '200': # success
                param = re.search(r'window.redirect_uri="(\S+?)";', r.text)
                self.redirect_uri = param.group(1)
                self.isLogin = True
                print("login success")
            else:
                pass

    def __getLoginParams(self):
        url = self.redirect_uri + '&fun=new&version=v2'
        r = self.session.get(url, headers=self.headers, allow_redirects=False, proxies=self.proxies)
        nodes = xml.dom.minidom.parseString(r.text).documentElement.childNodes
        for node in nodes:
            if node.nodeName == 'skey':
                self.skey = node.childNodes[0].data
                self.base_request['Skey'] = self.skey
                print("skey: %s" %self.skey)
            elif node.nodeName == 'wxsid':
                self.sid = node.childNodes[0].data
                self.base_request['Sid'] = self.sid
                print("sid: %s" %self.sid)
            elif node.nodeName == 'wxuin':
                self.uin = node.childNodes[0].data
                self.base_request['Uin'] = self.uin
                print("uin: %s" %self.uin)
            elif node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data
                print("pass_ticket: %s" %self.pass_ticket)
            else:
                # isgrayscale, not needed
                pass
        self.base_request['DeviceID'] = self.device_id
        print("base_request: %s" %self.base_request)

    def __initinate(self):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit'
        params = {
            'r': self.__getRTimeStamp(),
            'pass_ticket': self.pass_ticket
        }
        data = { 'BaseRequest': self.base_request }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        r = self.session.post(url, params=params, data=json.dumps(data), headers=headers, proxies=self.proxies)
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        self.sync_key = dic['SyncKey']
        self.sync_key_str = '|'.join([str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.sync_key['List']])
        self.user = dic['User']
        print("sync_key: %s" %self.sync_key)
        print("sync_key_str: %s" %self.sync_key_str)
        print("user: %s" %self.user)

    def __statusNotify(self):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxstatusnotify'
        params = { 'pass_ticket': self.pass_ticket }
        self.base_request['Uin'] = int(self.base_request['Uin'])
        data = {
            'BaseRequest'  : self.base_request,
            'ClientMsgId'  : self.__getTimeStamp(),
            'Code'         : 3,
            'FromUserName' : self.user['UserName'],
            'ToUserName'   : self.user['UserName']
        }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        self.session.post(url, params=params, data=json.dumps(data), headers=headers, proxies=self.proxies)

    def __getContact(self):
        member_list = []
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact'
        params = {
            'pass_ticket': self.pass_ticket,
            'r': self.__getTimeStamp(),
            'seq': 0,
            'skey': self.skey
        }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        r = self.session.post(url, params=params, headers=headers, timeout=180, proxies=self.proxies)
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        member_list.extend(dic['MemberList'])

        while dic["Seq"] != 0:
            params['seq'] = dic["Seq"]
            r = self.session.post(url, params=params, headers=headers, timeout=180, proxies=self.proxies)
            r.encoding = 'utf-8'
            dic = json.loads(r.text)
            member_list.extend(dic['MemberList'])

        for member in member_list:
            if member['UserName'].find('@@') != -1:
                self.group_list.append(member)   # not include detail members info
            elif member['VerifyFlag'] & 8 != 0:
                self.public_list.append(member)  # include weixin,weixinzhifu
            else:
                self.contact_list.append(member) # include filehelper

        print("len public_list %d:" %len(self.public_list))
        print("len group_list %d:" %len(self.group_list))
        print("len contact_list %d:" %len(self.contact_list))

    def __syncCheck(self):
        url = 'https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck'
        params = {
            'r': self.__getTimeStamp(),
            'skey': self.skey,
            'sid': self.sid,
            'uin': self.uin,
            'deviceid': self.device_id,
            'synckey': self.sync_key_str,
            '_': self.__getTimeStamp()
        }
        r = self.session.get(url, params=params, headers=self.headers, proxies=self.proxies)
        data = re.search(r'window.synccheck=\{retcode:"(\d+)",selector:"(\d+)"\}', r.text)
        retcode = data.group(1)
        selector = data.group(2)
        print("retcode: %s, selector: %s" %(retcode, selector))
        return retcode, selector

    def __webwxSync(self):
        msgList = []
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync'
        params = {
            'sid': self.sid,
            'skey': self.skey,
            'pass_ticket': self.pass_ticket
        }
        data = {
            'BaseRequest': self.base_request,
            'SyncKey': self.sync_key,
            'rr': self.__getRTimeStamp()
        }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        r = self.session.post(url, params=params, data=json.dumps(data), headers=headers, proxies=self.proxies)
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        if dic['BaseResponse']['Ret'] == 0:
            self.sync_key = dic['SyncKey']
            self.sync_key_str = '|'.join([str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.sync_key['List']])
            msgList = dic['AddMsgList']
        return msgList

    def __parseMsg(self, msg):
        parsedMsg = {}
        parsedMsg['fromUserName'] = msg['FromUserName']
        # TODO: get NickName/RemarkName via msg['FromUserName']
        parsedMsg['fromUserNickName'] = ""
        parsedMsg['fromUserRemarkName'] = ""
        parsedMsg['fromUserType'] = 'UNSUPPORTED'
        parsedMsg['msgType'] = 'UNSUPPORTED'

        if self.__isFromGroup(msg['FromUserName']):
            parsedMsg['fromUserType'] = 'GROUP'
        elif self.__isFromPublic(msg['FromUserName']):
            parsedMsg['fromUserType'] = 'PUBLIC'
        else:
            parsedMsg['fromUserType'] = 'CONTACT'

        msgType = msg['MsgType']
        if msgType == 1: # text/link/position
            subMsgType = msg['SubMsgType']
            if subMsgType == 0: # text/link
                parsedMsg['msgType'] = 'TEXT'
                parsedMsg['content'] = msg['Content']
            elif subMsgType == 48: # position
                parsedMsg['msgType'] = 'POSITION'
                doc = xml.dom.minidom.parseString(msg['OriContent']).documentElement
                node = doc.getElementsByTagName("location")[0]
                parsedMsg['x'] = node.getAttribute("x")
                parsedMsg['y'] = node.getAttribute("y")
                parsedMsg['scale'] = node.getAttribute("scale")
                parsedMsg['label'] = node.getAttribute("label")
                parsedMsg['poiname'] = node.getAttribute("poiname")
            else:
                pass
        elif msgType == 3: # image
            parsedMsg['msgType'] = 'IMAGE'
            parsedMsg['msgId'] = msg['MsgId']
            parsedMsg['imgHeight'] = msg['ImgHeight']
            parsedMsg['imgWidth'] = msg['ImgWidth']
            parsedMsg['downloadFunc'] = self.__imgDownloadFunc
        elif msgType == 34: # voice
            parsedMsg['msgType'] = 'VOICE'
            parsedMsg['msgId'] = msg['MsgId']
            parsedMsg['voiceLength'] = msg['VoiceLength']
            parsedMsg['downloadFunc'] = self.__voiceDownloadFunc
        elif msgType == 42: # card
            parsedMsg['msgType'] = 'CARD'
            parsedMsg['msgId'] = msg['MsgId']
            content = html.unescape(msg['Content'])
            content = content.replace('<br/>', '\n')
            doc = xml.dom.minidom.parseString(content).documentElement
            parsedMsg['username'] = doc.getAttribute("username")
            parsedMsg['nickname'] = doc.getAttribute("nickname")
            parsedMsg['alias'] = doc.getAttribute("alias")
            parsedMsg['province'] = doc.getAttribute("province")
            parsedMsg['city'] = doc.getAttribute("city")
            parsedMsg['sex'] = doc.getAttribute("sex")
            parsedMsg['regionCode'] = doc.getAttribute("regionCode")
        elif msgType == 43: # video
            parsedMsg['msgType'] = 'VIDEO'
            parsedMsg['msgId'] = msg['MsgId']
            parsedMsg['playLength'] = msg['PlayLength']
            parsedMsg['imgHeight'] = msg['ImgHeight']
            parsedMsg['imgWidth'] = msg['ImgWidth']
            parsedMsg['downloadFunc'] = self.__videoDownloadFunc
        elif msgType == 47: # animation
            parsedMsg['msgType'] = 'ANIMATION'
            parsedMsg['msgId'] = msg['MsgId']
            parsedMsg['imgHeight'] = msg['ImgHeight']
            parsedMsg['imgWidth'] = msg['ImgWidth']
        elif msgType == 49: # attachment
            appMsgType = msg['AppMsgType']
            if appMsgType == 6: # file
                parsedMsg['msgType'] = 'FILE'
                parsedMsg['msgId'] = msg['MsgId']
                parsedMsg['fileName'] = msg['FileName']
                parsedMsg['fileSize'] = msg['FileSize']
                parsedMsg['mediaId'] = msg['MediaId']
                parsedMsg['downloadFunc'] = self.__fileDownloadFunc
            else:
                pass
        else:
            pass
        return parsedMsg

    # replace with custom function via registerProcessMsgFunc
    def __processMsg(self, msg):
        pass

    def __isFromGroup(self, userName):
        return userName[:2] == "@@"

    def __isFromPublic(self, userName):
        for public in self.public_list:
            if userName == public['UserName']:
                return True
        return False

    def __imgDownloadFunc(self, msgId):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetmsgimg?MsgID=%s&skey=%s'%(msgId, self.skey)
        r = self.session.get(url, stream=True, headers=self.headers, proxies=self.proxies)
        fileName = 'img_' + msgId + '.jpg'
        with open(fileName, 'wb') as f:
            f.write(r.content)

    def __voiceDownloadFunc(self, msgId):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetvoice?msgID=%s&skey=%s'%(msgId, self.skey)
        r = self.session.get(url, stream=True, headers=self.headers, proxies=self.proxies)
        fileName = 'voice_' + msgId + '.mp3'
        with open(fileName, 'wb') as f:
            f.write(r.content)

    def __videoDownloadFunc(self, msgId):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetvideo?msgID=%s&skey=%s'%(msgId, self.skey)
        headers = {
            'Range': 'bytes=0-',
            'User-Agent' : self.headers['User-Agent']
        }
        r = self.session.get(url, stream=True, headers=headers, proxies=self.proxies)
        fileName = 'video_' + msgId + '.mp4'
        with open(fileName, 'wb') as f:
            f.write(r.content)

    def __fileDownloadFunc(self, msgId):
        # TODO: download file
        pass

    def registerProcessMsgFunc(self, func):
        Wechat.__processMsg = func

    def login(self):
        self.__getUuid()
        self.__genQRCode()
        self.__login()
        self.__getLoginParams()
        self.__initinate()
        self.__statusNotify()
        self.__getContact()

    def run(self):
        while (self.isLogin):
            retcode, selector = self.__syncCheck()
            if retcode == '0':
                if selector == '2':
                    msgList = self.__webwxSync()
                    for msg in msgList:
                        parsedMsg = self.__parseMsg(msg)
                        self.__processMsg(parsedMsg)
                else:
                    pass
            elif retcode == '1101':
                self.isLogin = False
                break
            else:
                pass
            time.sleep(3)
        print("logout")
