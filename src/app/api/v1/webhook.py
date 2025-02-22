from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError
import os
import json
import logging

from ...core.db.database import async_get_db
from ...core.config import settings
from fastapi import Depends

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks",tags=["webhooks"])

# Get webhook secret from environment
WEBHOOK_SECRET = settings.CLERK_SIGNING_SECRET
if not WEBHOOK_SECRET:
    raise Exception("Missing CLERK_WEBHOOK_SECRET environment variable")

async def process_user_created(event_data: dict, db: AsyncSession):
    """Handle user.created event"""
    user_id = event_data.get("id")
    # Add your logic to sync user data with your database
    print(f"User created: {user_id}")

async def process_user_updated(event_data: dict, db: AsyncSession):
    """Handle user.updated event"""
    user_id = event_data.get("id")
    # Add your logic to update user data in your database
    print(f"User updated: {user_id}")

async def process_user_deleted(event_data: dict, db: AsyncSession):
    """Handle user.deleted event"""
    user_id = event_data.get("id")
    # Add your logic to handle user deletion in your database
    print(f"User deleted: {user_id}")

@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(async_get_db)
):
    # Get the raw payload
    payload = await request.body()
    payload_str = payload.decode()
    
    # Get Svix headers
    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp")
    svix_signature = request.headers.get("svix-signature")
    
    if not all([svix_id, svix_timestamp, svix_signature]):
        missing_headers = [header for header, value in {
            'svix-id': svix_id,
            'svix-timestamp': svix_timestamp,
            'svix-signature': svix_signature
        }.items() if not value]
        error_msg = f"Missing Svix headers: {', '.join(missing_headers)}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Create Svix webhook instance
    wh = Webhook(WEBHOOK_SECRET)
    try:
        # Verify the webhook payload
        event = wh.verify(payload_str, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        })
    except WebhookVerificationError as e:
        error_msg = f"Webhook verification failed: {str(e)}"
        logger.error(f"{error_msg}\nPayload: {payload_str[:200]}...\nHeaders: svix-id={svix_id}, svix-timestamp={svix_timestamp}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Process the event based on type
    event_type = event.get("type")
    event_data = event.get("data", {})
    
    if event_type == "user.created":
        await process_user_created(event_data, db)
    elif event_type == "user.updated":
        await process_user_updated(event_data, db)
    elif event_type == "user.deleted":
        await process_user_deleted(event_data, db)
    else:
        print(f"Unhandled event type: {event_type}")
    
    return {"message": "Webhook processed successfully"}