from websocket import create_connection
import execjs
from loguru import logger
import json
import requests
from bs4 import BeautifulSoup
import ddddocr
import os
ocr = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)

def distance():
    with open('slider.jpg', 'rb') as f1, \
            open('background.jpg', 'rb') as f2:
        target = f1.read()
        background = f2.read()
    res = ocr.slide_match(target, background, simple_target=True)
    logger.info(f"滑块的距离为: {res['target'][0]}")
    return res['target'][0]


def save_pic(data):
    response=requests.get(data['data']['b'])
    with open('background.jpg','wb') as f:
        f.write(response.content)
    response=requests.get(data['data']['s'])
    with open('slider.jpg','wb') as f:
        f.write(response.content)
def js_call(name,c1=None,c2=None,c3=None,c4=None):
    with open('v5.js', 'r', encoding='utf-8') as f:
        js = f.read()
        js = execjs.compile(js)
        res = js.call(name, c1,c2,c3)
        return res
        # print(res)


def v5_get_token():
    response = requests.get('https://www.verify5.com/demo')
    soup = BeautifulSoup(response.text, 'html.parser')
    div_tag = soup.find('div', attrs={'v5-config': True})
    if div_tag:
        v5_config_str = div_tag['v5-config']
        v5_config_str = v5_config_str.replace("'", '"')
        v5_config_str = v5_config_str.replace('id:', '"id":') \
            .replace('name:', '"name":') \
            .replace('host:', '"host":') \
            .replace('token:', '"token":')
        return json.loads(v5_config_str)['token']


def wss_send(token):
    ws=create_connection("wss://rm0w8a6ckkco.verify5.com/api")
    res=js_call('encrypt_data_1',token)
    ws.send(res[0])
    ws.send(res[1])
    ws.send(res[2])
    logger.debug('第一次发送成功')
    response = ws.recv()
    print(response)
    res=js_call("decrypt_data_1",response,token)

    logger.debug(f'第一次获取数据成功{response} 明文为{res}')
    json_data = json.loads(res)
    res = js_call('encrypt_data_2', token,json_data['data']['u'])
    ws.send(res)
    logger.debug('第二次发送成功')
    response = ws.recv()
    res = js_call("decrypt_data_2", response, json_data['data']['u'],token)
    logger.debug(f'第二次获取数据成功{response} 明文为{res}')
    json_data = json.loads(res)
    save_pic(json_data)
    dis=distance()
    res = js_call('encrypt_data_3', token, json_data['data']['m'],dis)
    ws.send(res)
    logger.debug('第三次发送成功')
    response = ws.recv()
    res = js_call("decrypt_data_2", response, json_data['data']['m'], token)
    logger.debug(f'第二次获取数据成功{response} 明文为{res}')



if __name__ == '__main__':
    token = v5_get_token()
    logger.info(f'成功获取token--->{token}')
    wss_send(token)
