from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class URLScanRequest(BaseModel):
    url: str


class ScanJobInitResponse(BaseModel):
    scan_id: str
    message: str


class ScanJobStatus(BaseModel):
    scan_id: str
    status: str
    current_step: str
    logs: List[str]
    result: Optional[Dict[str, Any]] = None
