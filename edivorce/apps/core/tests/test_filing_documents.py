from django.test import TestCase

from edivorce.apps.core.models import BceidUser, Document, UserResponse
from edivorce.apps.core.utils.efiling_documents import forms_to_file
from edivorce.apps.core.utils.user_response import get_data_for_user


class FilingLogic(TestCase):
    fixtures = ['Question.json']

    def setUp(self):
        self.user = BceidUser.objects.create(user_guid='1234')
        self.create_response('how_to_file', 'Online')

    def create_response(self, question, value):
        response, _ = UserResponse.objects.get_or_create(bceid_user=self.user, question_id=question)
        response.value = value
        response.save()

    @property
    def questions_dict(self):
        return get_data_for_user(self.user)

    def test_initial_forms_to_file_in_person(self):

        self.create_response('how_to_sign', 'Together')
        self.create_response('original_marriage_certificate', 'NO')

        # Base forms required
        uploaded, generated = forms_to_file(self.questions_dict, initial=True)

        self.assertEqual(len(uploaded), 5)
        self.assertIn({'doc_type': doc_type("joint divorce proceedings"), 'party_code': 0}, uploaded)
        self.assertIn({'doc_type': doc_type("party's certificate"), 'party_code': 1}, uploaded)
        self.assertIn({'doc_type': doc_type("party's certificate"), 'party_code': 2}, uploaded)        
        self.assertIn({'doc_type': doc_type("electronic filing statement for affidavit of no marriage certificate"), 'party_code': 0}, uploaded)
        self.assertIn({'doc_type': doc_type("affidavit of no marriage certificate"), 'party_code': 0}, uploaded)

        self.assertEqual(len(generated), 1)
        self.assertIn({'doc_type': doc_type("notice of joint family claim"), 'form_number': 1}, generated)

        # Marriage certificate and translation required
        self.create_response('original_marriage_certificate', 'YES')
        self.create_response('marriage_certificate_in_english', 'NO')
        self.create_response('marriage_certificate_translated_to_english', 'YES')
        uploaded, generated = forms_to_file(self.questions_dict, initial=True)
        self.assertEqual(len(uploaded), 6)
        self.assertIn({'doc_type': doc_type("affidavit of translation"), 'party_code': 0}, uploaded)
        self.assertIn({'doc_type': doc_type("electronic filing statement for translation"), 'party_code': 1}, uploaded)
        self.assertIn({'doc_type': doc_type("proof of marriage"), 'party_code': 0}, uploaded)
        self.assertIn({'doc_type': doc_type("joint divorce proceedings"), 'party_code': 0}, uploaded)


    def test_final_forms_to_file_in_person(self):
        self.create_response('how_to_sign', 'Together')
        self.create_response('signing_location', 'In-person')

        # No conditional forms
        self.create_response('children_of_marriage', 'NO')
        uploaded, generated = forms_to_file(self.questions_dict, initial=False)

        self.assertEqual(len(uploaded), 3)
        self.assertIn({'doc_type': doc_type("electronic filing statement for affidavits"), 'party_code': 1}, uploaded)
        self.assertNotIn({'doc_type': doc_type("electronic filing statement for affidavits"), 'party_code': 2}, uploaded)
        self.assertIn({'doc_type': doc_type("desk order divorce form"), 'party_code': 0}, uploaded)
        self.assertIn({'doc_type': doc_type("draft final order"), 'party_code': 0}, uploaded)

        self.assertEqual(len(generated), 2)
        self.assertIn({'doc_type': doc_type("requisition form"), 'form_number': 35}, generated)
        self.assertIn({'doc_type': doc_type("certificate of pleadings"), 'form_number': 36}, generated)

        # Conditional forms
        self.create_response('children_of_marriage', 'YES')
        self.create_response('has_children_under_19', 'YES')
        uploaded, generated = forms_to_file(self.questions_dict, initial=False)
        self.assertEqual(len(uploaded), 5)
        self.assertIn({'doc_type': doc_type("child support affidavit"), 'party_code': 0}, uploaded)
        self.assertIn({'doc_type': doc_type("agreement as to annual income"), 'party_code': 0}, uploaded)

        self.create_response('want_which_orders', '["Other orders"]')
        self.create_response('name_change_you', 'YES')
        uploaded, generated = forms_to_file(self.questions_dict, initial=False)
        self.assertEqual(len(uploaded), 6)
        self.assertIn({'doc_type': doc_type("identification of applicant"), 'party_code': 1}, uploaded)

        self.create_response('name_change_spouse', 'YES')
        uploaded, generated = forms_to_file(self.questions_dict, initial=False)
        self.assertEqual(len(uploaded), 7)
        self.assertIn({'doc_type': doc_type("identification of applicant"), 'party_code': 2}, uploaded)

        self.create_response('want_which_orders', '["Other orders","Spousal support"]')
        uploaded, generated = forms_to_file(self.questions_dict, initial=False)
        self.assertEqual(len(uploaded), 9)
        self.assertIn({'doc_type': doc_type("statement of information for corollary relief proceedings"), 'party_code': 1}, uploaded)
        self.assertIn({'doc_type': doc_type("statement of information for corollary relief proceedings"), 'party_code': 2}, uploaded)


def doc_type(text):
    for doc_type, name in Document.form_types.items():
        if text.lower() in name.lower():
            return doc_type
    raise ValueError(f"Couldn't find doc with name that contains '{text}'")
