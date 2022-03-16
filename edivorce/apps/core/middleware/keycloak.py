from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from mozilla_django_oidc import views
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.utils import absolutify, add_state_and_nonce_to_session
from urllib.parse import urlencode


class EDivorceKeycloakBackend(OIDCAuthenticationBackend):

    def verify_claims(self, claims):
        print(claims)        
        return 'universal-id' in claims

    def create_user(self, claims):
        email = claims.get('email', '')
        user_guid = claims.get('universal-id')
        user = self.UserModel.objects.create_user(username=user_guid, email=email, user_guid=user_guid)
        user.first_name = claims.get('given_name', '')[0:30]
        user.last_name = claims.get('family_name', '')
        user.display_name = "{} {}".format(user.first_name, user.last_name).strip()
        user.sm_user = claims.get('preferred_username', '')
        roles = claims.get('roles', {})
        user.has_efiling_early_access = 'efiling_early_access' in roles

        user.save()

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.display_name = "{} {}".format(user.first_name, user.last_name).strip()
        user.sm_user = claims.get('preferred_username', '')
        user.user_guid = claims.get('universal-id', '')
        roles = claims.get('roles', {})
        user.has_efiling_early_access = 'efiling_early_access' in roles

        user.save()

        return user

    def filter_users_by_claims(self, claims):
        user_guid = claims.get('universal-id')
        if not user_guid:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(user_guid=user_guid)


class EDivorceKeycloakRequestView(views.OIDCAuthenticationRequestView):

    def get(self, request):
        """OIDC client authentication initialization HTTP endpoint"""
        state = get_random_string(self.get_settings('OIDC_STATE_SIZE', 32))
        redirect_field_name = self.get_settings('OIDC_REDIRECT_FIELD_NAME', 'next')
        reverse_url = self.get_settings('OIDC_AUTHENTICATION_CALLBACK_URL',
                                        'oidc_authentication_callback')

        params = {
            'response_type': 'code',
            'scope': self.get_settings('OIDC_RP_SCOPES', 'openid email'),
            'client_id': self.OIDC_RP_CLIENT_ID,
            'redirect_uri': absolutify(
                request,
                reverse(reverse_url)
            ),
            'state': state,
        }

        params.update(self.get_extra_params(request))

        if self.get_settings('OIDC_USE_NONCE', True):
            nonce = get_random_string(self.get_settings('OIDC_NONCE_SIZE', 32))
            params.update({
                'nonce': nonce
            })

        # begin patch to allow kc_idp_hint to be passed in the querystring
        kc_idp_hint = request.GET.get('kc_idp_hint', '')
        if kc_idp_hint:
            params.update({"kc_idp_hint": kc_idp_hint})
        else:
            return redirect(reverse('home'))
        # end patch

        add_state_and_nonce_to_session(request, state, params)

        request.session['oidc_login_next'] = views.get_next_url(request, redirect_field_name)

        query = urlencode(params)
        redirect_url = '{url}?{query}'.format(url=self.OIDC_OP_AUTH_ENDPOINT, query=query)
        return HttpResponseRedirect(redirect_url)


def keycloak_logout(request):
    request.session.flush()
    redirect_uri = absolutify(request, settings.FORCE_SCRIPT_NAME[:-1] + '/logout')
    return f'{settings.KEYCLOAK_LOGOUT}?redirect_uri={redirect_uri}'
