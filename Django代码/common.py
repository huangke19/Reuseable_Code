#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import authenticate
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth import login as django_login
from rest_framework_jwt.settings import api_settings


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
        obj = cls.objects.get(pk=id) if exist else None
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


class UserProfileInline(admin.StackedInline):
    model = UserProfile


class NewUserAdmin(UserAdmin):
    inlines = [UserProfileInline]


# 注册时，在第二个参数写上 admin model
admin.site.unregister(User)
admin.site.register(User, NewUserAdmin)
