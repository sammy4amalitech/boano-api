from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError
import os
import json
import logging

from ...core.db.database import async_get_db
from ...core.config import settings
from fastapi import Depends

from ...crud.crud_users import crud_users
from ...models.user import UserCreateInternal, UserUpdateInternal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks",tags=["webhooks"])

# Get webhook secret from environment
WEBHOOK_SECRET = settings.CLERK_SIGNING_SECRET
if not WEBHOOK_SECRET:
    raise Exception("Missing CLERK_WEBHOOK_SECRET environment variable")

async def process_user_created(event_data: dict, db: AsyncSession):
    """Handle user.created event"""
    # Extract user data from the event
    email_addresses = event_data.get("email_addresses", [])
    primary_email_id = event_data.get("primary_email_address_id")
    email = next((e["email_address"] for e in email_addresses if e["id"] == primary_email_id), None)
    
    if not email:
        logger.error(f"No primary email found for user {event_data.get('id')}")
        return
    
    # Create user data
    user_data = {
        "name": f"{event_data.get('first_name', '')} {event_data.get('last_name', '')}".strip(),
        "username": event_data.get('username') or email.split('@')[0],
        "email": email,
        "profile_image_url": event_data.get('profile_image_url', 'https://www.gravatar.com/avatar?d=mp'),
        "uuid": str(event_data.get('id'))  # Ensure the ID is converted to string
    }
    
    try:
        user_create = UserCreateInternal(**user_data)
        await crud_users.create(db=db, object=user_create)
        logger.info(f"User created successfully: {user_data['email']}")
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}\nUser data: {user_data}")

async def process_user_updated(event_data: dict, db: AsyncSession):
    """Handle user.updated event"""
    user_id = event_data.get("id")
    
    # Get existing user
    db_user = await crud_users.get(db=db, uuid=user_id)
    if not db_user:
        error_msg = f"User not found for update: {user_id}"
        logger.error(error_msg)
        raise HTTPException(status_code=404, detail=error_msg)
    
    # Extract updated data
    email_addresses = event_data.get("email_addresses", [])
    primary_email_id = event_data.get("primary_email_address_id")
    email = next((e["email_address"] for e in email_addresses if e["id"] == primary_email_id), None)
    
    update_data = {
        "name": f"{event_data.get('first_name', '')} {event_data.get('last_name', '')}".strip(),
        "profile_image_url": event_data.get('profile_image_url')
    }
    
    if email:
        update_data["email"] = email
    
    if event_data.get('username'):
        update_data["username"] = event_data["username"]
    
    try:
        user_update = UserUpdateInternal(**update_data)
        await crud_users.update(db=db, object=user_update, uuid=user_id)
        logger.info(f"User updated successfully: {user_id}")
    except Exception as e:
        error_msg = f"Error updating user: {str(e)}"
        logger.error(f"{error_msg}\nUpdate data: {update_data}")
        raise HTTPException(status_code=500, detail=error_msg)

async def process_user_deleted(event_data: dict, db: AsyncSession):
    """Handle user.deleted event"""
    user_id = event_data.get("id")
    
    try:
        # Get existing user
        db_user = await crud_users.get(db=db, uuid=user_id)
        if not db_user:
            logger.error(f"User not found for deletion: {user_id}")
            return
            
        # Soft delete the user
        await crud_users.delete(db=db, uuid=user_id)
        logger.info(f"User deleted successfully: {user_id}")
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")


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