"""Shared constants for the R0 interview record persistence boundary."""

DATABASE_URL_ENV = "DATABASE_URL"
API_DATABASE_PATH_ENV = "API_DATABASE_PATH"
DEFAULT_DATABASE_FILE = "api.sqlite3"
DEFAULT_DATABASE_DIR = "ai-for-interviewer"

DEFAULT_RECORD_SOURCE = "api"
DEFAULT_RECORD_VERSION = 1
DEFAULT_HISTORY_STATUS = "saved"

INTERVIEW_RECORDS_ROUTE_PREFIX = "/interview-records"
RECORD_ID_ROUTE = "/{record_id}"
RECORD_REVIEW_ROUTE = "/{record_id}/review"
RECORD_EXPORT_TRACE_ROUTE = "/{record_id}/export-trace"

TABLE_INTERVIEW_RECORDS = "interview_records"

FIELD_ID = "id"
FIELD_OWNER_ID = "owner_id"
FIELD_SOURCE = "source"
FIELD_VERSION = "version"
FIELD_PAYLOAD = "payload"
FIELD_PAYLOAD_JSON = "payload_json"
FIELD_CREATED_AT = "created_at"
FIELD_UPDATED_AT = "updated_at"

PAYLOAD_INTERVIEW = "interview"
PAYLOAD_REVIEW = "review"
PAYLOAD_EXPORT = "export"

RESPONSE_ITEMS = "items"
RESPONSE_STATUS = "status"
RESPONSE_REVIEW_AVAILABLE = "review_available"
RESPONSE_EXPORT_TRACE_AVAILABLE = "export_trace_available"

ERROR_INTERVIEW_RECORD_NOT_FOUND = "interview record not found"

SQL_COLUMNS = (
    FIELD_ID,
    FIELD_OWNER_ID,
    FIELD_SOURCE,
    FIELD_VERSION,
    FIELD_PAYLOAD_JSON,
    FIELD_CREATED_AT,
    FIELD_UPDATED_AT,
)
