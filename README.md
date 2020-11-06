# django-bitchoice-field
Multiple Choice Field by bit switch.

usage:

```python
# in models
class AnyModel(models.Model):
    field_a = BitChoiceField(
        "test_field",
        choices=(
        (0, "not choose"),
        (1, "choose 1"),
        (2, "choose 2"),
        (4, "choose 3"),
        (8, "choose 4"),
        )
    )

# using

>>> obj = AnyModel.objects.first()
>>> obj.field_a
[1, 2, 4]
>>> obj.field_a = [1, 8]
>>> obj.save()

# in mysql [1, 8] will be stored as 9
```

help search and rest_framework_filter support, use ` bit_choice_filter_method `
