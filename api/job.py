import uuid
import sys
from uuid import uuid4
from flask import request, jsonify
from email_notification import sent_recruiter_applied_job, sent_applicant_applied_job, sent_interview_selected

#TODO: include the actual endpoint
JOB_PATH = "http://localhost:5000/job/"
EMAIL_DOMAIN = "@gmail.com"

def get_single_job_post(mysql):
    jobID = request.args.get('jobID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * from JobPost where jobID = %s", [jobID])
        row = cur.fetchall()
        cur.close()
        if (len(row) == 1):
            job = to_job_json(row[0])
            return jsonify(job), 200
        else:
            return jsonify(message="Could not find job post."), 400
    except Exception as e:
        return jsonify(message=repr(e)), 400

def view_my_job_posts(mysql):
    userID = request.args.get('userID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * from JobPost where userID = %s", [userID])
        rows = cur.fetchall()
        cur.close()
        jobs = to_jobs_json(rows)
        return jsonify(jobs = jobs), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def get_job_posts(mysql):
    index = request.args.get('index')
    limit = request.args.get('limit') 
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * from JobPost LIMIT %s OFFSET %s", (int(limit), int(index)))
        rows = cur.fetchall()
        jobs = to_jobs_json(rows)
        cur.execute("SELECT * from JobPost")
        total_jobs = cur.rowcount
        cur.close()
        return jsonify(jobs = jobs, total_jobs = total_jobs), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def create_job_post(mysql):
    jobID = uuid4()
    post = request.get_json()
    userID = post.get('userID')
    title = post.get('title')
    description = post.get('description')
    content = post.get('content')
    expiry_date = post.get('expiry_date')
    tags = post.get('tags')
    remote = post.get('remote')
    address = post.get('address')
    external_link = post.get('external_link')
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO JobPost VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, UTC_TIMESTAMP())", (jobID, userID, title, description, content, tags, remote, address, external_link, expiry_date))
        mysql.connection.commit()
        cur.close()
        return jsonify(message="Post created", post_url="/job/%s" %(jobID)), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def delete_job_post(mysql):
    jobID = request.args.get('jobID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE from JobPost where jobID = %s", [jobID])
        mysql.connection.commit()
        deleted_row_count = cur.rowcount
        cur.close()
        if (deleted_row_count == 1):
            return jsonify(message=f"Job {jobID} deleted"), 200
        else:
            return jsonify(message="Could not find job post."), 400 
    except Exception as e:
        return jsonify(message=repr(e)), 400

def apply_job_post(mysql):
    jobID = request.args.get('jobID')
    userID = request.args.get('userID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO AppliedJob VALUES (%s, %s, UTC_TIMESTAMP(), false)", (jobID, userID))
        mysql.connection.commit()
        cur.close()
        notify_recruiter_applied_job(mysql, userID, jobID)
        notify_applicant_applied_job(mysql, userID, jobID)
        return jsonify(message=f"userID {userID} applied to jobID {jobID} successfully"), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def select_applicant_for_interview(mysql):
    req = request.get_json()
    jobID = req.get('jobID')
    userID = req.get('userID')
    message = req.get('message')
    interview_link = req.get('interview_link')
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE AppliedJob SET interview_selected = true WHERE jobID = %s AND userID = %s", (jobID, userID))
        mysql.connection.commit()
        cur.close()
        notify_interview_selected(mysql, userID, jobID, message, interview_link)
        return jsonify(message=f"userID {userID} is selected for jobID {jobID} interview"), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def view_job_applicants(mysql): 
    jobID = request.args.get('jobID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT userID, date_applied, interview_selected FROM AppliedJob where jobID = %s", [jobID])
        rows = cur.fetchall()
        row_count = cur.rowcount
        cur.close()
        if (row_count == 0):
            return jsonify(applicants_count = row_count, applicants = []), 200
        else:
            applicants = list(map(lambda applicant: {
                "userID": applicant[0],
                "date_applied": applicant[1],
                "interview_selected": bool(applicant[2])
            }, rows))
            return jsonify(applicants_count = row_count, applicants = applicants), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def view_applied_job_posts(mysql):
    userID = request.args.get('userID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT jobID, date_applied, interview_selected FROM AppliedJob where userID = %s", [userID])
        rows = cur.fetchall()
        row_count = cur.rowcount
        cur.close()
        if (row_count == 0):
            return jsonify(applied = row_count, applied_jobs = []), 200
        else:
            applied_jobs = list(map(lambda applied_job: {
                "jobID": applied_job[0],
                "date_applied": applied_job[1],
                "interview_selected": bool(applied_job[2])
            }, rows))
            return jsonify(applied = row_count, applied_jobs = applied_jobs), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def notify_recruiter_applied_job(mysql, applicant_userID, jobID): 
    cur = mysql.connection.cursor()
    applicant_name = get_user_name(cur, applicant_userID)
    recruiter_userID, job_title = get_job_userID_and_title(cur, jobID)
    recruiter_name = get_user_name(cur, recruiter_userID)
    job_link = f"{JOB_PATH}{jobID}"
    recruiter_email = f"{recruiter_userID}{EMAIL_DOMAIN}"
    cur.close()
    sent_recruiter_applied_job(recruiter_email, recruiter_name, applicant_name, job_title, job_link)

def notify_applicant_applied_job(mysql, applicant_userID, jobID): 
    cur = mysql.connection.cursor()
    applicant_name = get_user_name(cur, applicant_userID)
    _, job_title = get_job_userID_and_title(cur, jobID)
    job_link = f"{JOB_PATH}{jobID}"
    applicant_email = f"{applicant_userID}{EMAIL_DOMAIN}"
    cur.close()
    sent_applicant_applied_job(applicant_email, applicant_name, job_title, job_link)

def notify_interview_selected(mysql, applicant_userID, jobID, message, interview_link):
    cur = mysql.connection.cursor()
    applicant_name = get_user_name(cur, applicant_userID)
    _, job_title = get_job_userID_and_title(cur, jobID)
    job_link = f"{JOB_PATH}{jobID}"
    applicant_email = f"{applicant_userID}{EMAIL_DOMAIN}"
    cur.close()
    sent_interview_selected(applicant_email, applicant_name, job_title, job_link, message, interview_link)

def get_user_name(cur, userID):
    cur.execute("SELECT name FROM Users WHERE userID = %s", [userID])
    return cur.fetchone()[0]

def get_job_userID_and_title(cur, jobID):
    cur.execute("SELECT userID, title FROM JobPost WHERE jobID = %s", [jobID])
    row = cur.fetchone()
    userID = row[0]
    job_title = row[1]
    return userID, job_title

def to_jobs_json(jobs):
    return list(map(lambda job: to_job_json(job), jobs))

def to_job_json(job):
    return {
        "jobID": job[0],
        "userID": job[1],
        "title": job[2],
        "description": job[3],
        "content": job[4],
        "tag": job[5],
        "remote": bool(job[6]),
        "address": job[7],
        "external_link": job[8],
        "expiry_date": job[9],
        "date_created": job[10]
    }