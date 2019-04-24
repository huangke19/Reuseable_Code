import re
from decimal import Decimal

from django.db import models


# Create your models here.
class Bespoke(CModel):
    """
    预约信息
    """
    """"""

    RES_TYPE_CHOICE = (
        ("PERSONAL", '私人'),
        ("COMPANY", '公司')
    )

    res_time = models.DateTimeField(
        verbose_name='预约时间',
        auto_now_add=True,
        # default=timezone.now()
    )

    res_date = models.DateField(
        verbose_name='预约日期',
        blank=True,
        null=True
    )
    """"""

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

    class Meta:
        db_table = 'bespoke'
        verbose_name = '预约信息'
        verbose_name_plural = '预约信息'

    def __str__(self):
        return self.user.username
