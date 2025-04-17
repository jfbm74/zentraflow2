from django.urls import path
from .views import ConfiguracionView
from .views_oauth import oauth_authorize, oauth_callback, OAuthStatusView, OAuthRevokeView, OAuthSettingsView


urlpatterns = [
    path('', ConfiguracionView.as_view(), name='configuracion'),
    path('<int:tenant_id>/', ConfiguracionView.as_view(), name='configuracion_tenant'),

    # URLs para OAuth
    path('oauth/authorize/', oauth_authorize, name='oauth_authorize'),
    path('oauth/callback/', oauth_callback, name='oauth_callback'),
    path('oauth/status/', OAuthStatusView.as_view(), name='oauth_status'),
    path('oauth/status/<int:tenant_id>/', OAuthStatusView.as_view(), name='oauth_status_tenant'),
    path('oauth/revoke/', OAuthRevokeView.as_view(), name='oauth_revoke'),
    path('oauth/revoke/<int:tenant_id>/', OAuthRevokeView.as_view(), name='oauth_revoke_tenant'),
    path('oauth/settings/', OAuthSettingsView.as_view(), name='oauth_settings'),
    path('oauth/settings/<int:tenant_id>/', OAuthSettingsView.as_view(), name='oauth_settings_tenant'),

]