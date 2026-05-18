from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


RoleType = Literal["admin", "provider", "client"]


class UserOut(BaseModel):
    id: str
    email: str
    role: RoleType
