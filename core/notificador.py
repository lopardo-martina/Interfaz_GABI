"""
core/notificador.py

Envía notificaciones por mail al terminar la ejecución de un bot.

Separación de config:
  - Host y puerto SMTP → core/config.py (constantes de sistema)
  - Credenciales y destinatarios → settings.json vía core/settings.py:
        smtp.user         → mail remitente
        smtp.pass         → contraseña / app password
        smtp.mail_destino → destinatarios separados por coma
        smtp.notif_mail   → true / false (interruptor general)
"""

import smtplib
import ssl
from email.message import EmailMessage

from config.config import SMTP_HOST, SMTP_PORT
from config.settings import smtp_config, nombre_bot_sistema


def notif_mail_activa() -> bool:
    """True si las notificaciones por mail están activadas."""
    return bool(smtp_config().get("notif_mail", False))


def enviar_mail(asunto: str, cuerpo: str, cuerpo_html: str = None) -> tuple[bool, str]:
    """
    Envía el mail. Devuelve (exito, detalle).
    Nunca lanza excepción: los errores vuelven en el detalle.
    """
    c = smtp_config()
    user = str(c.get("user", "")).strip()
    pwd  = str(c.get("pass", "")).replace(" ", "").replace("\xa0", "")
    destinos = [d.strip() for d in str(c.get("mail_destino", "")).split(",") if d.strip()]

    if not user or not pwd:
        return False, "Faltan smtp.user / smtp.pass en settings.json"
    if not destinos:
        return False, "Falta smtp.mail_destino en settings.json"

    msg = EmailMessage()
    msg["Subject"] = asunto.replace("\xa0", " ")
    msg["From"] = user
    msg["To"] = ", ".join(destinos)
    msg.set_content(cuerpo)
    if cuerpo_html:
        msg.add_alternative(cuerpo_html, subtype="html")

    try:
        if SMTP_PORT == 465:
            # SSL directo desde el arranque
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30,
                                  context=ssl.create_default_context()) as s:
                s.login(user, pwd)
                s.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
                s.ehlo()
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
                s.login(user, pwd)
                s.send_message(msg)
        return True, f"Mail enviado a {len(destinos)} destinatario(s)"

    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación SMTP (revisá usuario/contraseña)"
    except smtplib.SMTPException as e:
        return False, f"Error SMTP: {e}"
    except OSError as e:
        return False, f"Error de conexión SMTP: {e}"
    except Exception as e:
        return False, f"Error inesperado enviando mail: {e}"


def render_html(nombre: str, exito: bool, duracion: int, fecha: str,
                fecha_inicio: str, equipo: str, error: str = None) -> str:
    """Arma el cuerpo HTML del mail de fin de bot."""

    if exito:
        color_barra = "#62af7b"
        color_badge = "#e8f5ec"
        color_texto = "#2d6b45"
        estado = "COMPLETADO"
        icono = "&#10003;"
    else:
        color_barra = "#d9534f"
        color_badge = "#fdecea"
        color_texto = "#a12622"
        estado = "CON ERRORES"
        icono = "&#33;"

    bot_nombre = nombre_bot_sistema()

    bloque_error = ""
    if error:
        error_escapado = (error.replace("&", "&amp;")
                               .replace("<", "&lt;")
                               .replace(">", "&gt;"))
        bloque_error = f"""
        <tr>
          <td style="padding:0 28px 24px 28px;">
            <div style="font:600 12px/1.4 -apple-system,Segoe UI,Roboto,sans-serif;
                        color:#666; text-transform:uppercase; letter-spacing:.6px;
                        margin-bottom:8px;">Detalle del error</div>
            <pre style="margin:0; padding:14px 16px; background:#1e1e20; color:#f0f0f0;
                        border-radius:6px; font:12px/1.6 Consolas,Monaco,monospace;
                        white-space:pre-wrap; word-break:break-word;
                        overflow-x:auto;">{error_escapado}</pre>
          </td>
        </tr>"""

    def fila(label, valor):
        return f"""
        <tr>
          <td style="padding:9px 0; border-bottom:1px solid #eceff1;
                     font:13px/1.4 -apple-system,Segoe UI,Roboto,sans-serif;
                     color:#78838c; width:110px;">{label}</td>
          <td style="padding:9px 0; border-bottom:1px solid #eceff1;
                     font:600 13px/1.4 -apple-system,Segoe UI,Roboto,sans-serif;
                     color:#2b3137;">{valor}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<body style="margin:0; padding:24px 12px; background:#f4f6f8;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0"
         style="max-width:560px; margin:0 auto; background:#ffffff;
                border-radius:10px; overflow:hidden;
                box-shadow:0 1px 3px rgba(0,0,0,.08);">

    <!-- Barra superior de color según estado -->
    <tr><td style="height:4px; background:{color_barra};"></td></tr>

    <!-- Encabezado -->
    <tr>
      <td style="padding:26px 28px 18px 28px;">
        <div style="font:700 18px/1.3 -apple-system,Segoe UI,Roboto,sans-serif;
                    color:#1e1e20; margin-bottom:10px;">{bot_nombre} &middot; Reporte de ejecución</div>
        <span style="display:inline-block; padding:5px 12px; border-radius:20px;
                     background:{color_badge}; color:{color_texto};
                     font:700 11px/1 -apple-system,Segoe UI,Roboto,sans-serif;
                     letter-spacing:.7px;">{icono}&nbsp;&nbsp;{estado}</span>
      </td>
    </tr>

    <!-- Tabla de datos -->
    <tr>
      <td style="padding:4px 28px 20px 28px;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
          {fila("Bot", nombre)}
          {fila("Duración", f"{duracion}s")}
          {fila("Fecha_Inicio", fecha_inicio)}
          {fila("Fecha_Fin", fecha)}
          {fila("Equipo", equipo)}
        </table>
      </td>
    </tr>

    {bloque_error}

    <!-- Pie -->
    <tr>
      <td style="padding:16px 28px 22px 28px; border-top:1px solid #eceff1;
                 font:11px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; color:#9aa4ac;">
        Mensaje automático generado por GABI. No responder a este correo.
      </td>
    </tr>
  </table>
</body>
</html>"""
