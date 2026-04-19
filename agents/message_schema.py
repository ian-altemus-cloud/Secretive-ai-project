from dataclasses import dataclass, field
from typing import Optional

@dataclass
class AgentJobMessage:
    """
    Message schema for the agent job queue.
    Published by the SQS consumer when booking intent is detected.
    Consumed by the agent worker Fargate service.
    """
    agent_type: str
    sender_id: str
    instagram_account_id: str
    parameters: dict

    def to_dict(self) -> dict:
        return {
            "agent_type": self.agent_type,
            "sender_id": self.sender_id,
            "instagram_account_id": self.instagram_account_id,
            "parameters": self.parameters
        }


@dataclass
class AgentResultMessage:
    """
    Message schema for the agent results queue.
    Published by the agent worker when availability check completes.
    Consumed by the SQS consumer for delivery to the customer.
    """
    agent_type: str
    sender_id: str
    instagram_account_id: str
    result: dict

    def to_dict(self) -> dict:
        return {
            "agent_type": self.agent_type,
            "sender_id": self.sender_id,
            "instagram_account_id": self.instagram_account_id,
            "result": self.result
        }