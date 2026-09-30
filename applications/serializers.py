from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):

    candidate_username = serializers.CharField(
        source="candidate.username",
        read_only=True
    )

    job_title = serializers.CharField(
        source="job.title",
        read_only=True
    )

    company_name = serializers.CharField(
        source="job.company_name",
        read_only=True
    )

    class Meta:
        model = Application

        fields = [
            "id",
            "job",
            "job_title",
            "company_name",
            "candidate",
            "candidate_username",
            "cover_letter",
            "resume",
            "status",
            "applied_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
             "candidate",
             "applied_at",
             "updated_at",
]
        