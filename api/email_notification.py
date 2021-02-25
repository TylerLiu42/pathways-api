import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

def sent_email(receiver_email, subject, body):
    port = 465  # SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "pathways.fydp@gmail.com" 
    f = open("email_pw.txt", "r")
    password = f.read().replace('\n','')

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    body = body
    message.attach(MIMEText(body,'plain'))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def sent_recruiter_applied_job_email(recruiter_email, job_title, job_link, applicant_name):
    subject = f"New job applicant for {job_title}"
    body = f"{applicant_name} applied for {job_title}, Link: {job_link}"
    sent_email(recruiter_email, subject, body)

def sent_applicant_applied_job_email(applicant_email, job_title, job_link, applicant_name):
    subject = f"Applied to {job_title} successfully"
    body = f"{applicant_name} applied for {job_title} successfully, Link: {job_link}"
    sent_email(applicant_email, subject, body)