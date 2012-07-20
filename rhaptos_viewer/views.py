# -*- coding: utf-8 -*-
from pyramid.view import view_config


SITE_TITLE = 'Connexions Web Viewer'

@view_config(route_name='casa', renderer='casa.jinja2')
def casa(request):
    """The home page for this application."""
    return {'title': SITE_TITLE}
