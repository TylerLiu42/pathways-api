import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from textwrap import dedent

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

def sent_recruiter_applied_job(recruiter_email, recruiter_name, applicant_name, job_title, job_link):
    subject = f"New job applicant for {job_title}"
    body = f'''
    Hey {recruiter_name},
    
    {applicant_name} just applied for {job_title}!
    {job_title} job link: 
    {job_link}

    Best,

    Pathways Team
    '''
    sent_email(recruiter_email, subject, dedent(body))

def sent_applicant_applied_job(applicant_email, applicant_name, job_title, job_link):
    subject = f"Applied to {job_title} successfully"
    body = f'''
    Hey {applicant_name}, 
    
    You applied to {job_title} successfully. 
    {job_title} job link: 
    {job_link}
    
    Best,

    Pathways Team
    '''
    sent_email(applicant_email, subject, dedent(body))

def sent_interview_selected(applicant_email, applicant_name, job_title, job_link, message, interview_link):
    subject = f"Congratulations! You have been selected to {job_title} interview"
    body = f'''
    Hey {applicant_name}, 
    
    You have been selected to {job_title} interview!
    
    Recruiter message: 
    {message}

    Interview link: 
    {interview_link}
    {job_title} job link: 
    {job_link}

    Best,

    Pathways Team
    '''
    sent_email(applicant_email, subject, dedent(body))