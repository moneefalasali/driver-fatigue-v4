"""
Middleware for handling JWT authentication from multiple sources
"""
from flask import request
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_jwt_extended.exceptions import JWTExtended

def jwt_required_with_fallback():
    """
    Decorator that checks for JWT in multiple locations:
    1. Authorization header (Bearer token)
    2. Cookies
    3. X-Access-Token header (from page navigation)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # Try standard JWT verification first
                verify_jwt_in_request(optional=False)
                return fn(*args, **kwargs)
            except:
                # If standard verification fails, try X-Access-Token header
                token = request.headers.get('X-Access-Token')
                if token:
                    try:
                        from flask_jwt_extended import decode_token
                        # Verify the token
                        decode_token(token)
                        # If verification succeeds, we can proceed
                        return fn(*args, **kwargs)
                    except:
                        pass
                
                # If all verification methods fail, raise the original exception
                raise JWTExtended("Token verification failed")
        
        return wrapper
    return decorator
