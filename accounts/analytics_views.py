from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.functions import Cast
from django.db.models import DateField
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from jobs.models import Job
from applications.models import Application


User = get_user_model()


def parse_date(value):
    """
    Convert YYYY-MM-DD string into a date.
    Returns None if invalid.
    """
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def parse_decimal(value):
    """
    Convert string into Decimal.
    Returns None if invalid.
    """
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def admin_only(request):
    """
    Analytics dashboard is available only to
    authenticated Django superusers.
    """
    return (
        request.user.is_authenticated
        and request.user.is_superuser
    )


@login_required
@require_GET
def analytics_dashboard_api(request):
    """
    Main Analytics Dashboard API.

    URL:
        /accounts/api/analytics/dashboard/

    Supported filters:
        date_from
        date_to
        location
        job_type
        experience
        salary_min
        salary_max
        status
        recruiter
        job_id
    """

    # =========================================================
    # ADMIN SECURITY
    # =========================================================

    if not admin_only(request):
        return JsonResponse(
            {
                "success": False,
                "message": "Admin access required.",
            },
            status=403,
        )

    # =========================================================
    # 1. READ FILTERS
    # =========================================================

    date_from = parse_date(
        request.GET.get("date_from")
    )

    date_to = parse_date(
        request.GET.get("date_to")
    )

    location = request.GET.get(
        "location",
        ""
    ).strip()

    job_type = request.GET.get(
        "job_type",
        ""
    ).strip()

    experience = request.GET.get(
        "experience",
        ""
    ).strip()

    status = request.GET.get(
        "status",
        ""
    ).strip()

    recruiter_id = request.GET.get(
        "recruiter",
        ""
    ).strip()

    job_id = request.GET.get(
        "job_id",
        ""
    ).strip()

    salary_min = parse_decimal(
        request.GET.get("salary_min")
    )

    salary_max = parse_decimal(
        request.GET.get("salary_max")
    )

    # =========================================================
    # 2. BASE JOB QUERYSET
    # =========================================================

    jobs = Job.objects.all()

    if location:
        jobs = jobs.filter(
            location__icontains=location
        )

    if job_type:
        jobs = jobs.filter(
            job_type=job_type
        )

    if experience:
        jobs = jobs.filter(
            experience__icontains=experience
        )

    if salary_min is not None:
        jobs = jobs.filter(
            Q(salary_max__gte=salary_min)
            | Q(salary_max__isnull=True)
        )

    if salary_max is not None:
        jobs = jobs.filter(
            Q(salary_min__lte=salary_max)
            | Q(salary_min__isnull=True)
        )

    if recruiter_id.isdigit():
        jobs = jobs.filter(
            recruiter_id=int(recruiter_id)
        )

    if job_id.isdigit():
        jobs = jobs.filter(
            id=int(job_id)
        )

    # Job date filters
    if date_from:
        jobs = jobs.filter(
            created_at__date__gte=date_from
        )

    if date_to:
        jobs = jobs.filter(
            created_at__date__lte=date_to
        )

    # Convert selected jobs into a list.
    job_ids = list(
        jobs.values_list(
            "id",
            flat=True
        )
    )

    # =========================================================
    # 3. APPLICATION QUERYSET
    # =========================================================

    applications = Application.objects.filter(
        job_id__in=job_ids
    )

    if status:
        applications = applications.filter(
            status=status
        )

    if date_from:
        applications = applications.filter(
            applied_at__date__gte=date_from
        )

    if date_to:
        applications = applications.filter(
            applied_at__date__lte=date_to
        )

    # =========================================================
    # 4. KPI COUNTS
    # =========================================================

    total_jobs = jobs.count()

    active_jobs = jobs.filter(
        is_active=True
    ).count()

    total_applications = applications.count()

    applied = applications.filter(
        status="applied"
    ).count()

    shortlisted = applications.filter(
        status="shortlisted"
    ).count()

    selected = applications.filter(
        status="selected"
    ).count()

    rejected = applications.filter(
        status="rejected"
    ).count()

    total_candidates = User.objects.filter(
        role="candidate"
    ).count()

    total_recruiters = User.objects.filter(
        role="recruiter"
    ).count()

    # =========================================================
    # 5. CALCULATED KPIs
    # =========================================================

    selection_rate = (
        round(
            (selected / total_applications) * 100,
            2
        )
        if total_applications
        else 0
    )

    applications_per_job = (
        round(
            total_applications / total_jobs,
            2
        )
        if total_jobs
        else 0
    )

    active_job_percentage = (
        round(
            (active_jobs / total_jobs) * 100,
            2
        )
        if total_jobs
        else 0
    )

    # =========================================================
    # 6. APPLICATION TREND
    # =========================================================

    trend_queryset = (
        applications
        .annotate(
            day=Cast(
                "applied_at",
                output_field=DateField()
            )
        )
        .values("day")
        .annotate(
            total=Count(
                "id",
                distinct=True
            ),
            applied=Count(
                "id",
                filter=Q(
                    status="applied"
                ),
                distinct=True
            ),
            shortlisted=Count(
                "id",
                filter=Q(
                    status="shortlisted"
                ),
                distinct=True
            ),
            selected=Count(
                "id",
                filter=Q(
                    status="selected"
                ),
                distinct=True
            ),
            rejected=Count(
                "id",
                filter=Q(
                    status="rejected"
                ),
                distinct=True
            ),
        )
        .order_by("day")
    )

    application_trend = []

    for row in trend_queryset:

        if row["day"]:

            application_trend.append(
                {
                    "date": row["day"].isoformat(),
                    "total": row["total"],
                    "applied": row["applied"],
                    "shortlisted": row["shortlisted"],
                    "selected": row["selected"],
                    "rejected": row["rejected"],
                }
            )

    # =========================================================
    # 7. APPLICATION STATUS ANALYSIS
    # =========================================================

    status_analysis = {
        "applied": applied,
        "shortlisted": shortlisted,
        "selected": selected,
        "rejected": rejected,
    }

    # =========================================================
    # 8. JOB TYPE ANALYSIS
    # =========================================================

    job_type_queryset = (
        jobs
        .values("job_type")
        .annotate(
            job_count=Count(
                "id",
                distinct=True
            ),
            application_count=Count(
                "applications",
                filter=Q(
                    applications__id__in=applications.values(
                        "id"
                    )
                ),
                distinct=True
            ),
        )
        .order_by(
            "-application_count",
            "-job_count"
        )
    )

    job_type_analysis = []

    job_type_labels = dict(
        Job.JOB_TYPE_CHOICES
    )

    for row in job_type_queryset:

        job_type_analysis.append(
            {
                "job_type": row["job_type"],
                "label": job_type_labels.get(
                    row["job_type"],
                    row["job_type"]
                ),
                "jobs": row["job_count"],
                "applications": row[
                    "application_count"
                ],
            }
        )

    # =========================================================
    # 9. LOCATION ANALYSIS
    # =========================================================

    location_queryset = (
        jobs
        .values("location")
        .annotate(
            jobs_count=Count(
                "id",
                distinct=True
            ),
            applications_count=Count(
                "applications",
                filter=Q(
                    applications__id__in=applications.values(
                        "id"
                    )
                ),
                distinct=True
            ),
        )
        .order_by(
            "-applications_count",
            "-jobs_count"
        )
    )

    location_analysis = []

    for row in location_queryset:

        location_analysis.append(
            {
                "location": row["location"],
                "jobs": row["jobs_count"],
                "applications": row[
                    "applications_count"
                ],
            }
        )

    # =========================================================
    # 10. EXPERIENCE ANALYSIS
    # =========================================================

    experience_queryset = (
        jobs
        .values("experience")
        .annotate(
            jobs_count=Count(
                "id",
                distinct=True
            ),
            applications_count=Count(
                "applications",
                filter=Q(
                    applications__id__in=applications.values(
                        "id"
                    )
                ),
                distinct=True
            ),
        )
        .order_by(
            "-applications_count",
            "-jobs_count"
        )
    )

    experience_analysis = []

    for row in experience_queryset:

        experience_analysis.append(
            {
                "experience": (
                    row["experience"]
                    or "Not specified"
                ),
                "jobs": row["jobs_count"],
                "applications": row[
                    "applications_count"
                ],
            }
        )

    # =========================================================
    # 11. TOP COMPANIES
    # =========================================================

    company_queryset = (
        jobs
        .values("company_name")
        .annotate(
            jobs_count=Count(
                "id",
                distinct=True
            ),
            applications_count=Count(
                "applications",
                filter=Q(
                    applications__id__in=applications.values(
                        "id"
                    )
                ),
                distinct=True
            ),
        )
        .order_by(
            "-applications_count",
            "-jobs_count"
        )[:10]
    )

    top_companies = []

    for row in company_queryset:

        top_companies.append(
            {
                "company": row["company_name"],
                "jobs": row["jobs_count"],
                "applications": row[
                    "applications_count"
                ],
            }
        )

    # =========================================================
    # 12. JOB PERFORMANCE
    # =========================================================

    job_performance_queryset = (
        jobs
        .annotate(
            application_count=Count(
                "applications",
                filter=Q(
                    applications__id__in=applications.values(
                        "id"
                    )
                ),
                distinct=True
            ),
            shortlisted_count=Count(
                "applications",
                filter=Q(
                    applications__id__in=applications.values(
                        "id"
                    ),
                    applications__status="shortlisted",
                ),
                distinct=True
            ),
            selected_count=Count(
                "applications",
                filter=Q(
                    applications__id__in=applications.values(
                        "id"
                    ),
                    applications__status="selected",
                ),
                distinct=True
            ),
        )
        .select_related("recruiter")
        .order_by(
            "-application_count",
            "-created_at"
        )[:20]
    )

    job_performance = []

    for job in job_performance_queryset:

        job_performance.append(
            {
                "id": job.id,
                "title": job.title,
                "company": job.company_name,
                "location": job.location,
                "job_type": job.job_type,
                "applications": job.application_count,
                "shortlisted": job.shortlisted_count,
                "selected": job.selected_count,
                "status": (
                    "Active"
                    if job.is_active
                    else "Inactive"
                ),
                "created_at": (
                    job.created_at.isoformat()
                ),
            }
        )

    # =========================================================
    # 13. RECENT ACTIVITY
    # =========================================================

    recent_applications = (
        applications
        .select_related(
            "candidate",
            "job"
        )
        .order_by(
            "-updated_at"
        )[:10]
    )

    recent_jobs = (
        jobs
        .select_related(
            "recruiter"
        )
        .order_by(
            "-created_at"
        )[:10]
    )

    activity = []

    # Application activity
    for application in recent_applications:

        activity.append(
            {
                "type": "application",
                "title": "Application updated",
                "message": (
                    f"{application.candidate.username} "
                    f"→ {application.job.title}"
                ),
                "status": application.status,
                "timestamp": (
                    application.updated_at.isoformat()
                ),
                "application_id": application.id,
            }
        )

    # Job activity
    for job in recent_jobs:

        activity.append(
            {
                "type": "job",
                "title": "New job posted",
                "message": (
                    f"{job.title} "
                    f"→ {job.company_name}"
                ),
                "status": (
                    "active"
                    if job.is_active
                    else "inactive"
                ),
                "timestamp": (
                    job.created_at.isoformat()
                ),
                "job_id": job.id,
            }
        )

    # Sort newest activity first
    activity.sort(
        key=lambda item: item["timestamp"],
        reverse=True
    )

    activity = activity[:15]

    # =========================================================
    # 14. FILTER OPTIONS
    # =========================================================

    available_job_types = [
        {
            "value": value,
            "label": label,
        }
        for value, label
        in Job.JOB_TYPE_CHOICES
    ]

    available_locations = list(
        Job.objects
        .exclude(
            location=""
        )
        .values_list(
            "location",
            flat=True
        )
        .distinct()
        .order_by(
            "location"
        )
    )

    available_experience = list(
        Job.objects
        .exclude(
            experience=""
        )
        .values_list(
            "experience",
            flat=True
        )
        .distinct()
        .order_by(
            "experience"
        )
    )

    available_statuses = [
        {
            "value": value,
            "label": label,
        }
        for value, label
        in Application.STATUS_CHOICES
    ]

    # =========================================================
    # 15. FINAL JSON RESPONSE
    # =========================================================

    return JsonResponse(
        {
            "success": True,

            "generated_at": (
                timezone.now().isoformat()
            ),

            # -------------------------------------------------
            # Active filters
            # -------------------------------------------------

            "filters": {
                "date_from": (
                    date_from.isoformat()
                    if date_from
                    else None
                ),

                "date_to": (
                    date_to.isoformat()
                    if date_to
                    else None
                ),

                "location": (
                    location
                    if location
                    else None
                ),

                "job_type": (
                    job_type
                    if job_type
                    else None
                ),

                "experience": (
                    experience
                    if experience
                    else None
                ),

                "salary_min": (
                    str(salary_min)
                    if salary_min is not None
                    else None
                ),

                "salary_max": (
                    str(salary_max)
                    if salary_max is not None
                    else None
                ),

                "status": (
                    status
                    if status
                    else None
                ),

                "recruiter": (
                    recruiter_id
                    if recruiter_id
                    else None
                ),

                "job_id": (
                    job_id
                    if job_id
                    else None
                ),
            },

            # -------------------------------------------------
            # KPI cards
            # -------------------------------------------------

            "kpis": {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "total_applications": total_applications,
                "applied": applied,
                "shortlisted": shortlisted,
                "selected": selected,
                "rejected": rejected,
                "total_candidates": total_candidates,
                "total_recruiters": total_recruiters,
                "application_success_rate": selection_rate,
                "selection_rate": selection_rate,
                "applications_per_job": applications_per_job,
                "active_job_percentage": active_job_percentage,
            },

            # -------------------------------------------------
            # Analytics
            # -------------------------------------------------

            "application_trend": application_trend,

            "status_analysis": status_analysis,

            "job_type_analysis": job_type_analysis,

            "location_analysis": location_analysis,

            "experience_analysis": experience_analysis,

            "top_companies": top_companies,

            "job_performance": job_performance,

            # -------------------------------------------------
            # Live activity
            # -------------------------------------------------

            "recent_activity": activity,

            # -------------------------------------------------
            # Filter dropdown options
            # -------------------------------------------------

            "filter_options": {
                "job_types": available_job_types,
                "locations": available_locations,
                "experiences": available_experience,
                "statuses": available_statuses,
            },
        }
    )