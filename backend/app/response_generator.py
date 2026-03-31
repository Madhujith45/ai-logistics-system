# app/response_generator.py

"""
Professional response generator for LogiAI.
Generates customer-friendly, enterprise-style messages
similar to Amazon/Flipkart support systems.
"""


def generate_professional_response(intent: str, policy_result: dict, order: dict = None) -> str:
    """
    Build a professional response string from the policy engine result.
    Falls back to the policy_result message if no special formatting is needed.
    """
    message = policy_result.get("message", "")

    eligibility = policy_result.get("eligibility")
    reason = policy_result.get("reason")
    next_steps = policy_result.get("next_steps") or []
    refund_options = policy_result.get("refund_options") or []
    pickup = policy_result.get("pickup")

    if message and any([
        eligibility is not None,
        reason,
        next_steps,
        refund_options,
        pickup,
        policy_result.get("return_status"),
        policy_result.get("refund_status"),
        policy_result.get("verification_status"),
    ]):
        lines = [message]
        if eligibility is not None:
            lines.append(f"Eligibility: {'Eligible' if eligibility else 'Not eligible'}")
        
        return_status = policy_result.get("return_status")
        if return_status:
            lines.append(f"Return Status: {return_status.replace('_', ' ').title()}")
            
        verification_status = policy_result.get("verification_status")
        if verification_status:
            lines.append(f"Verification Stage: {verification_status.replace('_', ' ').title()}")

        refund_status = policy_result.get("refund_status")
        if refund_status:
            lines.append(f"Refund Status: {refund_status.replace('_', ' ').title()}")

        if reason:
            lines.append(f"Reason: {reason}")
        if refund_options:
            lines.append(f"Refund options: {', '.join(refund_options)}")
        if pickup:
            lines.append(
                f"Pickup: {pickup.get('status', 'scheduled')} (attempts: {pickup.get('attempts', 0)})"
            )
        if next_steps:
            lines.append("Next steps:")
            for idx, step in enumerate(next_steps, 1):
                lines.append(f"{idx}. {step}")
        return "\n\n".join(lines)

    # If the policy engine already generated a detailed message, use it
    if message:
        return message

    # Fallback professional response per intent
    product_name = "your item"
    if order:
        product_name = order.get("product_name", "your item")

    fallback_messages = {
        "TRACK_ORDER": (
            f"We are currently looking up the status of your order. "
            f"Please provide your order ID so we can assist you better."
        ),
        "CANCEL_ORDER": (
            f"We understand you'd like to cancel your order. "
            f"Please provide your order ID and we'll check the eligibility for cancellation."
        ),
        "REFUND_REQUEST": (
            f"We have received your refund request. "
            f"Our team is reviewing the eligibility based on the return policy. "
            f"You will receive an update within 24 hours."
        ),
        "DAMAGED_PRODUCT": (
            f"We sincerely apologize for the inconvenience. "
            f"Your damage report has been logged and escalated to our quality team. "
            f"Please upload supporting images within 48 hours."
        ),
        "MISMATCH_PRODUCT": (
            f"We are sorry that you received an incorrect item. "
            f"A replacement process has been initiated. "
            f"Please upload images of the received product within 48 hours."
        ),
        "GENERAL_QUERY": (
            "Thank you for contacting LogiAI Support. "
            "We were unable to automatically process your request. "
            "Your query has been escalated to a support specialist who will respond within 24 hours."
        ),
    }

    return fallback_messages.get(intent, fallback_messages["GENERAL_QUERY"])
