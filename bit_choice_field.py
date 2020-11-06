#!/usr/bin/env python
# encoding: utf-8
# author: 04
# create: 2018-08-27


import math
from django import forms
from django.core import checks
from django.db import models
from django.utils.functional import curry
from django.core.exceptions import ValidationError


class BitChoiceField(models.IntegerField):
    """ 多选二进制位开关
    params:
    choices = [
        (0, 'aaa'),
        (1, 'xxx'),
        (2, 'yyy'),
        (4, 'zzz'),
        (8, 'jjj'),
    ]
    """

    def __init__(self, *args, **kwargs):
        super(BitChoiceField, self).__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super(BitChoiceField, self).check(**kwargs)
        errors.extend(self._check_for_bitchoice())
        return errors

    def _check_for_bitchoice(self):
        if not self.choices:
            return [
                checks.Error(
                    'choices must be given.',
                    obj=self,
                    id='fields.BitChoice01'
                )
            ]
        flags = [_[0] for _ in self.choices]
        if len(set(flags)) < len(flags):
            return [
                checks.Error(
                    'choices flag must not be repeated.',
                    obj=self,
                    id='fields.BitChoice02'
                )
            ]
        for i in flags:
            if i == 0:
                continue
            power = math.log(i, 2)
            if int(power) != power:
                return [
                    checks.Error(
                        'choices flag must be power of 2, cannot be %s.' % i,
                        obj=self,
                        id='fields.BitChoice03'
                    )
                ]
        return []

    def to_python(self, value):
        ret = []
        choices = dict(self.choices).keys()
        base = 2
        power = 0
        flag = pow(base, power)
        while flag <= value:
            if flag & value == flag and flag in choices:
                ret.append(flag)
            power += 1
            flag = pow(base, power)
        if not ret:
            ret = [0]
        return ret

    def get_prep_value(self, value):
        if isinstance(value, (set, list, tuple)):
            return sum(value)
        return value

    def from_db_value(self, value, *args, **kwargs):
        return self.to_python(value)

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        defaults = {
            'choices_form_class': forms.TypedMultipleChoiceField,
            'coerce': int
        }
        defaults.update(kwargs)
        return super(BitChoiceField, self).formfield(**defaults)

    def contribute_to_class(self, cls, name, **kwargs):
        super(BitChoiceField, self).contribute_to_class(cls, name)
        setattr(cls, 'get_%s_display' % self.name, curry(bit_choice_display, field=self))

    def clean(self, multi_value, model):
        for value in multi_value:
            if value not in dict(self.flatchoices):
                raise ValidationError(
                    self.error_mesasge['invalid_choice'],
                    code='invalid_choice',
                    params={'value': value}
                )
        return multi_value


def bit_choice_display(self, field=None):
    value = getattr(self, field.attname)
    bit_list = list(value)
    choices_dict = dict(field.flatchoices)
    return [choices_dict.get(i) for i in bit_list]


def bit_choice_filter_method(qs, name, value, op='='):
    """ For django rest_framework
    name can not contain query ops if join other table til now,
    make subquery or query directly.
    """
    name_step_list = name.split('__')
    steps, real_name = name_step_list[:-1], name_step_list[-1]
    value_list = [int(v.strip()) for v in value.split(',')]
    conditions = []
    for v in value_list:
        conditions.append('{0} & {1} {2} {1}'.format(real_name, v, op))
    condition_str = ' or '.join(conditions)
    if not steps:
        return qs.extra(where=[condition_str])
    target_qs = qs
    for step in steps:
        target_qs = getattr(qs.model, step).get_queryset()
    target_qs = target_qs.extra(where=[condition_str])
    qs_param = {'__'.join(steps + ['in']): target_qs}
    qs = qs.filter(**qs_param)
    return qs
