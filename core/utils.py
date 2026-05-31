def is_ajax_request(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"
