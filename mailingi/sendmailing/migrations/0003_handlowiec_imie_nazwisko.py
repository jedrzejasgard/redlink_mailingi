# Generated by Django 3.1.7 on 2021-03-04 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sendmailing', '0002_auto_20210304_1210'),
    ]

    operations = [
        migrations.AddField(
            model_name='handlowiec',
            name='imie_nazwisko',
            field=models.CharField(default='test', max_length=100),
        ),
    ]
