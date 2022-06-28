import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-jnnv8d0c.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'drinks_api'

# AuthError Exception


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# get authorization header
def get_token_auth_header(request):

    # get the headers
    headers = request.headers

    # check for Authorization in the headers
    if 'Authorization' not in headers:
        raise AuthError('Unauthorized', 401)

    auth_header = headers['Authorization']
    auth_header_parts = auth_header.split(' ')

    # check if token is valid
    if len(auth_header_parts) != 2:
        raise AuthError('Unauthorized', 401)
    elif auth_header_parts[0].lower() != 'bearer':
        raise AuthError('Unauthorized', 401)

    return auth_header_parts[1]

# check permission


def check_permissions(permission, payload):
    if "permissions" not in payload:
        raise AuthError('Forbidden', 403)

    if permission not in payload['permissions']:
        raise AuthError('Forbidden', 403)

    return True


# verify jwt
def verify_decode_jwt(token):
    # GET THE PUBLIC KEY FROM AUTH0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    # GET THE DATA IN THE HEADER
    unverified_header = jwt.get_unverified_header(token)

    # CHOOSE OUR KEY
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            # USE THE KEY TO VALIDATE THE JWT
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
        'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
    }, 400)


# require auth decorator
def requires_auth(permissions=''):

    def requires_auth_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            # do the authentication
            jwt = get_token_auth_header(request)

            # decode the jwt
            try:
                payload = verify_decode_jwt(jwt)
            except BaseException:
                raise AuthError("Forbidden", 403)

            # check for permissions, if ok continuew, else abort
            check_permissions(permissions, payload)

            return func(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator
