from django.db.models import Q

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import Job, SavedJob
from .serializers import JobSerializer


# ==============================================================
# Job List API
# ==============================================================

@api_view(["GET", "POST"])
def job_api_list(request):

    # ==========================================================
    # GET - Job List + Filters + Pagination
    # ==========================================================

    if request.method == "GET":

        # Only active jobs
        jobs = Job.objects.filter(
            is_active=True
        ).order_by("-created_at")

        # ------------------------------------------------------
        # SEARCH FILTER
        # Example:
        # /api/jobs/?search=python
        # ------------------------------------------------------

        search = request.query_params.get("search")

        if search:
            jobs = jobs.filter(
                Q(title__icontains=search)
                | Q(company_name__icontains=search)
                | Q(location__icontains=search)
                | Q(skills__icontains=search)
                | Q(description__icontains=search)
                | Q(experience__icontains=search)
                | Q(job_type__icontains=search)
            )

        # ------------------------------------------------------
        # LOCATION FILTER
        # Example:
        # /api/jobs/?location=hyderabad
        # ------------------------------------------------------

        location = request.query_params.get("location")

        if location:
            jobs = jobs.filter(
                location__icontains=location
            )

        # ------------------------------------------------------
        # MINIMUM SALARY FILTER
        # Example:
        # /api/jobs/?salary_min=40000
        # ------------------------------------------------------

        salary_min = request.query_params.get("salary_min")

        if salary_min:
            try:
                salary_min = float(salary_min)

                jobs = jobs.filter(
                    salary_max__gte=salary_min
                )

            except ValueError:
                return Response(
                    {
                        "error": "salary_min must be a valid number."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # ------------------------------------------------------
        # MAXIMUM SALARY FILTER
        # Example:
        # /api/jobs/?salary_max=70000
        # ------------------------------------------------------

        salary_max = request.query_params.get("salary_max")

        if salary_max:
            try:
                salary_max = float(salary_max)

                jobs = jobs.filter(
                    salary_min__lte=salary_max
                )

            except ValueError:
                return Response(
                    {
                        "error": "salary_max must be a valid number."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # ------------------------------------------------------
        # JOB TYPE FILTER
        #
        # Values:
        # full_time
        # part_time
        # internship
        # contract
        #
        # Example:
        # /api/jobs/?job_type=full_time
        # ------------------------------------------------------

        job_type = request.query_params.get("job_type")

        if job_type:
            jobs = jobs.filter(
                job_type__iexact=job_type
            )

        # ------------------------------------------------------
        # EXPERIENCE FILTER
        #
        # Example:
        # /api/jobs/?experience=4
        # ------------------------------------------------------

        experience = request.query_params.get("experience")

        if experience:
            jobs = jobs.filter(
                experience__icontains=experience
            )

        # ------------------------------------------------------
        # SORTING
        #
        # ?sort=latest
        # ?sort=oldest
        # ?sort=salary_high
        # ?sort=salary_low
        #
        # ------------------------------------------------------

        sort = request.query_params.get("sort")

        if sort == "latest":

            jobs = jobs.order_by(
                "-created_at"
            )

        elif sort == "oldest":

            jobs = jobs.order_by(
                "created_at"
            )

        elif sort == "salary_high":

            jobs = jobs.order_by(
                "-salary_max"
            )

        elif sort == "salary_low":

            jobs = jobs.order_by(
                "salary_min"
            )

        # ------------------------------------------------------
        # PAGINATION
        # ------------------------------------------------------

        paginator = PageNumberPagination()

        paginator.page_size = 2

        paginated_jobs = paginator.paginate_queryset(
            jobs,
            request
        )

        serializer = JobSerializer(
            paginated_jobs,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    # ==========================================================
    # POST - Create Job
    # ==========================================================

    if request.method == "POST":

        # Authentication
        if not request.user.is_authenticated:

            return Response(
                {
                    "error": "Authentication required."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Only recruiter
        if request.user.role != "recruiter":

            return Response(
                {
                    "error": "Only recruiters can create jobs."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = JobSerializer(
            data=request.data
        )

        if serializer.is_valid():

            job = serializer.save(
                recruiter=request.user
            )

            return Response(
                JobSerializer(job).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ==============================================================
# Job Detail API
# ==============================================================

@api_view(["GET", "PUT", "PATCH", "DELETE"])
def job_api_detail(request, job_id):

    # Find job
    try:

        job = Job.objects.get(
            id=job_id
        )

    except Job.DoesNotExist:

        return Response(
            {
                "error": "Job not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # ==========================================================
    # GET - Job Details
    # ==========================================================

    if request.method == "GET":

        if not job.is_active:

            return Response(
                {
                    "error": "Job not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = JobSerializer(
            job
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # ==========================================================
    # Authentication required
    # ==========================================================

    if not request.user.is_authenticated:

        return Response(
            {
                "error": "Authentication required."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # ==========================================================
    # Only recruiter can modify
    # ==========================================================

    if request.user.role != "recruiter":

        return Response(
            {
                "error": "Only recruiters can modify jobs."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # ==========================================================
    # Only owner recruiter can modify
    # ==========================================================

    if job.recruiter != request.user:

        return Response(
            {
                "error": "You can only modify your own jobs."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # ==========================================================
    # PUT / PATCH
    # ==========================================================

    if request.method in ["PUT", "PATCH"]:

        serializer = JobSerializer(
            job,
            data=request.data,
            partial=(request.method == "PATCH")
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # ==========================================================
    # DELETE
    # ==========================================================

    if request.method == "DELETE":

        job.delete()

        return Response(
            {
                "message": "Job deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )
    





    # ==============================================================
# Saved Jobs API
# ==============================================================

@api_view(["GET", "POST"])
def saved_job_api_list(request):

    # ----------------------------------------------------------
    # Authentication
    # ----------------------------------------------------------

    if not request.user.is_authenticated:
        return Response(
            {
                "error": "Authentication required."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # ----------------------------------------------------------
    # Only candidate
    # ----------------------------------------------------------

    if request.user.role != "candidate":
        return Response(
            {
                "error": "Only candidates can use saved jobs."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # ----------------------------------------------------------
    # GET - List saved jobs
    # ----------------------------------------------------------

    if request.method == "GET":

        saved_jobs = SavedJob.objects.filter(
            candidate=request.user
        ).select_related("job")

        paginator = PageNumberPagination()
        paginator.page_size = 10

        paginated_saved_jobs = paginator.paginate_queryset(
            saved_jobs,
            request
        )

        data = []

        for saved in paginated_saved_jobs:

            data.append(
                {
                    "id": saved.id,
                    "job": saved.job.id,
                    "title": saved.job.title,
                    "company_name": saved.job.company_name,
                    "location": saved.job.location,
                    "job_type": saved.job.job_type,
                    "salary_min": saved.job.salary_min,
                    "salary_max": saved.job.salary_max,
                    "saved_at": saved.saved_at,
                }
            )

        return paginator.get_paginated_response(data)

    # ----------------------------------------------------------
    # POST - Save a job
    # ----------------------------------------------------------

    if request.method == "POST":

        job_id = request.data.get("job")

        if not job_id:
            return Response(
                {
                    "error": "Job ID is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            job = Job.objects.get(
                id=job_id,
                is_active=True
            )

        except Job.DoesNotExist:
            return Response(
                {
                    "error": "Job not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if SavedJob.objects.filter(
            candidate=request.user,
            job=job
        ).exists():

            return Response(
                {
                    "error": "Job already saved."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        saved_job = SavedJob.objects.create(
            candidate=request.user,
            job=job
        )

        return Response(
            {
                "message": "Job saved successfully.",
                "id": saved_job.id,
                "job": job.id,
                "title": job.title
            },
            status=status.HTTP_201_CREATED
        )


@api_view(["DELETE"])
def saved_job_api_detail(request, saved_job_id):

    # ----------------------------------------------------------
    # Authentication
    # ----------------------------------------------------------

    if not request.user.is_authenticated:
        return Response(
            {
                "error": "Authentication required."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # ----------------------------------------------------------
    # Only candidate
    # ----------------------------------------------------------

    if request.user.role != "candidate":
        return Response(
            {
                "error": "Only candidates can delete saved jobs."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        saved_job = SavedJob.objects.get(
            id=saved_job_id,
            candidate=request.user
        )

    except SavedJob.DoesNotExist:
        return Response(
            {
                "error": "Saved job not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    saved_job.delete()

    return Response(
        {
            "message": "Job removed from saved jobs."
        },
        status=status.HTTP_200_OK
    )