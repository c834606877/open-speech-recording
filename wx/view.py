# -*- coding: utf-8 -*-

from flask import abort, request
import hashlib, xmltodict, time, random, json, os, urllib
from . import wx


wantted_words =     ['开始',  '向左',  '向右',  '向上', '向下', '确定',  '停止', '前进',   '后退',   '回家']
wantted_words_asc = ['start', 'left', 'right', 'up',  'down', 'confirm','stop', 'forward','goback', 'gohome']
access_token = ''
access_token_time = 0.0


@wx.route('/MP_verify_n8E9nOKLoy1P8xT6.txt')
def wx_verify():
    return 'n8E9nOKLoy1P8xT6'

@wx.route('/wx_getvoice/<media_id>')
def wx_getvoice(media_id):
    mediaurl = "http://api.weixin.qq.com/cgi-bin/media/get/jssdk?access_token="+get_access_token() +"&media_id="+media_id
    os.system('curl -o ' + media_id  + ' "'+ mediaurl+'"' )
    return ''


@wx.route('/wx_web', methods=['GET', 'POST'])
def wx_web():
    print request.data
    if request.method == "POST":
        print request.get_json()
        return 'ok';


    timestamp = '%d'%time.time()
    ticket = get_jsapi_ticket()
    enstr = 'jsapi_ticket=' + ticket + '&noncestr=ok&timestamp='+timestamp+'&url=https://osr.emlab.net/wx_web'
    signature = hashlib.sha1(enstr).hexdigest()


    return '''<html>
    <head>
    <script src="http://cdn.static.runoob.com/libs/jquery/1.10.2/jquery.min.js"> </script>
    <script src="http://res.wx.qq.com/open/js/jweixin-1.2.0.js"></script>
    
    <script type="text/javascript">
        wx.config({
        debug: false, // 开启调试模式,调用的所有api的返回值会在客户端alert出来，若要查看传入的参数，可以在pc端打开，参数信息会通过log打出，仅在pc端时才会打印。
        appId: 'wxb8d5a9dc426fae7f', // 必填，公众号的唯一标识
        timestamp: %s , // 必填，生成签名的时间戳
        nonceStr: 'ok', // 必填，生成签名的随机串
        signature: '%s',// 必填，签名
        jsApiList: ['startRecord', 'stopRecord', 'uploadVoice'] // 必填，需要使用的JS接口列表
    });
    //假设全局变量已经在外部定义
//按下开始录音
var START ;
var voice = {'localId': ''};
wx.ready(function(){
    document.getElementById('talk_btn').addEventListener("touchstart",function(event) {    
        //alert('touchstart');
        event.preventDefault();
        START = new Date().getTime();
        
        recordTimer = setTimeout(function(){

            wx.startRecord({
                success: function(){
                    localStorage.rainAllowRecord = 'true';
                },
                cancel: function () {
                    alert('用户拒绝授权录音');
                }
            });
        },300);
    });
    document.getElementById('talk_btn').addEventListener("touchend",function(event) {    
        //alert('touchend');
        event.preventDefault();
        END = new Date().getTime();
        
        if((END - START) < 300){
            END = 0;
            START = 0;
            //小于300ms，不录音
            clearTimeout(recordTimer);
        }else{

            wx.stopRecord({
              success: function (res) {
                voice.localId = res.localId;
               
                uploadVoice();
              },
              fail: function (res) {
                alert(JSON.stringify(res));
              }
            });
            
        }
    });
});


//上传录音
function uploadVoice(){
    //调用微信的上传录音接口把本地录音先上传到微信的服务器
    //不过，微信只保留3天，而我们需要长期保存，我们需要把资源从微信服务器下载到自己的服务器
    wx.uploadVoice({
        localId: voice.localId, // 需要上传的音频的本地ID，由stopRecord接口获得
        isShowProgressTips: 1, // 默认为1，显示进度提示
        success: function (res) {
            //把录音在微信服务器上的id（res.serverId）发送到自己的服务器供下载。
             alert(JSON.stringify(res));
            $.ajax({
                url:'/wx_getvoice/' + res.serverId,
                type: 'get',
                data: '',
                success: function (data) {
                    alert('文件已经保存到七牛的服务器');//这回，我使用七牛存储
                },
                error: function (xhr, errorType, error) {
                    console.log(error);
                }
            });
        }
    });
}

//注册微信播放录音结束事件【一定要放在wx.ready函数内】
wx.onVoicePlayEnd({
    success: function (res) {
        stopWave();
    }
});
    </script>

    </head>
    <body style="user-select:none;">
    <button style="user-select:none;" id='talk_btn' width='200'>start recorde</button>
    </body>


    </html>

    '''% (timestamp, signature) ;

@wx.route('/wx', methods=['GET', 'POST'])
def wx_index():
    my_signature = request.args.get('signature', '')
    my_timestamp = request.args.get('timestamp', '')
    my_nonce = request.args.get('nonce')

    token = 'wx_emlab' 

    data = [token,my_timestamp ,my_nonce ] 
    data.sort() 
    temp = ''.join(data)

    mysignature = hashlib.sha1(temp).hexdigest()
    if my_signature != mysignature:
        return my_signature, 403

    if request.method == "GET":
        my_echostr = request.args.get('echostr', '')

        
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
        Content = '录音前，请保持周围安静。建议在单独安静的房间内进行。\r\n\
请开始向我发送长2秒左右且仅包含命令词的语音。osr.emlab.net/wx_web'
        Content = Content + '\r\n请说 "%s"'% random.choice(wantted_words)


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
    MediaId = wx_args.get('MediaId', '')
    Format = wx_args.get('Format', '')
    Recognition = wx_args.get('Recognition', '没有识别到信息哦。') 


    

    reply = {
        'ToUserName': FromUserName,
        'FromUserName': ToUserName,
        'CreateTime': '%d'% time.time(),
        'MsgType': 'text',
        'Content': '已识别到内容为: %s'%Recognition if Recognition else '没有识别到内容哦。'
    }


    if Recognition and Recognition[0:2] in wantted_words:

        i = wantted_words.index(Recognition[0:2])
        file_name = wantted_words_asc[i] + '_' + FromUserName + '_' + MsgId + '.' + Format

        token = get_access_token()
        media_url = 'https://api.weixin.qq.com/cgi-bin/media/get?access_token='+ token + '&media_id=' + MediaId

        print 'mediaurl: ' + media_url
        os.system('wget "' + media_url + '" -O wx_data/' + file_name )  

        
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
    osr.emlab.net/wx_web
    '''
#    回复2获取开放命令词样本。
        
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



def fetch_access_token():
    if time.time() - access_token_time > 1000:
        os.system('bash gettoken.sh');
        access_token_time = time.time() 

def get_jsapi_ticket():
    #fetch_access_token()
    tiket_json = ''
    tiket_json = urllib.urlopen('https://api.weixin.qq.com/cgi-bin/ticket/getticket?type=jsapi&access_token=' + get_access_token()).read()

    tiket = json.loads(tiket_json)
    return tiket['ticket']


def get_access_token():
    #fetch_access_token()
    token_json = ''
    with open("token") as token_file:
        token_json = token_file.read()
    token = json.loads(token_json)
    return token['access_token']


call_table = {
        'text': reply_text,
        'voice': reply_voice,
        'subscribe': reply_subscribe,
        'unsubscribe': reply_unsubscribe
}