import base64
import hashlib
from django.conf import settings
from django.utils.encoding import force_bytes, smart_text, smart_bytes
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.utils import absolutify


class EDivorceKeycloakBackend(OIDCAuthenticationBackend):

    def verify_claims(self, claims):
        verified = super(EDivorceKeycloakBackend, self).verify_claims(claims)
        print(claims)

        return verified

    def create_user(self, claims):
        email = claims.get('email')
        universal_id = claims.get('universal-id')
        username = base64.urlsafe_b64encode(
        hashlib.sha1(force_bytes(universal_id)).digest()
            ).rstrip(b'=')

        user = self.UserModel.objects.create_user(username, email=email)
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.display_name = "{} {}".format(user.first_name, user.last_name).strip()
        user.sm_user = claims.get('preferred_username', '')
        user.user_guid = claims.get('universal-id', '')
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


def keycloak_logout(request):
    request.session.flush()
    redirect_uri = absolutify(request, settings.FORCE_SCRIPT_NAME[:-1] + '/logout')
    return f'{settings.KEYCLOAK_LOGOUT}?redirect_uri={redirect_uri}'
