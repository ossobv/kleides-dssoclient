Kleides Discourse SSO client
============================

*Discourse Single-Sign-on (DSSO) provider client* to connect your
*Django* project to a *Discourse Single-Sign-On provider server*.

See: https://meta.discourse.org/t/official-single-sign-on-for-discourse-sso/

Example usage:

* Add ``kleides_dssoclient`` to ``INSTALLED_APPS``.

* Create a custom ``DssoLoginBackend``, for example::

    from kleides_dssoclient.backends import DssoLoginBackend

    class MyProjectDssoLoginBackend(DssoLoginBackend):
        """
        DssoLoginBackend that rejects anyone without is_superuser, and that
        sets all mapped variables on the newly created User object.
        """
        def authenticate(self, sso_mapping):
            """
            Check that user is a superuser and pass along to DssoLoginBackend.
            """
            if sso_mapping.get('is_superuser') not in ('True', 'true', '1'):
                return None

            return super(MyProjectDssoLoginBackend, self).authenticate(
                sso_mapping)

        def configure_user(self, user, sso_mapping):
            """
            We expect username, email, is_superuser in the sso_mapping.
            """
            user = (
                super(MyProjectDssoLoginBackend, self)
                .configure_user(user, sso_mapping))

            user.email = sso_mapping.get('email', '')
            is_superuser = (
                sso_mapping.get('is_superuser') in ('True', 'true', '1'))
            user.is_staff = is_superuser
            user.is_superuser = is_superuser

            user.save()
            return user

* Add this to the *Django* ``settings``::

    AUTHENTICATION_BACKENDS = (  # the only backend needed
        'myproject.backends.MyProjectDssoLoginBackend',
    )
    MIDDLEWARE_CLASSES += (
        'kleides_dssoclient.middleware.DssoLoginMiddleware',
    )
    KLEIDES_DSSOCLIENT_ENDPOINT = 'https://SSO_SERVER/sso/'
    KLEIDES_DSSOCLIENT_SHARED_KEY = 'oh-sso-very-very-secret'
