# file: users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

# --------------------------
# 1. Hospital
# --------------------------
class Hospital(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)

    def __str__(self):
        return self.name

# --------------------------
# User Model for Login
# --------------------------
class User(models.Model):
    USER_ROLES = (
        ('admin', 'Admin'),
        ('hospitalAdmin', 'HospitalAdmin'),
    )

    id = models.AutoField(primary_key=True)
    userName = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=USER_ROLES)
    hospitalId = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.userName

# --------------------------
# 2. Product
# --------------------------
class Product(models.Model):
    
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

# --------------------------
# 3. Inventory
# --------------------------
class Inventory(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    threshold = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.product.name} at {self.hospital.name}"


class InventoryNotification(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
# --------------------------
# 4. Disease
# --------------------------
class Disease(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class DiseaseCase(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)
    date_reported = models.DateField()
    daily_cases = models.IntegerField(default=0)
    avg_7day_cases = models.FloatField(default=0.0)
    humidity = models.FloatField(default=0.0)
    temperature = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.disease.name} - {self.hospital.name} - {self.date_reported}"

class Outbreak(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)
    start_date = models.DateField()
    status = models.CharField(max_length=20, default='active')

    def __str__(self):
        return f"Outbreak: {self.disease.name} at {self.hospital.name}"

# --------------------------
# 7. ML Forecast (optional)
# --------------------------
class MLForecast(models.Model):
    id = models.AutoField(primary_key=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    forecast_date = models.DateField()
    predicted_demand = models.IntegerField()

    def __str__(self):
        return f"Forecast for {self.product.name} at {self.hospital.name} on {self.forecast_date}"
