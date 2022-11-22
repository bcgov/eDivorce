from django.conf import settings
from django.urls import include, path, re_path
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt

from .apps.core.views import main
from .apps.core.views.graphql import PrivateGraphQLView, graphql_schema

urlpatterns = []

if settings.ENVIRONMENT in ['localdev', 'dev', 'test']:
    import debug_toolbar
    urlpatterns.append(re_path(r'^__debug__/', include(debug_toolbar.urls)),)
    urlpatterns.append(path('api/graphql/', csrf_exempt(PrivateGraphQLView.as_view(graphiql=True, schema=graphql_schema)), name='graphql'))
else:
    urlpatterns.append(path('api/graphql/', csrf_exempt(PrivateGraphQLView.as_view(graphiql=False, schema=graphql_schema)), name='graphql'))

if settings.ENVIRONMENT == 'localdev':
    urlpatterns.append(re_path(r'^admin/', admin.site.urls))
    urlpatterns.append(path('404/', main.page_not_found, {'exception': Exception()}))
    urlpatterns.append(path('500/', main.server_error))

urlpatterns.append(re_path(r'^oidc/', include('mozilla_django_oidc.urls')))

urlpatterns.append(re_path(r'^', include('edivorce.apps.core.urls')))

handler404 = main.page_not_found
handler500 = main.server_error
