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
        def authenticate(self, dsso_mapping):
            """
            Check that user is a superuser and pass along to DssoLoginBackend.
            """
            if dsso_mapping.get('is_superuser') not in ('True', 'true', '1'):
                return None

            return super(MyProjectDssoLoginBackend, self).authenticate(
                dsso_mapping)

        def configure_user(self, user, dsso_mapping):
            """
            We expect username, email, is_superuser in the dsso_mapping.
            """
            user = (
                super(MyProjectDssoLoginBackend, self)
                .configure_user(user, dsso_mapping))

            user.email = dsso_mapping.get('email', '')
            is_superuser = (
                dsso_mapping.get('is_superuser') in ('True', 'true', '1'))
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
    KLEIDES_DSSO_ENDPOINT = 'https://DSSOSERVER/sso/'
    KLEIDES_DSSO_SHARED_KEY = 'oh-sso-very-very-secret'
