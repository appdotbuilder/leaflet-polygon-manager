from typing import Optional
from sqlmodel import select, desc
from app.database import get_session
from app.models import Polygon, PolygonCreate, PolygonUpdate, PolygonResponse, PolygonListResponse
import logging

logger = logging.getLogger(__name__)


class PolygonService:
    """Service class for managing polygon operations."""

    def create_polygon(self, polygon_data: PolygonCreate) -> Optional[PolygonResponse]:
        """Create a new polygon in the database."""
        try:
            with get_session() as session:
                polygon = Polygon(
                    name=polygon_data.name,
                    coordinates=polygon_data.coordinates,
                    properties=polygon_data.properties,
                )
                session.add(polygon)
                session.commit()
                session.refresh(polygon)

                if polygon.id is None:
                    return None

                return PolygonResponse.from_polygon(polygon)
        except Exception as e:
            logger.error(f"Failed to create polygon: {e}")
            return None

    def get_polygon(self, polygon_id: int) -> Optional[PolygonResponse]:
        """Get a single polygon by ID."""
        try:
            with get_session() as session:
                polygon = session.get(Polygon, polygon_id)
                if polygon is None:
                    return None
                return PolygonResponse.from_polygon(polygon)
        except Exception as e:
            logger.error(f"Failed to create polygon: {e}")
            return None

    def list_polygons(self) -> PolygonListResponse:
        """Get all polygons from the database."""
        try:
            with get_session() as session:
                statement = select(Polygon).order_by(desc(Polygon.created_at))
                polygons = session.exec(statement).all()

                polygon_responses = [PolygonResponse.from_polygon(polygon) for polygon in polygons]
                return PolygonListResponse(polygons=polygon_responses, total=len(polygon_responses))
        except Exception as e:
            logger.error(f"Failed to list polygons: {e}")
            return PolygonListResponse(polygons=[], total=0)

    def update_polygon(self, polygon_id: int, polygon_data: PolygonUpdate) -> Optional[PolygonResponse]:
        """Update an existing polygon."""
        try:
            with get_session() as session:
                polygon = session.get(Polygon, polygon_id)
                if polygon is None:
                    return None

                # Update fields that were provided
                if polygon_data.name is not None:
                    polygon.name = polygon_data.name
                if polygon_data.coordinates is not None:
                    polygon.coordinates = polygon_data.coordinates
                if polygon_data.properties is not None:
                    polygon.properties = polygon_data.properties

                polygon.update_timestamp()
                session.add(polygon)
                session.commit()
                session.refresh(polygon)

                return PolygonResponse.from_polygon(polygon)
        except Exception as e:
            logger.error(f"Failed to create polygon: {e}")
            return None

    def delete_polygon(self, polygon_id: int) -> bool:
        """Delete a polygon from the database."""
        try:
            with get_session() as session:
                polygon = session.get(Polygon, polygon_id)
                if polygon is None:
                    return False

                session.delete(polygon)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete polygon {polygon_id}: {e}")
            return False

    def polygon_exists(self, polygon_id: int) -> bool:
        """Check if a polygon exists."""
        try:
            with get_session() as session:
                polygon = session.get(Polygon, polygon_id)
                return polygon is not None
        except Exception as e:
            logger.error(f"Failed to delete polygon {polygon_id}: {e}")
            return False


# Global service instance
polygon_service = PolygonService()
