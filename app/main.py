import os
from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from langfuse import get_client, observe
from sqlmodel import Session, SQLModel, create_engine, select
from structlog.contextvars import bind_contextvars

from app.agent import run_agent_loop
from app.logging_config import configure_logging, get_logger
from app.middleware import CorrelationIdMiddleware
from app.models import (
    Event,
    EventType,
    Order,
    OrderStatus,
    Thread,
    Ticket,
    TicketStatus,
)
from app.pii import hash_user_id

load_dotenv()

configure_logging()


logger = get_logger()

# Initialize observability
langfuse = get_client()

sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'

engine = create_engine(sqlite_url, connect_args={'check_same_thread': False})


def _create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Seed data if empty
        if not session.exec(select(Order)).first():
            order1 = Order(
                id='ORD-001',
                customer_email='alice@example.com',
                total_amount=49.99,
                status=OrderStatus.DELIVERED,
                items='Blue T-Shirt',
            )
            order2 = Order(
                id='ORD-002',
                customer_email='bob@example.com',
                total_amount=129.99,
                status=OrderStatus.SHIPPED,
                items='Mechanical Keyboard',
            )
            session.add(order1)
            session.add(order2)
            session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _create_db_and_tables()
    yield


app = FastAPI(title='Resolve-It API', lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)


def get_session():
    with Session(engine) as session:
        yield session


@app.post('/tickets', response_model=Ticket)
@observe()
def create_ticket(
    customer_email: str,
    content: str,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
):
    ticket = Ticket(
        customer_email=customer_email,
        content=content,
    )
    session.add(ticket)
    session.flush()  # Ensure ticket.id is populated

    # Bind enrichment fields
    bind_contextvars(
        user_id_hash=hash_user_id(customer_email),
        session_id=str(ticket.id),
        feature="ticket_creation"
    )

    logger.info(
        event="ticket_created",
        payload={"ticket_id": str(ticket.id), "content": content},
    )

    # Link all future traces for this ticket into one session
    langfuse.update_current_generation(
        name='new_ticket',
        metadata={'correlation_id': str(ticket.id), 'user_id': customer_email},
    )

    # Initialize the thread relationship
    ticket.thread = Thread(ticket_id=ticket.id)
    ticket.thread.events = [
        Event(
            thread_id=ticket.thread.id,
            type=EventType.EMAIL_MESSAGE,
            data={
                'user_email': customer_email,
                'content': content,
            },
        ),
    ]
    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    # Factor 6: Launch/Pause/Resume with simple APIs
    background_tasks.add_task(run_agent_loop, ticket.id, engine)

    return ticket


@app.post('/tickets/{ticket_id}/resume', response_model=Ticket)
@observe()
def resume_ticket(
    ticket_id: UUID,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
):
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        logger.error(event="ticket_resume_failed", error_type="not_found", payload={"ticket_id": str(ticket_id)})
        raise HTTPException(status_code=404, detail='Ticket not found')

    # Bind enrichment fields
    bind_contextvars(
        user_id_hash=hash_user_id(ticket.customer_email),
        session_id=str(ticket.id),
        feature="ticket_resume"
    )

    logger.info(event="ticket_resumed", payload={"ticket_id": str(ticket_id)})

    langfuse.update_current_span(
        name='resume_ticket',
        metadata={'correlation_id': ticket_id},
    )

    if ticket.status != TicketStatus.PENDING_APPROVAL:
        logger.warning("Ticket not pending approval", event="ticket_resume_invalid_state", payload={"ticket_id": str(ticket_id), "status": ticket.status})
        raise HTTPException(status_code=400, detail='Ticket is not pending approval')

    ticket.status = TicketStatus.OPEN

    # Add human decision event to the thread
    event = Event(
        thread_id=ticket.thread.id,
        type=EventType.HUMAN_DECISION,
        data='Human approved the request.',
    )
    ticket.thread.events.append(event)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    # Resume the loop
    background_tasks.add_task(run_agent_loop, ticket.id, engine)

    return ticket


@app.get('/tickets', response_model=list[Ticket])
@observe(name='list_tickets')
def list_tickets(session: Annotated[Session, Depends(get_session)]) -> Sequence[Ticket]:
    bind_contextvars(feature="ticket_list")
    tickets = session.exec(select(Ticket)).all()
    logger.info(event="tickets_listed", payload={"count": len(tickets)})
    return tickets


@app.get('/tickets/{ticket_id}', response_model=Ticket)
@observe(name='')
def get_ticket(
    ticket_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        logger.error(event="ticket_get_failed", error_type="not_found", payload={"ticket_id": str(ticket_id)})
        raise HTTPException(status_code=404, detail='Ticket not found')

    # Bind enrichment fields
    bind_contextvars(
        user_id_hash=hash_user_id(ticket.customer_email),
        session_id=str(ticket.id),
        feature="ticket_get"
    )

    langfuse.update_current_span(
        name='get_ticket',
        metadata={'correlation_id': ticket_id},
    )
    
    logger.info(event="ticket_retrieved", payload={"ticket_id": str(ticket_id)})
    return ticket


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)
