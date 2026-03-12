"""Utilities for mapping OpenSearch errors to user-friendly messages."""

OPENSEARCH_DISK_WATERMARK_ERROR_MESSAGE = (
    "OpenSearch is in read-only mode because disk usage exceeded the flood-stage "
    "watermark. Free up disk space on the OpenSearch volume and then clear the "
    "read-only block to restore search."
)


def is_opensearch_disk_watermark_error(error_message: str) -> bool:
    """Return True when an error looks like OpenSearch flood-stage disk pressure."""
    if not error_message:
        return False

    message = error_message.lower()
    indicators = (
        "flood-stage watermark",
        "disk usage exceeded",
        "cluster_block_exception",
        "read-only / allow delete",
        "read-only-allow-delete",
        "forbidden/12",
        "blocked by: [forbidden/12",
    )
    return any(indicator in message for indicator in indicators)


def normalize_opensearch_error_message(error_message: str) -> str:
    """Convert raw OpenSearch errors into user-facing messages when possible."""
    if is_opensearch_disk_watermark_error(error_message):
        return OPENSEARCH_DISK_WATERMARK_ERROR_MESSAGE
    return error_message
