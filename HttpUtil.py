#!/usr/bin/python
# -*- coding:utf-8 -*-

from urlparse import urlparse
import datetime
import base64
import hmac
import hashlib
import json
import urllib2



class HttpUtil(object):
    """docstring for HttpUtil
    a http request implement of aliyun nls auth for kws.
    """
    def __init__(self, akId, akSecret):
        self.ak_id = akId
        self.ak_secret =  akSecret

    def get_current_date(self):
        date = datetime.datetime.strftime(datetime.datetime.utcnow(), "%a, %d %b %Y %H:%M:%S GMT")
        return date

    def to_md5_base64(self, body):
        hash = hashlib.md5()
        hash.update(body.encode('utf-8'))
        return hash.digest().encode('base64').strip()

    def to_sha1_base64(self, stringToSign):
        hmacsha1 = hmac.new(self.ak_secret.encode('utf-8'), stringToSign.encode('utf-8'), hashlib.sha1)
        return base64.b64encode(hmacsha1.digest()).decode('utf-8')

    # HttpUtil.sendGet("https://nlsapi.aliyun.com/transcriptions/9a38c83a7de14bf3972b2fa672e3db9d")
    #
    
    def sendPost(self, url, body):
        return self.sendReq('POST', url, body)

    
    def sendGet(self, url):
        return self.sendReq('GET', url)

    
    def sendPut(self, url, body):
        return self.sendReq('PUT', url, body)

    
    def sedDelete(self, url):
        return self.sendReq('DELETE', url)

    def sendReq(self, method, url, body = ''):
        options = {
            'url': url,
            'method': method,
            'body': body, 
            'headers': {
                'accept': 'application/json',
                'content-type': 'application/json',
                'date':  self.get_current_date(),
                'authorization': ''
            }
        }

        body = ''
        if 'body' in options:
            body = options['body']
        
        bodymd5 = ''
        if not body == '':
            bodymd5 = self.to_md5_base64(body)
        print body, ":", bodymd5
        # REST ASR 接口，需要做两次鉴权
        #bodymd5 = to_md5_base64(bodymd5)
        stringToSign = options['method'] + '\n' + options['headers']['accept'] + '\n' + bodymd5 + '\n' + options['headers']['content-type'] + '\n' + options['headers']['date'] 
        signature = self.to_sha1_base64(stringToSign)
        
        authHeader = 'Dataplus ' + self.ak_id + ':' + signature
        options['headers']['authorization'] = authHeader
        print  stringToSign, ":", authHeader
        request = None
        method = options['method']
        url = options['url']

        print method, ":", url
        if 'GET' == method or 'DELETE' == method:
            request = urllib2.Request(url)
        elif 'POST' == method or 'PUT' == method:
            request = urllib2.Request(url, body)
        request.get_method = lambda: method
        for key, value in options['headers'].items():
            request.add_header(key, value)
        try:
            conn = urllib2.urlopen(request)
            response = conn.read()
            print response
            return response
        except urllib2.HTTPError, e:
            print e.read()
            raise SystemExit(e)



def main():
    ht = HttpUtil(ak_id, ak_secret)
    req = ht.sendPost("https://nlsapi.aliyun.com/transcriptions", 
        json.dumps(
            {   "app_key":"nls-service-telephone8khz",
                "auto_split":False,
                "callback_url":"",
                "enable_callback":False,
                "oss_link":"http://aliyun-nls.oss.aliyuncs.com/asr/fileASR/examples/nls-sample.wav",
                "valid_times":[],
                "vocabulary_id":""
            }
            , separators=(',', ':')),
        )
    req_id = ''
    if not req == '':
        try:
            req_id = json.loads(req)['id']

        except Exception as e:
            print "parse respose failed!"
            raise e

    
    ht.sendGet("https://nlsapi.aliyun.com/transcriptions/" + req_id)



if __name__ == '__main__':
    main()
