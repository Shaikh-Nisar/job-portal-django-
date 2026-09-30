from rest_framework import serializers

from .models import Job


class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "company_name",
            "location",
            "salary_min",
            "salary_max",
            "job_type",
            "experience",
            "skills",
            "description",
            "vacancies",
            "application_deadline",
            "is_active",
            "created_at",
            "updated_at",
        ]