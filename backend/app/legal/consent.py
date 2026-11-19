from datetime import UTC, datetime


def record_consent(user_id, terms_version, privacy_version):

    return {
        "user_id": user_id,
        "terms_version": terms_version,
        "privacy_version": privacy_version,
        "timestamp": datetime.now(UTC),
    }
