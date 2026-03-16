import pytest
from pydantic import ValidationError

from app.domain.schemas import ProfileUpdateRequest, RatingParticipationUpdateRequest, UpdateScoreRequest


def test_update_score_request_requires_identifier() -> None:
    with pytest.raises(ValidationError):
        UpdateScoreRequest(score=10)


def test_update_score_request_accepts_user_id() -> None:
    payload = UpdateScoreRequest(user_id=1, score=10)

    assert payload.user_id == 1
    assert payload.score == 10


def test_profile_update_rejects_invalid_username() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdateRequest(username="bad!", participate_in_rating=True)


def test_rating_participation_update_accepts_boolean_toggle() -> None:
    payload = RatingParticipationUpdateRequest(participate_in_rating=False)

    assert payload.participate_in_rating is False
