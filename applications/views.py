from django.conf import settings
from django.core.mail import send_mail

from os.path import splitext

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from jobs.models import Job

from .models import Application


# =========================================================
# CONSTANTS
# =========================================================

ALLOWED_RESUME_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}

ALLOWED_APPLICATION_STATUSES = {
    "applied",
    "shortlisted",
    "rejected",
    "selected",
}

MAX_RESUME_SIZE = 5 * 1024 * 1024


# =========================================================
# APPLY FOR JOB
# =========================================================

@login_required
def apply_job(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        is_active=True
    )

    # Only candidates can apply
    if request.user.role != "candidate":
        messages.error(
            request,
            "Only candidates can apply for jobs."
        )
        return redirect(
            "job_detail",
            job_id=job.id
        )

    # Check application deadline
    if job.application_deadline:
        today = timezone.localdate()

        if today > job.application_deadline:
            messages.error(
                request,
                "The application deadline for this job has expired."
            )
            return redirect(
                "job_detail",
                job_id=job.id
            )

    # Check duplicate application
    if Application.objects.filter(
        job=job,
        candidate=request.user
    ).exists():
        messages.warning(
            request,
            "You have already applied for this job."
        )
        return redirect(
            "job_detail",
            job_id=job.id
        )

    # Check vacancies
    if job.vacancies:
        application_count = Application.objects.filter(
            job=job
        ).count()

        if application_count >= job.vacancies:
            messages.error(
                request,
                "Applications for this job are currently closed because all vacancies are filled."
            )
            return redirect(
                "job_detail",
                job_id=job.id
            )

    # GET request
    if request.method != "POST":
        return render(
            request,
            "applications/apply_job.html",
            {
                "job": job
            }
        )

    # =====================================================
    # POST REQUEST
    # =====================================================

    cover_letter = request.POST.get(
        "cover_letter",
        ""
    ).strip()

    resume = request.FILES.get("resume")

    # Cover letter validation
    if not cover_letter:
        messages.error(
            request,
            "Please enter a cover letter."
        )
        return render(
            request,
            "applications/apply_job.html",
            {
                "job": job,
                "cover_letter": cover_letter,
            }
        )

    if len(cover_letter) < 20:
        messages.error(
            request,
            "Cover letter must contain at least 20 characters."
        )
        return render(
            request,
            "applications/apply_job.html",
            {
                "job": job,
                "cover_letter": cover_letter,
            }
        )

    # Resume validation
    if not resume:
        messages.error(
            request,
            "Please upload your resume."
        )
        return render(
            request,
            "applications/apply_job.html",
            {
                "job": job,
                "cover_letter": cover_letter,
            }
        )

    # Resume extension validation
    extension = splitext(
        resume.name
    )[1].lower()

    if extension not in ALLOWED_RESUME_EXTENSIONS:
        messages.error(
            request,
            "Invalid resume format. Please upload PDF, DOC or DOCX."
        )
        return render(
            request,
            "applications/apply_job.html",
            {
                "job": job,
                "cover_letter": cover_letter,
            }
        )

    # Resume size validation
    if resume.size > MAX_RESUME_SIZE:
        messages.error(
            request,
            "Resume size must not exceed 5 MB."
        )
        return render(
            request,
            "applications/apply_job.html",
            {
                "job": job,
                "cover_letter": cover_letter,
            }
        )

    # Create application
    try:
        Application.objects.create(
            job=job,
            candidate=request.user,
            cover_letter=cover_letter,
            resume=resume,
        )

    except IntegrityError:
        messages.warning(
            request,
            "You have already applied for this job."
        )
        return redirect(
            "job_detail",
            job_id=job.id
        )

    # Success
    messages.success(
        request,
        "Application submitted successfully!"
    )

    return redirect(
        "my_applications"
    )


# =========================================================
# MY APPLICATIONS
# =========================================================

@login_required
def my_applications(request):

    applications = (
        Application.objects
        .filter(
            candidate=request.user
        )
        .select_related(
            "job"
        )
    )

    return render(
        request,
        "applications/my_applications.html",
        {
            "applications": applications,
        },
    )


# =========================================================
# JOB APPLICANTS
# =========================================================

@login_required
def job_applicants(request, job_id):

    # Only recruiters can view applicants
    if request.user.role != "recruiter":
        messages.error(
            request,
            "Only recruiters can view applicants."
        )
        return redirect(
            "candidate_dashboard"
        )

    # Recruiter can view only their own job
    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user
    )

    # Get applications with candidate in same query
    applications = (
        Application.objects
        .filter(
            job=job
        )
        .select_related(
            "candidate"
        )
    )

    return render(
        request,
        "applications/job_applicants.html",
        {
            "job": job,
            "applications": applications,
        },
    )


# =========================================================
# UPDATE APPLICATION STATUS
# =========================================================
@login_required
def update_application_status(request, application_id):
    if request.user.role != "recruiter":
        messages.error(
            request,
            "Only recruiters can update application status."
        )
        return redirect("candidate_dashboard")

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request method."
        )
        return redirect("recruiter_dashboard")

    application = get_object_or_404(
        Application,
        id=application_id,
        job__recruiter=request.user
    )

    status_value = request.POST.get(
        "status",
        ""
    ).strip()

    if status_value not in ALLOWED_APPLICATION_STATUSES:
        messages.error(
            request,
            "Invalid application status."
        )
        return redirect(
            "job_applicants",
            job_id=application.job.id
        )

    old_status = application.status

    application.status = status_value
    application.save(
        update_fields=[
            "status",
            "updated_at"
        ]
    )

    # Send real email only when status changes
    if old_status != status_value:

        try:
            send_mail(
                subject=(
                    f"Application Status Updated - "
                    f"{application.job.title}"
                ),

                message=(
                    f"Hello {application.candidate.username},\n\n"
                    f"Your application status has been updated.\n\n"
                    f"Job: {application.job.title}\n"
                    f"Company: {application.job.company_name}\n"
                    f"Previous Status: {old_status}\n"
                    f"New Status: {status_value}\n\n"
                    f"Please log in to JobPortal for more details.\n\n"
                    f"Thank you."
                ),

                from_email=settings.DEFAULT_FROM_EMAIL,

                recipient_list=[
                    application.candidate.email
                ],

                fail_silently=False,
            )

            messages.success(
                request,
                "Application status updated and email sent successfully!"
            )

        except Exception:
            messages.warning(
                request,
                "Application status updated, but email could not be sent."
            )

    else:
        messages.success(
            request,
            "Application status updated successfully!"
        )

    return redirect(
        "job_applicants",
        job_id=application.job.id
    )