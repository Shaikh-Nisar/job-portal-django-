from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('candidate', 'Candidate'),
        ('recruiter', 'Recruiter'),
    )

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='candidate'
    )

    phone = models.CharField(max_length=15, blank=True)

    skills = models.TextField(blank=True)

    education = models.TextField(blank=True)

    resume = models.FileField(
        upload_to='resumes/',
        blank=True,
        null=True
    )

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username


class CompanyProfile(models.Model):
    recruiter = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='company_profile'
    )

    company_name = models.CharField(max_length=200)

    company_email = models.EmailField(blank=True)

    company_phone = models.CharField(
        max_length=15,
        blank=True
    )

    website = models.URLField(blank=True)

    industry = models.CharField(
        max_length=150,
        blank=True
    )

    company_size = models.CharField(
        max_length=100,
        blank=True
    )

    location = models.CharField(
        max_length=200,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    company_logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.company_name