from app.core.config import settings
from app.services.mail import send_mail
from app.utils.url import create_token_url


async def send_reset_password_mail(user, token):

    url = create_token_url("auth/passwort-zuruecksetzen", token)

    user_dict = {"first_name": user.vorname, "last_name": user.nachname, "url": url}
    try:
        await send_mail(
            subject="Passwort zurücksetzen",
            to_recipient=user.email,
            template_name="reset-password.html",
            template_values=user_dict,
        )
    except:
        print("Error sending password reset email")
