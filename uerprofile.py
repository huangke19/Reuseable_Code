#!/usr/bin/env python
# -*- coding: utf-8 -*-

''' 用户模型 '''
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import models
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import login as django_login, authenticate


class UserProfile(models.Model):
    """
    用户系统
    """
    NORMAL = 0
    WEIXIN = 1
    QQ = 2

    USER_SOURCE = (
        (NORMAL, u'正常'),
        (QQ, u'QQ'),
        (WEIXIN, u'Weixin'),
    )

    MALE = 1
    FEMALE = 2

    GENDER_CHOICES = (
        (MALE, u'男'),
        (FEMALE, u'女'),
    )
    user = models.OneToOneField(
        User,
        verbose_name=u'用户',
        related_name='userprofile',
        on_delete=models.CASCADE
    )

    openid = models.CharField(
        verbose_name=u'openid',
        max_length=64,
        db_index=True,
        null=True,
        blank=True
    )

    """"""

    # 角色
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE
    )

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

    class Meta:
        # abstract = True
        db_table = 'userprofile'
        verbose_name = u'用户信息'
        verbose_name_plural = u'用户信息'

    def __str__(self):
        return self.user.username
