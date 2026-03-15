from app.services.mail import send_mail
from app.utils.url import create_token_url


async def send_verification_mail(user, token):

    url = create_token_url("auth/verifizieren", token)

    user_dict = {"first_name": user.vorname, "last_name": user.nachname, "url": url}

    try:
        await send_mail(
            subject="Account bestätigen",
            to_recipient=user.email,
            template_name="verify-account.html",
            template_values=user_dict,
        )
        print("Verification email sent")
    except:
        print("Error sending verification email")
