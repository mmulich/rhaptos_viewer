# -*- coding: utf-8 -*-
import urllib
from urlparse import urlparse
from opensearch import Client as OpenSearchClient
from pyramid.view import view_config


REPO_HOST = 'cnx.org'
REPO_PORT = 80
OPENSEARCH_URL = 'http://%s:%s/opensearchdescription' % (REPO_HOST, REPO_PORT)
SITE_TITLE = 'Connexions Web Viewer'

def _fix_url(url):
    """Fix a URL to put to this webview rather than the repository."""
    parts = urlparse(url)
    path = parts.path.split('/')
    if path[1] != 'content':
        return url
    id, version = path[:4][-2:]
    path = ['', 'content', '%s@%s' % (id, version)]
    return '/'.join(path)

@view_config(route_name='casa', renderer='casa.jinja2')
def casa(request):
    """The home page for this application."""
    return {'title': SITE_TITLE}

@view_config(route_name='search', renderer='search.jinja2')
def search(request):
    """Search the repository for the given terms."""
    client = OpenSearchClient(OPENSEARCH_URL)
    terms = urllib.unquote(request.params.get('q', '')).decode('utf8')
    results = client.search(terms)
    records = []
    for result in results:
        records.append({'title': result.title,
                        'link': _fix_url(result.link),
                        'summary': result.summary_detail['value'],
                        })
    return {'records': records,
            'q': terms,
            }
