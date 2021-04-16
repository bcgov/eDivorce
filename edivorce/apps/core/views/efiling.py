import base64
import random
import re

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from ..decorators import prequal_completed
from ..models import Document, UserResponse
from ..utils.efiling_documents import forms_to_file
from ..utils.efiling_packaging import EFilingPackaging
from ..utils.efiling_submission import EFilingSubmission
from ..utils.user_response import get_data_for_user

MAX_MEGABYTES = 10


@login_required
@prequal_completed
def submit_initial_files(request):
    return _submit_files(request, initial=True)


@login_required
@prequal_completed
def submit_final_files(request):
    return _submit_files(request, initial=False)


def _submit_files(request, initial=False):
    """ App flow logic """
    responses_dict = get_data_for_user(request.user)

    errors, hub_redirect_url = _validate_and_submit_documents(
        request, responses_dict, initial=initial)

    if hub_redirect_url:
        return redirect(hub_redirect_url)

    if initial:
        original_step = 'initial_filing'
        next_page = 'wait_for_number'
    else:
        original_step = 'final_filing'
        next_page = 'next_steps'

    if errors:
        next_page = original_step
        if not isinstance(errors, list):
            errors = [errors]
        for error in errors:
            messages.add_message(request, messages.ERROR, error)

    responses_dict['active_page'] = next_page

    return redirect(reverse('dashboard_nav', kwargs={'nav_step': next_page}), context=responses_dict)


def _validate_and_submit_documents(request, responses, initial=False):
    """ Validation and submission logic """
    user = request.user
    errors = []
    if not initial:
        user_has_submitted_initial = responses.get('initial_filing_submitted') == 'True'
        if not user_has_submitted_initial:
            errors.append(
                "You must file the initial filing first before submitting the final filing.")
        court_file_number = responses.get('court_file_number')
        if not court_file_number:
            errors.append("You must input your Court File Number")
        elif not re.search("^[0-9]{4,10}$", court_file_number):
            errors.append("A Court File Number contains only digits and must be between 4 and 10 digits in length")

    uploaded, generated = forms_to_file(responses, initial)
    for form in uploaded:
        if form['doc_type'] not in ['EFSS1', 'AFTL']:
            total_size = 0
            docs = Document.objects.filter(
                bceid_user=user, doc_type=form['doc_type'], party_code=form.get('party_code', 0))
            if docs.count() == 0:
                errors.append(f"Missing documents for {Document.form_types[form['doc_type']]}")
            for doc in docs:
                total_size += doc.size
            if total_size > MAX_MEGABYTES * 1024 * 1024:
                errors.append(
                    f"{Document.form_types[form['doc_type']]} exceeds the { MAX_MEGABYTES } MB size limit")

    if errors:
        return errors, None

    if not settings.EFILING_HUB_ENABLED:
        redirect = _after_submit_files(request, initial)
        return None, redirect.url

    msg, redirect_url = _package_and_submit(request, uploaded, generated, responses, initial)

    if redirect_url:
        return None, redirect_url

    if msg != 'success':
        errors.append(msg)
        return errors, None

    return None, None


def _package_and_submit(request, uploaded, generated, responses, initial):
    """ Build the efiling package and submit it to the efiling hub """
    packaging = EFilingPackaging(initial)
    hub = EFilingSubmission(initial, packaging)
    post_files, documents = packaging.get_files(request, responses, uploaded, generated)
    redirect_url, msg = hub.upload(request, responses, post_files, documents)
    return msg, redirect_url


@login_required
@prequal_completed
def after_submit_initial_files(request):
    return _after_submit_files(request, initial=True)


@login_required
@prequal_completed
def after_submit_final_files(request):
    return _after_submit_files(request, initial=False)


def _after_submit_files(request, initial=False):
    responses_dict = get_data_for_user(request.user)
    if initial:
        next_page = 'wait_for_number'
    else:
        next_page = 'next_steps'

    user = request.user

    prefix = 'initial' if initial else 'final'
    _save_response(user, f'{prefix}_filing_submitted', 'True')

    if not initial:
        _save_response(user, 'final_filing_status', 'Submitted')

    package_number = _get_package_number(request)
    _save_response(user, f'{prefix}_filing_package_number', package_number)

    package_link = _get_package_link(request, package_number)
    _save_response(user, f'{prefix}_filing_package_link', package_link)

    # purge the attachments
    Document.objects.filter(
        bceid_user=user,
        filing_type=('i' if initial else 'f')
    ).delete()    

    responses_dict['active_page'] = next_page

    return redirect(reverse('dashboard_nav', kwargs={'nav_step': next_page}), context=responses_dict)


def _get_package_number(request):
    if settings.EFILING_HUB_ENABLED:
        return request.GET.get('packageNo', '')
            
    # Generate a random string in format 000-000-000
    package_number_parts = []
    for _ in range(3):
        num = ''
        for _ in range(3):
            num += str(random.randint(0, 9))
        package_number_parts.append(num)
    return '-'.join(package_number_parts)


def _get_package_link(request, package_number):
    if settings.EFILING_HUB_ENABLED:
        base64_message = request.GET.get('packageRef', '')
        base64_bytes = base64_message.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        link = message_bytes.decode('ascii')
        return link

    if settings.DEPLOYMENT_TYPE == 'localdev':
        base_url = 'https://dev.justice.gov.bc.ca'
    else:
        base_url = settings.PROXY_BASE_URL

    return base_url + '/cso/accounts/bceidNotification.do?packageNo=' + package_number


def _save_response(user, question, value):
    response, _ = UserResponse.objects.get_or_create(bceid_user=user, question_id=question)
    response.value = value
    response.save()
