import pytest
from pydantic import ValidationError

from app.domain.schemas import (
    ProfileUpdateRequest,
    RatingParticipationUpdateRequest,
)


def test_profile_update_rejects_invalid_username() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdateRequest(username="bad!", participate_in_rating=True)


def test_rating_participation_update_accepts_boolean_toggle() -> None:
    payload = RatingParticipationUpdateRequest.model_validate({"participateInRating": False})

    assert payload.participate_in_rating is False


def test_profile_response_serializes_camel_case() -> None:
    payload = ProfileUpdateRequest(username="good_name", participate_in_rating=True)

    assert payload.model_dump(by_alias=True) == {
        "username": "good_name",
        "participateInRating": True,
    }
