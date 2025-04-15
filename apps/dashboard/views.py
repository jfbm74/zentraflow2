# In a file like apps/dashboard/views.py or apps/core/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'  # You'll need to create this template
    login_url = '/auth/login/'  # Redirect to login if user isn't authenticated