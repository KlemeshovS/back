from fastapi import APIRouter, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter()


@router.get("/api/swagger", include_in_schema=False)
def swagger_ui(request: Request):
    return get_swagger_ui_html(
        openapi_url=request.app.openapi_url,
        title=f"{request.app.title} - Swagger UI",
    )


@router.get("/docs", include_in_schema=False)
def legacy_swagger_redirect() -> RedirectResponse:
    return RedirectResponse(url="/api/swagger", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/api/docs", include_in_schema=False)
def docs_page(request: Request) -> FileResponse:
    return FileResponse(request.app.state.static_dir / "index.html")
