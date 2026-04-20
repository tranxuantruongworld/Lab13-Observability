class DoneForNow {
  intent "done" @description(#"
    when the ticket is processed.
  "#)
}

class GetOrderInformation {
  intent "get_order_information"
  order_id string
}

class DiscardSpam {
  intent "discard_spam" @description(#"
    when the ticket is considered spam and need to be discarded.
  "#)
}

class ProcessRefund {
  intent "process_refund"
  order_id string
  amount float
  reason string
}

class RejectRefund {
  intent "reject_refund"
  order_id string
  reason string
}

class RequestClarification {
  intent "request_clarification"
  reason string
}

class EscalateTechnicalSupport {
  intent "escalate_technical_support"
  content string @description(#"
    a summary of the user's problem
  "#)
  user_email string
}

class RequestHumanApproval {
  intent "request_human_approval"
  reason string
  ticket_id string
}
   
type Intent = DoneForNow | GetOrderInformation | DiscardSpam | ProcessRefund | RejectRefund | RequestClarification | EscalateTechnicalSupport | RequestHumanApproval


function DetermineNextStep(thread: string) -> Intent {
  client CustomGemini
  prompt #"
    {{ _.role("system") }}
    
    You are a helpful assistant that resolving tickets regarding orders.
    You work diligently to ensure high user retention and satisfaction by following best practices
    and proper resolution procedures.
    
    Before process the user ticket, you should check:
    - The user intent (either order refund, technical problem, or spam).
    - Accept all order whose amount is not greater than $50, and reason is reasonable. Otherwise, request human approval.
    
    You can use tools like get_order_information, discard_spam, process_refund, reject_refund, and escalate_technical_support
    to process the ticket. For vague tickets, use request_clarification to get more information from human.
    
    Always think about what to do first, like:
    - Check order information
    - Request approval if needed

    {{ ctx.output_format }}
    
    {{ _.role("user") }}
    ---
    {{ thread }}
    ---
    
    What should the next step be?
  "#
}
