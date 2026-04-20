from dataclasses import asdict
from uuid import UUID

from baml_py import Collector
from dotenv import load_dotenv
from langfuse import get_client, observe, propagate_attributes
from sqlalchemy.engine import Engine
from sqlmodel import Session
from structlog.contextvars import bind_contextvars

from app.baml_client.async_client import b
from app.baml_client.types import (
    DiscardSpam,
    DoneForNow,
    EscalateTechnicalSupport,
    GetOrderInformation,
    Intent,
    ProcessRefund,
    RejectRefund,
    RequestClarification,
    RequestHumanApproval,
)
from app.logging_config import get_logger
from app.models import (
    Event,
    EventType,
    Order,
    OrderStatus,
    RefundProcessError,
    RefundProcessSuccess,
    Ticket,
    TicketStatus,
)
from app.pii import hash_user_id
from app.utils import thread_to_prompt

load_dotenv()

langfuse = get_client()
collector = Collector(name='metrics-collector')
logger = get_logger()


@observe(as_type='tool', name='get_order_details')
def get_order_details(order_id: str, session: Session) -> Order | None:
    bind_contextvars(feature="tool_get_order_details")
    logger.info(event="tool_get_order_details", tool_name="get_order_details", payload={"order_id": order_id})
    return session.get(Order, order_id)


@observe(as_type='tool', name='process_refund')
def process_refund(
    order_id: str,
    amount: float,
    reason: str,
    session: Session,
) -> RefundProcessSuccess | RefundProcessError:
    bind_contextvars(feature="tool_process_refund")
    logger.info(event="tool_process_refund", tool_name="process_refund", payload={"order_id": order_id, "amount": amount, "reason": reason})
    order = session.get(Order, order_id)

    if not order:
        logger.error(event="tool_process_refund_failed", tool_name="process_refund", error_type="not_found", payload={"order_id": order_id})
        return RefundProcessError(
            order_id=order_id,
            reason=f'Error: Order {order_id} not found.',
        )

    if amount > order.total_amount:
        logger.error(event="tool_process_refund_failed", tool_name="process_refund", error_type="validation_error", payload={"order_id": order_id, "amount": amount, "total": order.total_amount})
        return RefundProcessError(
            order_id=order_id,
            reason=f'Error: Refund amount {amount} exceeds order total {order.total_amount}.',
        )

    order.status = OrderStatus.REFUNDED
    session.add(order)
    session.commit()
    logger.info(event="tool_process_refund_success", tool_name="process_refund", payload={"order_id": order_id, "amount": amount})
    return RefundProcessSuccess(order_id=order_id, amount=amount, reason=reason)


