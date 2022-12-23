from django.conf import settings


def settings_processor(_request):
    """ Add settings data to context to make visible in debug toolbar """
    return {
        'gtm_id': settings.GTM_ID,
        'proxy_root_path': settings.SCRIPT_NAME,
        'deployment_environment': settings.ENVIRONMENT,
        'show_debug': settings.ENVIRONMENT in ['localdev', 'dev', 'test']
    }
