from django.db import models
import uuid
import random
import string


def generate_user_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class User(models.Model):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    ]
    user_id = models.CharField(max_length=10, unique=True, default=generate_user_id, primary_key=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.role}) - {self.user_id}"


class AdminUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class PatientRecord(models.Model):
    RISK_CHOICES = [
        ('low', 'Low Risk (0-3)'),
        ('possible', 'Possible Dengue (4-6)'),
        ('probable', 'Probable Dengue (7-9)'),
        ('high', 'High Risk of Dengue (>=10)'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records')
    record_id = models.UUIDField(default=uuid.uuid4, unique=True)

    age = models.FloatField()
    weight = models.FloatField()
    is_pregnant = models.BooleanField(default=False)

    fever = models.BooleanField(default=False)
    severe_headache = models.BooleanField(default=False)
    joint_back_pain = models.BooleanField(default=False)
    nausea_vomiting = models.BooleanField(default=False)
    skin_rash = models.BooleanField(default=False)
    vomiting_more_than_3 = models.BooleanField(default=False)
    bleeding = models.BooleanField(default=False)
    extreme_weakness = models.BooleanField(default=False)
    urine_output_low = models.BooleanField(default=False)
    fever_not_improving = models.BooleanField(default=False)
    drop_in_fever_with_weakness = models.BooleanField(default=False)
    cold_hands_feet = models.BooleanField(default=False)
    restless_drowsy = models.BooleanField(default=False)

    clinical_score = models.IntegerField(default=0)
    clinical_risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, blank=True)

    platelet_count = models.FloatField(null=True, blank=True)
    wbc_count = models.FloatField(null=True, blank=True)
    igg = models.FloatField(null=True, blank=True)
    igm = models.FloatField(null=True, blank=True)

    ml_prediction = models.CharField(max_length=50, blank=True)
    ml_confidence = models.FloatField(null=True, blank=True)

    dosage_recommendation = models.TextField(blank=True)

    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_records'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_clinical_score(self):
        score = 0
        score += 2 if self.fever else 0
        score += 1 if self.severe_headache else 0
        score += 1 if self.joint_back_pain else 0
        score += 1 if self.nausea_vomiting else 0
        score += 1 if self.skin_rash else 0
        score += 2 if self.vomiting_more_than_3 else 0
        score += 3 if self.bleeding else 0
        score += 2 if self.extreme_weakness else 0
        score += 2 if self.urine_output_low else 0
        score += 1 if self.fever_not_improving else 0
        score += 3 if self.drop_in_fever_with_weakness else 0
        score += 2 if self.cold_hands_feet else 0
        score += 2 if self.restless_drowsy else 0
        return score

    def get_risk_level(self, score):
        if score <= 3:
            return 'low'
        elif score <= 6:
            return 'possible'
        elif score <= 9:
            return 'probable'
        else:
            return 'high'

    def save(self, *args, **kwargs):
        self.clinical_score = self.calculate_clinical_score()
        self.clinical_risk_level = self.get_risk_level(self.clinical_score)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Record {self.record_id} - {self.patient.name}"