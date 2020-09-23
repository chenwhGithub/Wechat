# -*- coding: utf-8 -*-

"""
webwx

This module provides interfaces to login, send and receive weixin msg
"""

import os
import platform
import subprocess
import time
import re
import random
import xml.dom.minidom
import json
import html
import mimetypes
import hashlib
import pickle
import qrcode
import requests


def get_timestamp():
    stamp = int(time.time() * 1000)
    return stamp

def get_rtimestamp():
    stamp = -int(time.time())
    return stamp

def get_msg_id():
    msg_id = str(get_timestamp()) + str(random.random())[2:6]
    return msg_id

def get_md5(file_name):
    with open(file_name, mode="rb") as fptr:
        f_bytes = fptr.read()
    md5 = hashlib.md5(f_bytes).hexdigest()
    return md5

def display_qrcode(file_name):
    env_os = platform.system()
    if env_os == 'Darwin':
        subprocess.call(['open', file_name])
    elif env_os == 'Linux':
        subprocess.call(['xdg-open', file_name])
    elif env_os == 'Windows':
        os.startfile(file_name)

class webwx:

    def __init__(self, proxies=None):
        self.headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36' }
        self.proxies = proxies
        self.session = requests.Session()
        self.uuid = ''
        self.is_login = False
        self.redirect_uri = ''
        self.skey = ''
        self.sid = ''
        self.uin = ''
        self.pass_ticket = ''
        self.device_id = 'e' + repr(random.random())[2:17]
        self.base_request = {}
        self.sync_key = {}
        self.sync_key_str = ''
        self.account_me = {}
        self.account_contacts = {}
        self.account_subscriptions = {}
        self.account_groups = {}
        self.account_groups_members = {}
        self.file_upload_index = 0
        self.file_pickle_name = 'webwx.pkl'
        self.file_qrcode_name = 'qrcode.jpg'
        self.enable_qrcode_cmd = True

    def __get_uuid(self):
        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'redirect_uri': 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage',
            'fun': 'new',
            'lang': 'en_US',
            '_': get_timestamp()
        }
        resp = self.session.get(url, params=params, headers=self.headers, proxies=self.proxies)
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)";'
        data = re.search(regx, resp.text)
        if data.group(1) == '200': # OK
            self.uuid = data.group(2)
            print("uuid: %s" %self.uuid)

    def __gen_qrcode(self):
        if self.enable_qrcode_cmd:
            url = 'https://login.weixin.qq.com/l/' + self.uuid
            code = qrcode.QRCode()
            code.add_data(url)
            code.print_ascii(invert=False)
        else:
            url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
            headers = {
                'ContentType': 'image/jpeg;',
                'User-Agent' : self.headers['User-Agent']
            }
            resp = self.session.get(url, headers=headers, proxies=self.proxies)
            with open(self.file_qrcode_name, 'wb') as fptr:
                fptr.truncate() # clean file
                fptr.write(resp.content)

            display_qrcode(self.file_qrcode_name)

    def __login(self):
        url = 'https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login'
        tip = 1 # 0:scaned, 1:not scaned

        while not self.is_login:
            params = {
                'loginicon': 'true',
                'uuid': self.uuid,
                'tip': tip,
                'r': get_rtimestamp(),
                '_': get_timestamp()
            }
            resp = self.session.get(url, params=params, headers=self.headers, proxies=self.proxies)
            data = re.search(r'window.code=(\d+)', resp.text)
            if data.group(1) == '408': # timeout
                tip = 1
            elif data.group(1) == '201': # scaned
                tip = 0
                print("scan success")
            elif data.group(1) == '200': # success
                param = re.search(r'window.redirect_uri="(\S+?)";', resp.text)
                self.redirect_uri = param.group(1)
                self.is_login = True
                print("login success")

    def __get_params(self):
        url = self.redirect_uri + '&fun=new&version=v2'
        resp = self.session.get(url, headers=self.headers, allow_redirects=False, proxies=self.proxies)
        nodes = xml.dom.minidom.parseString(resp.text).documentElement.childNodes
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
            'r': get_rtimestamp(),
            'pass_ticket': self.pass_ticket
        }
        data = { 'BaseRequest': self.base_request }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        resp = self.session.post(url, params=params, data=json.dumps(data), headers=headers, proxies=self.proxies)
        resp.encoding = 'utf-8'
        dic = json.loads(resp.text)
        self.sync_key = dic['SyncKey']
        self.sync_key_str = '|'.join([str(item['Key']) + '_' + str(item['Val']) for item in self.sync_key['List']])
        self.account_me = dic['User']
        print("sync_key: %s" %self.sync_key)
        print("sync_key_str: %s" %self.sync_key_str)
        print("account_me: %s" %self.account_me)

    def __status_notify(self):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxstatusnotify'
        params = { 'pass_ticket': self.pass_ticket }
        self.base_request['Uin'] = int(self.base_request['Uin'])
        data = {
            'BaseRequest'  : self.base_request,
            'ClientMsgId'  : get_timestamp(),
            'Code'         : 3,
            'FromUserName' : self.account_me['UserName'],
            'ToUserName'   : self.account_me['UserName']
        }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        self.session.post(url, params=params, data=json.dumps(data), headers=headers, proxies=self.proxies)

    def __get_contact(self):
        member_list = []
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact'
        params = {
            'pass_ticket': self.pass_ticket,
            'r': get_timestamp(),
            'seq': 0,
            'skey': self.skey
        }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        resp = self.session.post(url, params=params, headers=headers, timeout=180, proxies=self.proxies)
        resp.encoding = 'utf-8'
        dic = json.loads(resp.text)
        member_list.extend(dic['MemberList'])

        while dic["Seq"] != 0:
            params['seq'] = dic["Seq"]
            resp = self.session.post(url, params=params, headers=headers, timeout=180, proxies=self.proxies)
            resp.encoding = 'utf-8'
            dic = json.loads(resp.text)
            member_list.extend(dic['MemberList'])

        for member in member_list:
            if member['UserName'].find('@@') != -1:
                self.account_groups[member['UserName']] = member   # not include detail members info
            elif member['VerifyFlag'] & 8 != 0:
                self.account_subscriptions[member['UserName']] = member  # include weixin,weixinzhifu
            else:
                self.account_contacts[member['UserName']] = member # include filehelper

        print("len account_subscriptions  %d:" %len(self.account_subscriptions))
        print("len account_groups         %d:" %len(self.account_groups))
        print("len account_contacts       %d:" %len(self.account_contacts))

    def __get_group_members(self):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxbatchgetcontact'
        params = {
            'type': 'ex',
            'r': get_timestamp(),
            'lang': 'en_US'
        }
        grouplist = []
        for group in self.account_groups.values():
            grouplist.append({'UserName':group['UserName'], 'ChatRoomId':group['ChatRoomId']})
        data = {
            'BaseRequest': self.base_request,
            'Count': len(self.account_groups),
            'List': grouplist
        }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        resp = self.session.post(url, params=params, data=json.dumps(data), headers=headers, timeout=180, proxies=self.proxies)
        resp.encoding = 'utf-8'
        dic = json.loads(resp.text)
        for member in dic['ContactList']:
            self.account_groups_members[member['UserName']] = member # save group member list info

    def __sync_check(self):
        url = 'https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck'
        params = {
            'r': get_timestamp(),
            'skey': self.skey,
            'sid': self.sid,
            'uin': self.uin,
            'deviceid': self.device_id,
            'synckey': self.sync_key_str,
            '_': get_timestamp()
        }
        resp = self.session.get(url, params=params, headers=self.headers, proxies=self.proxies)
        data = re.search(r'window.synccheck=\{retcode:"(\d+)",selector:"(\d+)"\}', resp.text)
        retcode = data.group(1)
        selector = data.group(2)
        print("retcode: %s, selector: %s" %(retcode, selector))
        return retcode, selector

    def __webwx_sync(self):
        msg_list = []
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync'
        params = {
            'sid': self.sid,
            'skey': self.skey,
            'pass_ticket': self.pass_ticket
        }
        data = {
            'BaseRequest': self.base_request,
            'SyncKey': self.sync_key,
            'rr': get_rtimestamp()
        }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        resp = self.session.post(url, params=params, data=json.dumps(data), headers=headers, proxies=self.proxies)
        resp.encoding = 'utf-8'
        dic = json.loads(resp.text)
        if dic['BaseResponse']['Ret'] == 0:
            self.sync_key = dic['SyncKey']
            self.sync_key_str = '|'.join([str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.sync_key['List']])
            msg_list = dic['AddMsgList']
        return msg_list

    def __parse_msg(self, msg):
        parsed_msg = {}
        parsed_msg['senderType'] = 'UNSUPPORTED'
        parsed_msg['senderName'] = msg['FromUserName']
        parsed_msg['msgType'] = 'UNSUPPORTED'

        if self.account_groups.__contains__(msg['FromUserName']):
            parsed_msg['senderType'] = 'GROUP'
            parsed_msg['groupNickName'] = self.account_groups[msg['FromUserName']]['NickName']
            ret = re.match('(@[0-9a-z]*?):<br/>(.*)$', msg['Content']) # username:<br>content
            user_name = ret.groups()[0] # get member username
            for item in self.account_groups_members[msg['FromUserName']]['MemberList']:
                if item['UserName'] == user_name:
                    parsed_msg['userNickName'] = item['NickName']
                    parsed_msg['userDisplayName'] = item['DisplayName']
                    break
        elif self.account_subscriptions.__contains__(msg['FromUserName']):
            parsed_msg['senderType'] = 'SUBSCRIPTION'
            parsed_msg['subscriptionNickName'] = self.account_subscriptions[msg['FromUserName']]['NickName']
        elif self.account_contacts.__contains__(msg['FromUserName']):
            parsed_msg['senderType'] = 'CONTACT'
            parsed_msg['contactNickName'] = self.account_contacts[msg['FromUserName']]['NickName']
            parsed_msg['contactRemarkName'] = self.account_contacts[msg['FromUserName']]['RemarkName']
        elif self.account_me['UserName'] == msg['FromUserName']:
            parsed_msg['senderType'] = 'MYSELF'
            parsed_msg['myNickName'] = self.account_me['NickName']

        msg_type = msg['MsgType']
        if msg_type == 1: # text/link/position
            sub_msg_type = msg['SubMsgType']
            if sub_msg_type == 0: # text/link
                parsed_msg['msgType'] = 'TEXT'
                parsed_msg['content'] = msg['Content']
                if parsed_msg['senderType'] == 'GROUP':
                    ret = re.match('(@[0-9a-z]*?):<br/>(.*)$', msg['Content'])
                    parsed_msg['content'] = ret.groups()[1] # delete sender username info
            elif sub_msg_type == 48: # position
                parsed_msg['msgType'] = 'POSITION'
                doc = xml.dom.minidom.parseString(msg['OriContent']).documentElement
                node = doc.getElementsByTagName("location")[0]
                parsed_msg['x'] = node.getAttribute("x")
                parsed_msg['y'] = node.getAttribute("y")
                parsed_msg['scale'] = node.getAttribute("scale")
                parsed_msg['label'] = node.getAttribute("label")
                parsed_msg['poiname'] = node.getAttribute("poiname")
        elif msg_type == 3: # image
            parsed_msg['msgType'] = 'IMAGE'
            parsed_msg['msgId'] = msg['MsgId']
            parsed_msg['imgHeight'] = msg['ImgHeight']
            parsed_msg['imgWidth'] = msg['ImgWidth']
            parsed_msg['downloadFunc'] = self.__img_download
        elif msg_type == 34: # voice
            parsed_msg['msgType'] = 'VOICE'
            parsed_msg['msgId'] = msg['MsgId']
            parsed_msg['voiceLength'] = msg['VoiceLength']
            parsed_msg['downloadFunc'] = self.__voice_download
        elif msg_type == 42: # card
            parsed_msg['msgType'] = 'CARD'
            parsed_msg['msgId'] = msg['MsgId']
            content = html.unescape(msg['Content']) # TODO: delete emoji info
            content = content.replace('<br/>', '\n')
            doc = xml.dom.minidom.parseString(content).documentElement
            parsed_msg['username'] = doc.getAttribute("username")
            parsed_msg['nickname'] = doc.getAttribute("nickname")
            parsed_msg['alias'] = doc.getAttribute("alias")
            parsed_msg['province'] = doc.getAttribute("province")
            parsed_msg['city'] = doc.getAttribute("city")
            parsed_msg['sex'] = doc.getAttribute("sex")
            parsed_msg['regionCode'] = doc.getAttribute("regionCode")
        elif msg_type == 43: # video
            parsed_msg['msgType'] = 'VIDEO'
            parsed_msg['msgId'] = msg['MsgId']
            parsed_msg['playLength'] = msg['PlayLength']
            parsed_msg['imgHeight'] = msg['ImgHeight']
            parsed_msg['imgWidth'] = msg['ImgWidth']
            parsed_msg['downloadFunc'] = self.__video_download
        elif msg_type == 47: # animation
            parsed_msg['msgType'] = 'ANIMATION'
            parsed_msg['msgId'] = msg['MsgId']
            parsed_msg['imgHeight'] = msg['ImgHeight']
            parsed_msg['imgWidth'] = msg['ImgWidth']
        elif msg_type == 49: # attachment
            app_msg_type = msg['AppMsgType']
            if app_msg_type == 6: # file
                parsed_msg['msgType'] = 'FILE'
                parsed_msg['msgId'] = msg['MsgId']
                parsed_msg['fileName'] = msg['FileName']
                parsed_msg['fileSize'] = msg['FileSize']
                parsed_msg['mediaId'] = msg['MediaId']
                parsed_msg['downloadFunc'] = self.__file_download

        return parsed_msg

    # default msg process, do nothing
    def __process_msg(self, msg):
        pass

    def __img_download(self, msg_id):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetmsgimg?MsgID=%s&skey=%s'%(msg_id, self.skey)
        resp = self.session.get(url, stream=True, headers=self.headers, proxies=self.proxies)
        file_name = 'img_' + msg_id + '.jpg'
        with open(file_name, 'wb') as fptr:
            fptr.write(resp.content)

    def __voice_download(self, msg_id):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetvoice?msgID=%s&skey=%s'%(msg_id, self.skey)
        resp = self.session.get(url, stream=True, headers=self.headers, proxies=self.proxies)
        file_name = 'voice_' + msg_id + '.mp3'
        with open(file_name, 'wb') as fptr:
            fptr.write(resp.content)

    def __video_download(self, msg_id):
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetvideo?msgID=%s&skey=%s'%(msg_id, self.skey)
        headers = {
            'Range': 'bytes=0-',
            'User-Agent' : self.headers['User-Agent']
        }
        resp = self.session.get(url, stream=True, headers=headers, proxies=self.proxies)
        file_name = 'video_' + msg_id + '.mp4'
        with open(file_name, 'wb') as fptr:
            fptr.write(resp.content)

    def __file_download(self, msg_id):
        pass # TODO: download file

    def __dump_pickle(self):
        conf = {
            'skey': self.skey,
            'sid': self.sid,
            'uin': self.uin,
            'pass_ticket': self.pass_ticket,
            'device_id': self.device_id,
            'base_request': self.base_request,
            'sync_key': self.sync_key,
            'sync_key_str': self.sync_key_str,
            'account_me': self.account_me,
            'account_contacts': self.account_contacts,
            'account_subscriptions': self.account_subscriptions,
            'account_groups': self.account_groups,
            'account_groups_members': self.account_groups_members,
            'cookies': self.session.cookies.get_dict()
        }

        with open(self.file_pickle_name, 'wb') as fptr:
            fptr.truncate() # clean file
            pickle.dump(conf, fptr)

    def __load_pickle(self):
        if os.path.exists(self.file_pickle_name):
            with open(self.file_pickle_name, 'rb') as fptr:
                conf = pickle.load(fptr)

            self.skey = conf['skey']
            self.sid = conf['sid']
            self.uin = conf['uin']
            self.pass_ticket = conf['pass_ticket']
            self.device_id = conf['device_id']
            self.base_request = conf['base_request']
            self.sync_key = conf['sync_key']
            self.sync_key_str = conf['sync_key_str']
            self.account_me = conf['account_me']
            self.account_contacts = conf['account_contacts']
            self.account_subscriptions = conf['account_subscriptions']
            self.account_groups = conf['account_groups']
            self.account_groups_members = conf['account_groups_members']
            self.session.cookies = requests.utils.cookiejar_from_dict(conf['cookies'])

            ret_code, _ = self.__sync_check()
            if ret_code == "0":
                return True

        return False

    def __get_username(self, name):
        if self.account_contacts.__contains__(name) or self.account_groups.__contains__(name): # input contact/group UserName
            return name

        for value in self.account_contacts.values(): # input contact NickName/RemarkName
            if name in (value['NickName'], value['RemarkName']):
                return value['UserName']

        for value in self.account_groups.values(): # input group NickName
            if value['NickName'] == name:
                return value['UserName']

    def __upload_media(self, file_name, media_type, to_user_name):
        url = 'https://file.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json'
        file_len = os.path.getsize(file_name)
        file_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        md5 = get_md5(file_name)
        files = {
            'id': (None, 'WU_FILE_%s' % str(self.file_upload_index)),
            'name': (None, os.path.basename(file_name)),
            'type': (None, file_type),
            'lastModifiedDate': (None, '%s' % time.ctime(os.path.getmtime(file_name))),
            'size': (None, str(file_len)),
            'mediatype': (None, media_type),
            'uploadmediarequest': (None, json.dumps({
                'UploadType': 2,
                'BaseRequest': self.base_request,
                'ClientMediaId': get_msg_id(),
                'TotalLen': str(file_len),
                'StartPos': 0,
                'DataLen': str(file_len),
                'MediaType': 4,
                'FromUserName': self.account_me['UserName'],
                'ToUserName': to_user_name,
                'FileMd5': md5
            })),
            'webwx_data_ticket': (None, self.session.cookies['webwx_data_ticket']),
            'pass_ticket': (None, self.pass_ticket),
        }

        fptr = open(file_name, 'rb')
        chunks = int((file_len - 1) / (1 << 19)) + 1 # one time upload 524288 bytes
        if chunks > 1:
            for chunk in range(chunks):
                f_bytes = fptr.read(1 << 19)
                files['chunks'] = (None, str(chunks))
                files['chunk'] = (None, str(chunk))
                files['filename'] = (os.path.basename(file_name), f_bytes, file_type.split('/')[1])
                resp = self.session.post(url, files=files, headers=self.headers, proxies=self.proxies)
        else:
            f_bytes = fptr.read(1 << 19)
            files['filename'] = (os.path.basename(file_name), f_bytes, file_type.split('/')[1])
            resp = self.session.post(url, files=files, headers=self.headers, proxies=self.proxies)
        dic = json.loads(resp.text)
        fptr.close()
        self.file_upload_index += 1

        return dic['MediaId']

    def __send_media(self, url, file_name, media_type, receiver):
        params = {
            'fun': 'async',
            'f': 'json',
            'lang': 'en_US',
            'pass_ticket': self.pass_ticket
        }

        msg_id = get_msg_id()
        to_user_name = self.__get_username(receiver)
        data = {
            'BaseRequest': self.base_request,
            'Msg': {
                'ClientMsgId': msg_id,
                'FromUserName': self.account_me['UserName'],
                'LocalID': msg_id,
                'ToUserName': to_user_name,
            },
            'Scene': 0
        }
        media_id = self.__upload_media(file_name, media_type, to_user_name)
        if media_type == 'pic':
            data['Msg']['Content'] = ''
            data['Msg']['MediaId'] = media_id
            data['Msg']['Type'] = 3
        elif media_type == 'video':
            data['Msg']['Content'] = ''
            data['Msg']['MediaId'] = media_id
            data['Msg']['Type'] = 43
        elif media_type == 'doc':
            file_len = os.path.getsize(file_name)
            content = ("<appmsg appid='wxeb7ec651dd0aefa9' sdkver=''><title>%s</title>" % os.path.basename(file_name) +
                "<des></des><action></action><type>6</type><content></content><url></url><lowurl></lowurl>" +
                "<appattach><totallen>%s</totallen><attachid>%s</attachid>" % (str(file_len), media_id) +
                "<fileext>%s</fileext></appattach><extinfo></extinfo></appmsg>" % os.path.splitext(file_name)[1].replace('.', ''))
            data['Msg']['Content'] = content
            data['Msg']['Type'] = 6

        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        self.session.post(url, params=params, data=json.dumps(data), headers=headers, proxies=self.proxies)

    def send_text(self, text, receiver):
        ''' public method, send text to receiver, parameter receiver can be msg['senderName']/nickname/remarkname '''
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg'
        params = { 'pass_ticket': self.pass_ticket }
        msg_id = get_msg_id()
        to_username = self.__get_username(receiver)
        data = {
            'BaseRequest': self.base_request,
            'Msg': {
                "ClientMsgId": msg_id,
                "Content": text,
                "FromUserName": self.account_me['UserName'],
                "LocalID": msg_id,
                "ToUserName": to_username,
                "Type": 1
            },
            'Scene': 0
        }
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.headers['User-Agent']
        }
        self.session.post(url, params=params, data=json.dumps(data, ensure_ascii=False).encode('utf8'), headers=headers, proxies=self.proxies)

    def send_image(self, file_name, receiver):
        ''' public method, send image to receiver, parameter receiver can be msg['senderName']/nickname/remarkname '''
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsgimg'
        media_type = 'pic'
        self.__send_media(url, file_name, media_type, receiver)

    def send_video(self, file_name, receiver):
        ''' public method, send video to receiver, parameter receiver can be msg['senderName']/nickname/remarkname '''
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendvideomsg'
        media_type = 'video'
        self.__send_media(url, file_name, media_type, receiver)

    def send_file(self, file_name, receiver):
        ''' public method, send file to receiver, parameter receiver can be msg['senderName']/nickname/remarkname '''
        url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendappmsg'
        media_type = 'doc'
        self.__send_media(url, file_name, media_type, receiver)

    def register_process_msg_func(self, func):
        """ public method, replace __process_msg method with custom method """
        webwx.__process_msg = func

    def login(self, enable_qrcode_cmd=True):
        """ public method, scan qrcode to login, or hot reload without scan """
        self.enable_qrcode_cmd = enable_qrcode_cmd
        if self.__load_pickle(): # read cache from file
            self.is_login = True
            print("login success")
        else:
            self.__get_uuid()
            self.__gen_qrcode()
            self.__login()
            self.__get_params()
            self.__initinate()
            self.__status_notify()
            self.__get_contact()
            self.__get_group_members()
            self.__dump_pickle() # save cache to file

    def run(self):
        """ public method, loop receive and process messages """
        while self.is_login:
            retcode, selector = self.__sync_check()
            if retcode == '0':
                if selector == '2':
                    msg_list = self.__webwx_sync()
                    for msg in msg_list:
                        parsed_msg = self.__parse_msg(msg)
                        self.__process_msg(parsed_msg)
            elif retcode == '1101': # logout from phone
                self.is_login = False
                break
            time.sleep(3)
        print("logout")
