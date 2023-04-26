## How to add a new form to print and file

1) Update `forms_to_file` function in `edivorce/apps/core/utils/efiling_documents.py` 
to add a form to either initial or final filing; 
2) Update `form_types` mapping in `edivorce.apps.core.models.Document` model. 
3) If necessary add logic to re-map document types before submitting to the efiling hub. 
For that, update `_get_document` method in
`edivorce.apps.core.utils.efiling_packaging.EFilingPackaging`. - ***Optional***
4) Verify that the form definition exists in `vue/src/utils/forms.js` and add it if necessary;
Update unit tests in `edivorce/apps/core/tests/test_filing_documents.py` to 
check for the necessary form; 
5) Test submission with the efiling hub to ensure that it works;


## How to add a question to Questioner

These are general instructions on how to add a new question. The process may differ
depending on where the question needs to be added.

1. Add question text and metadata to `edivorce/fixtures/Question.json`, in the following format:
```json
    {
        "fields": {
            "name": "string",
            "description": "string",
            "summary_order": 0,
            "required": "Required/Conditional",
            "conditional_target": "string",
            "reveal_response": "YES/NO"
        },
        "model": "core.question",
        "pk": "string"
    }
```
`conditional_target` and `reveal_response` are only necessary for required questions.

2. Run Load questions from fixtures:

`python3.8 ./manage.py loaddata edivorce/fixtures/Question.json`

3. Add question key to the appropriate mapping in `edivorce/apps/core/utils/question_step_mapping.py`
4. Update templates with the question in `edivorce/apps/core/templates/prequalification`
5. Update appropriate tests in `edivorce/apps/core/tests/test_step_completeness.py`
   or `edivorce/apps/core/templates/question`
6. Other parts of the code may need to be updated depending on the business logic.
