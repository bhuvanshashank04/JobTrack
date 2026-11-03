from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
import json
from django.db.models import Count
from .forms import JobApplicationForm, InterviewForm
from .models import JobApplication, Interview
from django.utils import timezone
from datetime import timedelta


@login_required
def application_list(request):
    """
    Display the logged-in user's job applications.
    Supports searching, filtering, and pagination.
    """

    applications = JobApplication.objects.filter(
        user=request.user
    ).order_by("-applied_date", "-created_at")

    # Search by company, job title, or location.
    search_query = request.GET.get("q", "").strip()

    if search_query:
        applications = applications.filter(
            Q(company_name__icontains=search_query) |
            Q(job_title__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    # Filter by application status.
    selected_status = request.GET.get("status", "").strip()

    valid_statuses = {
        value for value, label
        in JobApplication._meta.get_field("status").choices
    }

    if selected_status in valid_statuses:
        applications = applications.filter(status=selected_status)

    # Pagination: 10 applications per page.
    paginator = Paginator(applications, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    status_choices = JobApplication._meta.get_field("status").choices

    context = {
        "applications": page_obj,
        "page_obj": page_obj,
        "search_query": search_query,
        "selected_status": selected_status,
        "status_choices": status_choices,
        "total_applications": paginator.count,
    }

    return render(
        request,
        "applications/application_list.html",
        context,
    )


@login_required
def application_create(request):
    """
    Add a new job application.
    """

    if request.method == "POST":
        form = JobApplicationForm(request.POST)

        if form.is_valid():
            application = form.save(commit=False)

            # Assign the application to the logged-in user.
            application.user = request.user

            application.save()

            messages.success(
                request,
                "Job application added successfully.",
            )

            return redirect("applications:application_list")

    else:
        form = JobApplicationForm()

    return render(
        request,
        "applications/application_form.html",
        {
            "form": form,
            "page_title": "Add Job Application",
            "button_text": "Save Application",
        },
    )


@login_required
def application_update(request, pk):
    """
    Update an application owned by the logged-in user.
    """

    application = get_object_or_404(
        JobApplication,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        form = JobApplicationForm(
            request.POST,
            instance=application,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Job application updated successfully.",
            )

            return redirect("applications:application_list")

    else:
        form = JobApplicationForm(instance=application)

    return render(
        request,
        "applications/application_form.html",
        {
            "form": form,
            "application": application,
            "page_title": "Edit Job Application",
            "button_text": "Update Application",
        },
    )
@login_required
def application_detail(request, pk):
    """
    Display the complete details of a job application
    owned by the logged-in user.
    """

    application = get_object_or_404(
        JobApplication,
        pk=pk,
        user=request.user,
    )

    context = {
        "application": application,
    }

    return render(
        request,
        "applications/application_detail.html",
        context,
    )

@login_required
def application_delete(request, pk):
    """
    Delete an application owned by the logged-in user.
    """

    application = get_object_or_404(
        JobApplication,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        application.delete()

        messages.success(
            request,
            "Job application deleted successfully.",
        )

        return redirect("applications:application_list")

    return render(
        request,
        "applications/application_confirm_delete.html",
        {
            "application": application,
        },
    )
@login_required
def dashboard(request):
    applications = JobApplication.objects.filter(
        user=request.user
    )

    # Count applications by status.
    status_counts = applications.values("status").annotate(
        total=Count("id")
    )

    status_counts_dict = {
        item["status"]: item["total"]
        for item in status_counts
    }

    total_applications = applications.count()

    interested_count = status_counts_dict.get(
        JobApplication.Status.INTERESTED, 0
    )
    applied_count = status_counts_dict.get(
        JobApplication.Status.APPLIED, 0
    )
    assessment_count = status_counts_dict.get(
        JobApplication.Status.ASSESSMENT, 0
    )
    interview_count = status_counts_dict.get(
        JobApplication.Status.INTERVIEW, 0
    )
    offers_count = status_counts_dict.get(
        JobApplication.Status.OFFER_RECEIVED, 0
    )
    rejected_count = status_counts_dict.get(
        JobApplication.Status.REJECTED, 0
    )
    withdrawn_count = status_counts_dict.get(
        JobApplication.Status.WITHDRAWN, 0
    )

    offer_rate = (
        round((offers_count / total_applications) * 100, 1)
        if total_applications > 0
        else 0
    )

    recent_applications = applications.order_by(
        "-created_at"
    )[:5]

    # Prepare chart labels and values.
    status_labels = [
        label
        for value, label in JobApplication._meta
        .get_field("status").choices
    ]

    status_values = [
        status_counts_dict.get(value, 0)
        for value, label in JobApplication._meta
        .get_field("status").choices
    ]

    # ---------------------------------
    # INTERVIEW DASHBOARD SECTION
    # ---------------------------------

    today = timezone.localdate()
    current_time = timezone.now()
    next_seven_days = today + timedelta(days=7)

    scheduled_interviews = Interview.objects.filter(
        application__user=request.user,
        status=Interview.Status.SCHEDULED,
    ).select_related("application")

    # Interviews scheduled for today.
    todays_interviews = scheduled_interviews.filter(
        scheduled_at__date=today,
        scheduled_at__gte=current_time,
    ).order_by("scheduled_at")  

    # Interviews scheduled within the next 7 days.
    upcoming_interviews = scheduled_interviews.filter(
        scheduled_at__date__gt=today,
        scheduled_at__date__lte=next_seven_days,
    ).order_by("scheduled_at")

    # Interviews whose scheduled time has passed.
    overdue_interviews = scheduled_interviews.filter(
        scheduled_at__lt=current_time
    ).order_by("scheduled_at")

    context = {
        "total_applications": total_applications,
        "interested_count": interested_count,
        "applied_count": applied_count,
        "assessment_count": assessment_count,
        "interview_count": interview_count,
        "offers_count": offers_count,
        "rejected_count": rejected_count,
        "withdrawn_count": withdrawn_count,
        "offer_rate": offer_rate,
        "recent_applications": recent_applications,

        # Chart data.
        "status_labels_json": json.dumps(status_labels),
        "status_values_json": json.dumps(status_values),

        # Interview data.
        "todays_interviews": todays_interviews,
        "upcoming_interviews": upcoming_interviews,
        "overdue_interviews": overdue_interviews,
    }

    return render(
        request,
        "applications/dashboard.html",
        context,
    )
# ------------------------------------------
# INTERVIEW MANAGEMENT
# ------------------------------------------

@login_required
def interview_list(request):
    today = timezone.localdate()
    current_time = timezone.now()
    next_seven_days = today + timedelta(days=7)

    # All interviews belonging to the logged-in user
    all_interviews = Interview.objects.filter(
        application__user=request.user
    ).select_related(
        "application"
    )

    # Define interview categories
    today_interviews = all_interviews.filter(
        status=Interview.Status.SCHEDULED,
        scheduled_at__date=today,
        scheduled_at__gte=current_time,
    )

    upcoming_interviews = all_interviews.filter(
        status=Interview.Status.SCHEDULED,
        scheduled_at__date__gt=today,
        scheduled_at__date__lte=next_seven_days,
    )

    overdue_interviews = all_interviews.filter(
        status=Interview.Status.SCHEDULED,
        scheduled_at__lt=current_time,
    )

    completed_interviews = all_interviews.filter(
        status=Interview.Status.COMPLETED
    )

    cancelled_interviews = all_interviews.filter(
        status=Interview.Status.CANCELLED
    )

    # Count interviews in each category
    interview_counts = {
        "all": all_interviews.count(),
        "today": today_interviews.count(),
        "upcoming": upcoming_interviews.count(),
        "overdue": overdue_interviews.count(),
        "completed": completed_interviews.count(),
        "cancelled": cancelled_interviews.count(),
    }

    # Read selected filter
    selected_period = request.GET.get("period", "all").strip().lower()

    # Apply selected filter
    filter_querysets = {
        "all": all_interviews,
        "today": today_interviews,
        "upcoming": upcoming_interviews,
        "overdue": overdue_interviews,
        "completed": completed_interviews,
        "cancelled": cancelled_interviews,
    }

    if selected_period not in filter_querysets:
        selected_period = "all"

    interviews = filter_querysets[selected_period].order_by(
        "scheduled_at"
    )

    context = {
        "interviews": interviews,
        "selected_period": selected_period,
        "interview_counts": interview_counts,
    }

    return render(
        request,
        "applications/interview_list.html",
        context
    )

@login_required
def interview_create(request):
    if request.method == "POST":
        form = InterviewForm(request.POST, user=request.user)

        if form.is_valid():
            interview = form.save()

            # Get the job application linked to this interview.
            application = interview.application

            # Automatically update the application status.
            protected_statuses = [
                JobApplication.Status.OFFER_RECEIVED,
                JobApplication.Status.REJECTED,
                JobApplication.Status.WITHDRAWN,
            ]

            if application.status not in protected_statuses:
                application.status = JobApplication.Status.INTERVIEW
                application.save(update_fields=["status", "updated_at"])

            messages.success(
                request,
                "Interview scheduled successfully. Application status updated."
            )
            return redirect("applications:interview_list")

    else:
        initial = {}

        # Check whether an application ID was passed in the URL.
        application_id = request.GET.get("application")

        if application_id:
            application = get_object_or_404(
                JobApplication,
                pk=application_id,
                user=request.user,
            )
            initial["application"] = application

        form = InterviewForm(
            user=request.user,
            initial=initial,
        )

    return render(request, "applications/interview_form.html", {
        "form": form,
        "button_text": "Schedule Interview",
    })

@login_required
def interview_update(request, pk):
    """Update an interview and synchronize its application status."""

    interview = get_object_or_404(
        Interview,
        pk=pk,
        application__user=request.user,
    )

    if request.method == "POST":
        form = InterviewForm(
            request.POST,
            instance=interview,
            user=request.user,
        )

        if form.is_valid():
            updated_interview = form.save()
            application = updated_interview.application

            protected_statuses = [
                JobApplication.Status.OFFER_RECEIVED,
                JobApplication.Status.REJECTED,
                JobApplication.Status.WITHDRAWN,
            ]

            if application.status not in protected_statuses:
                has_scheduled_interviews = application.interviews.filter(
                    status=Interview.Status.SCHEDULED
                ).exists()

                if has_scheduled_interviews:
                    application.status = JobApplication.Status.INTERVIEW
                else:
                    application.status = JobApplication.Status.APPLIED

                application.save(
                    update_fields=["status", "updated_at"]
                )

            messages.success(
                request,
                "Interview updated successfully.",
            )

            return redirect("applications:interview_list")

    else:
        form = InterviewForm(
            instance=interview,
            user=request.user,
        )

    return render(
        request,
        "applications/interview_form.html",
        {
            "form": form,
            "interview": interview,
            "page_title": "Edit Interview",
            "button_text": "Update Interview",
        },
    )


@login_required
def interview_delete(request, pk):
    """Delete an interview and synchronize the application status."""

    interview = get_object_or_404(
        Interview,
        pk=pk,
        application__user=request.user,
    )

    application = interview.application

    if request.method == "POST":
        interview.delete()

        protected_statuses = [
            JobApplication.Status.OFFER_RECEIVED,
            JobApplication.Status.REJECTED,
            JobApplication.Status.WITHDRAWN,
        ]

        if application.status not in protected_statuses:
            has_scheduled_interviews = application.interviews.filter(
                status=Interview.Status.SCHEDULED
            ).exists()

            if has_scheduled_interviews:
                application.status = JobApplication.Status.INTERVIEW
            else:
                application.status = JobApplication.Status.APPLIED

            application.save(
                update_fields=["status", "updated_at"]
            )

        messages.success(
            request,
            "Interview deleted successfully.",
        )

        return redirect("applications:interview_list")

    return render(
        request,
        "applications/interview_confirm_delete.html",
        {
            "interview": interview,
        },
    )