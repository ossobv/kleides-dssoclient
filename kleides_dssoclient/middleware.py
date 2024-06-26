import logging
import random
import time

import django
from django.conf import settings
from django.contrib import auth
from django.core.exceptions import (
    ImproperlyConfigured, MiddlewareNotUsed, PermissionDenied,
    SuspiciousOperation)
from django.http import HttpResponseRedirect
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object
from django.utils.encoding import escape_uri_path

from .dssoclient import DssoClientDecoder, DssoClientEncoder

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class DssoLoginMiddleware(MiddlewareMixin):
    """
    Middleware for utilizing DSSO-provided authentication.

    If request.user is not authenticated, then this middleware attempts
    to redirect the user to the ``KLEIDES_DSSO_ENDPOINT``. The user
    should then be redirected back here with SSO credentials in the URL.
    If the user is flagges as is_superuser, he is auto-created and
    peristed in the session.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not getattr(settings, 'KLEIDES_DSSO_ENDPOINT'):
            raise MiddlewareNotUsed()

    def process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The DSSO login auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the DssoLoginMiddleware class.")

        # The user is already authenticated? Nothing to do.
        if (request.user.is_authenticated if django.VERSION >= (1, 10)
                else request.user.is_authenticated()):
            log.debug('User %r is authenticated, skipping DSSO', request.user)
            return

        if not (settings.KLEIDES_DSSO_ENDPOINT and
                settings.KLEIDES_DSSO_SHARED_KEY):
            raise ImproperlyConfigured(
                "The DSSO login middleware requires KLEIDES_DSSO_ENDPOINT and"
                " KLEIDES_DSSO_SHARED_KEY to be set. If they're not set, you"
                " shouldn't load this module.")

        # So, we're seeing this user for the first or second time,
        # depending on the query_string.
        if not ('sso' in request.GET and 'sig' in request.GET):
            return self.redirect_to_dsso_endpoint(request)
        elif 'kleides_dsso_nonce' in request.session:
            return self.return_from_dsso_endpoint(request)

        # This is bad..? Session not saved? Or an error during processing?
        # Shouldn't redirect because that may start a loop if the failure
        # is persistent.
        raise SuspiciousOperation(
            'Session data corrupt? Or user playing around?')

    def redirect_to_dsso_endpoint(self, request):
        # Construct nonce by using timestamp and a bit of random junk.
        nonce = '{}-{}'.format(int(time.time()), random.random())
        log.debug('Starting DSSO authentication with nonce: %r', nonce)
        return_url = request.build_absolute_uri()
        try:
            enc = DssoClientEncoder(
                settings.KLEIDES_DSSO_SHARED_KEY.encode('ascii'),
                nonce, return_url)
            uri = enc.get_redirect_url(settings.KLEIDES_DSSO_ENDPOINT)
        except ValueError as e:
            log.debug('Error encoding DSSO payload: %r', e, exc_info=True)
            raise PermissionDenied(str(e))

        request.session['kleides_dsso_nonce'] = nonce
        # Must save now, as the session response middleware is never called.
        request.session.save()

        return HttpResponseRedirect(uri)

    def return_from_dsso_endpoint(self, request):
        sso_nonce = request.session.pop('kleides_dsso_nonce')
        log.debug('Returned from DSSO endpoint with nonce: %r', sso_nonce)
        sso_time, sso_rand = sso_nonce.split('-', 1)
        if (time.time() - int(sso_time)) > 60:
            log.debug('Stale kleides_dsso_nonce in session')
            raise PermissionDenied('stale kleides_dsso_nonce in session')

        try:
            dec = DssoClientDecoder(
                settings.KLEIDES_DSSO_SHARED_KEY.encode('ascii'),
                sso_nonce, request.get_full_path())
            mapping = dec.get_mapping()
        except ValueError as e:
            log.debug('Error decoding DSSO payload: %r', e, exc_info=True)
            raise PermissionDenied(str(e))

        user = auth.authenticate(dsso_mapping=mapping)
        if not user:
            log.debug('DSSO mapping did not yield a user')
            raise PermissionDenied('not for you')

        # User is valid.  Set request.user and persist user in the session
        # by logging the user in.
        request.user = user
        auth.login(request, user)
        log.debug('Logged in %r using kleides_dssoclient', user)
        return HttpResponseRedirect(self.get_redirect_url(request))

    def get_redirect_url(self, request):
        '''
        Return the request url without dsso params.
        '''
        if len(request.GET) > 2:
            query = request.GET.copy()
            query.pop('sso')
            query.pop('sig')
            query_string = '?' + query.urlencode()
        else:
            query_string = ''
        return escape_uri_path(request.path) + query_string
