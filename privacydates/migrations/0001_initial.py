# Generated by Django 3.1.4 on 2021-06-24 08:58

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnnihilationEnumContext',
            fields=[
                ('context_key', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('last_count', models.IntegerField(default=0)),
                ('last_date', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AnnihilationPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('policy', models.JSONField()),
                ('enumeration_key', models.CharField(blank=True, max_length=64, null=True)),
            ],
            options={
                'unique_together': {('policy', 'enumeration_key')},
            },
        ),
        migrations.CreateModel(
            name='EnumerationContext',
            fields=[
                ('context_key', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('last_count', models.IntegerField(default=0)),
                ('similarity_distance', models.IntegerField(default=0)),
                ('last_date', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DateTimeAnnihilation',
            fields=[
                ('dta_key', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('dt', models.DateTimeField()),
                ('annihilation_policy', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='privacydates.annihilationpolicy')),
            ],
            options={
                'ordering': ('dt',),
            },
        ),
        migrations.CreateModel(
            name='AnnihilationEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_date', models.DateTimeField()),
                ('iteration', models.IntegerField()),
                ('datetime_annihilation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='privacydates.datetimeannihilation')),
            ],
        ),
    ]