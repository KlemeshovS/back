from fastapi import APIRouter, Request, status
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()


@router.get("/", include_in_schema=False)
def landing_page(request: Request):
    host = request.headers.get("host", "")
    if host.startswith("wobbly.site"):
        return FileResponse(request.app.state.static_dir / "pages" / "landing.html")

    return HTMLResponse(content="<h1>Wobbly API</h1>", status_code=status.HTTP_200_OK)


@router.get("/privacy", include_in_schema=False)
def privacy_page(request: Request):
    host = request.headers.get("host", "")
    if host.startswith("wobbly.site"):
        return FileResponse(request.app.state.static_dir / "pages" / "privacy.html")

    return HTMLResponse(content="<h1>Not Found</h1>", status_code=status.HTTP_404_NOT_FOUND)
