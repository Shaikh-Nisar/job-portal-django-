from django.urls import path
from . import api_views


urlpatterns = [

    path(
        "applications/",
        api_views.application_api_list,
        name="application_api_list"
    ),

    path(
        "applications/<int:application_id>/",
        api_views.application_api_detail,
        name="application_api_detail"
    ),

]