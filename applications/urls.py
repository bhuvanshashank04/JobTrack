from django.urls import path

from . import views


app_name = "applications"

urlpatterns = [
    path(
        "",
        views.application_list,
        name="application_list",
    ),

    path(
        "add/",
        views.application_create,
        name="application_create",
    ),

    path(
        "<int:pk>/edit/",
        views.application_update,
        name="application_update",
    ),

    path(
        "<int:pk>/delete/",
        views.application_delete,
        name="application_delete",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
            "<int:pk>/",
            views.application_detail,
            name="application_detail",
        ),
        path(
            "interviews/",
            views.interview_list,
            name="interview_list",
        ),
        path(
            "interviews/add/",
            views.interview_create,
            name="interview_create",
        ),
        path(
            "interviews/<int:pk>/edit/",
            views.interview_update,
            name="interview_update",
        ),
        path(
            "interviews/<int:pk>/delete/",
            views.interview_delete,
            name="interview_delete",
        ),
]