# -*- coding: utf-8 -*-
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import User


def _safe_delete_field_file(field):
    try:
        f = field
        if not f:
            return
        storage = getattr(f, 'storage', None)
        name = getattr(f, 'name', None)
        # 仅当有有效存储与名称时删除
        if storage and name and storage.exists(name):
            storage.delete(name)
    except Exception:
        # 忽略删除异常，避免影响业务流程
        pass


@receiver(pre_save, sender=User)
def delete_old_avatar_on_change(sender, instance: User, **kwargs):
    """用户更新头像时，删除旧头像文件。"""
    if not instance or not getattr(instance, 'pk', None):
        return
    try:
        old = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return
    try:
        old_name = getattr(old.avatar, 'name', None)
        new_name = getattr(instance.avatar, 'name', None)
        if old_name and old_name != new_name:
            _safe_delete_field_file(old.avatar)
    except Exception:
        pass


@receiver(post_delete, sender=User)
def delete_avatar_on_user_delete(sender, instance: User, **kwargs):
    """用户被删除时，删除头像文件。"""
    try:
        _safe_delete_field_file(getattr(instance, 'avatar', None))
    except Exception:
        pass

