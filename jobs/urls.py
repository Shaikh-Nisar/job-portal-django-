from django.urls import path
from . import views

urlpatterns = [
    path("", views.job_list, name="job_list"),
    path("create/", views.create_job, name="create_job"),
    path("my-jobs/", views.my_jobs, name="my_jobs"),
    path("saved/", views.saved_jobs, name="saved_jobs"),
    path("save/<int:job_id>/", views.save_job, name="save_job"),
    path("edit/<int:job_id>/", views.edit_job, name="edit_job"),
    path("delete/<int:job_id>/", views.delete_job, name="delete_job"),
    path("<int:job_id>/", views.job_detail, name="job_detail"),
]