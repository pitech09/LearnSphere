import random
import string
from django.utils.text import slugify
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import threading


def send_html_email(subject, recipient_list, template, context):

    html_message = render_to_string(template, context)
    plain_message = strip_tags(html_message)

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=recipient_list,
        subject=subject,
        plain_text_content=plain_message,
        html_content=html_message
    )
    print(f"Sending email to {recipient_list} with subject '{subject}' using template '{template}'...")
    print(settings.SENDGRID_API_KEY)
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = sg.send(message)

    return response.status_code





def send_email_thread(subject, recipient_list, template, context):
    thread = threading.Thread(
        target=send_html_email,
        args=(subject, recipient_list, template, context)
    )
    thread.start()


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def unique_slug_generator(instance, new_slug=None):
    """
    Assumes the instance has a model with a slug field and a title
    character (char) field.
    """
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.title)

    klass = instance.__class__
    qs_exists = klass.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = f"{slug}-{random_string_generator(size=4)}"
        return unique_slug_generator(instance, new_slug=new_slug)
    return slug
