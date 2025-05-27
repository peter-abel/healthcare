import logging
import uuid
from django.core.cache import cache
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('django')

def custom_exception_handler(exc, context):
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Generate a unique error reference ID
    error_id = str(uuid.uuid4())
    
    # If response is None, it means DRF couldn't handle the exception
    if response is None:
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True, extra={'error_id': error_id})
        return Response(
            {
                'error': 'Internal server error',
                'error_id': error_id,
                'message': 'An unexpected error occurred. Please try again later.',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Add more details to the response
    if response.status_code == 400:
        response.data = {
            'error': 'Bad request',
            'error_id': error_id,
            'message': 'The request was invalid.',
            'details': response.data,
            'status_code': response.status_code
        }
    elif response.status_code == 401:
        response.data = {
            'error': 'Unauthorized',
            'error_id': error_id,
            'message': 'Authentication credentials were not provided or are invalid.',
            'status_code': response.status_code
        }
    elif response.status_code == 403:
        response.data = {
            'error': 'Forbidden',
            'error_id': error_id,
            'message': 'You do not have permission to perform this action.',
            'status_code': response.status_code
        }
    elif response.status_code == 404:
        response.data = {
            'error': 'Not found',
            'error_id': error_id,
            'message': 'The requested resource was not found.',
            'status_code': response.status_code
        }
    elif response.status_code == 405:
        response.data = {
            'error': 'Method not allowed',
            'error_id': error_id,
            'message': 'The request method is not allowed for this endpoint.',
            'status_code': response.status_code
        }
    elif response.status_code == 429:
        response.data = {
            'error': 'Too many requests',
            'error_id': error_id,
            'message': 'You have exceeded the rate limit. Please try again later.',
            'status_code': response.status_code
        }
    else:
        # Log the error
        logger.error(f"Exception: {str(exc)}", exc_info=True, extra={'error_id': error_id})
        
        # Add error ID to the response
        response.data = {
            'error': 'Error',
            'error_id': error_id,
            'message': str(exc),
            'details': response.data if hasattr(response, 'data') else {},
            'status_code': response.status_code
        }
    
    return response

def get_cached_data(cache_key, timeout, query_function, *args, **kwargs):
    
    # Try to get data from cache
    data = cache.get(cache_key)
    
    # If not in cache, execute the query function and cache the result
    if data is None:
        data = query_function(*args, **kwargs)
        cache.set(cache_key, data, timeout)
    
    return data

def invalidate_cache_pattern(pattern):
  
    # This is a simplified version. In a real-world scenario, you would need
    # to use a more sophisticated approach to find and delete keys matching a pattern.
    # Redis supports the SCAN command for this purpose.
    keys = cache.keys(pattern)
    if keys:
        cache.delete_many(keys)
