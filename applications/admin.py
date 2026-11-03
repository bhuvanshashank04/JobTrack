from django.contrib import admin

from .models import JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "job_title",
        "status",
        "user",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "company_name",
        "job_title",
        "location",
    )

    ordering = ("-created_at",)