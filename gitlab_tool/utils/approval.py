"""Human approval system for critical operations."""

import asyncio
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Approval request status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    """Approval request for a critical operation."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation: str
    description: str
    project: str
    details: dict = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ApprovalManager:
    """Manages approval requests for critical operations."""

    def __init__(self, timeout_seconds: int = 300):
        """Initialize approval manager."""
        self.timeout_seconds = timeout_seconds
        self._requests: dict[str, ApprovalRequest] = {}
        self._events: dict[str, asyncio.Event] = {}

    def create_request(
        self, operation: str, description: str, project: str, details: dict = None
    ) -> ApprovalRequest:
        """Create a new approval request."""
        request = ApprovalRequest(
            operation=operation,
            description=description,
            project=project,
            details=details or {},
            expires_at=datetime.utcnow() + timedelta(seconds=self.timeout_seconds),
        )

        self._requests[request.request_id] = request
        self._events[request.request_id] = asyncio.Event()

        return request

    async def wait_for_approval(self, request_id: str) -> ApprovalRequest:
        """Wait for approval or rejection."""
        if request_id not in self._requests:
            raise ValueError(f"Unknown approval request: {request_id}")

        request = self._requests[request_id]
        event = self._events[request_id]

        # Calculate timeout
        now = datetime.utcnow()
        if now >= request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            return request

        timeout = (request.expires_at - now).total_seconds()

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            request.status = ApprovalStatus.EXPIRED

        return request

    def approve(self, request_id: str) -> ApprovalRequest:
        """Approve a request."""
        if request_id not in self._requests:
            raise ValueError(f"Unknown approval request: {request_id}")

        request = self._requests[request_id]
        request.status = ApprovalStatus.APPROVED
        request.approved_at = datetime.utcnow()

        if request_id in self._events:
            self._events[request_id].set()

        return request

    def reject(self, request_id: str, reason: str = None) -> ApprovalRequest:
        """Reject a request."""
        if request_id not in self._requests:
            raise ValueError(f"Unknown approval request: {request_id}")

        request = self._requests[request_id]
        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reason

        if request_id in self._events:
            self._events[request_id].set()

        return request

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID."""
        return self._requests.get(request_id)

    def list_pending(self) -> list[ApprovalRequest]:
        """List all pending approval requests."""
        now = datetime.utcnow()
        pending = []

        for request in self._requests.values():
            if request.status == ApprovalStatus.PENDING:
                if now >= request.expires_at:
                    request.status = ApprovalStatus.EXPIRED
                else:
                    pending.append(request)

        return pending

    def cleanup_old_requests(self, max_age_seconds: int = 3600) -> int:
        """Clean up old requests."""
        cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        to_remove = [
            req_id
            for req_id, req in self._requests.items()
            if req.created_at < cutoff and req.status != ApprovalStatus.PENDING
        ]

        for req_id in to_remove:
            del self._requests[req_id]
            if req_id in self._events:
                del self._events[req_id]

        return len(to_remove)


# Global approval manager instance
_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """Get global approval manager instance."""
    global _approval_manager
    if _approval_manager is None:
        from gitlab_tool.config import get_settings

        settings = get_settings()
        _approval_manager = ApprovalManager(settings.approval_timeout_seconds)
    return _approval_manager


def set_approval_manager(manager: ApprovalManager) -> None:
    """Set global approval manager instance."""
    global _approval_manager
    _approval_manager = manager
