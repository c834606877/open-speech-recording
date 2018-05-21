# -*- coding: utf-8 -*-

from flask import abort, request
import hashlib, xmltodict, time, random
from . import wx


wantted_words = ['开始', '向左', '向右', '向上', '向右', '开始', '结束']


@wx.route('/wx', methods=['GET', 'POST'])
def wx_index():
    my_signature = request.args.get('signature', '')
    my_timestamp = request.args.get('timestamp', '')
    my_nonce = request.args.get('nonce')
    if request.method == "GET":

        my_echostr = request.args.get('echostr', '')

        token = 'wx_emlab' 
        data = [token,my_timestamp ,my_nonce ] 
        data.sort() 
        temp = ''.join(data)
        mysignature = hashlib.sha1(temp).hexdigest() 
        if my_signature == mysignature:
            return my_echostr
    
    elif request.method == "POST":
        wx_args = xmltodict.parse(request.data).get('xml', {})
        print wx_args

        event = ''
        if 'MsgType' in wx_args and wx_args['MsgType'] == 'event':
            event = wx_args.get('Event', '')
        elif 'MsgType' in wx_args:
            event = wx_args['MsgType']

        if event in call_table.keys():
            return call_table[event](wx_args)
        else:
            return default_relpy(wx_args)


def default_relpy(wx_args):
    print "Recevied a unschedule event [%s]"% wx_args['MsgType']
    return ''


def reply_text(wx_args):
    print "Recevied a text event"
    ToUserName = wx_args.get('ToUserName', '')
    FromUserName = wx_args.get('FromUserName', '')
    Content = wx_args.get('Content', 'abc')
    CreateTime = wx_args.get('CreateTime', '')
    MsgId = wx_args.get('MsgId', '')

    print Content

    if Content == '2':
        Content = '请先贡献你的声音样本。回复1开始。'
    elif Content == '1':
        Content = '请说 "%s"'% random.choice(wantted_words)


    reply = {
        'ToUserName': FromUserName,
        'FromUserName': ToUserName,
        'CreateTime': '%d'% time.time(),
        'MsgType': 'text',
        'Content': Content
    }


    return trans_dict_to_xml(reply)

def reply_voice(wx_args):
    print "Recevied a voice event"
    ToUserName = wx_args.get('ToUserName', '')
    FromUserName = wx_args.get('FromUserName', '')
    Content = wx_args.get('Content', 'abc')
    CreateTime = wx_args.get('CreateTime', '')
    MsgId = wx_args.get('MsgId', '')
    Recognition = wx_args.get('Recognition', '没有识别到信息哦。')


    

    reply = {
        'ToUserName': FromUserName,
        'FromUserName': ToUserName,
        'CreateTime': '%d'% time.time(),
        'MsgType': 'text',
        'Content': '已识别到内容为: %s'%Recognition if Recognition else '没有识别到内容哦。'
    }


    if Recognition[0:2] in wantted_words:
        reply['Content'] = '好，请继续说词语: ‘%s’'% random.choice(wantted_words)
        



    return trans_dict_to_xml(reply)

def reply_subscribe(wx_args):
    print "Recevied a subscribe event"
    ToUserName = wx_args.get('ToUserName', '')
    FromUserName = wx_args.get('FromUserName', '')
    reply = {
        'ToUserName': FromUserName,
        'FromUserName': ToUserName,
        'CreateTime': '%d'% time.time(),
        'MsgType': 'text',
        'Content': '''欢迎关注 Emlab 实验室 (Emlab.net)\n
    向我发送语音，我将返回文本。
    回复1进入命令词收集模式。
    回复2获取开放命令词样本。
        '''
    }
    return trans_dict_to_xml(reply)

def reply_unsubscribe(wx_args):
    print "Recevied a unsubscribe event"
    return ''


def trans_dict_to_xml(data):
    xml = []
    for k in sorted(data.keys()):
        v = data.get(k)
        if (k in ['ToUserName', 'FromUserName', 'MsgType', 'Content'])\
            and not v.startswith('<![CDATA['):
            v = '<![CDATA[{}]]>'.format(v)
        xml.append('<{key}>{value}</{key}>'.format(key=k, value=v))
    ret =  '<xml>{}</xml>'.format(''.join(xml))
    print ret
    return ret


call_table = {
        'text': reply_text,
        'voice': reply_voice,
        'subscribe': reply_subscribe,
        'unsubscribe': reply_unsubscribe
}