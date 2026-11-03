from django.conf import settings
from django.db import models


class JobApplication(models.Model):

    class Status(models.TextChoices):
        INTERESTED = "INTERESTED", "Interested"
        APPLIED = "APPLIED", "Applied"
        ASSESSMENT = "ASSESSMENT", "Assessment"
        INTERVIEW = "INTERVIEW", "Interview"
        OFFER_RECEIVED = "OFFER_RECEIVED", "Offer Received"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )

    company_name = models.CharField(max_length=200)

    job_title = models.CharField(max_length=200)

    location = models.CharField(
        max_length=200,
        blank=True,
    )

    job_url = models.URLField(
        blank=True,
    )

    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INTERESTED,
    )

    applied_date = models.DateField(
        null=True,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company_name} - {self.job_title}"

class Interview(models.Model):

    class InterviewType(models.TextChoices):
        HR = "HR", "HR Interview"
        TECHNICAL = "TECHNICAL", "Technical Interview"
        MANAGERIAL = "MANAGERIAL", "Managerial Interview"
        ASSESSMENT = "ASSESSMENT", "Assessment"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="interviews",
    )

    interview_type = models.CharField(
        max_length=20,
        choices=InterviewType.choices,
        default=InterviewType.TECHNICAL,
    )

    scheduled_at = models.DateTimeField()

    meeting_link = models.URLField(
        blank=True,
    )

    interviewer_name = models.CharField(
        max_length=200,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["scheduled_at"]

    def __str__(self):
        return (
            f"{self.application.company_name} - "
            f"{self.get_interview_type_display()} - "
            f"{self.scheduled_at:%d %b %Y %I:%M %p}"
        )