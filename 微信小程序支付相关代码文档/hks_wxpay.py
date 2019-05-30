#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
参考文档： https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=7_3&index=1

小程序支付是专门被定义使用在小程序中的支付产品。目前在小程序中能且只能使用小程序支付的方式来唤起微信支付。

微信支付流程:

1. 注册APPID
2. 生成支付订单
3. 调用 '统一下单API'生成预付单，获取prepay_id
4. 将参数再次签名传输给APP发起支付
5. 支付结果回调，查看 errCode
    * 0  成功
    * -1 错误
    * -2 用户取消


商户系统和微信支付系统主要交互：

1、小程序内调用登录接口，获取到用户的openid,api参见公共api【小程序登录API】

2、商户server调用支付统一下单，api参见公共api【统一下单API】

3、商户server调用再次签名，api参见公共api【再次签名】

4、商户server接收支付通知，api参见公共api【支付结果通知API】

5、商户server查询支付结果，api参见公共api【查询订单API】
"""
import time

import requests

from aviation_service.settings import WX_APPID, WX_REFUND_URL, MCH_ID, WX_NOTIFY_URL, WX_TRADE_TYPE, \
    WX_API_KEY, WX_SECRET, KEY_PATH, CERT_PATH
from commons.models import Business
from .hks_utils import unify_order, wx_sign, dict_to_xml, xml_to_dict, generate_nonce_str, get_openid


def get_unify_order_params(business_id, order, js_code):
    """
    统一下单函数
    """

    bs = Business.objects.get(pk=business_id)
    # bs = Business.objects.get(pk=bs.parent_id) if bs.pay_used else bs

    # 此处需由前端通过wei提供code值，小程序调用wx.login() 获取 临时登录凭证code，并回传到开发者服务器。
    open_id = get_openid(bs.wx_app_id, bs.wx_app_secret, js_code)

    unify_param_dict = dict(
        appid=bs.wx_app_id,
        mch_id=bs.wx_mch_id,
        nonce_str=generate_nonce_str(),
        body='TuoFeng',  # 例如：综合超市
        out_trade_no=order.out_trade_no,  # 商户订单号
        # total_fee=int(order.total_fee),  # 消费金额 单位是分
        total_fee=1,  # 消费金额 单位是分
        spbill_create_ip=order.spbill_create_ip,  # 调用微信企业付款接口服务器公网IP地址,只有使用NATIVE支付方式时才是服务器IP
        notify_url=WX_NOTIFY_URL,
        trade_type=WX_TRADE_TYPE,
        openid=open_id  # trade_type为JSAPI时此参数必传
    )
    print("第一次签名参数")
    sign = wx_sign(bs.wx_mch_api_key, **unify_param_dict)
    print(sign)
    unify_param_dict.update({'sign': sign})

    # 检查必填参数是否缺失, 此项检查total不能为0
    wx_params = all(list(unify_param_dict.values()))
    if not wx_params:
        # 微信支付必填参数缺失
        return {}
    else:
        response_dict = unify_order(**unify_param_dict)
        return response_dict


def get_resigned_params(business_id, **params_dict):
    """
    商户server调用再次签名
    将移动端调起支付所需要的参数进行再次签名
    """
    if not params_dict: return {}

    bs = Business.objects.get(pk=business_id)
    # bs = Business.objects.get(pk=bs.parent_id) if bs.pay_used else bs

    # 多参数字典中取出移动端调起支付所必需的5个参数
    appid = params_dict.get("appid")
    prepayid = params_dict.get("prepay_id")
    noncestr = params_dict.get("nonce_str")
    timestamp = str(int(time.time()))
    package = "prepay_id=%s" % prepayid

    if not all([appid, prepayid, package, noncestr]): return
    # 进行二次签名
    # WX_MCH_KEY: 微信支付重要密钥，请登录微信支付商户平台，在 账户中心-API安全-设置API密钥设置
    necess_params_dic = dict(
        appId=appid,
        timeStamp=timestamp,
        nonceStr=noncestr,
        package=package,
        signType='MD5'
    )
    wx_mch_key = bs.wx_mch_api_key  # 参数加密密钥,位于微信商户平台(pay.weixin.qq.com)-->账户设置-->API安全-->密钥设置
    print("第二次签名参数----------")
    print(necess_params_dic)
    sign = wx_sign(wx_mch_key, **necess_params_dic)
    necess_params_dic.update({"sign": sign, "timestamp": timestamp})
    return necess_params_dic


def weixin_refund(bs, **kwargs):
    """
    微信退款功能函数
    url: https://api.mch.weixin.qq.com/secapi/pay/refund
    """
    """
    1. 获取参数
    2. 拼接XML
    3. 向API发送请求
    4. 解析返回结果
    """
    xml_str = dict_to_xml(**kwargs)
    # 发送退款请求
    headers = {'Content-Type': 'application/xml'}  # se
    res = requests.post(
        url=WX_REFUND_URL,
        data=xml_str,
        headers=headers,
        cert=(CERT_PATH, KEY_PATH)                                  # 调试用
        # cert=(bs.wx_mch_apiclient_cert, bs.wx_mch_apiclient_key)  # 正式启用时路径写入商户表
    )
    response_dict = xml_to_dict(res.content)
    return_code = response_dict.get("return_code")
    return_msg = response_dict.get("return_msg")
    print("退款api返回结果", response_dict)
    if return_code == "SUCCESS" and return_msg == "OK":
        return True
    elif return_code == "SUCCESS":
        return False
    else:
        return False


def wexin_check_payment():
    """
    查询支付结果
    """
    # TODO
    pass
