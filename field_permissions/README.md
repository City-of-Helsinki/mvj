Field permissions
=================

Field permissions app limits access to models fields. When running
migrate, the field permissions app creates custom permissions
for all of the fields in the registered models.

Permissions
-----------

Field permission connects a signal receiver to the `post_migrate`-signal.

The signal receiver goes through all of the models that are registered to field_permissions and creates the following custom permissions for every field in the model:

```
view_[model name]_[field_name]
change_[model name]_[field_name]
```

### Custom permissions

Add non-model-field permissions on models Meta class with the prefix `view_` or `change_` and the permissions will be picked up by `get_field_permissions_for_model()`.

For example:
```python
class MyModel(models.Model):
   ...
   class Meta:
      permissions = [("view_modelname_custom_value", "Can view modelname custom value")]
```

Usage
-----

Add `field_permissions` to `INSTALLED_APPS`

Register models to the field permissions registry in your apps models.py

```python
from django.contrib.gis.db import models
from field_permissions.registry import field_permissions


class DemoModel(models.Model):
    """An example"""

field_permissions.register(DemoModel) 
```

Inherit `field_permissions.serializers.FieldPermissionsSerializerMixin` in any model serializer you want to limit field access in.

```python
from field_permissions.serializers import FieldPermissionsSerializerMixin
from rest_framework import serializers

from .models import DemoModel


class DemoModelSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = DemoModel
        fields = '__all__'
```

The `FieldPermissionsSerializerMixin` provides the method `modify_fields_by_field_permissions` which can be used to remove fields the user doesn't have permission to read.

No fields are removed if the serializer doesn't have access to the serializer context.

Lastly, in view sets inherit `field_permissions.viewsets.FieldPermissionsViewsetMixin` which will make sure that the `modify_fields_by_field_permissions`-method is called when the serializer is used in the views.

```python
from field_permissions.viewsets import FieldPermissionsViewsetMixin
from rest_framework import viewsets

from .models import DemoModel
from .serializers import DemoModelSerializer


class DemoModelViewSet(FieldPermissionsViewsetMixin, viewsets.ModelViewSet):
    queryset = DemoModel.objects.all()
    serializer_class = DemoModelSerializer
```
