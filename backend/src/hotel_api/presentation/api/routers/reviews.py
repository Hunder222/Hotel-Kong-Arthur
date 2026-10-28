"""`/api/v1/reviews`: list, create, read (K3). Handlers only call the service."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from hotel_api.business.domain.models import Season
from hotel_api.business.services.review_service import ReviewService
from hotel_api.presentation.api.dependencies import get_review_service
from hotel_api.presentation.api.schemas.bookings import RoomTypeName
from hotel_api.presentation.api.schemas.reviews import Review, ReviewInput, ReviewList

router = APIRouter(prefix="/api/v1/reviews", tags=["Reviews"])

ReviewId = Annotated[int, Path(ge=1)]


@router.get("", response_model=ReviewList, operation_id="listReviews")
def list_reviews(
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    season: Season | None = None,
    room_type: RoomTypeName | None = None,
    service: ReviewService = Depends(get_review_service),
) -> ReviewList:
    reviews = service.list(year=year, season=season, room_type=room_type)
    return ReviewList(items=[Review.from_model(r) for r in reviews])


@router.post("", response_model=Review, status_code=201, operation_id="createReview")
def create_review(
    body: ReviewInput, response: Response, service: ReviewService = Depends(get_review_service)
) -> Review:
    review = service.create(body.model_dump())
    response.headers["Location"] = f"/api/v1/reviews/{review.id}"
    return Review.from_model(review)


@router.get("/{review_id}", response_model=Review, operation_id="getReview")
def get_review(review_id: ReviewId, service: ReviewService = Depends(get_review_service)) -> Review:
    return Review.from_model(service.get(review_id))
