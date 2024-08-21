import os
import sys

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Checks links in the eDivorce application.'

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }

    def _check_link(self, session, address):
        try:
            print(f'Checking link: {address}')
            response = session.get(address, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return str(e)
        return None

    def handle(self, *args, **options):
        session = requests.Session()
        links_to_check = {}
        errors = []

        for root, _, files in os.walk(os.path.join(settings.BASE_DIR, 'apps/core/templates/')):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    print(f'Parsing: {file_path}')

                    with open(file_path, 'r') as fs:
                        soup = BeautifulSoup(fs, 'html.parser')
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if href.startswith('http') and 'localhost' not in href:
                                links_to_check.setdefault(href, {'href': href, 'filename': []})['filename'].append(file_path)

        for link_info in links_to_check.values():
            status = self._check_link(session, link_info['href'])
            if status:
                errors.append({'link': link_info['href'], 'error': status, 'file': link_info['filename']})

        if errors:
            print('\nErrors found:\n')
            for error in errors:
                print('-------------------------------------------------------------')
                print(f"File: {', '.join(error['file'])}")
                print(f"Link: {error['link']}")
                print(f"Error: {error['error']}")
            sys.exit(1)
