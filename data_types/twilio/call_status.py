from enum import Enum

class CallStatus(str, Enum):
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no-answer"
    FAILED_TO_CONNECT = "failed-to-connect"
    CANCELLED = "cancelled"
    INCOMING = "incoming"