@observe(name='agent_action', as_type='span')
def _perform_action(action: Intent, ticket: Ticket, session: Session) -> bool:
    """Perform an action and append resulted event to the thread.

    Returns weather the agent loop should stop.
    """
    thread = ticket.thread
    # Record the intent for business distribution metrics
    langfuse.update_current_span(
        metadata={'intent_data': action.model_dump()},
    )

    match action:
        case GetOrderInformation():
            thread.events.append(
                Event(
                    thread_id=thread.id,
                    type=EventType.GET_ORDER_INFORMATION,
                    data=action.model_dump(),
                ),
            )

            order = get_order_details(action.order_id, session)
            if order is None:
                # Log as a soft failure in observability
                langfuse.update_current_span(
                    level='WARNING',
                    status_message=f'Order {action.order_id} not found',
                )
                thread.events.append(
                    Event(
                        thread_id=thread.id,
                        type=EventType.ERROR,
                        data=f'Order with id={action.order_id} not found.',
                    ),
                )
            else:
                thread.events.append(
                    Event(
                        thread_id=thread.id,
                        type=EventType.ORDER_INFORMATION,
                        data=order.model_dump(),
                    ),
                )
            return True

        case EscalateTechnicalSupport():
            # Track escalation rate as a business metric
            langfuse.score_current_span(
                name='escalation',
                value=0,
                comment='Technical support required',
                data_type='BOOLEAN',
            )
            thread.events.append(
                Event(
                    thread_id=thread.id,
                    type=EventType.ESCALATE_TECHNICAL_SUPPORT,
                    data=action.model_dump(),
                ),
            )
            ticket.status = TicketStatus.ESCALATED
            return False

        case RequestHumanApproval():
            langfuse.score_current_span(
                name='human_intervention',
                value=1,
                data_type='BOOLEAN',
            )
            thread.events.append(
                Event(
                    thread_id=thread.id,
                    type=EventType.REQUEST_HUMAN_APPROVAL,
                    data=action.model_dump(),
                ),
            )
            ticket.status = TicketStatus.PENDING_APPROVAL
            return False

        case ProcessRefund():
            thread.events.append(
                Event(
                    thread_id=thread.id,
                    type=EventType.PROCESS_REFUND,
                    data=action.model_dump(),
                ),
            )
            process_result = process_refund(
                order_id=action.order_id,
                amount=action.amount,
                reason=action.reason,
                session=session,
            )
            if isinstance(process_result, RefundProcessError):
                # Critical business failure metric
                langfuse.score_current_span(
                    name='refund_success',
                    value=0,
                    comment=process_result.reason,
                    data_type='BOOLEAN',
                )
                langfuse.update_current_span(
                    level='ERROR',
                    status_message=process_result.reason,
                )
                thread.events.append(
                    Event(
                        thread_id=thread.id,
                        type=EventType.ERROR,
                        data=asdict(process_result),
                    ),
                )
            else:
                # Business success metric
                langfuse.score_current_span(
                    name='refund_success',
                    value=1,
                    data_type='BOOLEAN',
                )
                thread.events.append(
                    Event(
                        thread_id=thread.id,
                        type=EventType.PROCESS_REFUND_SUCESS,
                        data=asdict(process_result),
                    ),
                )
            return True

        case RejectRefund():
            langfuse.score_current_span(
                name='refund_success',
                value=0,
                data_type='BOOLEAN',
            )
            thread.events.append(
                Event(
                    thread_id=thread.id,
                    type=EventType.REJECT_REFUND,
                    data=action.model_dump(),
                ),
            )
            return True

        case RequestClarification():
            thread.events.append(
                Event(
                    thread_id=thread.id,
                    type=EventType.REQUEST_CLARIFICATION,
                    data=action.model_dump(),
                ),
            )
            return False

        case DiscardSpam():
            langfuse.score_current_span(
                name='spam',
                value=1,
                comment='Spam discarded',
                data_type='BOOLEAN',
            )
            thread.events.append(
                Event(
                    thread_id=thread.id,
                    type=EventType.DISCARD_SPAM,
                    data=action.model_dump(),
                ),
            )
            ticket.status = TicketStatus.RESOLVED
            return False

        case DoneForNow():
            langfuse.score_current_span(
                name='ticket_close',
                value=1,
                data_type='BOOLEAN',
            )
            thread.events.append(
                Event(
                    thread_id=thread.id,
                    type=EventType.DONE,
                    data='Ticket closed.',
                ),
            )
            langfuse.flush()
            ticket.status = TicketStatus.RESOLVED
            return False


@observe(as_type='generation', name='agent_decision')
async def determine_next_step(input_: str) -> Intent:
    next_step = await b.DetermineNextStep(input_, baml_options={'collector': collector})
    if not collector.last:
        return next_step
    
    last_call = collector.last.calls[-1]
    usage = collector.last.usage
    
    logger.info(
        event="agent_decision",
        model=last_call.client_name,
        tokens_in=usage.input_tokens or 0,
        tokens_out=usage.output_tokens or 0,
        payload={"intent": next_step.__class__.__name__, "intent_data": next_step.model_dump()},
    )

    langfuse.update_current_generation(
        model=last_call.client_name,
        input=input_,
        output=collector.last.raw_llm_response,
        usage_details={
            'input': usage.input_tokens or 0,
            'output': usage.output_tokens or 0,
            'cached_input_tokens': usage.cached_input_tokens or 0,
        },
    )
    return next_step


@observe(name='run_agent_loop', as_type='agent')
async def run_agent_loop(ticket_id: UUID, engine: Engine) -> None:
    # Bind correlation_id for background task logging
    bind_contextvars(correlation_id=str(ticket_id))
    
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
        if not ticket:
            logger.error(event="agent_loop_failed", error_type="not_found", payload={"ticket_id": str(ticket_id)})
            return

        # Bind enrichment fields
        bind_contextvars(
            user_id_hash=hash_user_id(ticket.customer_email),
            session_id=str(ticket.id),
            feature="agent_loop"
        )
        
        logger.info(event="agent_loop_started", payload={"ticket_id": str(ticket_id)})

        # Simple limit to prevent infinite loops
        max_steps = 10
        with propagate_attributes(
            session_id=str(ticket.id),
            user_id=ticket.customer_email,
        ):
            for i in range(max_steps):
                logger.info(event="agent_loop_step", payload={"step": i, "ticket_id": str(ticket_id)})
                thread_prompt = thread_to_prompt(ticket.thread)

                next_step = await determine_next_step(thread_prompt)
                should_continue = _perform_action(next_step, ticket, session)

                session.add(ticket)
                session.commit()

                if not should_continue:
                    logger.info(event="agent_loop_finished", payload={"ticket_id": str(ticket_id), "status": ticket.status})
                    break
            else:
                logger.warning(event="agent_loop_max_steps", payload={"ticket_id": str(ticket_id)})
