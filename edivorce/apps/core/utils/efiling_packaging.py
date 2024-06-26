import copy
import datetime
import hashlib
import json
import logging
import re

from django.conf import settings
from django.urls import reverse

from ..models import Document
from ..views.pdf import images_to_pdf, pdf_form
from .efiling_court_locations import EFilingCourtLocations

logger = logging.getLogger(__name__)

PACKAGE_DOCUMENT_FORMAT = {
    "name": "string",
    "type": "AFDO",
    "isAmendment": "false",
    "isSupremeCourtScheduling": "false",
    "data": {},
    "md5": "string"
}

PACKAGE_PARTY_FORMAT = {
    "partyType": "IND",
    "roleType": "CLA1",
    "firstName": "FirstName",
    "middleName": "",
    "lastName": "LastName",
}

PACKAGE_FORMAT = {
    "clientAppName": "Online Divorce Assistant",
    "filingPackage": {
        "documents": [],
        "court": {
            "location": "4801",
            "level": "S",
            "courtClass": "E",
            "division": "I",
            "fileNumber": None
        },
        "parties": []
    },
    "navigationUrls": {
        "success": "string",
        "error": "string",
        "cancel": "string"
    }
}

NJF_ALIAS_FORMAT = {
    "nameType": "AKA",
    "surname": "",
    "given1": "",
    "given2": "",
    "given3": ""
}

NJF_JSON_FORMAT = {
    "parties": [
        {
            "label": "Claimant 1",
            "surname": "",
            "given1": "",
            "given2": "",
            "given3": "",
            "birthDate": "",
            "email": "",
            "aliases": [],
            "surnameAtBirth": "",
            "surnameBeforeMarriage": "",
            "signingVirtually": False
        },
        {
            "label": "Claimant 2",
            "surname": "",
            "given1": "",
            "given2": "",
            "given3": "",
            "birthDate": "",
            "email": "",
            "aliases": [],
            "surnameAtBirth": "",
            "surnameBeforeMarriage": "",
            "signingVirtually": False
        }
    ],
    "placeOfMarriage": {
        "country": "",
        "province": "",
        "city": ""
    },
    "dateOfMarriage": "",
    "reasonForDivorce": "S",
    "childSupportAct": [],
    "spouseSupportAct": "",
    "ordersSought": []
}


