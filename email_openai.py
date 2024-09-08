import imaplib
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import openai

IMAP_SERVER = ""
IMAP_PORT = 143
SMTP_SERVER = ""
SMTP_PORT = 587

EMAIL_ACCOUNT = ""
PASSWORD = ""  # Leave password empty since it's not required
OPENAI_API_KEY = ""  # Make sure this is set correctly

# Enable debugging output
imaplib.Debug = 4

try:
    # Connect and login to IMAP server without SSL
    mail = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, 'UNSEEN')
    mail_ids = messages[0].split()

    for mail_id in mail_ids:
        status, msg_data = mail.fetch(mail_id, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        
        from_email = email.utils.parseaddr(msg['From'])[1]
        subject = msg['Subject']
        email_body = msg.get_payload(decode=True).decode('utf-8')

        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful automated email rseponser for Oy Yritys Ltd customers from Founder/Owner Will Smith."},
                {"role": "user", "content": f"Respond to this email: {email_body}"}
            ],
            max_tokens=150
        )

        reply_text = response["choices"][0]["message"]["content"]

        print("Original email subject:", subject)
        print("Original email body:", email_body)
        print("Generated reply:", reply_text)

        # Now send the reply via SMTP
        smtp_server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp_server.starttls()  # Start TLS, if required by the server

        # No login needed since no password is required by the server
        reply = MIMEMultipart()
        reply['From'] = EMAIL_ACCOUNT
        reply['To'] = from_email
        reply['Subject'] = "Re: " + subject
        reply.attach(MIMEText(reply_text + '\n\nThis is Oy Yritys Ltd AI automatic email response and Oy Yritys Ltd do not have any warranty for what AI will response for you! Attention! If you are trying to sell us your services then stop sendind us emails. We are not interested!', 'plain'))
        
        smtp_server.sendmail(EMAIL_ACCOUNT, from_email, reply.as_string())
        smtp_server.quit()

        # Mark the email as read
        mail.store(mail_id, '+FLAGS', '(\Seen)')

    mail.logout()
    
except Exception as e:
    print(f"Error: {e}")

finally:
    if 'mail' in locals() and mail.state == 'SELECTED':
        mail.close()
    if 'mail' in locals() and mail.state in ['SELECTED', 'AUTH']:
        mail.logout()