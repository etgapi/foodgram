from rest_framework.pagination import PageNumberPagination

PAGE_SIZE = 6


class LimitPagePagination(PageNumberPagination):
    page_size = PAGE_SIZE
    # page_query_param = "page"
    page_size_query_param = "limit"
