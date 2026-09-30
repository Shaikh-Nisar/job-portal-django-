from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from .models import Job, SavedJob


# =========================================================
# VALIDATION HELPERS
# =========================================================

MAX_SALARY = Decimal("99999999.99")


def parse_salary(value):
    """
    Convert salary string into Decimal.
    Returns:
        Decimal value
        None for empty value
        Raises ValueError for invalid input
    """

    value = value.strip()

    if not value:
        return None

    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError("Salary must be a valid number.")

    if amount < 0:
        raise ValueError("Salary cannot be negative.")

    if amount > MAX_SALARY:
        raise ValueError(
            "Salary cannot be greater than 99,999,999.99."
        )

    if amount.as_tuple().exponent < -2:
        raise ValueError(
            "Salary can contain maximum 2 decimal places."
        )

    return amount


def parse_vacancies(value):
    """
    Convert vacancies into positive integer.
    """

    value = value.strip()

    if not value:
        return 1

    try:
        vacancies = int(value)
    except (TypeError, ValueError):
        raise ValueError(
            "Vacancies must be a valid whole number."
        )

    if vacancies < 1:
        raise ValueError(
            "Vacancies must be at least 1."
        )

    return vacancies


def parse_deadline(value):
    """
    Convert YYYY-MM-DD string into date.
    """

    value = value.strip()

    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        raise ValueError(
            "Application deadline must be a valid date."
        )


def validate_salary_range(salary_min, salary_max):
    """
    Validate relationship between minimum and maximum salary.
    """

    if (
        salary_min is not None
        and salary_max is not None
        and salary_min > salary_max
    ):
        raise ValueError(
            "Minimum salary cannot be greater than maximum salary."
        )


def get_valid_job_types():
    """
    Get valid values directly from model choices.
    """

    return {
        value
        for value, label in Job.JOB_TYPE_CHOICES
    }


# =========================================================
# JOB LIST / SEARCH / FILTER / PAGINATION
# =========================================================

@login_required
def job_list(request):

    # -----------------------------------------------------
    # Base queryset
    # -----------------------------------------------------

    jobs = Job.objects.filter(
        is_active=True
    ).order_by(
        "-created_at"
    )


    # -----------------------------------------------------
    # GET FILTER VALUES
    # -----------------------------------------------------

    search = request.GET.get(
        "search",
        ""
    ).strip()

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

    min_salary = request.GET.get(
        "min_salary",
        ""
    ).strip()

    max_salary = request.GET.get(
        "max_salary",
        ""
    ).strip()


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search:

        search_words = search.split()

        for word in search_words:

            jobs = jobs.filter(

                Q(title__icontains=word)

                | Q(company_name__icontains=word)

                | Q(skills__icontains=word)

                | Q(description__icontains=word)

                | Q(location__icontains=word)

                | Q(experience__icontains=word)
            )


    # -----------------------------------------------------
    # LOCATION FILTER
    # -----------------------------------------------------

    if location:

        jobs = jobs.filter(
            location__icontains=location
        )


    # -----------------------------------------------------
    # JOB TYPE FILTER
    # -----------------------------------------------------

    valid_job_types = get_valid_job_types()

    if job_type in valid_job_types:

        jobs = jobs.filter(
            job_type=job_type
        )


    # -----------------------------------------------------
    # EXPERIENCE FILTER
    # -----------------------------------------------------

    if experience:

        jobs = jobs.filter(
            experience__icontains=experience
        )


    # -----------------------------------------------------
    # MINIMUM SALARY FILTER
    # -----------------------------------------------------

    min_salary_value = None
    max_salary_value = None


    if min_salary:

        try:

            min_salary_value = parse_salary(
                min_salary
            )

        except ValueError:

            messages.warning(
                request,
                "Invalid minimum salary filter."
            )


    # -----------------------------------------------------
    # MAXIMUM SALARY FILTER
    # -----------------------------------------------------

    if max_salary:

        try:

            max_salary_value = parse_salary(
                max_salary
            )

        except ValueError:

            messages.warning(
                request,
                "Invalid maximum salary filter."
            )


    # -----------------------------------------------------
    # SALARY RANGE FILTER
    # -----------------------------------------------------

    if (
        min_salary_value is not None
        and max_salary_value is not None
        and min_salary_value > max_salary_value
    ):

        messages.warning(
            request,
            "Minimum salary cannot be greater than maximum salary."
        )

        min_salary_value = None
        max_salary_value = None


    if min_salary_value is not None:

        jobs = jobs.filter(
            salary_max__gte=min_salary_value
        )


    if max_salary_value is not None:

        jobs = jobs.filter(
            salary_min__lte=max_salary_value
        )


    # -----------------------------------------------------
    # PAGINATION
    # -----------------------------------------------------

    paginator = Paginator(
        jobs,
        10
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )


    # -----------------------------------------------------
    # SAVED JOB IDS
    # Only candidates need saved-job information
    # -----------------------------------------------------

    saved_job_ids = set()


    if request.user.role == "candidate":

        saved_job_ids = set(

            SavedJob.objects.filter(
                candidate=request.user
            ).values_list(
                "job_id",
                flat=True
            )
        )


    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render(
        request,
        "jobs/job_list.html",
        {
            "jobs": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "search": search,
            "location": location,
            "job_type": job_type,
            "experience": experience,
            "min_salary": min_salary,
            "max_salary": max_salary,
            "saved_job_ids": saved_job_ids,
        },
    )


