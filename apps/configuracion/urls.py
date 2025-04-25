from django.urls import path
from .views import ConfiguracionView
from .views_email import EmailConfigView, TestConnectionView


urlpatterns = [
    path('', ConfiguracionView.as_view(), name='configuracion'),
    path('<int:tenant_id>/', ConfiguracionView.as_view(), name='configuracion_tenant'),
    path('email/config/', EmailConfigView.as_view(), name='email_config'),
    path('email/config/<int:tenant_id>/', EmailConfigView.as_view(), name='email_config_tenant'),
    path('email/test-connection/', TestConnectionView.as_view(), name='test_email_connection'),
    path('email/test-connection/<int:tenant_id>/', TestConnectionView.as_view(), name='test_email_connection_tenant'),
]