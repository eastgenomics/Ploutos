# Generated by Django 4.0.4 on 2022-05-11 13:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dates',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Projects',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dx_id', models.CharField(max_length=35, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('created', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.dates')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.users')),
            ],
        ),
    ]
