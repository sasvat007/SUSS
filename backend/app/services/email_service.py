"""
Email Draft Service — uses OpenAI to generate professional emails for
payment deferrals and collection reminders.
"""

import logging
from app.config import settings

logger = logging.getLogger(__name__)


async def draft_deferral(obligation_id: str, reason: str, proposed_date: str) -> dict:
    prompt = (
        f"Write a professional and polite email requesting a payment deferral.\n"
        f"Reason: {reason}\n"
        f"Proposed new payment date: {proposed_date}\n"
        f"Keep it concise (under 200 words), professional, and maintain a positive relationship tone."
    )
    return await _generate_email(prompt, default_subject="Payment Deferral Request")


async def draft_reminder(client_name: str, amount: float, due_date: str) -> dict:
    prompt = (
        f"Write a friendly but firm payment reminder email.\n"
        f"Client: {client_name}\n"
        f"Amount due: ₹{amount:,.2f}\n"
        f"Due date: {due_date}\n"
        f"Keep it polite, professional, and under 150 words."
    )
    return await _generate_email(prompt, default_subject=f"Payment Reminder — ₹{amount:,.2f} Due")


async def _generate_email(prompt: str, default_subject: str) -> dict:
    if not settings.OPENAI_API_KEY:
        return {
            "subject": default_subject,
            "body": "[OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.]",
        }
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional business email writer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
        )
        body = resp.choices[0].message.content or ""
        # Try to extract subject from first line if the model includes it
        lines = body.strip().split("\n")
        subject = default_subject
        if lines and lines[0].lower().startswith("subject:"):
            subject = lines[0][8:].strip()
            body = "\n".join(lines[1:]).strip()
        return {"subject": subject, "body": body}
    except Exception as exc:
        logger.error("Email draft OpenAI error: %s", exc)
        return {"subject": default_subject, "body": "Email generation temporarily unavailable."}
