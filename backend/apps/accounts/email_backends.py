from __future__ import annotations

from typing import Iterable

import boto3
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage


class SESV2EmailBackend(BaseEmailBackend):
    """Send Django emails through AWS SES v2 API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        region_name = getattr(settings, 'AWS_SES_REGION_NAME', None)
        endpoint_url = getattr(settings, 'AWS_SES_ENDPOINT_URL', None)
        config_set = getattr(settings, 'AWS_SES_CONFIGURATION_SET', '')
        self._configuration_set = (config_set or '').strip()
        self._client = boto3.client(
            'sesv2',
            region_name=region_name,
            endpoint_url=endpoint_url or None,
        )

    def send_messages(self, email_messages: Iterable[EmailMessage]) -> int:
        if not email_messages:
            return 0

        sent_count = 0
        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', '')

        for message in email_messages:
            try:
                from_email = (message.from_email or default_from or '').strip()
                if not from_email:
                    raise ValueError('Missing from email address.')

                destinations = [addr for addr in (message.to or []) if addr]
                if not destinations:
                    continue

                content = {
                    'Simple': {
                        'Subject': {'Data': message.subject or '', 'Charset': 'UTF-8'},
                        'Body': {'Text': {'Data': message.body or '', 'Charset': 'UTF-8'}},
                    }
                }

                for alternative_body, mime_type in message.alternatives:
                    if mime_type == 'text/html':
                        content['Simple']['Body']['Html'] = {
                            'Data': alternative_body or '',
                            'Charset': 'UTF-8',
                        }
                        break

                payload = {
                    'FromEmailAddress': from_email,
                    'Destination': {'ToAddresses': destinations},
                    'Content': content,
                }
                if self._configuration_set:
                    payload['ConfigurationSetName'] = self._configuration_set

                self._client.send_email(**payload)
                sent_count += 1
            except Exception:
                if not self.fail_silently:
                    raise

        return sent_count
