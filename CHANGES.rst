Changes
-------

v0.7 - *2019-07-16*
~~~~~~~~~~~~~~~~~~~

- Allow bypassing the middleware by setting KLEIDES_DSSO_ENDPOINT to None.


v0.6 - *2019-03-06*
~~~~~~~~~~~~~~~~~~~

- Add ``request`` arg to ``DssoLoginBackend`` for Django 2.1.


v0.5 - *2019-03-06*
~~~~~~~~~~~~~~~~~~~

- Add logging to help investigate problems.


v0.3 - *2018-12-18*
~~~~~~~~~~~~~~~~~~~

- Add support for Django 1.10 style middleware.
- Check Django version for is_authenticated usage.


v0.2 - *2018-11-19*
~~~~~~~~~~~~~~~~~~~

- Replace ``sso_mapping`` with ``dsso_mapping`` in authenticate argument list.


v0.1 - *2018-11-16*
~~~~~~~~~~~~~~~~~~~

- Initial release.
