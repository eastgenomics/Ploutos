# Generated by Django 3.2.5 on 2022-05-06 14:14

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
            name='Projects',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dx_id', models.CharField(max_length=35, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('created', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.dates')),
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
            name='StorageCosts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_size_live', models.FloatField()),
                ('unique_size_archived', models.FloatField()),
                ('total_size_live', models.FloatField()),
                ('total_size_archived', models.FloatField()),
                ('unique_cost_live', models.FloatField()),
                ('unique_cost_archived', models.FloatField()),
                ('total_cost_live', models.FloatField()),
                ('total_cost_archived', models.FloatField()),
                ('date', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.dates', unique=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.projects', unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='projects',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.users'),
        ),
        migrations.CreateModel(
            name='DailyOrgRunningTotal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('storage_charges', models.FloatField()),
                ('compute_charges', models.FloatField()),
                ('egress_charges', models.FloatField()),
                ('estimated_balance', models.FloatField()),
                ('date', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.dates', unique=True)),
            ],
        ),
    ]
