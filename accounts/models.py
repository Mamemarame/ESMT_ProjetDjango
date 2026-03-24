from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('Etudiant', 'Etudiant'),
        ('Professeur', 'Professeur'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Etudiant')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
