from django.db import models
from django.conf import settings

class Conversation(models.Model):
    """
    Groups messages between a patient and a doctor (or AI).
    """
    CONVERSATION_TYPES = [
        ('patient_doctor', 'Patient-Doctor'),
        ('patient_ai', 'Patient-AI'),
    ]

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    conv_type = models.CharField(
        max_length=20,
        choices=CONVERSATION_TYPES,
        default='patient_ai'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.conv_type} - {self.id}"

class Message(models.Model):
    """
    A single message within a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages'
    )
    content = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    is_ai = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        sender_name = self.sender.phone_number if self.sender else "AI"
        return f"Msg from {sender_name} at {self.timestamp}"
