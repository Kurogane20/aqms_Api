from math import ceil
from pydantic import BaseModel
from typing import Any

def paginate_meta(page: int, per_page: int, total: int) -> dict[str, Any]:
    total_pages = max(1, ceil(total / per_page)) if per_page > 0 else 1
    page = max(1, min(page, total_pages))
    return {
        "page": page,
        "per_page": per_page,
        "total_items": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }
