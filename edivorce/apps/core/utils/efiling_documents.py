from edivorce.apps.core.utils.derived import get_derived_data


def forms_to_file(responses_dict, initial=False):
    generated = []
    uploaded = []

    how_to_file = responses_dict.get('how_to_file')
    how_to_sign = responses_dict.get('how_to_sign')

    derived = responses_dict.get('derived', get_derived_data(responses_dict))

    name_change_you = derived['wants_other_orders'] and responses_dict.get('name_change_you') == 'YES'
    name_change_spouse = derived['wants_other_orders'] and responses_dict.get('name_change_spouse') == 'YES'
    has_children = derived['has_children_of_marriage']
    f102_required = derived['f102_required']

    provide_marriage_certificate = responses_dict.get('original_marriage_certificate') == 'YES'
    provide_certificate_later = responses_dict.get('provide_certificate_later') == 'YES'

    if initial:
        generated.append({'doc_type': 'NJF', 'form_number': 1})
        uploaded.append({'doc_type': 'PCER', 'party_code': 1})
        uploaded.append({'doc_type': 'PCER', 'party_code': 2})

        if provide_marriage_certificate:
            uploaded.append({'doc_type': 'MC', 'party_code': 0})

        elif not provide_certificate_later:
            uploaded.append({'doc_type': 'AFF', 'party_code': 0})
            uploaded.append({'doc_type': 'EFSS0', 'party_code': 0})

        if responses_dict.get('marriage_certificate_in_english') == 'NO':
            uploaded.append({'doc_type': 'AFTL', 'party_code': 0})
            uploaded.append({'doc_type': 'EFSS1', 'party_code': 1})

        uploaded.append({'doc_type': 'RDP', 'party_code': 0})

    else:  # Final Filing

        generated.append({'doc_type': 'RFO', 'form_number': 35})
        generated.append({'doc_type': 'RCP', 'form_number': 36})

        if how_to_sign == 'Together':
            if has_children:
                uploaded.append({'doc_type': 'CSA', 'party_code': 0})
            uploaded.append({'doc_type': 'AFDO', 'party_code': 0})
        else:
            if has_children:
                uploaded.append({'doc_type': 'CSA', 'party_code': 1})
                uploaded.append({'doc_type': 'CSA', 'party_code': 2})
            uploaded.append({'doc_type': 'AFDO', 'party_code': 1})
            uploaded.append({'doc_type': 'AFDO', 'party_code': 2})

        uploaded.append({'doc_type': 'OFI', 'party_code': 0})

        if f102_required:
            uploaded.append({'doc_type': 'SICR', 'party_code': 1})
            uploaded.append({'doc_type': 'SICR', 'party_code': 2})

        uploaded.append({'doc_type': 'EFSS2', 'party_code': 1})

        if how_to_sign == 'Separately':
            uploaded.append({'doc_type': 'EFSS2', 'party_code': 2})

        if has_children:
            uploaded.append({'doc_type': 'AAI', 'party_code': 0})
        if name_change_you:
            uploaded.append({'doc_type': 'NCV', 'party_code': 1})
        if name_change_spouse:
            uploaded.append({'doc_type': 'NCV', 'party_code': 2})

    return uploaded, generated
