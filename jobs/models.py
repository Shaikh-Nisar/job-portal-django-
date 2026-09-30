from django.conf import settings
from django.db import models


class Job(models.Model):

    JOB_TYPE_CHOICES = (
        ("full_time", "Full Time"),
        ("part_time", "Part Time"),
        ("internship", "Internship"),
        ("contract", "Contract"),
    )

    title = models.CharField(
        max_length=200
    )

    company_name = models.CharField(
        max_length=200
    )

    location = models.CharField(
        max_length=200
    )

    salary_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    salary_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        default="full_time"
    )

    experience = models.CharField(
        max_length=100,
        blank=True
    )

    skills = models.TextField(
        help_text="Example: Python, Django, MySQL, REST API"
    )

    description = models.TextField()

    vacancies = models.PositiveIntegerField(
        default=1
    )

    application_deadline = models.DateField(
        null=True,
        blank=True
    )

    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posted_jobs"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        indexes = [
            models.Index(
                fields=["is_active", "-created_at"],
                name="job_active_created_idx"
            ),

            models.Index(
                fields=["recruiter", "-created_at"],
                name="job_recruiter_created_idx"
            ),

            models.Index(
                fields=["job_type"],
                name="job_type_idx"
            ),

            models.Index(
                fields=["location"],
                name="job_location_idx"
            ),

            models.Index(
                fields=["application_deadline"],
                name="job_deadline_idx"
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.company_name}"


class SavedJob(models.Model):

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_jobs"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="saved_by_candidates"
    )

    saved_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job"],
                name="unique_saved_job"
            )
        ]

        indexes = [
            models.Index(
                fields=["candidate", "-saved_at"],
                name="saved_candidate_idx"
            ),

            models.Index(
                fields=["job"],
                name="saved_job_idx"
            ),
        ]

        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"