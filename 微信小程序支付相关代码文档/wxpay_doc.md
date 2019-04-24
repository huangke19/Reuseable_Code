



# 小程序微信支付说明文档



## 微信小程序支付流程分为5步

1. 移动端调用登录接口获取用户openid (和后端无关)
2. 后端生成订单
3. 后端调用微信支付统一下单API获取prepayid
4. 服务端将5个参数再次签名生成sign，再和5个参数一起返回给前端用于调起支付
5. 前端调起支付，用户进行付款
6. 后台的回调接口会收到微信发来的支付结果通知





## 一、移动端获取openid

pass



## 二、后端生成订单

调用create_order函数，略



## 三、后端调用微信统一下单API

官方文档： <https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=9_1&index=1>

不需要证书



#### 请求

必填参数： 

|      字段名       |                含义                |
| :---------------: | :--------------------------------: |
|       appid       |              小程序ID              |
|      mch_id       |               商户号               |
|     nonce_str     |             随机字符串             |
|       sign        |             第一次签名             |
|       body        |              商品描述              |
|   out_trade_no    |             商户订单号             |
|     total_fee     |    订单总金额(**单位是分！**）     |
| spibill_create_ip |               终端IP               |
|    notify_url     | 异步接收微信支付结果通知的回调地址 |
|    trade_type     |      交易类型(小程序是JSAPI)       |

以上必填参数转换为XML格式后，发送至微信统一下单接口地址。





#### 结果



只有通信成功

| 小程序ID     | appid        | wx8888888888888888               | 调用接口提交的小程序ID                                       |
| ------------ | ------------ | -------------------------------- | ------------------------------------------------------------ |
| 商户号       | mch_id       | 1900000109                       | 调用接口提交的商户号                                         |
| 设备号       | device_info  | 013467007045764                  | 自定义参数，可以为请求支付的终端设备号等                     |
| 随机字符串   | nonce_str    | 5K8264ILTKCH16CQ2502SI8ZNMTM67VS | 微信返回的随机字符串                                         |
| 签名         | sign         | C380BEC2BFD727A4B6845133519F3AD6 | 微信返回的签名值，详见[签名算法](https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=4_3) |
| 业务结果     | result_code  | SUCCESS                          | SUCCESS/FAIL                                                 |
| 错误代码     | err_code     | SYSTEMERROR                      | 详细参见下文错误列表                                         |
| 错误代码描述 | err_code_des | 系统错误                         | 错误信息描述                                                 |



通信和下单都成功  

return_code 和result_code都为SUCCESS，除了上面参数，还有下面的

|       字段名       | 变量名     | 示例值                                            | 描述                                                         |
| :----------------: | :--------- | :------------------------------------------------ | :----------------------------------------------------------- |
|      交易类型      | trade_type | JSAPI                                             | 交易类型，取值为：JSAPI，NATIVE，APP等，说明详见[参数规定](https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=4_2) |
| 预支付交易会话标识 | prepay_id  | wx201410272009395522657a690389285100              | 微信生成的预支付会话标识，用于后续接口调用中使用，该值有效期为2小时 |
|     二维码链接     | code_url   | weixin://wxpay/bizpayurl/up?pr=NwY5Mz9&groupid=00 | trade_type=NATIVE时有返回，此url用于生成支付二维码，然后提供给用户进行扫码支付。注意：code_url的值并非固定，使用时按照URL格式转成二维码即可 |



当通信和下单都成功时，第三步统一下单完成





## 四、二次签名



统一下单接口返回的数据里有5个是我们下一步需要的，它们是：

| 字段名   |  变量名   | 必填 | 类型   |                                           示例值 | 描述                                                         |
| :------- | :-------: | :--- | :----- | -----------------------------------------------: | :----------------------------------------------------------- |
| 小程序ID |   appId   | 是   | String |                               wxd678efh567hg6787 | 微信分配的小程序ID                                           |
| 时间戳   | timeStamp | 是   | String |                                       1490840662 | 时间戳从1970年1月1日00:00:00至今的秒数,即当前的时间          |
| 随机串   | nonceStr  | 是   | String |                 5K8264ILTKCH16CQ2502SI8ZNMTM67VS | 随机字符串，不长于32位。推荐[随机数生成算法](https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=4_3) |
| 数据包   |  package  | 是   | String | prepay_id=*wx2017033010242291fcfe0db70013231072* | 统一下单接口返回的 prepay_id 参数值，提交格式如：prepay_id=*wx2017033010242291fcfe0db70013231072* |
| 签名方式 | signType  | 是   | String |                                              MD5 | 签名类型，默认为MD5，支持HMAC-SHA256和MD5。注意此处需与统一下单的签名类型一致 |

将这5个参数再次按微信规定的方式（加key）进行签名加密生成第二个sign，然后和5个参数一起发送给移动端，此步完成。



## 五、调起支付

由移动端完成



## 六、后台接收微信支付结果通知

支付完成后，微信会把相关支付结果及用户信息通过数据流的形式发送给商户，商户需要接收处理，并按文档规范返回应答。

如果不能正确应答，微信会间间歇的发送10次通知，之后需要查询，由用户主动发起。



#### 接口url

该链接是通过【[统一下单API](https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=9_1)】中提交的参数notify_url设置

通知url必须为直接可访问的url，不能携带参数。

示例：notify_url：“https://pay.weixin.qq.com/wxpay/pay.action”



后台接收到微信请求后直接解析raw数据，从request.body中取数据

后台校验完成后返回xml格式的消息给微信服务器