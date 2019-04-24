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

    # 发送统一下单请求
    res = requests.post(
        url=unify_url,
        data=xml,
        headers=headers,
        cert=('/path/to/client.cert', '/path/to/client.key')
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


# rtn_dict = {'return_code': "SUCCESS", "return_msg": "1"}
# fail_msg = rtn_dict.get("return_msg")
# print(dict_to_notify_xml(**rtn_dict))


@login_required
def get_resigned_params(request):
    """
    商户server调用再次签名
    小程序请求此接口获取调起支付所需要的参数（5个参数和1个sign）
    """
    rtn = {}
    bs_id = request.session.get("business_id")
    if request.method == 'POST':
        data = simplejson.loads(request.body)
        order_id = data.get("order_id")
        if order_id:
            try:
                order = Order.objects.get(pk=order_id)
            except Order.DoesNotExist:
                rtn.update(code_msg(500005))
            else:
                params_dict = weixin_pay(bs_id, order)

                # 多参数字典中取出移动端调起支付所必需的5个参数
                appid = params_dict.get("appid")
                partnerid = params_dict.get("partnerid")
                prepayid = params_dict.get("prepayid")
                package = params_dict.get("package")
                noncestr = params_dict.get("noncestr")
                timestamp = int(time.time())

                # 进行二次签名
                # WX_MCH_KEY: 微信支付重要密钥，请登录微信支付商户平台，在 账户中心-API安全-设置API密钥设置
                necess_params = dict(appid=appid, partnerid=partnerid, prepayid=prepayid, package=package,
                                     noncestr=noncestr)
                WX_MCH_KEY = 'to_be_replaced'  # 临时填充，申请通过后替换到settings中
                sign = wx_sign(WX_MCH_KEY, **necess_params)

                if not all([appid, partnerid, prepayid, package, noncestr, sign]):
                    rtn.update(code_msg(400009))
                else:
                    rtn.update({
                        "appid": appid,
                        "partnerid": appid,
                        "prepayid": prepayid,
                        "package": package,
                        "noncestr": noncestr,
                        "timestamp": timestamp,
                        "sign": sign,
                    })
                    rtn.update(code_msg(0))
        else:
            rtn.update(code_msg(500005))
    else:
        rtn.update(code_msg(400005))

    response = simplejson.dumps(rtn)
    return HttpResponse(response, content_type=settings.JSON_MIME)


def payment_success(request):
    """
    支付成功回传接口
    """
    rtn_dict = {}
    _xml = request.body
    param_dict = xml_to_dict(_xml)

    out_trade_no = param_dict.setdefault("out_trade_no", -1)
    return_code = param_dict.setdefault("return_code", -1)
    result_code = param_dict.get("result_code", -1)
    total_fee = param_dict.get("total_fee", -1)
    return_msg = param_dict.get("return_msg", -1)
    sign = param_dict.get("sign", -1)

    # 采用数据锁进行并发控制
    with transaction.Atomic:
        _order = Order.objects.get(out_refund_no=out_trade_no)
        # 判断该通知是否已经处理过
        if _order.status == Order.PAYEND:
            # 此订单已处理过
            rtn_dict.update({"return_code": "SUCCESS"})
        else:
            if result_code == "SUCCESS" and return_code == "SUCCESS":
                # 校验签名和金额
                if _order.total_fee == total_fee and _order.sign == sign:
                    # 校验成功，保存数据，返回成功消息
                    _order.status = Order.PAYEND
                    _order.save()
                    rtn_dict.update({"return_code": "SUCCESS"})
                elif _order.total_fee != total_fee:
                    # 返回失败消息,金额校验不通过
                    rtn_dict.update({"return_code": "FAIL", "return_msg": "the total_fee does not match"})
                elif _order.sign != sign:
                    rtn_dict.update({"return_code": "FAIL", "return_msg": "the sign does not match"})
                else:
                    rtn_dict.update({"return_code": "FAIL", "return_msg": return_msg})
            elif return_code == "SUCCESS" and return_msg:
                rtn_dict.update({"return_code": "FAIL", "return_msg": return_msg})
            else:
                rtn_dict.update({"return_code": "FAIL", "return_msg": return_msg})

    rtn_xml = dict_to_notify_xml(**rtn_dict)
    return render_to_response(rtn_xml, content_type='application/xml')
