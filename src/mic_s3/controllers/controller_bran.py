from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from datetime import date
from mic_s3.controllers.dependencies import get_session
from mic_s3.services.bran_import_service import BranImportService
from mic_s3.parsers.bran_parser import BranParserError

router = APIRouter(prefix="/bran", tags=["BRAN Import"])


class BranPreviewRow(BaseModel):
    nombre: str
    perfil: str
    servicio_nombre: str


class BranPreviewResponse(BaseModel):
    total_parsed: int
    rows: list[BranPreviewRow]
    warnings: list[str]
    servicios_not_found: list[str]


class BranConfirmResponse(BaseModel):
    created: int
    skipped: int
    total: int


@router.post("/preview", response_model=BranPreviewResponse)
async def preview_bran_import(file: UploadFile = File(...)):
    """Upload BRAN Excel and get a preview without persisting."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos Excel (.xlsx)")

    content = await file.read()
    try:
        with get_session() as session:
            service = BranImportService(session)
            result = service.preview(content)
            return BranPreviewResponse(
                total_parsed=result.total_parsed,
                rows=[BranPreviewRow(nombre=r.nombre, perfil=r.perfil, servicio_nombre=r.servicio_nombre) for r in result.rows],
                warnings=result.warnings,
                servicios_not_found=result.servicios_not_found,
            )
    except BranParserError as e:
        raise HTTPException(status_code=422, detail={"message": str(e), "details": e.details})


@router.post("/confirm", response_model=BranConfirmResponse)
async def confirm_bran_import(file: UploadFile = File(...), mes: date = Query(..., description="Mes del snapshot (YYYY-MM-DD, usar primer día del mes)")):
    """Confirm BRAN import and persist monthly snapshot."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos Excel (.xlsx)")

    content = await file.read()
    try:
        with get_session() as session:
            service = BranImportService(session)
            result = service.confirm(content, mes)
            return BranConfirmResponse(**result)
    except BranParserError as e:
        raise HTTPException(status_code=422, detail={"message": str(e), "details": e.details})