# =========================================================
# JOB DETAIL
# =========================================================

@login_required
def job_detail(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        is_active=True
    )


    # Only candidates need saved status

    is_saved = False


    if request.user.role == "candidate":

        is_saved = SavedJob.objects.filter(
            candidate=request.user,
            job=job
        ).exists()


    return render(
        request,
        "jobs/job_detail.html",
        {
            "job": job,
            "is_saved": is_saved,
        },
    )


# =========================================================
# SAVE / UNSAVE JOB
# =========================================================

@login_required
def save_job(request, job_id):

    # Only POST request is allowed

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request method."
        )

        return redirect(
            "job_detail",
            job_id=job_id
        )


    # Only candidates can save jobs

    if request.user.role != "candidate":

        messages.error(
            request,
            "Only candidates can save jobs."
        )

        return redirect(
            "job_detail",
            job_id=job_id
        )


    job = get_object_or_404(
        Job,
        id=job_id,
        is_active=True
    )


    # Save or remove saved job

    saved_job, created = SavedJob.objects.get_or_create(
        candidate=request.user,
        job=job
    )


    if created:

        messages.success(
            request,
            "Job saved successfully!"
        )

    else:

        saved_job.delete()

        messages.success(
            request,
            "Job removed from saved jobs."
        )


    return redirect(
        "job_detail",
        job_id=job.id
    )


# =========================================================
# SAVED JOBS
# =========================================================

@login_required
def saved_jobs(request):

    if request.user.role != "candidate":

        messages.error(
            request,
            "Only candidates can access saved jobs."
        )

        return redirect(
            "recruiter_dashboard"
        )


    saved_jobs = (
        SavedJob.objects
        .filter(
            candidate=request.user
        )
        .select_related(
            "job"
        )
    )


    return render(
        request,
        "jobs/saved_jobs.html",
        {
            "saved_jobs": saved_jobs,
        },
    )


# =========================================================
# CREATE JOB
# =========================================================

