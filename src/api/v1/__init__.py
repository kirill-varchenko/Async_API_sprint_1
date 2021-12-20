from fastapi import Query

async def list_parameters(sort: str = None,
                          page_size: int = Query(50, alias='page[size]'),
                          page_number: int = Query(1, alias='page[number]')):
    return {"sort": sort,
            "page": {"size": page_size,
                     "number": page_number}
            }