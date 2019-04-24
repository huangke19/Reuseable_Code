



#### 用户资料

```python
class UserProfile(models.Model):
    """
    用户资料
    """

    user = models.OneToOneField(
        User,
        verbose_name=u'用户',
        related_name='userprofile',
        on_delete=models.CASCADE
    )

    @classmethod
    def check_mobile(cls, mobile_num):
        pattern = "^1[3|4|5|7|8][0-9]{9}$"
        res = re.match(pattern, str(mobile_num))
        return bool(res)

    @classmethod
    def check_and_obtain_by_id(cls, id):
        exist = cls.objects.filter(pk=id, is_active=True).exists()
        obj = cls.objects.get(pk=id)
        return exist, obj

    def update_obj(self, **kwargs):
        """
        更新模型字段值
        """

        # 取带值的参数名为列表1
        args_name_list = [i for i, v in kwargs.items() if v]
        # 取模型所有字段名为列表2
        cls_fields_list = [f.get_attname() for f in self._meta.fields]
        # 取交集为需要更新的字段名列表
        update_fields_list = [i for i in cls_fields_list if i in args_name_list]

        # 更新字段
        for name in update_fields_list:
            value = kwargs.get(name)
            name_type = type(self._meta.get_field(name)).__name__
            if name_type == 'DecimalField':
                value = Decimal(value)
            if name_type == 'IntegerField':
                value = int(value)
            setattr(self, name, value)
        self.save()
        
        @property
    def token(self):
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        """
        手动签发jwt
        """
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        return token

    @classmethod
    def db_change_password(cls, username, old_pwd, new_pwd):
        """
        修改密码
        """
        user = authenticate(username=username, password=old_pwd)
        if user is not None:
            if user.is_active:
                user.set_password(new_pwd)
                user.save()
                return 0
            else:
                # 帐号被禁用
                return 500013
        else:
            # 用户名密码错误
            return 500004

    @classmethod
    def db_login(cls, request, username, password):
        """
        登录认证
        """
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                django_login(request, user)
                return 0
            else:
                # 帐号被禁用
                return 500013
        else:
            # 用户名密码错误
            return 500004

```



集成User和Userprofile

```python
class UserProfileInline(admin.StackedInline):
    model = UserProfile


class NewUserAdmin(UserAdmin):
    inlines = [UserProfileInline]


# 注册时，在第二个参数写上 admin model
admin.site.unregister(User)
admin.site.register(User, NewUserAdmin)
```





微信登录

```python
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
```

