import imaplib
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import openai
import os
import base64
from io import BytesIO
from PIL import Image

# Configuration
IMAP_SERVER = ""
IMAP_PORT = 143
SMTP_SERVER = ""
SMTP_PORT = 587
EMAIL_ACCOUNT = ""
PASSWORD = ""
OPENAI_API_KEY = ""

openai.api_key = OPENAI_API_KEY

def save_image_from_base64(image_data, filename="generated_image.png"):
    image = Image.open(BytesIO(base64.b64decode(image_data)))
    image.save(filename)
    return filename

def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_data = response['data'][0]['b64_json']
    return save_image_from_base64(image_data)

def respond_to_email(mail, mail_id, subject, from_email, email_body):
    if "generate image" in email_body.lower():
        prompt = email_body.replace("generate image", "").strip()
        image_path = generate_image(prompt)
        
        # Prepare the email with the generated image as an attachment
        reply = MIMEMultipart()
        reply['From'] = EMAIL_ACCOUNT
        reply['To'] = from_email
        reply['Subject'] = "Re: " + subject
        
        # Email body
        reply.attach(MIMEText(f"Here is the generated image based on your request: {prompt}", 'plain'))
        
        # Attach the image
        attachment = open(image_path, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(image_path)}')
        reply.attach(part)
        attachment.close()

        # Send email
        smtp_server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp_server.starttls()
        smtp_server.login(EMAIL_ACCOUNT, PASSWORD)
        smtp_server.sendmail(EMAIL_ACCOUNT, from_email, reply.as_string())
        smtp_server.quit()

def main():
    try:
        # Connect and login to IMAP server
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
            
            # Respond to email (with or without image generation)
            respond_to_email(mail, mail_id, subject, from_email, email_body)

            # Mark email as read
            mail.store(mail_id, '+FLAGS', '(\Seen)')

        mail.logout()
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
