from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


RoleType = Literal["admin", "provider", "client"]


class UserOut(BaseModel):
    id: int
    email: str
    role: RoleType
