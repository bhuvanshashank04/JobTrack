from django import forms
from .models import JobApplication,Interview


class JobApplicationForm(forms.ModelForm):

    class Meta:
        model = JobApplication

        fields = [
            "company_name",
            "job_title",
            "location",
            "job_url",
            "salary_min",
            "salary_max",
            "status",
            "applied_date",
            "description",
            "notes",
        ]

        widgets = {
            "company_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter company name",
            }),
            "job_title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter job title",
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter job location",
            }),
            "job_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://example.com/job",
            }),
            "salary_min": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Minimum salary",
                "step": "0.01",
            }),
            "salary_max": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Maximum salary",
                "step": "0.01",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
            "applied_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter job description",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Add your notes",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        salary_min = cleaned_data.get("salary_min")
        salary_max = cleaned_data.get("salary_max")

        if (
            salary_min is not None
            and salary_max is not None
            and salary_min > salary_max
        ):
            self.add_error(
                "salary_max",
                "Maximum salary cannot be less than minimum salary.",
            )

        return cleaned_data

class InterviewForm(forms.ModelForm):

    class Meta:
        model = Interview

        fields = [
            "application",
            "interview_type",
            "scheduled_at",
            "meeting_link",
            "interviewer_name",
            "status",
            "notes",
        ]

        widgets = {
            "application": forms.Select(
                attrs={"class": "form-select"}
            ),
            "scheduled_at": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "meeting_link": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com/meeting",
                }
            ),
            "interviewer_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter interviewer name",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Interview preparation notes...",
                }
            ),
            "interview_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["application"].queryset = (
                JobApplication.objects.filter(user=user)
            )
        else:
            self.fields["application"].queryset = (
                JobApplication.objects.none()
            )

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault(
                    "class", "form-select"
                )
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault(
                    "class", "form-control"
                )
            else:
                field.widget.attrs.setdefault(
                    "class", "form-control"
                )