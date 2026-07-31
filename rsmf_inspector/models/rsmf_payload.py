from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Participant:
    id: str
    display: str = ""
    email: str = ""
    avatar: str = ""
    account_id: str = ""

@dataclass
class AttachmentItem:
    id: str
    display_name: str
    size: int = 0
    mime_type: str = ""
    archive_path: str = ""

@dataclass
class MessageEvent:
    id: str
    type: str = "message"
    body: str = ""
    timestamp: str = ""
    participant: str = ""
    direction: str = ""  # "incoming" or "outgoing"
    reactions: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Any] = field(default_factory=list)

@dataclass
class RSMFPayload:
    file_path: str
    file_name: str
    version: str = "2.0.0"
    participants: List[Participant] = field(default_factory=list)
    events: List[MessageEvent] = field(default_factory=list)
    attachments: List[AttachmentItem] = field(default_factory=list)
    raw_json_str: str = ""
    manifest_name: str = ""
    date_range_str: str = "N/A"
    
    # EML Envelope Metadata
    eml_subject: str = ""
    eml_from: str = ""
    eml_to: str = ""
    
    @property
    def participant_count(self) -> int:
        return len(self.participants)
    
    @property
    def event_count(self) -> int:
        return len(self.events)
    
    @property
    def attachment_count(self) -> int:
        return len(self.attachments)
