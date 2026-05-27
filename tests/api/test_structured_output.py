from app.application.llm.structured_output import (
    filter_untrusted_structured_metadata,
    normalize_structured_status,
)


def test_structured_status_ok_ready_done_and_missing_normalize_to_success() -> None:
    for value, warning in (
        ("ok", "status_ok_normalized"),
        ("ready", "status_ready_normalized"),
        ("done", "status_done_normalized"),
        (None, "status_missing_normalized"),
        ("", "status_missing_normalized"),
    ):
        status, warnings, errors = normalize_structured_status(value)

        assert status == "success"
        assert warning in warnings
        assert errors == ()


def test_structured_status_rejects_failed_and_unknown_values() -> None:
    failed_status, failed_warnings, failed_errors = normalize_structured_status("failed")
    unknown_status, unknown_warnings, unknown_errors = normalize_structured_status("maybe")

    assert failed_status is None
    assert failed_warnings == ()
    assert failed_errors[0].field == "status"
    assert failed_errors[0].code == "failed"
    assert unknown_status is None
    assert unknown_warnings == ()
    assert unknown_errors[0].field == "status"
    assert unknown_errors[0].code == "unsupported"


def test_filter_untrusted_structured_metadata_removes_provider_supplied_identity_fields() -> None:
    trusted, ignored = filter_untrusted_structured_metadata(
        {
            "generated_at": "2099-01-01T00:00:00Z",
            "model_name": "forged",
            "session_id": "forged_session",
            "job_id": "forged_job",
            "resume_id": "forged_resume",
            "quality_target": "6-9 leaves",
        }
    )

    assert trusted == {"quality_target": "6-9 leaves"}
    assert ignored == ("generated_at", "job_id", "model_name", "resume_id", "session_id")
