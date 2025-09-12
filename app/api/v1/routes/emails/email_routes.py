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
from app.models.schemas.task_comment import TaskCommentInDB

from app.services.organization_service import get_organization_name
from app.services.user_service import get_user_details_by_username

from datetime import datetime

router = APIRouter()

logger = get_logger(__name__)

# default_sender: str = os.getenv("DEFAULT_SENDER_EMAIL", "no-reply@tasksmate.com")
default_sender: str = os.getenv("DEFAULT_SENDER_EMAIL", "dharmatej.nandikanti@indrasol.com")

from_email: Email = Email(default_sender, 'TasksMate Team')

default_web_link:str = os.getenv("DEFAULT_WEB_LINK","https://tasksmate.indrasol.com")


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
    Sends an invitation email to join an organization on TasksMate.
    """
    try:
        email = invite_data.get("email")
        name = invite_data.get("name") or (email.split("@")[0] if email else "there")
        invited_by = invite_data.get("invited_by") or "a TasksMate user"
        invite_link = invite_data.get("invite_link") or default_web_link

        # Get org name
        org_name = invite_data.get("org_name")
        if not org_name and invite_data.get("org_id"):
            org_info = await get_organization_name(invite_data.get("org_id"))
            org_name = org_info.data.get("name") if org_info and org_info.data else "an organization"

        # Construct invite link
        full_link = invite_link
        if not invite_data.get("invite_link"):
            full_link += "/org"

        subject = f"TasksMate - Invited to Join {org_name}"

        greeting = f"<p>Hi <strong>{name}</strong>,</p>"
        body = (
            f"<strong>{invited_by}</strong> has invited you to join their workspace "
            f"<strong>{org_name}</strong> on <strong>TasksMate</strong> — a collaborative task management platform.<br><br>"
            f"Accept the invitation to start managing tasks, sharing progress, and collaborating with your team more effectively.<br><br>"
            f"<strong>Note:</strong> This invite link may expire soon for security reasons. If you were not expecting this invite, feel free to ignore this message."
        )

        html_content = generate_email_html(
            title=f"Join {org_name} on TasksMate",
            greeting=greeting,
            body=body,
            cta_text="Accept Your Invite",
            cta_link=full_link,
        )

        return await send_mail_to_user(email, subject, html_content)

    except Exception as e:
        logger.error(f"Error sending organization invite email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send invitation email.")

@router.post("/send-task-assignment-email")
async def send_task_assignment_email(task_data: TaskInDB):
    """
    Sends an email to notify a user that a task has been assigned to them.
    """
    try:
        assignee = task_data.get("assignee")
        if not assignee:
            raise ValueError("Assignee username is required.")

        user = await get_user_details_by_username(assignee)
        email = user.get("email")
        task_title = task_data.get("title") or "a new task"
        task_id = task_data.get("task_id")
        org_id = task_data.get("org_id")

        invited_by = task_data.get("updated_by") or task_data.get("created_by") or "a TasksMate user"
        base_link = task_data.get("invite_link") or default_web_link

        if assignee == invited_by:
            return {"success": False, "message": "Self assignment - no mail sent."}

        # Build detailed task link
        full_link = base_link
        if not task_data.get("invite_link") and task_id:
            full_link += f"/tasks/{task_id}"
            if org_id:
                full_link += f"?org_id={org_id}"

        subject = f"TasksMate - You've been assigned a task"

        greeting = f"<p>Hi <strong>{assignee}</strong>,</p>"
        body = (
            f"<strong>{invited_by}</strong> just assigned you a new task: <strong>{task_title}</strong> on <strong>TasksMate</strong>.<br><br>"
            f"You can now track its progress, collaborate, and mark it complete directly from your workspace.<br><br>"
            f"<strong>Stay organized and productive!</strong><br>"
            f"If you have any questions, feel free to reach out to your team or reply to this email."
        )

        html_content = generate_email_html(
            title="Task Assigned",
            greeting=greeting,
            body=body,
            cta_text="View Task",
            cta_link=full_link,
        )

        return await send_mail_to_user(email, subject, html_content)

    except Exception as e:
        logger.error(f"Error sending task assignment email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send task assignment email.")


@router.post("/send-task-comment-email")
async def send_task_comment_email(task_data: TaskCommentInDB):
    """
    Sends an email to notify a user that a task has been assigned to them.
    """

    # Loop through Mentions and send the email accordingly
    try:
        if not task_data.get("mentions"):
            return {"success": False, "message": "No mentions found in the task comment."}

        task_title = task_data.get("task_title") or "a new task"
        task_id = task_data.get("task_id")
        org_id = task_data.get("org_id")

        invited_by = task_data.get("updated_by") or task_data.get("created_by") or "a TasksMate user"
        base_link = task_data.get("invite_link") or default_web_link

        # Build detailed task link
        full_link = base_link
        if not task_data.get("invite_link") and task_id:
            full_link += f"/tasks/{task_id}"
            if org_id:
                full_link += f"?org_id={org_id}"


        for mention in task_data.get("mentions"):
            try:
                assignee = mention.get("username") or mention.get("email")
                email = mention.get("email")
                

                if assignee == invited_by:
                    return {"success": False, "message": "Self assignment - no mail sent."}

                

                subject = f"TasksMate - You've been mentioned in a task comment"

                greeting = f"<p>Hi <strong>{assignee}</strong>,</p>"
                body = (
                    f"<strong>{invited_by}</strong> just commented on a task: <strong>{task_title}</strong> on <strong>TasksMate</strong>.<br><br>"
                    f"The comment reads: <br> <strong>{task_data.get('comment') or task_data.get('content')}</strong>.<br><br>"
                    f"You can now track its progress, collaborate, and mark it complete directly from your workspace.<br><br>"
                    f"<strong>Stay organized and productive!</strong><br>"
                    f"If you have any questions, feel free to reach out to your team or reply to this email."
                )

                html_content = generate_email_html(
                    title="Comment on Task",
                    greeting=greeting,
                    body=body,
                    cta_text="View Task",
                    cta_link=full_link,
                )

                return await send_mail_to_user(email, subject, html_content)

            except Exception as e:
                logger.error(f"Error sending task assignment email: {str(e)}")
                # raise HTTPException(status_code=500, detail="Failed to send task assignment email.")
            
    except Exception as e:
        logger.error(f"Error sending task comment email: {str(e)}")
        # raise HTTPException(status_code=500, detail="Failed to send task comment email.")

    return {"success": True, "message": "Task comment email sent successfully"}


def generate_email_html(title: str, greeting: str, body: str, cta_text: str, cta_link: str) -> str:
    year = datetime.now().year
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <meta name="color-scheme" content="light dark">
        <style>
            :root {{ color-scheme: light dark; }}
            body {{
                background-color: #f6f8fa;
                color: #333;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #fff;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }}
            @media (prefers-color-scheme: dark) {{
                body {{ background-color: #0d1117; color: #c9d1d9; }}
                .container {{ background-color: #161b22; box-shadow: 0 0 0 1px #30363d; }}
                .button {{ background-color: #238636 !important; }}
                a.button {{ color: white !important; }}
            }}
            h2 {{ margin-top: 0; }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #4e6eff;
                color: #fff;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 20px;
            }}
            .footer {{
                font-size: 12px;
                color: #888;
                margin-top: 40px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>{title}</h2>
            {greeting}
            <p>{body}</p>
            <a href="{cta_link}" class="button">{cta_text}</a>
            <p>If the button above doesn't work, you can also copy and paste this link into your browser:<br>
            <a href="{cta_link}">{cta_link}</a></p>
            <div class="footer">
                &copy; {year} TasksMate &mdash; Empowering teams to get things done.<br />
                Need help? Contact us at <a href="mailto:support-tasksmate@indrasol.com">support-tasksmate@indrasol.com</a>
            </div>
        </div>
    </body>
    </html>
    '''

