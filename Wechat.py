import os
import sys
import time
import re
import requests
import qrcode
import random
import xml.dom.minidom
import json

class Wechat:

    def __init__(self, porxyUsed=True):
        self.headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36' }
        self.proxies = {}
        if porxyUsed:
            self.proxies = { 'http':'http://10.144.1.10:8080', 'https':'https://10.144.1.10:8080' }
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
        if data and data.group(1) == '200': # OK
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
            if member['VerifyFlag'] & 8 != 0:
                self.public_list.append(member)
            elif member['UserName'].find('@@') != -1:
                self.group_list.append(member)
            else:
                self.contact_list.append(member)
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
        if msg['ToUserName'] == 'filehelper':
            msgType = msg['MsgType']
            if msgType == 1: # text/link/position
                subMsgType = msg['SubMsgType']
                if subMsgType == 0: # text/link
                    parsedMsg['msgType'] = 'TEXT'
                    parsedMsg['content'] = msg['Content']
                elif subMsgType == 48: # position
                    oriContent = msg['OriContent']
                    parsedMsg['msgType'] = 'POSITION'
                    parsedMsg['position'] = msg['OriContent'] # delete this IE after TODO parsed
                    # TODO: parse IEs
                    # nodes = xml.dom.minidom.parseString(oriContent).documentElement.childNodes
                    # for node in nodes:
                    #     if node.nodeName == 'x':
                    #         parsedMsg['x'] = node.childNodes[0].data
                    #     if node.nodeName == 'y':
                    #         parsedMsg['y'] = node.childNodes[0].data
                    #     if node.nodeName == 'scale':
                    #         parsedMsg['scale'] = node.childNodes[0].data
                    #     if node.nodeName == 'label':
                    #         parsedMsg['label'] = node.childNodes[0].data
                    #     if node.nodeName == 'poiname':
                    #         parsedMsg['poiname'] = node.childNodes[0].data
            elif msgType == 3: # image
                parsedMsg['msgType'] = 'IMAGE'
                parsedMsg['msgId'] = msg['MsgId']
                parsedMsg['imgHeight'] = msg['ImgHeight']
                parsedMsg['imgWidth'] = msg['ImgWidth']
                parsedMsg['imgUrl'] = self.__getImgUrl(msg['MsgId'])
            elif msgType == 34: # voice
                parsedMsg['msgType'] = 'VOICE'
                parsedMsg['msgId'] = msg['MsgId']
                parsedMsg['voiceLength'] = msg['VoiceLength']
                parsedMsg['voiceUrl'] = self.__getVoiceUrl(msg['MsgId'])
            elif msgType == 42: # card
                parsedMsg['msgType'] = 'CARD'
                parsedMsg['msgId'] = msg['MsgId']
                content = msg['Content']
                parsedMsg['content'] = msg['Content'] # delete this IE after TODO parsed
                # TODO: parse IEs
                # nodes = xml.dom.minidom.parseString(content).documentElement.childNodes
                # for node in nodes:
                #     if node.nodeName == 'username':
                #         parsedMsg['username'] = node.childNodes[0].data
                #     if node.nodeName == 'nickname':
                #         parsedMsg['nickname'] = node.childNodes[0].data
                #     if node.nodeName == 'alias':
                #         parsedMsg['alias'] = node.childNodes[0].data
                #     if node.nodeName == 'province':
                #         parsedMsg['province'] = node.childNodes[0].data
                #     if node.nodeName == 'city':
                #         parsedMsg['city'] = node.childNodes[0].data
                #     if node.nodeName == 'sex':
                #         parsedMsg['sex'] = node.childNodes[0].data
                #     if node.nodeName == 'regionCode':
                #         parsedMsg['regionCode'] = node.childNodes[0].data
            elif msgType == 43: # video
                parsedMsg['msgType'] = 'VIDEO'
                parsedMsg['msgId'] = msg['MsgId']
                parsedMsg['playLength'] = msg['PlayLength']
                parsedMsg['imgHeight'] = msg['ImgHeight']
                parsedMsg['imgWidth'] = msg['ImgWidth']
                parsedMsg['videoUrl'] = self.__getVideoUrl(msg['MsgId'])
            elif msgType == 47: # animation
                parsedMsg['msgType'] = 'ANIMATION'
                parsedMsg['msgId'] = msg['MsgId']
                parsedMsg['imgHeight'] = msg['ImgHeight']
                parsedMsg['imgWidth'] = msg['ImgWidth']
            elif msgType == 49: # attachment
                parsedMsg['msgType'] = 'FILE'
                parsedMsg['msgId'] = msg['MsgId']
                appMsgType = msg['AppMsgType']
                if appMsgType == 6: # file
                    parsedMsg['fileName'] = msg['FileName']
                    parsedMsg['fileSize'] = msg['FileSize']
                    parsedMsg['mediaId'] = msg['MediaId']
        elif msg['FromUserName'][:2] == "@@":
            # TODO: process group msg
            pass
        elif self.__isPublic(msg['FromUserName']):
            # TODO: process public msg
            pass
        elif self.__isContact(msg['FromUserName']):
            # TODO: same with filehelper
            pass

        return parsedMsg

    def __isPublic(self, userName):
        for public in self.public_list:
            if userName == public['UserName']:
                return True
        return False

    def __isContact(self, userName):
        for contact in self.contact_list:
            if userName == contact['UserName']:
                return True
        return False

    def __getImgUrl(self, msgId):
        # return self.base_uri + '/webwxgetmsgimg?MsgID=%s&skey=%s' % (msgId, self.skey)
        pass

    def __getVoiceUrl(self, msgId):
        # return self.base_uri + '/webwxgetvoice?MsgID=%s&skey=%s' % (msgId, self.skey)
        pass

    def __getVideoUrl(self, msgId):
        # return self.base_uri + '/webwxgetvideo?msgid=%s&skey=%s' % (msgId, self.skey)
        pass

    def processMsg(self, msg):
        print(msg)
        pass

    def run(self):
        self.__getUuid()
        self.__genQRCode()
        self.__login()
        self.__getLoginParams()
        self.__initinate()
        self.__statusNotify()
        self.__getContact()
        while (self.isLogin):
            retcode, selector = self.__syncCheck()
            if retcode == '1101':
                self.isLogin = False
            if retcode == '0' and selector == '2':
                msgList = self.__webwxSync()
                for msg in msgList:
                    parsedMsg = self.__parseMsg(msg)
                    self.processMsg(parsedMsg)
            time.sleep(3)
        print("logout")
