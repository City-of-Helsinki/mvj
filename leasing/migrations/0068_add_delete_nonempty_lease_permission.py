# Generated by Django 2.2.1 on 2019-05-07 07:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leasing', '0067_inspectionattachment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lease',
            options={'permissions': [('delete_nonempty_lease', 'Can delete non-empty Lease')], 'verbose_name': 'Lease', 'verbose_name_plural': 'Leases'},
        ),
    ]
