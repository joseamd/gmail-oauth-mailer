import base64
import json
import logging
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText

from django.conf  import settings

from google.oauth2.credentials  import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery  import build
from google_auth_oauthlib.flow  import Flow

from .models import OAuthToken, EmailLog

logger = logging.getLogger(__name__)


def get_oauth_flow():
    """Crea y retorna el flujo OAuth2 de Google."""
    client_config = {
        "web": {
            "client_id":     settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
            "token_uri":     "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    return flow


def get_authorization_url():
    """Genera la URL para que el usuario autorice la aplicación."""
    flow = get_oauth_flow()
    
    # Generar code_verifier y code_challenge para PKCE
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    code_verifier = code_verifier.rstrip('=')  # Remover padding
    
    code_challenge = base64.urlsafe_b64encode(
        __import__('hashlib').sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8')
    code_challenge = code_challenge.rstrip('=')
    
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        code_challenge=code_challenge,
        code_challenge_method='S256',
    )
    
    # Guardar code_verifier en sesión para usarlo después
    # Nota: esto se pasará en la vista
    return auth_url, state, code_verifier


def exchange_code_for_tokens(code, code_verifier=None):
    """
    Intercambia el código de autorización por access_token y refresh_token.
    Guarda los tokens en la base de datos.
    """
    flow = get_oauth_flow()
    
    try:
        # Si tenemos code_verifier, usarlo
        if code_verifier:
            flow.fetch_token(code=code, code_verifier=code_verifier)
        else:
            flow.fetch_token(code=code)
            
        credentials = flow.credentials

        # Obtener el email de la cuenta autorizada
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        email   = profile.get('emailAddress')

        # Guardar o actualizar el token en la BD
        token_obj, created = OAuthToken.objects.update_or_create(
            email=email,
            defaults={
                'access_token':  credentials.token,
                'refresh_token': credentials.refresh_token or '',
                'token_expiry':  credentials.expiry,
            }
        )
        logger.info(f"Tokens {'creados' if created else 'actualizados'} para {email}")
        return token_obj
        
    except Exception as e:
        logger.error(f"Error en exchange_code_for_tokens: {e}")
        raise Exception(f"Error al intercambiar código por tokens: {e}")


def get_gmail_service(email=None):
    """
    Obtiene el servicio de Gmail autenticado.
    Refresca el token si está vencido.
    """
    try:
        if email:
            token_obj = OAuthToken.objects.get(email=email)
        else:
            token_obj = OAuthToken.objects.latest('updated_at')
    except OAuthToken.DoesNotExist:
        raise Exception("No hay tokens OAuth2 almacenados. Debes autorizar la aplicación primero.")

    credentials = Credentials(
        token         = token_obj.access_token,
        refresh_token = token_obj.refresh_token,
        token_uri     = "https://oauth2.googleapis.com/token",
        client_id     = settings.GOOGLE_CLIENT_ID,
        client_secret = settings.GOOGLE_CLIENT_SECRET,
        scopes        = settings.GOOGLE_SCOPES,
    )

    # Refrescar automáticamente si el token expiró
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_obj.access_token = credentials.token
        token_obj.token_expiry = credentials.expiry
        token_obj.save()
        logger.info(f"Token refrescado para {token_obj.email}")

    return build('gmail', 'v1', credentials=credentials), token_obj.email


def send_email(to_email, subject, body_html, body_text=None, sender_email=None):
    """
    Envía un correo electrónico usando la Gmail API.
    
    Args:
        to_email:     Destinatario
        subject:      Asunto
        body_html:    Cuerpo en HTML
        body_text:    Cuerpo en texto plano (opcional)
        sender_email: Cuenta remitente (usa la más reciente si no se especifica)
    
    Returns:
        dict con resultado del envío
    """
    try:
        service, from_email = get_gmail_service(sender_email)

        # Construir el mensaje MIME
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From']    = from_email
        message['To']      = to_email

        if body_text:
            message.attach(MIMEText(body_text, 'plain', 'utf-8'))
        message.attach(MIMEText(body_html, 'html', 'utf-8'))

        # Codificar en base64 (requerido por la API)
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode('utf-8')

        # Enviar
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        # Registrar en el log
        EmailLog.objects.create(
            recipient=to_email,
            subject=subject,
            body=body_html,
            status='sent',
        )
        logger.info(f"Correo enviado a {to_email} | Message ID: {result.get('id')}")
        return {'success': True, 'message_id': result.get('id')}

    except Exception as e:
        # Registrar el error
        EmailLog.objects.create(
            recipient=to_email,
            subject=subject,
            body=body_html,
            status='failed',
            error_msg=str(e),
        )
        logger.error(f"Error enviando correo a {to_email}: {e}")
        return {'success': False, 'error': str(e)}


def send_bulk_emails(recipients, subject, body_html, body_text=None):
    """
    Envía correos masivos a una lista de destinatarios.
    
    Args:
        recipients: Lista de emails ['a@b.com', 'c@d.com']
        subject:    Asunto común
        body_html:  Cuerpo HTML (puede contener {name} para personalizar)
    
    Returns:
        dict con resumen: enviados, fallidos, detalles
    """
    results = {'sent': 0, 'failed': 0, 'details': []}

    for recipient in recipients:
        # Permite personalización básica si pasas una lista de dicts
        if isinstance(recipient, dict):
            email = recipient.get('email')
            name  = recipient.get('name', '')
            personalized_body = body_html.replace('{name}', name)
            personalized_subj = subject.replace('{name}', name)
        else:
            email = recipient
            personalized_body = body_html
            personalized_subj = subject

        result = send_email(email, personalized_subj, personalized_body, body_text)
        results['details'].append({'email': email, **result})

        if result['success']:
            results['sent'] += 1
        else:
            results['failed'] += 1

    return results