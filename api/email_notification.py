import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from textwrap import dedent

#TODO: include the actual endpoint
JOB_PATH = "http://localhost:5000/job/"
EMAIL_HOST = "gmail.com"

def sent_email(receiver_email, subject, body):
    port = 465  # SSL
    smtp_server = f"smtp.{EMAIL_HOST}"
    sender_email = f"pathways.fydp@{EMAIL_HOST}" 
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

def sent_recruiter_applied_job(mysql, applicant_userID, jobID):
    cur = mysql.connection.cursor()
    applicant_name = get_user_name(cur, applicant_userID)
    recruiter_userID, job_title = get_job_userID_and_title(cur, jobID)
    recruiter_name = get_user_name(cur, recruiter_userID)
    job_link = f"{JOB_PATH}{jobID}"
    recruiter_email = f"{recruiter_userID}@{EMAIL_HOST}"
    cur.close()

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

def sent_applicant_applied_job(mysql, applicant_userID, jobID):
    cur = mysql.connection.cursor()
    applicant_name = get_user_name(cur, applicant_userID)
    _, job_title = get_job_userID_and_title(cur, jobID)
    job_link = f"{JOB_PATH}{jobID}"
    applicant_email = f"{applicant_userID}@{EMAIL_HOST}"
    cur.close()

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

def sent_interview_selected(mysql, applicant_userID, jobID, message, interview_link):
    cur = mysql.connection.cursor()
    applicant_name = get_user_name(cur, applicant_userID)
    _, job_title = get_job_userID_and_title(cur, jobID)
    job_link = f"{JOB_PATH}{jobID}"
    applicant_email = f"{applicant_userID}@{EMAIL_HOST}"
    cur.close()

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

def get_user_name(cur, userID):
    cur.execute("SELECT name FROM Users WHERE userID = %s", [userID])
    return cur.fetchone()[0]

def get_job_userID_and_title(cur, jobID):
    cur.execute("SELECT userID, title FROM JobPost WHERE jobID = %s", [jobID])
    row = cur.fetchone()
    userID = row[0]
    job_title = row[1]
    return userID, job_title
