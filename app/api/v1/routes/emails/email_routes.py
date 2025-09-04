from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel, EmailStr, ValidationError

import os
from dotenv import load_dotenv

load_dotenv()
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.config.settings import SENDGRID_API_KEY
from app.utils.logger import get_logger

from app.models.schemas.organization_invite import OrganizationInviteInDB
from app.models.schemas.task import TaskInDB

from app.services.organization_service import get_organization_name
from app.services.user_service import get_user_details_by_username

from datetime import datetime

router = APIRouter()

logger = get_logger(__name__)

# default_sender: str = os.getenv("DEFAULT_SENDER_EMAIL", "no-reply@tasksmate.com")
default_sender: str = os.getenv("DEFAULT_SENDER_EMAIL", "dharmatej.nandikanti@indrasol.com")

from_email: Email = Email(default_sender, 'TasksMate Team')

default_web_link:str = os.getenv("DEFAULT_WEB_LINK","https://mytasksmate.netlify.app")


# class EmailValidator(BaseModel):
#     email: EmailStr

async def send_mail_to_user(email: str, subject: str, html_content: str):
    try:
        # ✅ Validate email format using Pydantic
        # try:
        #     EmailValidator(email=default_sender)
        # except ValidationError:
        #     logger.warning(f"Invalid email format: {default_sender}")
        #     raise HTTPException(status_code=400, detail="Invalid email address format.")
        

        # # ✅ Validate email format using Pydantic
        # try:
        #     EmailValidator(email=email)
        # except ValidationError:
        #     logger.warning(f"Invalid email format: {email}")
        #     raise HTTPException(status_code=400, detail="Invalid email address format.")

        if not SENDGRID_API_KEY:
            raise HTTPException(status_code=500, detail="SendGrid API key not configured.")

        sg = SendGridAPIClient(SENDGRID_API_KEY)

        message = Mail(
            from_email=from_email,
            to_emails=To(email),
            subject=subject,
            html_content=Content('text/html', html_content)
        )

        response = sg.send(message)
        logger.info(f"SendGrid Status: {response.status_code}")
        logger.debug(f"SendGrid Response Body: {response.body}")
        logger.debug(f"SendGrid Response Headers: {response.headers}")

        if response.status_code >= 400:
            raise HTTPException(status_code=500, detail="Failed to send email via SendGrid.")

        return {"success": True, "message": "Email sent successfully"}

    except HTTPException:
        # Allow explicit HTTP exceptions to propagate cleanly
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending email to {email} from {default_sender}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error sending email to {email} from {default_sender}: {e}")


