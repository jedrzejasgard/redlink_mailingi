# Generated by Django 3.1.7 on 2021-03-08 12:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sendmailing', '0004_auto_20210304_1422'),
    ]

    operations = [
        migrations.RenameField(
            model_name='kampaniaredlink',
            old_name='dostarczone_wiadomoscidostarczone_wiadomosci_de',
            new_name='dostarczone_wiadomosci_de',
        ),
        migrations.RenameField(
            model_name='kampaniaredlink',
            old_name='dostarczone_wiadomoscidostarczone_wiadomosci_en',
            new_name='dostarczone_wiadomosci_en',
        ),
        migrations.RenameField(
            model_name='kampaniaredlink',
            old_name='dostarczone_wiadomoscidostarczone_wiadomosci_fr',
            new_name='dostarczone_wiadomosci_fr',
        ),
        migrations.RenameField(
            model_name='kampaniaredlink',
            old_name='dostarczone_wiadomoscidostarczone_wiadomosci_pl',
            new_name='dostarczone_wiadomosci_pl',
        ),
    ]