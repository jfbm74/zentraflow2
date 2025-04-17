# apps/configuracion/migrations/0002_emailoauthcredentials_ingesta_enabled.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuracion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailoauthcredentials',
            name='ingesta_enabled',
            field=models.BooleanField(default=True, verbose_name='Habilitar Ingesta'),
        ),
    ]