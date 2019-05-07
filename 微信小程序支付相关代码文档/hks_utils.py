#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
商户系统和微信支付系统主要交互：

1、小程序内调用登录接口，获取到用户的openid,api参见公共api【小程序登录API】

2、商户server调用支付统一下单，api参见公共api【统一下单API】

3、商户server调用再次签名，api参见公共api【再次签名】

4、商户server接收支付通知，api参见公共api【支付结果通知API】

5、商户server查询支付结果，api参见公共api【查询订单API】
"""

# 标准库
import hashlib
import random
import string
from xml.etree import cElementTree as ETree

# 项目导入
import requests

from xxx.settings import WX_APPID, WX_UNIFIEDORDER_URL


class WxPayError(Exception):
    def __init__(self, msg):
        super(WxPayError, self).__init__(msg)


def get_openid(appid, secret, js_code, grant_type='authorization_code'):
    """
    请求openid

    :param appid:       小程序 appId
    :param secret:      小程序 appSecret
    :param js_code:     登录时获取的 code
    :param grant_type:  授权类型，此处只需填写 authorization_code

    :return: openid
    """
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    parmas = {
        'appid': appid,
        'secret': secret,
        'js_code': js_code,
        'grant_type': grant_type
    }
    res = requests.get(url, params=parmas)
    openid = res.json().get('openid', '')
    return openid


def to_utf8(raw):
    return raw.encode("utf-8") if isinstance(raw, str) else raw


def xml_to_dict(xml):
    """
    将xml转为dict
    """
    dic = {}
    root = ETree.fromstring(xml)
    for child in root:
        dic[child.tag] = child.text
    return dic


def dict_to_xml(**kwargs):
    """
    将dict转换为指定格式的xml
    """
    _str = ''.join(["<{0}>{1}</{0}>".format(key, value) for key, value in kwargs.items()])
    xml_str = "<xml>{0}</xml>".format(_str)
    return xml_str


def wx_sign(WX_MCH_KEY, **raw):
    """
    生成签名
    参考微信签名生成算法
    https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=4_3

    WX_MCH_KEY: 微信支付重要密钥，请登录微信支付商户平台，在 账户中心-API安全-设置API密钥设置
    """
    raw = [(k, str(raw[k]) if isinstance(raw[k], (int, float)) else raw[k]) for k in sorted(raw.keys())]
    s = "&".join("=".join(kv) for kv in raw if kv[1])
    s += "&key={0}".format(WX_MCH_KEY)
    return hashlib.md5(to_utf8(s)).hexdigest().upper()


def generate_nonce_str(length=32):
    char = string.ascii_letters + string.digits
    return "".join(random.choice(char) for _ in range(length))


def unify_order(**kwargs):
    '''
    统一下单函数

    应用场景: 商户在小程序中先调用该接口在微信支付服务后台生成预支付交易单，返回正确的预支付交易后调起支付。
    接口 URL地址：https://api.mch.weixin.qq.com/pay/unifiedorder
    统一下单文档：https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=9_1&index=1

    必填参数： appid, mch_id, nonce_str, sign, body, out_trade_no, total_fee, spibill_create_ip, notify_url, trade_type,
    返回参数:  返回的所有参数，移动端调起支付需要的5个参数在另外的函数里自已取。
    '''
    import requests
    xml = dict_to_xml(**kwargs)
    headers = {'Content-Type': 'application/xml'}  # se
    unify_url = WX_UNIFIEDORDER_URL

    # 发送统一下单请求
    res = requests.post(
        url=unify_url,
        data=xml,
        headers=headers,
    )
    response_dict = xml_to_dict(res.content)

    return_code = response_dict.get('return_msg')
    result_code = response_dict.get('result_code')
    return_msg = response_dict.get('return_msg')
    err_code_des = response_dict.get('err_code_des')

    # 统一下单成功
    if return_code == "SUCCESS" and result_code == "SUCCESS":
        return response_dict

    elif return_code == "SUCCESS":
        raise WxPayError(err_code_des)
    else:
        raise WxPayError(return_msg)


def dict_to_notify_xml(**kwargs):
    """
    支付结果通知
    按微信指定的格式生成返回的xml
    """
    fail_msg = kwargs.get("return_msg")
    rtn_xml_code = """<xml>\n<return_code><![CDATA[{return_code}]]></return_code>""".format(**kwargs)
    rtn_xml_msg = """\n<return_msg><![CDATA[{}]]></return_msg>""".format(fail_msg) if fail_msg else ''
    tail = "\n</xml>"
    rtn_xml = ''.join([rtn_xml_code, rtn_xml_msg, tail])
    return rtn_xml
