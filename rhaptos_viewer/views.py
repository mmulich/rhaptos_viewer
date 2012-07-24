# -*- coding: utf-8 -*-
import urllib
import urllib2
from urlparse import urljoin, urlparse
from opensearch import Client as OpenSearchClient
from BeautifulSoup import BeautifulSoup
from pyramid.view import view_config


REPO_HOST = 'cnx.org'
REPO_PORT = 80
OPENSEARCH_URL = 'http://%s:%s/opensearchdescription' % (REPO_HOST, REPO_PORT)
SITE_TITLE = 'Connexions Web Viewer'
NAME_DIV_CHAR = '@'

def _fix_url(url):
    """Fix a URL to put to this webview rather than the repository."""
    parts = urlparse(url)
    path = parts.path.split('/')
    if path[1] != 'content':
        return url
    id, version = path[:4][-2:]
    path = ['', 'module', '%s@%s' % (id, version)]
    return '/'.join(path)

def _split_name(name):
    """Split an name (e.g. 'col123@1.4') into an id and version.
    """
    if len(name.split(NAME_DIV_CHAR)) <= 1:
        id = name
        version = 'latest'
    else:
        id, version = name.split(NAME_DIV_CHAR)
    return id, version

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

@view_config(route_name='module', renderer='module.jinja2')
def module(request):
    """A view for displaying a CNX module."""
    module_id = request.matchdict['id']
    module_version = 'latest'
    if '@' in module_id:
        module_id, module_version = module_id.split('@')
    title, content = _process_module(module_id, module_version)
    return {'title': SITE_TITLE,
            'module_title': title,
            'module_body': str(content),
            }

def _process_module(id, version='latest'):
    # Request the content from the repository.
    url = 'http://%s:%s/content/%s/%s/' % (REPO_HOST, REPO_PORT, id, version)
    title = urllib2.urlopen(url + 'Title').read().decode('utf-8')
    body = urllib2.urlopen(url + 'body').read().decode('utf-8')

    soup = BeautifulSoup(body)
    # Transform the relative resource links to point to the origin.
    for img in soup.findAll('img'):
        src = img['src']
        if src.startswith('http'):
            continue
        img['src'] = urljoin(url, src)

    # Transform the relative links to point to the correct local
    # address
    for a in soup.findAll('a'):
        href = a.get('href')
        if not href or href.startswith('#') or href.startswith('http'):
            continue
        # Massage the path into this app's URL scheme.
        href = href.rstrip('/')
        path = href.split('/')

        if path[0] != '':
            # Handle resources like .jar files.
            href = urljoin(url, href)
        elif path[1] == 'content':
            # Handles links to other modules.
            link_id, link_version = path[-2:]
            href = "/module/%s@%s" % (link_id, link_version)
        else:
            # Hopefully everything else falls into this category but
            # I'm doubtful.
            href = urljoin(url, href)
        a['href'] = href

    return title, str(soup)

@view_config(route_name='collection', renderer='collection.jinja2')
def collection(request):
    """A view for displaying a collection of modules."""
    id = request.matchdict['id']
    version = 'latest'
    if '@' in id:
        id, version = id.split('@')
    title, content, contents_tree = _process_collection(id, version)
    return {'title': SITE_TITLE,
            'collection_title': title,
            'collection_body': "TODO: I need to work with the OAI interface " \
                               "to get this working until then... There is " \
                               "nothing to see here.",
            'collections_contents_tree': contents_tree,
            }

def _process_collection(id, version='latest'):
    # Request the content from the repository.
    url = 'http://%s:%s/content/%s/%s/' % (REPO_HOST, REPO_PORT,
                                           id, version)
    title = urllib2.urlopen(url + 'getTitle').read()

    # XXX This is the only way to get the Contents Tree ATM...
    contents_tree = urllib2.urlopen(url + 'htmlContentsTree').read()
    contents_tree_soup = BeautifulSoup(contents_tree)
    # Fix the link locations in the contents tree html.
    for a in contents_tree_soup.findAll('a'):
        href = a.get('href')
        if href is None:
            continue
        href = href.split('?')[0]
        href = href.rstrip('/')
        path = href.split('/')
        # It is assumed that all items in the contents tree link to a
        # module or subcollection.
        link_id, link_version = path[-2:]
        if link_id.startswith('m'):
            href = "/module/%s@%s" % (link_id, link_version)
        else:
            href = "/collection/%s@%s" % (link_id, link_version)
        a['href'] = href
    return title.decode('utf-8'), '', str(contents_tree_soup).decode('utf-8')

@view_config(route_name='module_in_collection', renderer='module.jinja2')
def module_in_collection(request):
    """Display a module within the context of a collection."""
    # XXX There is likely a better way to reuse the work done in
    #     previous views here.
    ids = list(request.matchdict.get('ids', ()))

    # This only handles one level of inheritence at the moment
    # (e.g. /<collection/<module>/).
    module_title, module_content = _process_module(*_split_name(ids.pop()))
    collection_title, collection_content, collection_contents_tree = \
            _process_collection(*_split_name(ids.pop()))

    return {'title': SITE_TITLE,
            'collection_title': collection_title,
            'collection_body': "TODO: I need to work with the OAI interface " \
                "to get this working until then... There is " \
                "nothing to see here.",
            'collections_contents_tree': collection_contents_tree,
            'module_title': module_title,
            'module_body': module_content,
            }
