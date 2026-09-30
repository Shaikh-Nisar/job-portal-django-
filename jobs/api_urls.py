from django.urls import path

from . import api_views


urlpatterns = [
    path(
        "jobs/",
        api_views.job_api_list,
        name="job_api_list"
    ),

    path(
        "jobs/<int:job_id>/",
        api_views.job_api_detail,
        name="job_api_detail"
    ),

    path(
        "saved-jobs/",
        api_views.saved_job_api_list,
        name="saved_job_api_list"
    ),

    path(
        "saved-jobs/<int:saved_job_id>/",
        api_views.saved_job_api_detail,
        name="saved_job_api_detail"
    ),
]