@router.post("/send-org-invite-email")
async def send_org_invite_email(invite_data: OrganizationInviteInDB):
    """
    Send an organization invite email using SendGrid.
    Expects invite_data to contain: email, name, org_name, invite_link, invited_by
    """
    try:
        
        email = invite_data.get("email")
        name = invite_data.get("name") or (email.split('@')[0] if email else "there") 

        if invite_data.get("org_name"):
            org_name = invite_data.get("org_name")
        elif invite_data.get("org_id"):
            org_name = await get_organization_name(invite_data.get("org_id"))
            if org_name and org_name.data and 'name' in org_name.data:
                org_name = org_name.data['name']

        invite_link = invite_data.get("invite_link") or default_web_link
        invited_by = invite_data.get("invited_by") or "a TasksMate user"

        additional_link = ""
        
        if invite_data.get("invite_link"):
            additional_link = ""
        else:
            additional_link = "/org"

        # Prefer dynamic sender (inviter's email) if provided; fall back to env/default
        # inviter_email = invite_data.get("invited_by_email")
        # If inviter email is provided, set it as reply-to to facilitate direct responses
        # try:
        #     if inviter_email:
        #         message.reply_to = Email(inviter_email)
        # except Exception:
        #     pass

        year = datetime.now().year

        subject = f"🎉 Invitation to Join {org_name} on TasksMate"
        html_content = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <title>Your Invitation to Join TasksMate</title>
            <meta name="color-scheme" content="light dark" />
            <style>
            :root {{
                color-scheme: light dark;
            }}
            body {{
                margin: 0;
                padding: 0;
                background-color: #f6f8fa;
                color: #333;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            }}
            @media (prefers-color-scheme: dark) {{
                body {{
                background-color: #0d1117;
                color: #c9d1d9;
                }}
                .container {{
                background-color: #161b22;
                color: #c9d1d9;
                box-shadow: 0 0 0 1px #30363d;
                }}
                .button {{
                background-color: #238636 !important;
                }}
                a.button {{
                color: white !important;
                }}
            }}
            h2 {{
                color: inherit;
            }}
            .button {{
                display: inline-block;
                padding: 12px 20px;
                background-color: #4e6eff;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                margin-top: 12px;
                font-weight: bold;
            }}
            .footer {{
                font-size: 12px;
                text-align: center;
                color: #888;
                margin-top: 40px;
            }}
            </style>
        </head>
        <body>
            <div class="container">
            <h2>🎉 Invitation to Join {org_name}</h2>
            <p>Hi <strong>{name}</strong>,</p>
            <p>
                <strong>{invited_by}</strong> has invited you to join <strong>{org_name}</strong> on TasksMate.
            </p>
            <p>Click the button below to Login/Signup and accept the invitation:</p>
            <a href="{invite_link}{additional_link}" class="button">Open TasksMate</a>
            <p>This invitation link will expire soon. If you did not expect this invite, please ignore this email.</p>
            <div class="footer">
                &copy; {year} TasksMate<br />
                <a href="mailto:support-tasksmate@indrasol.com">support-tasksmate@indrasol.com</a>
            </div>
            </div>
        </body>
        </html>
        '''        

        return await send_mail_to_user(email, subject, html_content)
    except Exception as e:
        logger.error(f"Error sending organization invite email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Send Task Assignment Mail
@router.post("/send-task-assignment-email")
async def send_task_assignment_email(task_data: TaskInDB):
    """
    Send a task assignment email using SendGrid.
    Expects task_data to contain: email, name, task_name, task_link, assigned_by
    """
    try:
        
        if not task_data.get("assignee"):
            raise ValueError("Assignee is required")

        user_details = await get_user_details_by_username(task_data.get("assignee"))
        email = user_details.get("email")
        assignee = task_data.get("assignee")
        title = task_data.get("title")
        
        invite_link = task_data.get("invite_link") or default_web_link
        invited_by = task_data.get("updated_by") or task_data.get("created_by") or "a TasksMate user"

        additional_link = ""

        if task_data.get("invite_link"):
            additional_link = ""
        else:
            if task_data.get("task_id"):
                if task_data.get("org_id"):
                    additional_link = f"/tasks/{task_data.get('task_id')}?org_id={task_data.get('org_id')}"
                else:
                    additional_link = f"/tasks/{task_data.get('task_id')}"

        # Prefer dynamic sender (inviter's email) if provided; fall back to env/default
        # inviter_email =  await get_user_details_by_username(task_data.get("updated_by"))
        # from_email = Email(inviter_email or default_sender, 'TasksMate Team')

       
        year = datetime.now().year

        subject = f"📝 New Task Assigned to You on TasksMate!"
        html_content = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <title>You've been assigned a task on TasksMate</title>
            <meta name="color-scheme" content="light dark" />
            <style>
            :root {{
                color-scheme: light dark;
            }}
            body {{
                margin: 0;
                padding: 0;
                background-color: #f6f8fa;
                color: #333;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            }}
            @media (prefers-color-scheme: dark) {{
                body {{
                background-color: #0d1117;
                color: #c9d1d9;
                }}
                .container {{
                background-color: #161b22;
                color: #c9d1d9;
                box-shadow: 0 0 0 1px #30363d;
                }}
                .button {{
                background-color: #238636 !important;
                }}
                a.button {{
                color: white !important;
                }}
            }}
            h2 {{
                color: inherit;
            }}
            .button {{
                display: inline-block;
                padding: 12px 20px;
                background-color: #4e6eff;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                margin-top: 12px;
                font-weight: bold;
            }}
            .footer {{
                font-size: 12px;
                text-align: center;
                color: #888;
                margin-top: 40px;
            }}
            </style>
        </head>
        <body>
            <div class="container">
            <h2>📝 New Task Assigned on TasksMate</h2>
            <p>Hi <strong>{assignee}</strong>,</p>
            <p>
                <strong>{invited_by}</strong> has assigned you a new task: <strong>{title}</strong> on TasksMate.
            </p>
            <p>
                Click the button below to log in and view your task:
            </p>
            <a href="{invite_link}{additional_link}" class="button">View Task</a>
            <div class="footer">
                &copy; {year} TasksMate<br />
                <a href="mailto:support-tasksmate@indrasol.com">support-tasksmate@indrasol.com</a>
            </div>
            </div>
        </body>
        </html>
        '''

        

        return await send_mail_to_user(email, subject, html_content)
    except Exception as e:
        logger.error(f"Error sending task assignment email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
