from django.urls import path
from .views import ConfiguracionView

urlpatterns = [
    path('', ConfiguracionView.as_view(), name='configuracion'),
    path('<int:tenant_id>/', ConfiguracionView.as_view(), name='configuracion_tenant'),
]