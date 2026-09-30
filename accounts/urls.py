from . import analytics_views
from django.urls import path
from . import views


urlpatterns = [
    # Register
    path(
        "register/",
        views.register,
        name="register"
    ),

    # Login
    path(
        "login/",
        views.user_login,
        name="login"
    ),

    # Logout
    path(
        "logout/",
        views.user_logout,
        name="logout"
    ),

    # Candidate Profile
    path(
        "profile/",
        views.profile,
        name="profile"
    ),

    # Recruiter Company Profile
    path(
        "company-profile/",
        views.company_profile,
        name="company_profile"
    ),

    # Candidate Dashboard
    path(
        "candidate/dashboard/",
        views.candidate_dashboard,
        name="candidate_dashboard"
    ),

    # Recruiter Dashboard
    path(
        "recruiter/dashboard/",
        views.recruiter_dashboard,
        name="recruiter_dashboard"
    ),

    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-users/", views.admin_users, name="admin_users"),

    path(
    "admin-users/toggle/<int:user_id>/",
    views.toggle_user_status,
    name="toggle_user_status",
    ),




    path(
    "admin-jobs/",
    views.admin_jobs,
    name="admin_jobs",
    ),


    path(
    "admin-applications/",
    views.admin_applications,
    name="admin_applications",
    ),


    path(
    "admin-reports/",
    views.admin_reports,
    name="admin_reports",
    ),




   path(
    "api/analytics/dashboard/",
    analytics_views.analytics_dashboard_api,
    name="analytics_dashboard_api",
    ),


    path(
    "admin-analytics/",
    views.admin_analytics_dashboard,
    name="admin_analytics_dashboard",
    ),



]