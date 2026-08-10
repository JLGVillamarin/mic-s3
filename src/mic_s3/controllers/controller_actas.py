import hashlib

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from mic_s3.controllers.dependencies import get_session
from mic_s3.parsers.acta_parser_errors import ActaParserError
from mic_s3.services.acta_import_service import ActaImportService

router = APIRouter(prefix="/actas", tags=["Actas Import"])


class ServiceMappingItem(BaseModel):
    parsed_name: str
    matched_id: int | None
    matched_name: str | None
    confidence: str


class ActaParsedServiceResponse(BaseModel):
    servicio_nombre: str
    fecha_reunion: str
    asistentes: list[str]
    puntos_tratados: str
    propuestas: list[dict]


class ActaPreviewResponse(BaseModel):
    services: list[ActaParsedServiceResponse]
    service_mappings: list[ServiceMappingItem]
    warnings: list[str]


class ActaConfirmRequest(BaseModel):
    service_mapping: dict[str, int]  # {parsed_name: servicio_id}


class ActaConfirmResponse(BaseModel):
    actas_created: int
    propuestas_created: int
    skipped_services: int


# Store uploaded files temporarily for the confirm step
_upload_cache: dict[str, bytes] = {}


@router.post("/preview", response_model=ActaPreviewResponse)
async def preview_acta_import(file: UploadFile = File(...)):
    """Upload acta PDF and get parsed preview with service mappings."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")

    content = await file.read()
    try:
        with get_session() as session:
            service = ActaImportService(session)
            result = service.preview(content)

            # Cache for confirm step
            file_hash = hashlib.sha256(content).hexdigest()[:16]
            _upload_cache[file_hash] = content

            return ActaPreviewResponse(
                services=[
                    ActaParsedServiceResponse(
                        servicio_nombre=s.servicio_nombre,
                        fecha_reunion=s.fecha_reunion,
                        asistentes=s.asistentes,
                        puntos_tratados=s.puntos_tratados,
                        propuestas=s.propuestas,
                    )
                    for s in result.parsed.services
                ],
                service_mappings=[ServiceMappingItem(**m) for m in result.service_mappings],
                warnings=result.warnings,
            )
    except ActaParserError as e:
        raise HTTPException(status_code=422, detail={"message": str(e), "details": e.details})


@router.post("/confirm/{file_hash}", response_model=ActaConfirmResponse)
def confirm_acta_import(file_hash: str, request: ActaConfirmRequest):
    """Confirm acta import with user-verified service mapping."""
    content = _upload_cache.pop(file_hash, None)
    if not content:
        raise HTTPException(status_code=404, detail="Archivo no encontrado. Repita el paso de preview.")

    try:
        with get_session() as session:
            service = ActaImportService(session)
            result = service.confirm(content, request.service_mapping)
            return ActaConfirmResponse(**result)
    except ActaParserError as e:
        raise HTTPException(status_code=422, detail={"message": str(e), "details": e.details})
