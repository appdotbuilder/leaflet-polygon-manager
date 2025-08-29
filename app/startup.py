from app.database import create_tables
import app.map_app


def startup() -> None:
    # this function is called before the first request
    create_tables()
    app.map_app.create()
