# Generated migration for total_sold field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_transaction_transactionitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='total_sold',
            field=models.PositiveIntegerField(default=0, help_text='Total units sold'),
        ),
    ]
