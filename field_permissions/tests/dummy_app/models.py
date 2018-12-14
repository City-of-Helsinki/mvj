from django.db import models


class DummySecondSub(models.Model):
    secondsubfield1 = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Dummy second sub"
        verbose_name_plural = "Dummy second sub"


class Dummy(models.Model):
    field1 = models.CharField(max_length=255)
    field2 = models.BooleanField(default=False)
    field3 = models.BooleanField(default=False)
    second_sub = models.ForeignKey(DummySecondSub, verbose_name="Second sub", null=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Dummy"
        verbose_name_plural = "Dummies"


class DummySub(models.Model):
    subfield1 = models.CharField(max_length=255)
    dummy = models.ForeignKey(Dummy, verbose_name="Dummy", on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Dummy sub"
        verbose_name_plural = "Dummy subs"
