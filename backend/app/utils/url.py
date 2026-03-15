from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

from app.core.config import settings


def add_query_params(url: str, params: dict):
    # Parse the URL
    url_parts = list(urlparse(url))

    # Convert existing query parameters into a dictionary
    query = dict(parse_qsl(url_parts[4]))

    # Update the query parameters with the new ones
    query.update(params)

    # Encode the updated query parameters and add them back to the URL
    url_parts[4] = urlencode(query)

    # Return the modified URL
    return urlunparse(url_parts)


def create_token_url(endpoint: str, token: str):
    return add_query_params(f"{settings.HOST_URL}/{endpoint}", {"token": token})


def create_backend_token_url(endpoint: str, token: str):
    return add_query_params(
        f"{settings.HOST_URL}{settings.API_V1_STR}/{endpoint}", {"token": token}
    )
