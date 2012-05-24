from django.views.generic.base import TemplateView
from .models import DashboardReport


class Dashboard(TemplateView):
    slug = None
    per_user = False
    user_editable = False

    def get_context_data(self):
        return {}
