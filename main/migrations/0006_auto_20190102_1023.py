# Generated by Django 2.0 on 2019-01-02 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_auto_20181229_1924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.CharField(max_length=500, primary_key=True, serialize=False),
        ),
    ]