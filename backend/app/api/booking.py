from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_services
from app.models.schemas import (
    AvailabilityRequest,
    AvailabilityResponse,
    BookingRequest,
    BookingResponse,
)
from app.services.container import ServiceContainer


router = APIRouter(tags=["booking"])


@router.post("/availability", response_model=AvailabilityResponse)
def availability(
    request: AvailabilityRequest,
    services: ServiceContainer = Depends(get_services),
) -> AvailabilityResponse:
    try:
        slots = services.calcom.get_availability(request)
    except Exception as exc:
        services.evaluation.log_failure("booking_api_error", {"error": str(exc), "action": "availability"})
        raise HTTPException(status_code=503, detail="Could not fetch availability.") from exc
    return AvailabilityResponse(slots=slots)


@router.post("/book", response_model=BookingResponse)
def book_slot(
    request: BookingRequest,
    services: ServiceContainer = Depends(get_services),
) -> BookingResponse:
    try:
        return services.calcom.book_slot(request)
    except Exception as exc:
        services.evaluation.log_failure("booking_api_error", {"error": str(exc), "action": "book"})
        raise HTTPException(status_code=503, detail="Could not create booking.") from exc

