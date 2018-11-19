from unittest import TestCase
import base64
import hashlib
import hmac

try:
    # py3
    from base64 import decodebytes
    from urllib.parse import parse_qs, parse_qsl, urlsplit, urlencode, unquote
except ImportError:
    # py2
    from base64 import decodestring as decodebytes
    from urllib import urlencode
    from urlparse import parse_qs, parse_qsl, urlsplit, unquote


class DssoClientEncoder(object):
    def __init__(self, client_to_server_secret, nonce, return_url):
        """
        Pass secret, nonce and target return URL.

        Get redirect URL by calling get_redirect_url(dsso_url).
        """
        assert isinstance(client_to_server_secret, bytes)
        payload = base64.b64encode(
            urlencode((('nonce', nonce), ('return_sso_url', return_url)))
            .encode('utf-8')).rstrip(b'=')
        h = hmac.new(
            client_to_server_secret, payload, digestmod=hashlib.sha256)
        sig = h.hexdigest()
        self._sso = payload.decode('ascii')
        self._sig = sig

    def get_redirect_url(self, dsso_url):
        assert '?' not in dsso_url, dsso_url
        return '{url}?sso={payload}&sig={signature}'.format(
            url=dsso_url, payload=self._sso, signature=self._sig)


class DssoClientDecoder(object):
    def __init__(self, server_to_client_secret, nonce, return_location):
        """
        Pass secret and the redirect Location (destination).

        Raises ValueError on decode failures.
        """
        assert isinstance(server_to_client_secret, bytes)
        self._url = urlsplit(return_location)
        sso, sig, self._parsed_qs = self._parse_query_string(self._url.query)

        h = hmac.new(
            server_to_client_secret, sso.encode('utf-8'),
            digestmod=hashlib.sha256)
        if sig != h.hexdigest():
            raise ValueError('signature mismatch')

        decoded = parse_qs(decodebytes(
            unquote(sso).encode('ascii')).decode('utf-8'))
        self._mapping = {}
        for key, value in decoded.items():
            if len(value) != 1:
                raise ValueError('multiple values for {!r} in {!r}'.format(
                    key, decoded))
            self._mapping[key] = value[0]

        if self._mapping.pop('nonce', None) != nonce:
            raise ValueError('bad nonce')

    def _parse_query_string(self, qs):
        query = parse_qsl(qs)
        sig, sso = None, None
        leftover = []
        for key, value in query:
            if key == 'sso':
                if sso is not None:
                    raise ValueError('multiple sso values')
                sso = value
            elif key == 'sig':
                if sig is not None:
                    raise ValueError('multiple sig values')
                sig = value
            else:
                leftover.append((key, value))

        if sig is None or sso is None:
            raise ValueError('missing sso or sig value')

        return sso, sig, leftover

    def get_destination(self):
        return '{}://{}{}{}'.format(
            self._url.scheme, self._url.netloc, self._url.path,
            self.get_destination_query_string())

    def get_destination_query_params(self):
        return self._parsed_qs

    def get_destination_query_string(self):
        if self._parsed_qs:
            return '?{}'.format(urlencode(self._parsed_qs))
        return ''

    def get_mapping(self):
        return self._mapping


class DssoClientTestCase(TestCase):
    def test_encoder(self):
        encoder = DssoClientEncoder(
            b'geheim', 'abc', 'https://host/path/x.cgi')
        redir_url = encoder.get_redirect_url('https://authserver/somewhere')
        expected_url = (
            'https://authserver/somewhere'
            '?sso=bm9uY2U9YWJjJnJldHVybl9zc29fdXJsPWh0dHBzJTNBJTJGJTJGa'
            'G9zdCUyRnBhdGglMkZ4LmNnaQ'
            '&sig=3e8682b54e3e93a14b7d4b6c8282e03480632317fd06a37b9f693'
            'a6cbaacd23f')
        self.assertEqual(expected_url, redir_url)

    def test_decoder(self):
        input_ = (
            'https://destserver/return?arg=defined'
            '&sig=6ce8f00814e76d0dcd7a9c03ba69244fac1b6e1248a46993b7bc0'
            '7c8992544ec'
            '&sso=bm9uY2U9YWJjZGVmJmV4dGVybmFsX2lkPTQmZW1haWw9YXV0aG9ya'
            'XplZCU0MG9zc28ubmwmdXNlcm5hbWU9YXV0aG9yaXplZA%3D%3D')

        with self.assertRaises(ValueError):
            # sig-mismatch without %3D%3D
            DssoClientDecoder(b'geheim', 'abcde', input_[0:-6])
        with self.assertRaises(ValueError):
            # nonce mismatch
            DssoClientDecoder(b'geheim', 'abcde', input_)
        with self.assertRaises(ValueError):
            # secret mismatch
            DssoClientDecoder(b'geheim2', 'abcdef', input_)

        decoder = DssoClientDecoder(b'geheim', 'abcdef', input_)
        self.assertEqual(
            decoder.get_destination(), 'https://destserver/return?arg=defined')
        self.assertEqual(
            decoder.get_mapping(),
            {'email': 'authorized@osso.nl', 'external_id': '4',
             'username': 'authorized'})


if __name__ == '__main__':
    from unittest import main
    main()
