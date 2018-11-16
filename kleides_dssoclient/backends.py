from django.contrib.auth.backends import ModelBackend, get_user_model


class DssoLoginBackend(ModelBackend):
    """
    This backend is to be used in conjunction with the
    ``DssoLoginMiddleware`` found in the middleware module of this
    package, and is used when the server is handling authentication
    through a Discourse Single-Sign-On (DSSO) endpoint.

    By default, the ``authenticate`` method creates ``User`` objects for
    usernames that don't already exist in the database.  Subclasses can
    disable this behavior by setting the ``create_unknown_user``
    attribute to ``False``.
    """

    # Create a User object if not already in the database?
    create_unknown_user = True

    def authenticate(self, sso_mapping):
        """
        The username passed in the ``sso_mapping`` dict is considered
        trusted. This method simply returns the ``User`` object with
        the given username, creating a new ``User`` object if
        ``create_unknown_user`` is ``True``.

        Returns None if ``create_unknown_user`` is ``False`` and a
        ``User`` object with the given username is not found in the
        database.
        """
        if not sso_mapping or not sso_mapping.get('username'):
            return

        user = None
        username = sso_mapping['username']
        UserModel = get_user_model()

        # Note that this could be accomplished in one try-except clause,
        # but instead we use get_or_create when creating unknown users
        # since it has built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = UserModel._default_manager.get_or_create(**{
                UserModel.USERNAME_FIELD: username
            })
            if created:
                user = self.configure_user(user, sso_mapping)
        else:
            try:
                user = UserModel._default_manager.get_by_natural_key(username)
            except UserModel.DoesNotExist:
                pass

        return user

    def configure_user(self, user, sso_mapping):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified.
        """
        return user
