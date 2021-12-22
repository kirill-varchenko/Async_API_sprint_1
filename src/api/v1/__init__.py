from fastapi import Query

async def list_parameters(sort: str = None,
                          page_size: int = Query(50, alias='page[size]'),
                          page_number: int = Query(1, alias='page[number]')):
    return {'sort': sort,
            'page_size': page_size,
            'page_number': page_number}