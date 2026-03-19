import json
from django.shortcuts  import render, redirect
from django.http       import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib    import messages

from .gmail_service import (
    get_authorization_url,
    exchange_code_for_tokens,
    send_email,
    send_bulk_emails,
)
from .models import OAuthToken, EmailLog


def index(request):
    """Página principal: muestra si hay una cuenta autorizada."""
    tokens    = OAuthToken.objects.all()
    email_log = EmailLog.objects.order_by('-sent_at')[:20]
    return render(request, 'mailer/index.html', {
        'tokens':    tokens,
        'email_log': email_log,
    })


def authorize(request):
    """Inicia el flujo OAuth2 redirigiendo a Google."""
    auth_url, state, code_verifier = get_authorization_url()
    
    # Guardar state y code_verifier en sesión
    request.session['oauth_state'] = state
    request.session['oauth_code_verifier'] = code_verifier
    request.session.set_expiry(600)  # 10 minutos
    
    return redirect(auth_url)


def oauth2_callback(request):
    """
    Google redirige aquí después de que el usuario autoriza.
    Recibe el código y lo intercambia por tokens.
    """
    code  = request.GET.get('code')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description', '')

    if error:
        return render(request, 'mailer/callback.html', {
            'success': False,
            'error':   f"{error}: {error_description}"
        })

    if not code:
        return render(request, 'mailer/callback.html', {
            'success': False,
            'error':   "No se recibió código de autorización."
        })

    try:
        # Obtener code_verifier de la sesión
        code_verifier = request.session.get('oauth_code_verifier')
        
        if not code_verifier:
            return render(request, 'mailer/callback.html', {
                'success': False,
                'error':   "Sesión expirada. Intenta de nuevo."
            })
        
        token_obj = exchange_code_for_tokens(code, code_verifier)
        
        # Limpiar sesión
        if 'oauth_state' in request.session:
            del request.session['oauth_state']
        if 'oauth_code_verifier' in request.session:
            del request.session['oauth_code_verifier']
        
        return render(request, 'mailer/callback.html', {
            'success': True,
            'email':   token_obj.email,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render(request, 'mailer/callback.html', {
            'success': False,
            'error':   str(e),
        })


def send_email_view(request):
    """Vista para enviar un correo de prueba individual."""
    if request.method == 'POST':
        to_email   = request.POST.get('to_email')
        subject    = request.POST.get('subject')
        body       = request.POST.get('body')

        result = send_email(to_email, subject, body)

        if result['success']:
            messages.success(request, f"Correo enviado exitosamente a {to_email}")
        else:
            messages.error(request, f"Error: {result['error']}")

        return redirect('mailer:index')

    return render(request, 'mailer/send_email.html')


@csrf_exempt
def send_bulk_view(request):
    """
    API endpoint para envío masivo.
    POST con JSON con lista de destinatarios.
    
    Ejemplo de request:
    POST /mailer/send-bulk/
    Content-Type: application/json
    
    {
        "recipients": [
            {"email": "a@b.com", "name": "Ana"},
            {"email": "c@d.com", "name": "Carlos"}
        ],
        "subject": "Hola {name}",
        "body_html": "<h1>Hola {name}</h1><p>Contenido</p>"
    }
    """
    if request.method != 'POST':
        return JsonResponse(
            {'error': 'Solo se permite método POST'}, 
            status=405
        )
    
    try:
        data = json.loads(request.body)
        recipients = data.get('recipients', [])
        subject = data.get('subject', 'Sin asunto')
        body_html = data.get('body_html', '')

        # Validaciones básicas
        if not recipients:
            return JsonResponse(
                {'error': 'Campo "recipients" requerido'}, 
                status=400
            )
        
        if not isinstance(recipients, list):
            return JsonResponse(
                {'error': 'recipients debe ser una lista'}, 
                status=400
            )
        
        if len(recipients) > 500:
            return JsonResponse(
                {'error': 'Máximo 500 destinatarios por solicitud'}, 
                status=400
            )
        
        if not subject or not body_html:
            return JsonResponse(
                {'error': 'subject y body_html son requeridos'}, 
                status=400
            )

        # Enviar
        results = send_bulk_emails(recipients, subject, body_html)
        return JsonResponse(results, status=200)

    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'JSON inválido en el body'}, 
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'Error del servidor: {str(e)}'}, 
            status=500
        )