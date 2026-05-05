import core.models
from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('user_id', models.CharField(default=core.models.generate_user_id, max_length=10, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('password', models.CharField(max_length=255)),
                ('role', models.CharField(choices=[('patient', 'Patient'), ('doctor', 'Doctor')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PatientRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_id', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('age', models.FloatField()),
                ('weight', models.FloatField()),
                ('is_pregnant', models.BooleanField(default=False)),
                ('fever', models.BooleanField(default=False)),
                ('severe_headache', models.BooleanField(default=False)),
                ('joint_back_pain', models.BooleanField(default=False)),
                ('nausea_vomiting', models.BooleanField(default=False)),
                ('skin_rash', models.BooleanField(default=False)),
                ('vomiting_more_than_3', models.BooleanField(default=False)),
                ('bleeding', models.BooleanField(default=False)),
                ('extreme_weakness', models.BooleanField(default=False)),
                ('urine_output_low', models.BooleanField(default=False)),
                ('fever_not_improving', models.BooleanField(default=False)),
                ('drop_in_fever_with_weakness', models.BooleanField(default=False)),
                ('cold_hands_feet', models.BooleanField(default=False)),
                ('restless_drowsy', models.BooleanField(default=False)),
                ('clinical_score', models.IntegerField(default=0)),
                ('clinical_risk_level', models.CharField(blank=True, choices=[('low', 'Low Risk (0-3)'), ('possible', 'Possible Dengue (4-6)'), ('probable', 'Probable Dengue (7-9)'), ('high', 'High Risk of Dengue (>=10)')], max_length=20)),
                ('platelet_count', models.FloatField(blank=True, null=True)),
                ('wbc_count', models.FloatField(blank=True, null=True)),
                ('igg', models.FloatField(blank=True, null=True)),
                ('igm', models.FloatField(blank=True, null=True)),
                ('ml_prediction', models.CharField(blank=True, max_length=50)),
                ('ml_confidence', models.FloatField(blank=True, null=True)),
                ('dosage_recommendation', models.TextField(blank=True)),
                ('is_reviewed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='core.user')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_records', to='core.user')),
            ],
        ),
    ]
