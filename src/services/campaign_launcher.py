"""Campaign launcher service for creating email tasks from recipients"""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.models import Campaign, EmailRecipient, EmailTemplate as EmailTemplateModel, Task
from src.services.email_template_engine import EmailTemplate


class CampaignLauncherService:
    """Service for launching email campaigns and generating tasks"""

    def __init__(self, db: Session):
        self.db = db

    def launch_campaign(
        self,
        campaign_id: UUID,
        template_id: Optional[UUID] = None,
        send_immediately: bool = True,
        scheduled_at: Optional[datetime] = None,
    ) -> Tuple[int, List[UUID]]:
        """
        Launch a campaign by creating email tasks for all recipients.
        
        Args:
            campaign_id: Campaign to launch
            template_id: Optional template to use (overrides campaign template)
            send_immediately: Whether to send immediately or schedule
            scheduled_at: Schedule time if not sending immediately
            
        Returns:
            Tuple of (total_recipients, list of created task IDs)
            
        Raises:
            ValueError: If campaign not found or has no recipients
        """
        # Get campaign
        campaign = self.db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get recipients
        recipients = (
            self.db.query(EmailRecipient)
            .filter(
                EmailRecipient.campaign_id == campaign_id,
                EmailRecipient.status == "PENDING"
            )
            .all()
        )

        if not recipients:
            raise ValueError(f"Campaign {campaign_id} has no pending recipients")

        # Get template (either provided or from campaign)
        template_subject = campaign.template_subject
        template_body = campaign.template_body

        if template_id:
            template = (
                self.db.query(EmailTemplateModel)
                .filter(EmailTemplateModel.email_template_id == template_id)
                .first()
            )
            if template:
                template_subject = template.subject
                template_body = template.body

        # Create email template engine
        try:
            engine = EmailTemplate(template_subject, template_body)
        except ValueError as e:
            raise ValueError(f"Invalid template syntax: {e}")

        # Create tasks for each recipient
        task_ids = []
        created_count = 0

        for recipient in recipients:
            try:
                # Validate and render template with recipient personalization
                is_valid, missing = engine.validate_variables(recipient.personalization)
                
                if not is_valid:
                    # Mark recipient as failed if missing required variables
                    recipient.status = "FAILED"
                    recipient.error_message = f"Missing required variables: {', '.join(missing)}"
                    continue

                # Render template
                subject, body = engine.render(recipient.personalization)

                # Create email task
                task = Task(
                    task_id=uuid4(),
                    task_name="send_email",
                    task_kwargs={
                        "to": recipient.email,
                        "subject": subject,
                        "body": body,
                        "recipient_id": str(recipient.recipient_id),
                        "campaign_id": str(campaign_id),
                    },
                    priority=7,
                    max_retries=3,
                    campaign_id=campaign_id,
                    scheduled_at=scheduled_at if not send_immediately else None,
                    status="PENDING" if send_immediately else "SCHEDULED",
                )

                self.db.add(task)
                task_ids.append(task.task_id)

                # Link recipient to task
                recipient.task_id = task.task_id
                recipient.status = "QUEUED"
                created_count += 1

            except Exception as e:
                # Mark recipient as failed
                recipient.status = "FAILED"
                recipient.error_message = str(e)

        # Update campaign status
        campaign.status = "RUNNING" if send_immediately else "SCHEDULED"
        campaign.started_at = datetime.utcnow() if send_immediately else None
        campaign.total_recipients = len(recipients)

        # Commit all changes
        self.db.commit()

        return created_count, task_ids

    def get_campaign_status(self, campaign_id: UUID) -> dict:
        """
        Get current status of a campaign.
        
        Returns dict with:
        - total_recipients: Total number of recipients
        - pending: Recipients not yet processed
        - queued: Recipients with tasks created
        - sent: Successfully sent emails
        - failed: Failed recipients
        - bounced: Bounced emails
        """
        recipients = (
            self.db.query(EmailRecipient)
            .filter(EmailRecipient.campaign_id == campaign_id)
            .all()
        )

        status_counts = {
            "PENDING": 0,
            "QUEUED": 0,
            "SENT": 0,
            "FAILED": 0,
            "BOUNCED": 0,
        }

        for recipient in recipients:
            status = recipient.status.upper()
            if status in status_counts:
                status_counts[status] += 1

        return {
            "total_recipients": len(recipients),
            "pending": status_counts["PENDING"],
            "queued": status_counts["QUEUED"],
            "sent": status_counts["SENT"],
            "failed": status_counts["FAILED"],
            "bounced": status_counts["BOUNCED"],
        }

    def add_recipients(
        self,
        campaign_id: UUID,
        recipients_data: List[dict],
    ) -> Tuple[int, List[dict]]:
        """
        Add recipients to a campaign.
        
        Args:
            campaign_id: Campaign to add recipients to
            recipients_data: List of recipient dicts with email, name, personalization
            
        Returns:
            Tuple of (successful_count, list of error dicts)
        """
        campaign = self.db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        successful = 0
        errors = []

        # Get existing emails to check for duplicates
        existing_emails = {
            r.email
            for r in self.db.query(EmailRecipient.email)
            .filter(EmailRecipient.campaign_id == campaign_id)
            .all()
        }

        for idx, recipient_data in enumerate(recipients_data):
            try:
                email = recipient_data.get("email", "").lower().strip()
                
                # Validate email
                if not email or "@" not in email:
                    errors.append({
                        "row": idx + 1,
                        "email": email,
                        "error": "Invalid email address"
                    })
                    continue

                # Check for duplicate
                if email in existing_emails:
                    errors.append({
                        "row": idx + 1,
                        "email": email,
                        "error": "Duplicate email in campaign"
                    })
                    continue

                # Create recipient
                recipient = EmailRecipient(
                    recipient_id=uuid4(),
                    campaign_id=campaign_id,
                    email=email,
                    personalization=recipient_data.get("personalization", {}),
                    status="PENDING",
                )

                self.db.add(recipient)
                existing_emails.add(email)
                successful += 1

            except Exception as e:
                errors.append({
                    "row": idx + 1,
                    "email": recipient_data.get("email", ""),
                    "error": str(e)
                })

        # Commit all successful additions
        if successful > 0:
            self.db.commit()

        return successful, errors
