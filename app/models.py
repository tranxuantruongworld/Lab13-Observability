from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


@dataclass
class EmailMessage:
    user_email: str
    content: str


class EventType(str, Enum):
    DONE = 'done'
    EMAIL_MESSAGE = 'email_message'
    DISCARD_SPAM = 'discard_spam'
    ERROR = 'error'

    GET_ORDER_INFORMATION = 'get_order_information'
    ORDER_INFORMATION = 'order_infomation'

    PROCESS_REFUND = 'process_refund'
    PROCESS_REFUND_SUCESS = 'process_refund_success'
    REJECT_REFUND = 'reject_refund'

    ESCALATE_TECHNICAL_SUPPORT = 'escalate_technical_support'
    TECHNICAL_SUPPORT_ANSWER = 'technical_support_answer'

    REQUEST_CLARIFICATION = 'request_clarification'
    CLARIFICATION_RESPONSE = 'clarification_response'

    REQUEST_HUMAN_APPROVAL = 'request_human_approval'
    HUMAN_DECISION = 'human_decision'


class Event(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    thread_id: UUID = Field(foreign_key='thread.id')

    type: EventType = Field(...)
    data: object | str = Field(sa_column=Column(JSON))
    # data: (
    #     DiscardSpam
    #     | DoneForNow
    #     | EscalateTechnicalSupport
    #     | GetOrderInformation
    #     | ProcessRefund
    #     | RejectRefund
    #     | RequestClarification
    #     | RequestHumanApproval
    #     | EmailMessage
    #     | str
    # ) = Field(sa_column=Column(JSON))

    thread: 'Thread' = Relationship(back_populates='events')


class Thread(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticket_id: UUID = Field(foreign_key='ticket.id', unique=True)

    events: list[Event] = Relationship(back_populates='thread')
    ticket: 'Ticket' = Relationship(back_populates='thread')


class TicketStatus(str, Enum):
    OPEN = 'open'
    PENDING_APPROVAL = 'pending_approval'
    RESOLVED = 'resolved'
    ESCALATED = 'escalated'


class OrderStatus(str, Enum):
    PENDING = 'pending'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    REFUNDED = 'refunded'


class Ticket(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_email: str
    content: str
    status: TicketStatus = Field(default=TicketStatus.OPEN)
    agent_step: str | None = None

    # Relationships
    thread: Thread = Relationship(back_populates='ticket')

    # Optional relationship to Order
    order_id: str | None = Field(default=None, foreign_key='order.id')
    order: 'Order' = Relationship(back_populates='tickets')

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Order(SQLModel, table=True):
    id: str = Field(primary_key=True)
    customer_email: str
    total_amount: float
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    items: str  # Simplified as a comma-separated string for MVP

    tickets: list[Ticket] | None = Relationship(back_populates='order')


@dataclass
class RefundProcessError:
    order_id: str
    reason: str


@dataclass
class RefundProcessSuccess:
    order_id: str
    amount: float
    reason: str
