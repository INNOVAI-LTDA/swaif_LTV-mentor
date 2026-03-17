from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


RoleType = Literal["admin", "mentor", "client"]


class UserOut(BaseModel):
    id: str
    email: str
    role: RoleType
