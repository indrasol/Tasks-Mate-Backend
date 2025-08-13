from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.config.settings import SENDGRID_API_KEY
from app.utils.logger import get_logger

from app.models.schemas.organization_invite import OrganizationInviteInDB

from app.services.organization_service import get_organization_name

router = APIRouter()

logger = get_logger(__name__)

@router.post("/send-org-invite-email")
async def send_org_invite_email(invite_data: OrganizationInviteInDB):
    """
    Send an organization invite email using SendGrid.
    Expects invite_data to contain: email, name, org_name, invite_link, invited_by
    """
    try:
        if not SENDGRID_API_KEY:
            raise ValueError("SendGrid API key is not configured")
            
        sg = SendGridAPIClient(SENDGRID_API_KEY)

        # name = "there" if not invite_data.email else invite_data.email.split('@')[0]
        # org_name = invite_data.org_id or "TasksMate"
        # invite_link = "https://tasksmate.com"
        # invited_by = invite_data.invited_by or "a TasksMate user"
        # email = invite_data.email

        email = invite_data.get("email")
        name = invite_data.get("name") or (email.split('@')[0] if email else "there") 

        if invite_data.get("org_id"):
            org_name = await get_organization_name(invite_data.get("org_id"))
            if org_name and org_name.data and 'name' in org_name.data:
                org_name = org_name.data['name']

        org_name = org_name or invite_data.get("org_name") or "TasksMate"
        invite_link = invite_data.get("invite_link") or "https://mytasksmate.netlify.app"
        invited_by = invite_data.get("invited_by") or "a TasksMate user"


        message = Mail(
            from_email=Email('dharmatej.nandikanti@indrasol.com', 'TasksMate Team'),
            to_emails=To(email),
            subject=f"You've been invited to join {org_name} on TasksMate!",
            html_content=Content(
                'text/html',
                f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #2563eb;">Invitation to join {org_name}</h1>
                    <p>Hi {name},</p>
                    <p>
                        <strong>{invited_by}</strong> has invited you to join <strong>{org_name}</strong> on TasksMate.
                    </p>
                    <p>
                        Click the button below to Login/Signup and accept the invitation.
                    </p>
                    <p style="text-align: center; margin: 24px 0;">
                        <a href="{invite_link}" style="background: #2563eb; color: #fff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                            Open TasksMate
                        </a>
                    </p>
                    <p>
                        If you have any questions, feel free to reply to this email.
                    </p>
                    <hr style="margin: 20px 0;">
                    <p style="font-size: 12px; color: #666;">
                        If you did not expect this invitation, you can safely ignore this email.
                    </p>
                </div>
                '''
            )
        )
        
        response = sg.send(message)
        # logger.info(f"SendGrid Response Status: {response.status_code}")
        # logger.info(f"SendGrid Response Headers: {response.headers}")
        # logger.info(f"SendGrid Response Body: {response.body}")
        logger.info(f"Organization invite email sent successfully to {email}")
        
        return {"success": True, "message": "Organization invite email sent successfully"}
    except Exception as e:
        logger.error(f"Error sending organization invite email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))