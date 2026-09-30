from os.path import splitext

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import Application
from .serializers import ApplicationSerializer
from jobs.models import Job


ALLOWED_RESUME_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_RESUME_SIZE = 5 * 1024 * 1024


@api_view(["GET", "POST"])
def application_api_list(request):

    # ==========================================================
    # GET - List Applications
    # ==========================================================

    if request.method == "GET":

        # Authentication check
        if not request.user.is_authenticated:
            return Response(
                {
                    "error": "Authentication required."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Candidate - see only own applications
        if request.user.role == "candidate":

            applications = Application.objects.filter(
                candidate=request.user
            ).select_related(
                "job",
                "candidate"
            )

        # Recruiter - see applications for own jobs
        elif request.user.role == "recruiter":

            applications = Application.objects.filter(
                job__recruiter=request.user
            ).select_related(
                "job",
                "candidate"
            )

        else:

            applications = Application.objects.none()


        # ------------------------------------------------------
        # Status Filter
        # Example:
        # /api/applications/?status=selected
        # ------------------------------------------------------

        status_filter = request.query_params.get("status")

        if status_filter:

            applications = applications.filter(
                status=status_filter
            )


        # ------------------------------------------------------
        # Pagination
        # ------------------------------------------------------

        paginator = PageNumberPagination()

        paginator.page_size = 2

        paginated_applications = paginator.paginate_queryset(
            applications,
            request
        )


        serializer = ApplicationSerializer(
            paginated_applications,
            many=True
        )


        return paginator.get_paginated_response(
            serializer.data
        )


    # ==========================================================
    # POST - Apply for a Job
    # ==========================================================

    if request.method == "POST":

        # ------------------------------------------------------
        # Authentication check
        # ------------------------------------------------------

        if not request.user.is_authenticated:

            return Response(
                {
                    "error": "Authentication required."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


        # ------------------------------------------------------
        # Only candidate can apply
        # ------------------------------------------------------

        if request.user.role != "candidate":

            return Response(
                {
                    "error": "Only candidates can apply for jobs."
                },
                status=status.HTTP_403_FORBIDDEN
            )


        # ------------------------------------------------------
        # Get Job ID
        # ------------------------------------------------------

        job_id = request.data.get("job")


        if not job_id:

            return Response(
                {
                    "error": "Job ID is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ------------------------------------------------------
        # Validate Job ID
        # ------------------------------------------------------

        try:

            job_id = int(job_id)

        except (TypeError, ValueError):

            return Response(
                {
                    "error": "Job ID must be a valid number."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ------------------------------------------------------
        # Find active job
        # ------------------------------------------------------

        try:

            job = Job.objects.get(
                id=job_id,
                is_active=True
            )

        except Job.DoesNotExist:

            return Response(
                {
                    "error": "Job not found or inactive."
                },
                status=status.HTTP_404_NOT_FOUND
            )


        # ------------------------------------------------------
        # Check Application Deadline
        # ------------------------------------------------------

        if job.application_deadline:

            today = timezone.localdate()

            if today > job.application_deadline:

                return Response(
                    {
                        "error": (
                            "The application deadline for this job "
                            "has expired."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


        # ------------------------------------------------------
        # Check Vacancy Limit
        # ------------------------------------------------------

        if job.vacancies:

            application_count = Application.objects.filter(
                job=job
            ).count()

            if application_count >= job.vacancies:

                return Response(
                    {
                        "error": (
                            "Applications for this job are currently "
                            "closed because all vacancies are filled."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


        # ------------------------------------------------------
        # Check Duplicate Application
        # ------------------------------------------------------

        if Application.objects.filter(
            job=job,
            candidate=request.user
        ).exists():

            return Response(
                {
                    "error": "You have already applied for this job."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ------------------------------------------------------
        # Cover Letter Validation
        # ------------------------------------------------------

        cover_letter = str(
            request.data.get("cover_letter", "")
        ).strip()


        if not cover_letter:

            return Response(
                {
                    "error": "Please enter a cover letter."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        if len(cover_letter) < 20:

            return Response(
                {
                    "error": (
                        "Cover letter must contain at least "
                        "20 characters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ------------------------------------------------------
        # Resume Validation
        # ------------------------------------------------------

        resume = request.FILES.get("resume")


        if not resume:

            return Response(
                {
                    "error": "Please upload your resume."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ------------------------------------------------------
        # Resume Extension
        # ------------------------------------------------------

        extension = splitext(
            resume.name
        )[1].lower()


        if extension not in ALLOWED_RESUME_EXTENSIONS:

            return Response(
                {
                    "error": (
                        "Invalid resume format. "
                        "Please upload PDF, DOC or DOCX."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ------------------------------------------------------
        # Resume Size
        # ------------------------------------------------------

        if resume.size > MAX_RESUME_SIZE:

            return Response(
                {
                    "error": "Resume size must not exceed 5 MB."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ------------------------------------------------------
        # Validate Application Data
        # ------------------------------------------------------

        serializer = ApplicationSerializer(
            data=request.data
        )


        if serializer.is_valid():

            application = serializer.save(
                job=job,
                candidate=request.user
            )


            return Response(
                ApplicationSerializer(application).data,
                status=status.HTTP_201_CREATED
            )


        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ==============================================================
# Application Detail API
# ==============================================================

@api_view(["GET", "PATCH", "PUT", "DELETE"])
def application_api_detail(request, application_id):

    # ==========================================================
    # Find Application
    # ==========================================================

    try:

        application = Application.objects.select_related(
            "job",
            "candidate"
        ).get(
            id=application_id
        )

    except Application.DoesNotExist:

        return Response(
            {
                "error": "Application not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )


    # ==========================================================
    # Authentication Check
    # ==========================================================

    if not request.user.is_authenticated:

        return Response(
            {
                "error": "Authentication required."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )


    # ==========================================================
    # GET - Application Details
    # ==========================================================

    if request.method == "GET":

        # Candidate can see own application
        # Recruiter can see applications for own job

        if (
            request.user != application.candidate
            and request.user != application.job.recruiter
        ):

            return Response(
                {
                    "error": (
                        "You do not have permission "
                        "to view this application."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )


        serializer = ApplicationSerializer(
            application
        )


        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    # ==========================================================
    # PATCH / PUT - Update Application
    # ==========================================================

    if request.method in ["PATCH", "PUT"]:

        # Only recruiter can update application

        if request.user != application.job.recruiter:

            return Response(
                {
                    "error": (
                        "Only the recruiter can update "
                        "this application."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )


        serializer = ApplicationSerializer(
            application,
            data=request.data,
            partial=(request.method == "PATCH")
        )


        if serializer.is_valid():

            old_status = application.status


            updated_application = serializer.save()


            new_status = updated_application.status


            # --------------------------------------------------
            # Send email only when status changes
            # --------------------------------------------------

            if old_status != new_status:

                send_mail(

                    subject=(
                        f"Application Status Updated - "
                        f"{updated_application.job.title}"
                    ),


                    message=(

                        f"Hello "
                        f"{updated_application.candidate.username},"
                        f"\n\n"

                        f"Your application status has been "
                        f"updated."
                        f"\n\n"

                        f"Job: "
                        f"{updated_application.job.title}"
                        f"\n"

                        f"Company: "
                        f"{updated_application.job.company_name}"
                        f"\n"

                        f"Previous Status: "
                        f"{old_status}"
                        f"\n"

                        f"New Status: "
                        f"{new_status}"
                        f"\n\n"

                        f"Thank you."
                    ),


                    from_email=settings.DEFAULT_FROM_EMAIL,


                    recipient_list=[
                        updated_application.candidate.email
                    ],


                    fail_silently=False,
                )


            return Response(
                ApplicationSerializer(
                    updated_application
                ).data,
                status=status.HTTP_200_OK
            )


        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


    # ==========================================================
    # DELETE - Delete Application
    # ==========================================================

    if request.method == "DELETE":

        # Candidate can delete own application
        # Recruiter can delete application for own job

        if (
            request.user != application.candidate
            and request.user != application.job.recruiter
        ):

            return Response(
                {
                    "error": (
                        "You do not have permission "
                        "to delete this application."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )


        application.delete()


        return Response(
            {
                "message": "Application deleted successfully."
            },
            status=status.HTTP_200_OK
        )