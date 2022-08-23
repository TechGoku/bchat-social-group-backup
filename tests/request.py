from json import dumps
from auth import x_bsgs_for
from werkzeug.datastructures import Headers


def bsgs_get(client, url, user):
    """
    GETs a test `client` request to `url` with X-BSGS-* signature headers signing the request for
    `user`.
    """
    return client.get(url, headers=x_bsgs_for(user, "GET", url))


def bsgs_delete(client, url, user):
    """
    DETELEs a test `client` request to `url` with X-BSGS-* signature headers signing the request for
    `user`.
    """
    return client.delete(url, headers=x_bsgs_for(user, "DELETE", url))


def bsgs_post_raw(client, url, data, user, *, ctype='application/octet-stream', extra_headers={}):
    """
    POSTs a test `client` request to `url` with the given `data` as bytes body and X-BSGS-*
    signature headers signing the request for `user`.
    """
    headers = Headers(x_bsgs_for(user, "POST", url, data))
    for k, v in extra_headers.items():
        if isinstance(v, str):
            headers.add(k, v)
        else:
            headers.add(k, v[0], **v[1])

    return client.post(url, data=data, content_type=ctype, headers=headers)


def bsgs_post(client, url, json, user):
    """
    POSTs a test `client` request to `url` with the given `json` as body and X-BSGS-* signature
    headers signing the request for `user`.
    """
    return bsgs_post_raw(client, url, dumps(json).encode(), user, ctype='application/json')


def bsgs_put(client, url, json, user):
    """
    PUTs a test `client` request to `url` with the given `json` as body and X-BSGS-* signature
    headers signing the request for `user`.
    """
    data = dumps(json).encode()

    return client.put(
        url, data=data, content_type='application/json', headers=x_bsgs_for(user, "PUT", url, data)
    )