@login_required
def create_job(request):

    # -----------------------------------------------------
    # Only recruiters
    # -----------------------------------------------------

    if request.user.role != "recruiter":

        messages.error(
            request,
            "Only recruiters can post jobs."
        )

        return redirect(
            "candidate_dashboard"
        )


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        company_name = request.POST.get(
            "company_name",
            ""
        ).strip()

        location = request.POST.get(
            "location",
            ""
        ).strip()

        salary_min_raw = request.POST.get(
            "salary_min",
            ""
        ).strip()

        salary_max_raw = request.POST.get(
            "salary_max",
            ""
        ).strip()

        job_type = request.POST.get(
            "job_type",
            "full_time"
        ).strip()

        experience = request.POST.get(
            "experience",
            ""
        ).strip()

        skills = request.POST.get(
            "skills",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        vacancies_raw = request.POST.get(
            "vacancies",
            "1"
        ).strip()

        application_deadline_raw = request.POST.get(
            "application_deadline",
            ""
        ).strip()


        # -------------------------------------------------
        # Required fields validation
        # -------------------------------------------------

        if (

            not title

            or not company_name

            or not location

            or not skills

            or not description

        ):

            messages.error(
                request,
                "Please fill all required fields."
            )

            return render(
                request,
                "jobs/create_job.html"
            )


        # -------------------------------------------------
        # Job type validation
        # -------------------------------------------------

        valid_job_types = get_valid_job_types()


        if job_type not in valid_job_types:

            messages.error(
                request,
                "Invalid job type selected."
            )

            return render(
                request,
                "jobs/create_job.html"
            )


        # -------------------------------------------------
        # Salary validation
        # -------------------------------------------------

        try:

            salary_min = parse_salary(
                salary_min_raw
            )

            salary_max = parse_salary(
                salary_max_raw
            )

            validate_salary_range(
                salary_min,
                salary_max
            )

        except ValueError as error:

            messages.error(
                request,
                str(error)
            )

            return render(
                request,
                "jobs/create_job.html"
            )


        # -------------------------------------------------
        # Vacancies validation
        # -------------------------------------------------

        try:

            vacancies = parse_vacancies(
                vacancies_raw
            )

        except ValueError as error:

            messages.error(
                request,
                str(error)
            )

            return render(
                request,
                "jobs/create_job.html"
            )


        # -------------------------------------------------
        # Deadline validation
        # -------------------------------------------------

        try:

            application_deadline = parse_deadline(
                application_deadline_raw
            )

        except ValueError as error:

            messages.error(
                request,
                str(error)
            )

            return render(
                request,
                "jobs/create_job.html"
            )


        # -------------------------------------------------
        # Deadline cannot be in the past
        # -------------------------------------------------

        if (

            application_deadline
            and application_deadline < timezone.localdate()

        ):

            messages.error(
                request,
                "Application deadline cannot be in the past."
            )

            return render(
                request,
                "jobs/create_job.html"
            )


        # -------------------------------------------------
        # Create job
        # -------------------------------------------------

        Job.objects.create(

            title=title,

            company_name=company_name,

            location=location,

            salary_min=salary_min,

            salary_max=salary_max,

            job_type=job_type,

            experience=experience,

            skills=skills,

            description=description,

            vacancies=vacancies,

            application_deadline=application_deadline,

            recruiter=request.user,
        )


        messages.success(
            request,
            "Job posted successfully!"
        )


        return redirect(
            "recruiter_dashboard"
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render(
        request,
        "jobs/create_job.html"
    )


# =========================================================
# MY JOBS
# =========================================================

@login_required
def my_jobs(request):

    if request.user.role != "recruiter":

        messages.error(
            request,
            "Only recruiters can access this page."
        )

        return redirect(
            "candidate_dashboard"
        )


    jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by(
        "-created_at"
    )


    return render(
        request,
        "jobs/my_jobs.html",
        {
            "jobs": jobs,
        },
    )


# =========================================================
# EDIT JOB
# =========================================================

@login_required
def edit_job(request, job_id):

    # -----------------------------------------------------
    # Only recruiters
    # -----------------------------------------------------

    if request.user.role != "recruiter":

        messages.error(
            request,
            "Only recruiters can edit jobs."
        )

        return redirect(
            "candidate_dashboard"
        )


    # -----------------------------------------------------
    # Recruiter can edit only their own job
    # -----------------------------------------------------

    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user
    )


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        job.title = request.POST.get(
            "title",
            ""
        ).strip()

        job.company_name = request.POST.get(
            "company_name",
            ""
        ).strip()

        job.location = request.POST.get(
            "location",
            ""
        ).strip()

        salary_min_raw = request.POST.get(
            "salary_min",
            ""
        ).strip()

        salary_max_raw = request.POST.get(
            "salary_max",
            ""
        ).strip()

        job.job_type = request.POST.get(
            "job_type",
            "full_time"
        ).strip()

        job.experience = request.POST.get(
            "experience",
            ""
        ).strip()

        job.skills = request.POST.get(
            "skills",
            ""
        ).strip()

        job.description = request.POST.get(
            "description",
            ""
        ).strip()

        vacancies_raw = request.POST.get(
            "vacancies",
            "1"
        ).strip()

        application_deadline_raw = request.POST.get(
            "application_deadline",
            ""
        ).strip()


        # -------------------------------------------------
        # Required fields validation
        # -------------------------------------------------

        if (

            not job.title

            or not job.company_name

            or not job.location

            or not job.skills

            or not job.description

        ):

            messages.error(
                request,
                "Please fill all required fields."
            )

            return render(
                request,
                "jobs/edit_job.html",
                {
                    "job": job
                }
            )


        # -------------------------------------------------
        # Job type validation
        # -------------------------------------------------

        valid_job_types = get_valid_job_types()


        if job.job_type not in valid_job_types:

            messages.error(
                request,
                "Invalid job type selected."
            )

            return render(
                request,
                "jobs/edit_job.html",
                {
                    "job": job
                }
            )


        # -------------------------------------------------
        # Salary validation
        # -------------------------------------------------

        try:

            salary_min = parse_salary(
                salary_min_raw
            )

            salary_max = parse_salary(
                salary_max_raw
            )

            validate_salary_range(
                salary_min,
                salary_max
            )

        except ValueError as error:

            messages.error(
                request,
                str(error)
            )

            return render(
                request,
                "jobs/edit_job.html",
                {
                    "job": job
                }
            )


        # -------------------------------------------------
        # Vacancies validation
        # -------------------------------------------------

        try:

            vacancies = parse_vacancies(
                vacancies_raw
            )

        except ValueError as error:

            messages.error(
                request,
                str(error)
            )

            return render(
                request,
                "jobs/edit_job.html",
                {
                    "job": job
                }
            )


        # -------------------------------------------------
        # Do not allow vacancies below existing applications
        # -------------------------------------------------

        current_applications = job.applications.count()


        if vacancies < current_applications:

            messages.error(
                request,
                (
                    "Vacancies cannot be less than the "
                    f"existing applications ({current_applications})."
                )
            )

            return render(
                request,
                "jobs/edit_job.html",
                {
                    "job": job
                }
            )


        # -------------------------------------------------
        # Deadline validation
        # -------------------------------------------------

        try:

            application_deadline = parse_deadline(
                application_deadline_raw
            )

        except ValueError as error:

            messages.error(
                request,
                str(error)
            )

            return render(
                request,
                "jobs/edit_job.html",
                {
                    "job": job
                }
            )


        # -------------------------------------------------
        # Update job
        # -------------------------------------------------

        job.salary_min = salary_min

        job.salary_max = salary_max

        job.vacancies = vacancies

        job.application_deadline = application_deadline


        job.save()


        messages.success(
            request,
            "Job updated successfully!"
        )


        return redirect(
            "my_jobs"
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render(
        request,
        "jobs/edit_job.html",
        {
            "job": job
        }
    )


# =========================================================
# DELETE JOB
# =========================================================

@login_required
def delete_job(request, job_id):

    if request.user.role != "recruiter":

        messages.error(
            request,
            "Only recruiters can delete jobs."
        )

        return redirect(
            "candidate_dashboard"
        )


    # Recruiter can delete only their own job

    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user
    )


    if request.method == "POST":

        job.delete()

        messages.success(
            request,
            "Job deleted successfully!"
        )

        return redirect(
            "my_jobs"
        )


    return render(
        request,
        "jobs/delete_job.html",
        {
            "job": job
        }
    )