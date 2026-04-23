# -*- coding: utf-8 -*-
from sqladmin import ModelView
from app.models import Provider, Prompt, UserPreference, FailedRecord


class ProviderAdmin(ModelView, model=Provider):
    column_list = [Provider.id, Provider.name, Provider.base_url, Provider.is_active, Provider.is_deleted, Provider.created_at, Provider.updated_at]
    column_searchable_list = [Provider.name]
    form_excluded_columns = [Provider.id, Provider.api_key, Provider.created_at, Provider.updated_at]
    can_export = False
    name = "提供商"
    name_plural = "提供商"


class PromptAdmin(ModelView, model=Prompt):
    column_list = [Prompt.id, Prompt.name, Prompt.is_deleted, Prompt.created_at, Prompt.updated_at]
    column_searchable_list = [Prompt.name]
    form_excluded_columns = [Prompt.id, Prompt.created_at, Prompt.updated_at]
    can_export = True
    name = "提示词"
    name_plural = "提示词"


class UserPreferenceAdmin(ModelView, model=UserPreference):
    column_list = [UserPreference.id, UserPreference.key, UserPreference.value, UserPreference.created_at, UserPreference.updated_at]
    column_searchable_list = [UserPreference.key]
    form_excluded_columns = [UserPreference.id, UserPreference.created_at, UserPreference.updated_at]
    can_export = True
    name = "用户偏好"
    name_plural = "用户偏好"


class FailedRecordAdmin(ModelView, model=FailedRecord):
    column_list = [FailedRecord.id, FailedRecord.source, FailedRecord.error, FailedRecord.retryable, FailedRecord.created_at, FailedRecord.updated_at]
    column_searchable_list = [FailedRecord.source, FailedRecord.error]
    form_excluded_columns = [FailedRecord.id, FailedRecord.created_at, FailedRecord.updated_at]
    can_export = True
    can_create = False
    name = "失败记录"
    name_plural = "失败记录"
