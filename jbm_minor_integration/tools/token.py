# -*- coding: utf-8 -*-
import jwt
from datetime import datetime, timedelta
from odoo.http import request
import functools
from .exception import InvalidRefreshToken
from odoo.exceptions import AccessDenied

refresh_token_info = {
    "days": 30,
    "algorithm": "HS256",
    "secret": "SecretWassefRefreshToken",
}

access_token_info = {
    "hours": 4,
    "algorithm": "HS256",
    "secret": "SecretWassefAccessToken",
}


def get_employee_object():
    """Return employee object from token"""
    token = dict(list(request.httprequest.headers.items())).get('Authorization').split()[1]
    token_info = jwt.decode(token, key=access_token_info.get("secret"), algorithms=access_token_info.get("algorithm"))
    return request.env['hr.employee'].sudo().search([('id', '=', token_info['employee_id'])])


def get_claims_access_token():
    """Return claims from access token even is expired"""
    try:
        # if token is valid return
        token = dict(list(request.httprequest.headers.items())).get('Authorization').split()[1]
        access_token_claim = jwt.decode(token, key=access_token_info.get("secret"),
                                        algorithms=access_token_info.get("algorithm"))
    except jwt.ExpiredSignatureError as e:
        # if token is expired
        # get claims from access token
        access_token_claim = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
    return access_token_claim


def get_claims_refresh_token(refresh_token):
    """Return claims from refresh token
    @param: refresh_token"""
    try:
        claims_refresh_token = jwt.decode(refresh_token, key=refresh_token_info.get("secret"),
                                          algorithms=refresh_token_info.get("algorithm"))
    except jwt.ExpiredSignatureError as e:
        raise InvalidRefreshToken
    except Exception as e:
        raise InvalidRefreshToken

    return claims_refresh_token


def create_access_token(user):
    """Create Token Using jwt
    :param user indicate the user object
    return token which created
    """
    try:
        exp = datetime.utcnow() + timedelta(hours=access_token_info.get("hours") or 1)
        payload = {'exp': exp, 'id': user.id}
        encoded = jwt.encode(payload, key=access_token_info.get("secret"), algorithm=access_token_info.get("algorithm"))
        return encoded, exp.timestamp()
    except (jwt.exceptions.InvalidKeyError, jwt.exceptions.InvalidAlgorithmError):
        return Exception("Can not create access token")


def create_refresh_token(user):
    """Create Refresh Token Using jwt
    :param user indicate the employee object
    return refresh token which created
    """
    try:
        exp = datetime.utcnow() + timedelta(days=refresh_token_info.get("days"))
        payload = {'exp': exp, 'id': user.id}
        encoded = jwt.encode(payload, key=refresh_token_info.get("secret"),
                             algorithm=refresh_token_info.get("algorithm"))
        return encoded
    except (jwt.exceptions.InvalidKeyError, jwt.exceptions.InvalidAlgorithmError):
        raise Exception("Can not create refresh token")


def _get_user_id():
    headers = dict(request.httprequest.headers.items())
    token = headers.get('Authorization')
    token = token.split()[1]
    token_info = jwt.decode(token, key=access_token_info.get("secret"),
                            algorithms=access_token_info.get("algorithm"))
    return request.env['res.users'].sudo().search([('id', '=', token_info['id'])])


def check_refresh_token(refresh_token):
    """Check if id of user in claims of access_token is equal to user_id in claims of refresh token
    return employee object"""
    claims_access_token = get_claims_access_token()
    claims_refresh_token = get_claims_refresh_token(refresh_token)
    if claims_refresh_token:
        if claims_refresh_token.get("id") == claims_access_token.get("id"):
            return request.env['res.users'].sudo().search([('id', '=', claims_refresh_token['id'])])
    return False


def validate_token(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        headers = dict(request.httprequest.headers.items())
        token = headers.get('Authorization')
        if isinstance(token, str):
            token = token.split()[1]
            token_info = jwt.decode(token, key=access_token_info.get("secret"),
                                    algorithms=access_token_info.get("algorithm"))
            if token_info.get('id'):
                user = request.env['res.users'].sudo().search([('id', '=', token_info['id'])])
                if user:
                    return func(*args, **kwargs)
                else:
                    raise AccessDenied
            else:
                raise jwt.InvalidTokenError
        else:
            raise jwt.InvalidTokenError

    return inner
