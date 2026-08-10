from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from mic_s3.models.area import Area
from mic_s3.controllers.dependencies import get_session

router = APIRouter(prefix="/areas", tags=["Areas"])


class AreaCreateRequest(BaseModel):
    nombre: str
    responsable: str | None = None


class AreaResponse(BaseModel):
    id: int
    nombre: str
    responsable: str | None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[AreaResponse])
def list_areas():
    with get_session() as session:
        return list(session.scalars(select(Area)))


@router.post("/", response_model=AreaResponse, status_code=201)
def create_area(request: AreaCreateRequest):
    with get_session() as session:
        area = Area(**request.model_dump())
        session.add(area)
        session.commit()
        session.refresh(area)
        return area
