import requests
import json

BASE_URL = "http://127.0.0.1:8000"
BULK_ENDPOINT = f"{BASE_URL}/mailer/send-bulk/"

def test_bulk_emails():
    """Prueba el endpoint de envío masivo"""
    
    payload = {
        "recipients": [
            {"email": "test1@gmail.com", "name": "Test Usuario 1"},
            {"email": "test2@gmail.com", "name": "Test Usuario 2"},
        ],
        "subject": "Hola {name}, bienvenido",
        "body_html": """
            <html>
                <head><meta charset="UTF-8"></head>
                <body style="font-family: Arial; padding: 20px;">
                    <h2>¡Hola {name}!</h2>
                    <p>Este es un correo de prueba desde tu aplicación Django.</p>
                    <p>Si lo recibiste correctamente, ¡funciona!</p>
                    <hr>
                    <footer style="color: #999; font-size: 12px;">
                        Enviado por: App Correo Gmail
                    </footer>
                </body>
            </html>
        """
    }
    
    print("📧 Enviando correos masivos...")
    print(f"🔗 URL: {BULK_ENDPOINT}")
    print(f"👥 Destinatarios: {len(payload['recipients'])}")
    print("-" * 50)
    
    try:
        response = requests.post(
            BULK_ENDPOINT,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        result = response.json()
        
        print(f"✅ Enviados: {result.get('sent', 0)}")
        print(f"❌ Fallidos: {result.get('failed', 0)}")
        
        if 'details' in result:
            print("\n📋 Detalles:")
            for detail in result['details']:
                status = "✅" if detail.get('success') else "❌"
                email = detail.get('email', 'N/A')
                msg = detail.get('message_id', detail.get('error', 'N/A'))
                print(f"  {status} {email}: {msg[:50]}")
        
        print("-" * 50)
        print("✅ Prueba completada")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor")
        print("   ¿Está corriendo? → python manage.py runserver")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("TEST API - ENVÍO MASIVO DE CORREOS")
    print("=" * 50)
    test_bulk_emails()