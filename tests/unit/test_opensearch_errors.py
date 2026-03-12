import json
import pytest

from api.chat import ChatBody, chat_endpoint
from api.search import SearchBody, search
from utils.opensearch_errors import (
    OPENSEARCH_DISK_WATERMARK_ERROR_MESSAGE,
    is_opensearch_disk_watermark_error,
    normalize_opensearch_error_message,
)


def test_detects_flood_stage_watermark_message():
    error_message = (
        "cluster_block_exception: index [documents] blocked by: "
        "[FORBIDDEN/12/index read-only / allow delete (api)]"
    )
    assert is_opensearch_disk_watermark_error(error_message) is True


def test_detects_explicit_disk_usage_threshold_message():
    error_message = "disk usage exceeded flood-stage watermark on one or more nodes"
    assert is_opensearch_disk_watermark_error(error_message) is True


def test_normalize_maps_disk_watermark_error_to_user_friendly_message():
    raw_message = "FORBIDDEN/12/index read-only / allow delete (api)"
    assert normalize_opensearch_error_message(raw_message) == OPENSEARCH_DISK_WATERMARK_ERROR_MESSAGE


def test_normalize_leaves_other_errors_unchanged():
    raw_message = "AuthenticationException(401, 'Unauthorized')"
    assert normalize_opensearch_error_message(raw_message) == raw_message


class _FailingSearchService:
    async def search(self, *_args, **_kwargs):
        raise RuntimeError(
            "cluster_block_exception: index [documents] blocked by: "
            "[FORBIDDEN/12/index read-only / allow delete (api)]"
        )


class _FailingChatService:
    async def chat(self, *_args, **_kwargs):
        raise RuntimeError(
            "disk usage exceeded flood-stage watermark on one or more nodes"
        )


class _TestUser:
    user_id = "test-user"
    jwt_token = "test-token"


@pytest.mark.asyncio
async def test_search_endpoint_returns_503_for_disk_watermark_errors():
    response = await search(
        SearchBody(query="*", limit=10),
        search_service=_FailingSearchService(),
        session_manager=None,
        user=_TestUser(),
    )
    body = json.loads(response.body.decode("utf-8"))
    assert response.status_code == 503
    assert body["error"] == OPENSEARCH_DISK_WATERMARK_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_chat_endpoint_returns_503_for_disk_watermark_errors():
    response = await chat_endpoint(
        ChatBody(prompt="hello", stream=False),
        chat_service=_FailingChatService(),
        session_manager=None,
        user=_TestUser(),
    )
    body = json.loads(response.body.decode("utf-8"))
    assert response.status_code == 503
    assert body["error"] == OPENSEARCH_DISK_WATERMARK_ERROR_MESSAGE
