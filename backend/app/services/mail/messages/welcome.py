from app.services.mail import send_mail


async def send_welcome_mail(user):
    user_dict = {
        "first_name": user.vorname,
        "last_name": user.nachname,
    }
    try:
        await send_mail(
            subject="Willkommen beim namowo Standortcheck",
            to_recipient=user.email,
            template_name="welcome-user.html",
            template_values=user_dict,
        )
    except:
        print("Error sending welcome email")
