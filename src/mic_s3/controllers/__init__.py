from mic_s3.controllers.controller_actas import router as actas_router
from mic_s3.controllers.controller_areas import router as areas_router
from mic_s3.controllers.controller_bran import router as bran_router
from mic_s3.controllers.controller_servicios import router as servicios_router

routers = [servicios_router, areas_router, bran_router, actas_router]
