import json
import logging
import requests

from django.conf import settings
from django.http import HttpResponse
from django.core.cache import cache
from django.core.exceptions import PermissionDenied

from .efiling_hub_caller_base import EFilingHubCallerBase

logger = logging.getLogger(__name__)


class EFilingCourtLocations(EFilingHubCallerBase):

    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        EFilingHubCallerBase.__init__(self)

    def _get_api(self, url, headers):
        # make sure we have an access token
        if not self.access_token:
            if not self._get_token():
                raise Exception('EFH - Unable to get API Token')

        headers = self._set_headers(headers)
        response = requests.get(url, headers=headers)
        logging.debug('EFH - Get Locations %d %s', response.status_code, response.text)

        if response.status_code == 401:
            # not authorized .. try refreshing token
            if self._refresh_token():
                headers = self._set_headers(headers)
                response = requests.get(url, headers=headers)
                logging.debug('EFH - Get Locations Retry %d %s', response.status_code, response.text)

        return response

    def courts(self, request):

        if cache.get('courts'):
            return cache.get('courts')

        url = f'{self.api_base_url}/courts?courtLevel=S'
        print('DEBUG: ' + url)

        if settings.EFILING_HUB_ENABLED:
            response = self._get_api(url, headers={})
        else:
            response = HttpResponse()
            response.status_code = 401

        if response.status_code == 200:
            cso_locations = json.loads(response.text)
            locations = {}

            for location in cso_locations['courts']:
                city = location['address']['cityName']
                locations[city] = {
                    'address_1': location['address']['addressLine1'],
                    'address_2': location['address']['addressLine2'],
                    'address_3': location['address']['addressLine3'],
                    'postal': location['address']['postalCode'],
                    'location_id': location['identifierCode']
                }

            cache.set('courts', locations)

            return locations

        if response.status_code == 401:
            if hasattr(response, 'headers'):
                print(response.headers.get('WWW-Authenticate', ''))
            return {
                "Authentication error calling court locations API": {},
                "Vancouver": {"address_1": "API Error", "postal": "APIERR", "location_id": "6011"}
            }

        print(str(response.status_code) + " - " + response.text)
        return {
            "Error calling court locations API": {},
            "Vancouver": {"address_1": "API Error", "postal": "APIERR", "location_id": "6011"}
        }
