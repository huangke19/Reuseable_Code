#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Author: huangke
# Email: huangkwell@163.com
# Date: 2019-04-24


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
from xml.etree import cElementTree as ETree


# 项目导入


class WxPayError(Exception):
    def __init__(self, msg):
        super(WxPayError, self).__init__(msg)


# 必填参数
# appid = 'to'
# mch_id = ''
# nonce_str = ''
# sign = ''
# body = ''
# out_trade_no = ''
# total_fee = ''
# spibill_create_ip = ''
# notify_url = ''
# trade_type = ''


# NECESSARY_PARAMS = (
#     appid, mch_id, nonce_str,
#     sign, body, out_trade_no,
#     total_fee, spibill_create_ip,
#     notify_url, trade_type
# )

unify_url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'

NECESSARY_PARAMS_DICT = dict(
    mch_id='todo',
    nonce_str='todo',
    sign='todo',
    notify_url='todo',
    trade_type='todo'
)


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


def sign(self, raw):
    """
    生成签名
    参考微信签名生成算法
    https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=4_3
    """
    raw = [(k, str(raw[k]) if isinstance(raw[k], (int, float)) else raw[k]) for k in sorted(raw.keys())]
    s = "&".join("=".join(kv) for kv in raw if kv[1])
    s += "&key={0}".format(self.WX_MCH_KEY)
    return hashlib.md5(self.to_utf8(s)).hexdigest().upper()


def unify_order(**kwargs):
    '''
    统一下单函数

    应用场景: 商户在小程序中先调用该接口在微信支付服务后台生成预支付交易单，返回正确的预支付交易后调起支付。
    接口 URL地址：https://api.mch.weixin.qq.com/pay/unifiedorder
    统一下单文档：https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=9_1&index=1

    必填参数： appid, mch_id, nonce_str, sign, body, out_trade_no, total_fee, spibill_create_ip, notify_url, trade_type,
    返回参数:  return_code, return_msg
    '''
    import requests
    xml = dict_to_xml(**kwargs)
    headers = {'Content-Type': 'application/xml'}  # se
    res = requests.post(
        url=unify_url,
        data=xml,
        headers=headers,
        cert=('/path/to/client.cert', '/path/to/client.key')
    )
    res_dict = xml_to_dict(res.content)

    return_code = res_dict.get('return_msg')
    result_code = res_dict.get('result_code')
    return_msg = res_dict.get('return_msg')
    err_code_des = res_dict.get('err_code_des')

    # 统一下单成功
    if return_code == "SUCCESS" and result_code == "SUCCESS":
        # 预支付交易会话标识
        prepay_id = res_dict.get('prepay_id')
        # 二维码链接
        code_url = res_dict.get('code_url')

        return prepay_id, code_url

    elif return_code == "SUCCESS":
        raise WxPayError(err_code_des)
    else:
        raise WxPayError(return_msg)