class EFilingPackaging:

    def __init__(self, initial_filing):
        self.initial_filing = initial_filing

    def format_package(self, request, responses, documents):
        package = copy.deepcopy(PACKAGE_FORMAT)
        package['filingPackage']['documents'] = documents
        package['filingPackage']['court']['location'] = self._get_location(request, responses)
        package['filingPackage']['parties'] = self._get_parties(responses)
        file_number = self._get_file_number(responses)
        if file_number:
            package['filingPackage']['court']['fileNumber'] = file_number
        # update return urls
        if self.initial_filing:
            package['navigationUrls']['error'] = self._get_absolute_url(
                request, reverse('dashboard_nav', args=['initial_filing']))
            package['navigationUrls']['cancel'] = self._get_absolute_url(
                request, reverse('dashboard_nav', args=['initial_filing'])) + '?cancelled=1'
            package['navigationUrls']['success'] = self._get_absolute_url(
                request, reverse('after_submit_initial_files'))
        else:
            package['navigationUrls']['error'] = self._get_absolute_url(
                request, reverse('dashboard_nav', args=['final_filing']))
            package['navigationUrls']['cancel'] = self._get_absolute_url(
                request, reverse('dashboard_nav', args=['final_filing'])) + '?cancelled=1'
            package['navigationUrls']['success'] = self._get_absolute_url(
                request, reverse('after_submit_final_files'))

        return package

    def _get_document(self, doc_type, party_code):
        document = copy.deepcopy(PACKAGE_DOCUMENT_FORMAT)
        filename = self._get_filename(doc_type, party_code)
        document['name'] = filename
        if doc_type in ['EFSS0', 'EFSS1', 'EFSS2']:
            document['type'] = 'EFSS'
        else:
            document['type'] = doc_type
        return document

    def _get_filename(self, doc_type, party_code):
        form_name = Document.form_types[doc_type]
        slug = re.sub('[^0-9a-zA-Z]+', '-', form_name).strip('-')
        if party_code == 0:
            return slug + ".pdf"
        if party_code == 1:
            return slug + "--Claimant1.pdf"
        return slug + "--Claimant2.pdf"

    def _format_date(self, s):
        try:
            return datetime.datetime.strptime(s, '%b %d, %Y').strftime('%Y-%m-%d')
        except Exception:
            return ''

    def _get_aliases(self, s):
        aliases = []
        names = json.loads(s)
        for name in names:
            if len(name) == 5 and name[1] != '' and name[2] != '':
                alias = copy.deepcopy(NJF_ALIAS_FORMAT)
                alias["surname"] = name[1]
                alias["given1"] = name[2]
                alias["given2"] = name[3]
                alias["given3"] = name[4]
                aliases.append(alias)
        return aliases

    def _get_json_data(self, responses):

        r = responses
        d = copy.deepcopy(NJF_JSON_FORMAT)

        signing_location_you = ''
        signing_location_spouse = ''

        if r.get('how_to_sign') == 'Together':
            signing_location_you = r.get('signing_location')
            signing_location_spouse = r.get('signing_location')
        elif r.get('how_to_sign') == 'Separately':
            signing_location_you = r.get('signing_location_you')
            signing_location_spouse = r.get('signing_location_spouse')

        party1 = d["parties"][0]
        party1["surname"] = r.get('last_name_you', '')
        party1["given1"] = r.get('given_name_1_you', '')
        party1["given2"] = r.get('given_name_2_you', '')
        party1["given3"] = r.get('given_name_3_you', '')
        party1["birthDate"] = self._format_date(r.get('birthday_you'))
        party1["surnameAtBirth"] = r.get('last_name_born_you', '')
        party1["surnameBeforeMarriage"] = r.get('last_name_before_married_you', '')
        email = r.get('email_you', '')
        if not email:
            email = r.get('address_to_send_official_document_email_you', '')
        party1["email"] = email
        party1["signingVirtually"] = signing_location_you == 'Virtual'
        if r.get('any_other_name_you') == 'YES':
            party1["aliases"] = self._get_aliases(r.get('other_name_you'))

        party2 = d["parties"][1]
        party2["surname"] = r.get('last_name_spouse', '')
        party2["given1"] = r.get('given_name_1_spouse', '')
        party2["given2"] = r.get('given_name_2_spouse', '')
        party2["given3"] = r.get('given_name_3_spouse', '')
        party2["birthDate"] = self._format_date(r.get('birthday_spouse'))
        party2["surnameAtBirth"] = r.get('last_name_born_spouse', '')
        party2["surnameBeforeMarriage"] = r.get('last_name_before_married_spouse', '')
        email = r.get('email_spouse', '')
        if not email:
            email = r.get('address_to_send_official_document_email_spouse', '')
        party2["email"] = email
        party2["signingVirtually"] = signing_location_spouse == 'Virtual'
        if r.get('any_other_name_spouse') == 'YES':
            party2["aliases"] = self._get_aliases(r.get('other_name_spouse'))

        d["dateOfMarriage"] = self._format_date(r.get('when_were_you_married'))
        d["placeOfMarriage"]["country"] = r.get('where_were_you_married_country', '')
        d["placeOfMarriage"]["province"] = r.get('where_were_you_married_prov', '')
        d["placeOfMarriage"]["city"] = r.get('where_were_you_married_city', '')

        d["childSupportAct"] = json.loads(r.get('child_support_act', '[]'))
        d["spouseSupportAct"] = r.get('spouse_support_act', '')

        orders_sought = json.loads(r.get('want_which_orders', '[]'))

        if 'A legal end to the marriage' in orders_sought:
            d["ordersSought"].append('DIV')

        if 'Spousal support' in orders_sought:
            d["ordersSought"].append('SSU')

        if 'Division of property and debts' in orders_sought:
            division = r.get('deal_with_property_debt', '')
            if division == 'Equal division':
                d["ordersSought"].append('DFA')
            if division == 'Unequal division':
                d["ordersSought"].append('RFA')
            if re.sub(r'\W+', '', r.get('other_property_claims', '')) != '':
                d["ordersSought"].append('PRO')

        if 'Child support' in orders_sought:
            d["ordersSought"].append('CSU')

        if 'Other orders' in orders_sought:
            if r.get('name_change_you') == 'YES' or r.get('name_change_spouse') == 'YES':
                d["ordersSought"].append('NAM')
            if re.sub(r'\W+', '', r.get('other_orders_detail ', '')) != '':
                d["ordersSought"].append('OTH')

        return d

    def _get_absolute_url(self, request, path):
        if settings.PROXY_BASE_URL:
            return settings.PROXY_BASE_URL + path
        return request.build_absolute_uri(path)

    # -- EFILING HUB INTERFACE --
    def get_files(self, request, responses, uploaded, generated):

        post_files = []
        documents = []

        for form in generated:
            doc_type = form['doc_type']
            document = self._get_document(doc_type, 0)
            if doc_type == 'NJF':
                document['data'] = self._get_json_data(responses)
            pdf_response = pdf_form(request, str(form['form_number']))
            document['md5'] = hashlib.md5(pdf_response.content).hexdigest()  # nosec
            post_files.append(('files', (document['name'], pdf_response.content)))
            documents.append(document)

        for form in uploaded:
            party_code = form['party_code']
            doc_type = form['doc_type']
            pdf_response = images_to_pdf(request, doc_type, party_code)
            if pdf_response.status_code == 200:
                document = self._get_document(doc_type, party_code)
                document['md5'] = hashlib.md5(pdf_response.content).hexdigest()  # nosec
                post_files.append(('files', (document['name'], pdf_response.content)))
                documents.append(document)

        return post_files, documents

    def _get_parties(self, responses):

        # generate the list of parties to send to eFiling Hub
        parties = []

        party1 = copy.deepcopy(PACKAGE_PARTY_FORMAT)
        party1['roleType'] = "CLA1"
        party1['firstName'] = responses.get('given_name_1_you', '')
        party1['middleName'] = (responses.get('given_name_2_you', '') +
                                ' ' +
                                responses.get('given_name_3_you', '')).strip()
        party1['lastName'] = responses.get('last_name_you', '')
        parties.append(party1)

        party2 = copy.deepcopy(PACKAGE_PARTY_FORMAT)
        party2['roleType'] = "CLA2"
        party2['firstName'] = responses.get('given_name_1_spouse', '')
        party2['middleName'] = (responses.get('given_name_2_spouse', '') +
                                ' ' +
                                responses.get('given_name_3_spouse', '')).strip()
        party2['lastName'] = responses.get('last_name_spouse', '')
        parties.append(party2)

        return parties

    def _get_location(self, request, responses):
        location_name = responses.get('court_registry_for_filing', '')
        court_locations = EFilingCourtLocations().courts(request)
        return court_locations.get(location_name,
                                   {'location_id': '0000'}).get('location_id')

    def _get_file_number(self, responses):
        if not self.initial_filing:
            return responses.get('court_file_number', '')
        return ''
