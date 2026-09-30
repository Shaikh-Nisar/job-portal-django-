from django.urls import path
from . import views

urlpatterns = [
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),
    path("my-applications/", views.my_applications, name="my_applications"),
    path("job/<int:job_id>/applicants/", views.job_applicants, name="job_applicants"),

    path(
        "update-status/<int:application_id>/",
        views.update_application_status,
        name="update_application_status",
    ),
]