from django.conf import settings
from django.db import models

from jobs.models import Job


class Application(models.Model):

    STATUS_CHOICES = (
        ("applied", "Applied"),
        ("shortlisted", "Shortlisted"),
        ("rejected", "Rejected"),
        ("selected", "Selected"),
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications"
    )

    cover_letter = models.TextField(
        blank=True
    )

    resume = models.FileField(
        upload_to="applications/resumes/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="applied"
    )

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-applied_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["job", "candidate"],
                name="unique_job_candidate_application"
            )
        ]

        indexes = [
            models.Index(
                fields=["job", "-applied_at"],
                name="app_job_applied_idx"
            ),
            models.Index(
                fields=["candidate", "-applied_at"],
                name="app_candidate_applied_idx"
            ),
            models.Index(
                fields=["status", "-updated_at"],
                name="app_status_updated_idx"
            ),
        ]

    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"