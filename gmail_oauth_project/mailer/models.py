from django.db import models

class OAuthToken(models.Model):
    """
    Almacena los tokens OAuth2 de la cuenta autorizada.
    Solo debe existir UN registro activo.
    """
    email         = models.EmailField(unique=True)
    access_token  = models.TextField()
    refresh_token = models.TextField()
    token_expiry  = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Token para {self.email}"


class EmailLog(models.Model):
    """Registro de correos enviados para auditoría."""
    STATUS_CHOICES = [
        ('sent',   'Enviado'),
        ('failed', 'Fallido'),
    ]
    recipient  = models.EmailField()
    subject    = models.CharField(max_length=255)
    body       = models.TextField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES)
    error_msg  = models.TextField(blank=True, null=True)
    sent_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient} - {self.subject} [{self.status}]"


