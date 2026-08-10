from mic_s3.controllers.controller_servicios import router as servicios_router
from mic_s3.controllers.controller_areas import router as areas_router

routers = [servicios_router, areas_router]
