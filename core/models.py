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
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    user_id  = models.CharField(max_length=10, unique=True, default=generate_user_id, primary_key=True)
    name     = models.CharField(max_length=100)
    email    = models.EmailField(max_length=254, unique=True, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    password = models.CharField(max_length=255)
    role     = models.CharField(max_length=10, choices=ROLE_CHOICES)

    

    # Patient profile fields (used when role = 'patient')
    age         = models.FloatField(null=True, blank=True)
    weight      = models.FloatField(null=True, blank=True)
    gender      = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    is_pregnant = models.BooleanField(default=False)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

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
        ('low', 'Low Risk'),
        ('high', 'High Risk'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records')
    record_id = models.UUIDField(default=uuid.uuid4, unique=True)

    age = models.FloatField()
    weight = models.FloatField()
    gender = models.CharField(
    max_length=10,
    choices=[('male','Male'), ('female','Female'), ('other','Other')]
    )
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
    abdominal_pain = models.BooleanField(default=False)   

    clinical_score = models.IntegerField(default=0)
    clinical_risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, blank=True)

    platelet_count = models.FloatField(null=True, blank=True)
    wbc_count = models.FloatField(null=True, blank=True)
    ns1 = models.FloatField(null=True, blank=True)
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
        score += 1 if self.fever else 0
        score += 2 if self.severe_headache else 0
        score += 2 if self.joint_back_pain else 0
        score += 1 if self.nausea_vomiting else 0
        score += 0.5 if self.skin_rash else 0
        score += 2 if self.vomiting_more_than_3 else 0
        score += 3 if self.bleeding else 0
        score += 3 if self.extreme_weakness else 0
        score += 3 if self.urine_output_low else 0
        score += 2 if self.fever_not_improving else 0
        score += 3 if self.drop_in_fever_with_weakness else 0
        score += 1 if self.cold_hands_feet else 0
        score += 3 if self.restless_drowsy else 0
        score += 1 if self.abdominal_pain else 0
        # Age and pregnancy bonuses
        if self.age and self.age > 70:
            score += 1
        if self.is_pregnant:
            score += 1
        return score

    def get_risk_level(self, score):
        if score <= 4:
            return 'low'
        else:
            return 'high'
        

    def save(self, *args, **kwargs):
        self.clinical_score = self.calculate_clinical_score()
        self.clinical_risk_level = self.get_risk_level(self.clinical_score)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Record {self.record_id} - {self.patient.name}"