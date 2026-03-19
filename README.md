# 📧 Gmail OAuth2 Mass Mailer — Django

Sistema de envío de correos masivos usando **Gmail API con autenticación OAuth2**, desarrollado en Django. Permite autorizar una cuenta de Gmail institucional y enviar correos individuales o masivos personalizados desde una interfaz web, sin exponer contraseñas.

Desarrollado por: **José Alexander Muñoz Delgado**  
Proyecto: **Sistema Tesis — Universidad del Valle**

---

## 🎯 Características principales

✅ **Autenticación OAuth2 segura** — Sin almacenar contraseñas  
✅ **Múltiples cuentas** — Autoriza y gestiona varias cuentas Gmail  
✅ **Envío individual** — Correos puntuales con HTML personalizado  
✅ **Envío masivo** — Personalización automática con variables ({name})  
✅ **Interfaz web moderna** — Panel completo en una sola página  
✅ **Historial completo** — Registro de todos los envíos (exitosos y fallidos)  
✅ **Control de desautorización** — Revoca acceso fácilmente desde la UI  
✅ **Rate limiting** — Protección contra exceso de solicitudes  
✅ **Validación de emails** — Previene errores antes de enviar  

---

## 🚀 Tecnologías

- Python 3.10+
- Django 4.2+
- Gmail API (Google Cloud)
- OAuth2 (`google-auth-oauthlib`)
- SQLite (desarrollo) / PostgreSQL (producción)

---

## 📋 Requisitos previos

Antes de comenzar, asegúrate de tener:

- **Python 3.10+** instalado
- **pip** (gestor de paquetes)
- **Git**
- Cuenta en **Google Cloud Console**
- Proyecto de Google con **Gmail API** habilitada

---

## ⚙️ Instalación local

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/gmail-oauth-mailer.git
cd gmail-oauth-mailer
```

### 2. Crear y activar el entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y completa los valores:
```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:
```env
SECRET_KEY=tu_django_secret_key
DEBUG=True
GOOGLE_CLIENT_ID=tu_client_id
GOOGLE_CLIENT_SECRET=tu_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/mailer/oauth2/callback/
```

### 5. Aplicar migraciones
```bash
cd gmail_oauth_project
python manage.py makemigrations mailer
python manage.py migrate
```

### 6. Iniciar el servidor
```bash
python manage.py runserver
```

Abre: [http://localhost:8000/mailer/](http://localhost:8000/mailer/)

---

## 🔑 Flujo de autorización OAuth2
```
1. Ir a http://localhost:8000/mailer/
2. Click en "Autorizar cuenta Gmail"
3. Iniciar sesión con la cuenta institucional
4. Aceptar los permisos (gmail.send, gmail.readonly)
5. ✅ Tokens guardados — listo para enviar correos
```

---

## 🖥️ Interfaz web

El panel principal (`/mailer/`) incluye todo en una sola pantalla:

### Pestaña Individual
Envía un correo a un destinatario específico con asunto y cuerpo HTML.

### Pestaña Masivo
- Agrega destinatarios uno a uno con nombre y correo
- Soporte para personalización con `{name}` en asunto y cuerpo
- Barra de progreso en tiempo real
- Resumen de enviados / fallidos al finalizar

---

## 📤 Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/mailer/` | Panel principal con interfaz de envío |
| GET | `/mailer/authorize/` | Inicia flujo OAuth2 |
| GET | `/mailer/oauth2/callback/` | Callback de Google |
| POST | `/mailer/send/` | Enviar correo individual (form) |
| POST | `/mailer/send-bulk/` | Envío masivo (JSON API) |

---

## 📨 API de envío masivo (opcional vía curl)

También puedes consumir el endpoint directamente:
```bash
curl -X POST http://localhost:8000/mailer/send-bulk/ \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      {"email": "estudiante1@correounivalle.edu.co", "name": "María"},
      {"email": "estudiante2@correounivalle.edu.co", "name": "Juan"}
    ],
    "subject": "Notificación Tesis - {name}",
    "body_html": "<h2>Hola {name}</h2><p>Tienes una actualización en tu tesis.</p>"
  }'
```

Respuesta esperada:
```json
{
  "sent": 2,
  "failed": 0,
  "details": [
    {"email": "estudiante1@correounivalle.edu.co", "success": true, "message_id": "..."},
    {"email": "estudiante2@correounivalle.edu.co", "success": true, "message_id": "..."}
  ]
}
```

---

## 🗂️ Estructura del proyecto
```
gmail-oauth-mailer/
├── gmail_oauth_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── mailer/
│   ├── models.py          # OAuthToken, EmailLog
│   ├── views.py           # Vistas y endpoints
│   ├── urls.py            # Rutas
│   ├── gmail_service.py   # Lógica OAuth2 y envío
│   └── templates/mailer/
│       ├── index.html     # Panel principal (individual + masivo)
│       ├── callback.html  # Resultado de autorización OAuth2
│       └── send_email.html
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔐 Seguridad

- **Nunca subas** el archivo `.env` ni el JSON de credenciales de Google al repositorio.
- En producción usa **HTTPS** y elimina `OAUTHLIB_INSECURE_TRANSPORT` del `settings.py`.
- Los tokens OAuth2 se almacenan en base de datos — asegura acceso restringido en producción.

---

## ☁️ Configuración Google Cloud requerida

1. Proyecto creado en [Google Cloud Console](https://console.cloud.google.com/)
2. Gmail API habilitada
3. Pantalla de consentimiento OAuth configurada (tipo **Interno**)
4. Scopes habilitados:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
5. Credenciales OAuth2 tipo **Aplicación Web** creadas
6. URI de redirección registrada

---

## 📝 Licencia

Uso institucional — Universidad del Valle © 2026
