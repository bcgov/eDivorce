import json

from django.test import TestCase

from edivorce.apps.core.models import BceidUser, UserResponse
from edivorce.apps.core.utils.conditional_logic import get_cleaned_response_value, get_num_children_living_with
from edivorce.apps.core.utils.user_response import get_data_for_user
from edivorce.apps.core.models import Document


class ConditionalLogicTestCase(TestCase):
    fixtures = ['Question.json']

    def setUp(self):
        self.user = BceidUser.objects.create(user_guid='1234')
        self.child_live_with_you = {"child_name": "Child with you", "child_birth_date": "Dec 30, 2018", "child_live_with": "Lives with you", "child_relationship_to_you": "Natural child", "child_relationship_to_spouse": "Natural child", "child_live_with_other_details": ""}
        self.child_live_with_spouse = {"child_name": "Child with spouse", "child_birth_date": "Jan 4, 2009", "child_live_with": "Lives with spouse", "child_relationship_to_you": "Adopted child", "child_relationship_to_spouse": "Adopted child", "child_live_with_other_details": ""}
        self.child_live_with_both = {"child_name": "Child with both", "child_birth_date": "Jan 4, 2009", "child_live_with": "Lives with both", "child_relationship_to_you": "Adopted child", "child_relationship_to_spouse": "Adopted child", "child_live_with_other_details": ""}

    def create_response(self, question, value):
        response, _ = UserResponse.objects.get_or_create(bceid_user=self.user, question_id=question)
        response.value = value
        response.save()

    @property
    def questions_dict(self):
        return get_data_for_user(self.user)

    def test_get_cleaned_response_no_value(self):
        self.assertIsNone(get_cleaned_response_value(None))
        self.assertIsNone(get_cleaned_response_value(''))
        self.assertIsNone(get_cleaned_response_value('  '))
        self.assertIsNone(get_cleaned_response_value('[]'))
        self.assertIsNone(get_cleaned_response_value('[["","  "]]'))
        self.assertIsNone(get_cleaned_response_value('[["also known as",""]]'))
        self.assertIsNone(get_cleaned_response_value('[["also known as",""],["also known as",""]]'))

    def test_get_cleaned_response_with_value(self):
        self.assertIsNotNone(get_cleaned_response_value('0'))
        self.assertIsNotNone(get_cleaned_response_value('["hi"]'))
        self.assertIsNotNone(get_cleaned_response_value('[["also known as","a"]]'))

    def test_num_children(self):
        self.assertEqual(get_num_children_living_with(self.questions_dict, 'Lives with you'), '0')
        self.assertEqual(get_num_children_living_with(self.questions_dict, 'Lives with spouse'), '0')
        self.assertEqual(get_num_children_living_with(self.questions_dict, 'Lives with both'), '0')

        children = [self.child_live_with_you, self.child_live_with_spouse, self.child_live_with_spouse,
                    self.child_live_with_both, self.child_live_with_both, self.child_live_with_both]
        self.create_response('claimant_children', json.dumps(children))

        self.assertEqual(get_num_children_living_with(self.questions_dict, 'Lives with you'), '1')
        self.assertEqual(get_num_children_living_with(self.questions_dict, 'Lives with spouse'), '2')
        self.assertEqual(get_num_children_living_with(self.questions_dict, 'Lives with both'), '3')


class ViewLogic(TestCase):
    def test_content_type_from_filename(self):
        self.assertEqual(Document.content_type_from_filename('test_file1.pdf'), 'application/pdf')
        self.assertEqual(Document.content_type_from_filename('redis_key_test_file1_pdf'), 'application/pdf')
        self.assertEqual(Document.content_type_from_filename('test_file2.png'), 'image/png')
        self.assertEqual(Document.content_type_from_filename('redis_key_test_file2_png'), 'image/png')
        self.assertEqual(Document.content_type_from_filename('Test File 3.GIF'), 'image/gif')
        self.assertEqual(Document.content_type_from_filename('redis_key_test_file_3_GIF'), 'image/gif')
        self.assertEqual(Document.content_type_from_filename('Test_File--4.JPEG'), 'image/jpeg')
        self.assertEqual(Document.content_type_from_filename('redis_key_test_file_4_jpeg'), 'image/jpeg')
        self.assertEqual(Document.content_type_from_filename('TestFile5.jpe'), 'image/jpeg')
        self.assertEqual(Document.content_type_from_filename('redis_key_test_file_5_jpe'), 'image/jpeg')
        self.assertEqual(Document.content_type_from_filename('testFile6.jpeg'), 'image/jpeg')
        self.assertEqual(Document.content_type_from_filename('redis_key_testfile_6_jpeg'), 'image/jpeg')
        self.assertEqual(Document.content_type_from_filename('test_file7.HEIC'), 'application/unknown')
        self.assertEqual(Document.content_type_from_filename('redis_key_testfile_7_svgg'), 'application/unknown')
