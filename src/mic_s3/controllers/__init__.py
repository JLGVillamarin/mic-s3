from mic_s3.controllers.controller_servicios import router as servicios_router
from mic_s3.controllers.controller_areas import router as areas_router
from mic_s3.controllers.controller_bran import router as bran_router
from mic_s3.controllers.controller_actas import router as actas_router
from mic_s3.controllers.controller_dimensionamiento import router as dimensionamiento_router
from mic_s3.controllers.controller_horas import router as horas_router
from mic_s3.controllers.controller_propuestas import router as propuestas_router
from mic_s3.controllers.controller_alertas import router as alertas_router
from mic_s3.controllers.controller_dashboard import router as dashboard_router

routers = [servicios_router, areas_router, bran_router, actas_router, dimensionamiento_router, horas_router, propuestas_router, alertas_router, dashboard_router]
