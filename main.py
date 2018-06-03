# -*- coding: utf-8 -*-

from flask import Flask
from flask import abort
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request, url_for, session, send_from_directory

from werkzeug.utils import secure_filename

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

import os, time
import uuid
from urllib import urlencode

import json

import wx

import HttpUtil 

app = Flask(__name__)

app.register_blueprint(wx.wx)


ali_ak_id = 'LTAIio3iLMnbWw0K'
ali_ak_key = 'sU7sfP35tuvjSyNWE649JeBzTQSvDB'

secret_id = 'AKIDujZItKUjgS3TihC9oQ7i9QYWKxQiRpdH'      # 替换为用户的 secretId
secret_key = os.environ.get('CLOUD_STORAGE_KEY') or 'a'      # 替换为用户的 secretKey
region = 'ap-guangzhou'     # 替换为用户的 Region
token = ''                  # 使用临时秘钥需要传入 Token，默认为空，可不填
config = CosConfig(Secret_id=secret_id, Secret_key=secret_key, Region=region, Token=token)
client = CosS3Client(config)





# Configure this environment variable via app.yaml
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET') or 'open-speech-recorder-1252042671'
# [end config]

@app.route("/")
def welcome():
    session_id = request.cookies.get('session_id')
    if session_id:
        all_done = request.cookies.get('all_done')
        if all_done:
            return render_template("thanks.html")
        else:
            return render_template("record.html")
    else:
        return render_template("welcome.html")

@app.route("/legal")
def legal():
    return render_template("legal.html")

@app.route("/start")
def start():
    response = make_response(redirect('/'))
    session_id = uuid.uuid4().hex
    response.set_cookie('session_id', session_id)
    return response



@app.route('/upload', methods=['POST'])
def upload():
    session_id = request.cookies.get('session_id') or 'session_id'
    if not session_id:
        make_response('No session', 400)
    word = request.args.get('word') or 'word'
    audio_data = request.data
    filename = word + '_' + session_id + '_' + uuid.uuid4().hex + '.ogg'
    secure_name = secure_filename(filename)
    # Left in for debugging purposes. If you comment this back in, the data
    # will be saved to the local file system.
    with open("web_data/" + secure_name, 'wb') as f:
        f.write(audio_data)
    # Create a Cloud Storage client.
    # gcs = storage.Client()
    # bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)
    # blob = bucket.blob(secure_name)
    # blob.upload_from_string(audio_data, content_type='audio/ogg')
    # response = client.put_object(
    #     Bucket=CLOUD_STORAGE_BUCKET,
    #     Body=audio_data,
    #     Key=secure_name,
    #     StorageClass='STANDARD',
    #     ContentType='audio/ogg'
    # )
    # print response['ETag']
    return make_response('All good')

def verify_mp3(link):
    ht = HttpUtil.HttpUtil(ali_ak_id, ali_ak_key)
    req = ht.sendPost("https://nlsapi.aliyun.com/transcriptions", 
        json.dumps(
            {   "app_key":"nls-service-telephone8khz",
                "auto_split":False,
                "callback_url":"",
                "enable_callback":False,
                "oss_link":link,
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

    time.sleep(3);
    ret = ht.sendGet("https://nlsapi.aliyun.com/transcriptions/" + req_id)
    return ret


        
    #if json.loads(ret)['status'] != "RUNNING":
    #        break


@app.route('/upload_mp3', methods=['POST'])
def upload_mp3():
    session_id = request.form.get('session_id') or 'session_id'
    word = request.form.get('word') or 'word'
    if 'file' not in request.files:
        return make_response('No file')
    file = request.files['file']

    filename = word + '_' + session_id + '_' + uuid.uuid4().hex + '.mp3'
    secure_name = secure_filename(filename)
    # Left in for debugging purposes. If you comment this back in, the data
    # will be saved to the local file system.
    filepath = "data/" + secure_name;
    file.save(filepath)

    response = client.put_object_from_local_file(
        Bucket = CLOUD_STORAGE_BUCKET,
        LocalFilePath = filepath,
        Key = filename
    )

    #verify_mp3("https://osr.emlab.net/"+ filepath)



    return make_response('All good')



@app.route('/data/<path:filename>')
def base_data(filename):
    return send_from_directory(app.root_path + '/data/', filename)




# CSRF protection, see http://flask.pocoo.org/snippets/3/.
@app.before_request
def csrf_protect():
    if request.method == "POST" and '_csrf_token' in session:
        token = session['_csrf_token']
        if not token or token != request.args.get('_csrf_token'):
            abort(403)

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = uuid.uuid4().hex
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token
# Change this to your own number before you deploy.
app.secret_key = os.environ.get('SESSION_SECRET_KEY') or 'defaul7_s3ssi0n_t0ken1'


if __name__ == "__main__":
    print app.url_map
    #app.run(host="0.0.0.0",debug=True)
    re = verify_mp3("http://open-speech-recording-wx.oss-cn-shanghai.aliyuncs.com/right_081CebZ81ABJfR1AvAZ81jt3Z81CebZ4_6fdd10dd710f47688b12fa8f50cafba6.mp3")
    print re.decode("utf-8")


