from pydantic import BaseModel
from typing import Optional

class LookupQuery(BaseModel):
    domain: Optional[str] = None
    keyword: Optional[str] = None
    faculty: Optional[str] = None
