import warnings

from pydantic.warnings import UnsupportedFieldAttributeWarning

from app.api.app import create_app

warnings.filterwarnings("ignore", category=UnsupportedFieldAttributeWarning)

app = create_app()
