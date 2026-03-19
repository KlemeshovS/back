from fastapi import APIRouter, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

router = APIRouter()


@router.get("/", include_in_schema=False)
def landing_page(request: Request):
    host = request.headers.get("host", "")
    if host.startswith("wobbly.site"):
        return FileResponse(request.app.state.static_dir / "pages" / "landing.html")
    if host.startswith("admin.wobbly.site"):
        return RedirectResponse(url="/production/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    return HTMLResponse(content="<h1>Wobbly API</h1>", status_code=status.HTTP_200_OK)


@router.get("/privacy", include_in_schema=False)
def privacy_page(request: Request):
    host = request.headers.get("host", "")
    if host.startswith("wobbly.site"):
        return FileResponse(request.app.state.static_dir / "pages" / "privacy.html")

    return HTMLResponse(content="<h1>Not Found</h1>", status_code=status.HTTP_404_NOT_FOUND)


@router.get("/production", include_in_schema=False)
@router.get("/production/", include_in_schema=False)
@router.get("/staging", include_in_schema=False)
@router.get("/staging/", include_in_schema=False)
def admin_panel(request: Request):
    host = request.headers.get("host", "")
    if host.startswith("admin.wobbly.site"):
        return FileResponse(request.app.state.static_dir / "pages" / "admin.html")

    return HTMLResponse(content="<h1>Not Found</h1>", status_code=status.HTTP_404_NOT_FOUND)


@router.get("/production/assets/{asset_path:path}", include_in_schema=False)
@router.get("/staging/assets/{asset_path:path}", include_in_schema=False)
def admin_assets(request: Request, asset_path: str):
    host = request.headers.get("host", "")
    if not host.startswith("admin.wobbly.site"):
        return HTMLResponse(content="<h1>Not Found</h1>", status_code=status.HTTP_404_NOT_FOUND)

    asset_file = request.app.state.static_dir / asset_path
    if asset_file.is_file():
        return FileResponse(asset_file)

    return HTMLResponse(content="<h1>Not Found</h1>", status_code=status.HTTP_404_NOT_FOUND)
