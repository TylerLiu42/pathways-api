import uuid
import sys
from uuid import uuid4
from io import BytesIO
from flask import request, jsonify, send_file
from email_notification import sent_recruiter_applied_job, sent_applicant_applied_job, sent_interview_selected

ALLOWED_EXTENSIONS = ('pdf', 'png', 'jpg', 'jpeg')

def get_single_job_post(mysql):
    jobID = request.args.get('jobID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * from JobPost where jobID = %s", [jobID])
        row = cur.fetchall()
        if (len(row) == 1):
            job = to_job_json(cur, row[0])
            cur.close()
            return jsonify(job), 200
        else:
            cur.close()
            return jsonify(message="Could not find job post."), 400
    except Exception as e:
        return jsonify(message=repr(e)), 400

def view_my_job_posts(mysql):
    userID = request.args.get('userID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT jobID, title, remote, date_created, company from JobPost where userID = %s ORDER BY date_created DESC", [userID])
        rows = cur.fetchall()
        jobs = to_jobs_json(cur, rows)
        cur.close()
        return jsonify(jobs = jobs), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def get_job_posts(mysql):
    index = request.args.get('index')
    limit = request.args.get('limit') 
    try:
        cur = mysql.connection.cursor()
        cur.execute("""SELECT jobID, title, remote, date_created, company from JobPost
        WHERE expiry_date>CURRENT_TIMESTAMP ORDER BY date_created DESC LIMIT %s OFFSET %s""", (int(limit), int(index)))
        rows = cur.fetchall()
        jobs = to_jobs_json(cur, rows)
        cur.execute("SELECT * from JobPost WHERE expiry_date>CURRENT_TIMESTAMP")
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
        cur.execute("SELECT company FROM Employer WHERE userID = %s", [userID])
        company = cur.fetchone()
        cur.execute("INSERT INTO JobPost VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, UTC_TIMESTAMP(), %s)",
        (jobID, userID, title, description, content, tags, remote, address, external_link, expiry_date, company))
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
    file = request.files['file']
    if file.filename == '':
        return jsonify(message="No resume file selected"), 400
    elif not allowed_file(file.filename):
        return jsonify(message=f"Resume file type not suppported. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"), 400
    try:
        cur = mysql.connection.cursor()
        resume = file.read()
        extension = get_file_extension(file.filename)
        cur.execute("INSERT INTO AppliedJob VALUES (%s, %s, UTC_TIMESTAMP(), false, %s, %s) ON DUPLICATE KEY UPDATE resume=%s, resume_extension=%s",
        (jobID, userID, resume, extension, resume, extension))
        mysql.connection.commit()
        cur.close()
        sent_recruiter_applied_job(mysql, userID, jobID)
        sent_applicant_applied_job(mysql, userID, jobID)
        return jsonify(success=True), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def get_applicant_resume(mysql):
    jobID = request.args.get('jobID')
    userID = request.args.get('userID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT resume, resume_extension FROM AppliedJob WHERE jobID=%s AND userID=%s", (jobID, userID))
        row = cur.fetchall()
        user_name = get_user_name(cur, userID)
        cur.close()
        if (len(row) == 1):
            resume = row[0][0]
            resume_extension = row[0][1]
            return send_file(BytesIO(resume), attachment_filename=f"{user_name} resume.{resume_extension}", as_attachment=True), 200
        else:
            return jsonify(message="Could not find applicant resume"), 400
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
        sent_interview_selected(mysql, userID, jobID, message, interview_link)
        return jsonify(message=f"userID {userID} is selected for jobID {jobID} interview"), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def view_job_applicants(mysql): 
    jobID = request.args.get('jobID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT userID, date_applied, interview_selected FROM AppliedJob where jobID = %s ORDER BY date_applied DESC", [jobID])
        rows = cur.fetchall()
        row_count = cur.rowcount
        if (row_count == 0):
            cur.close()
            return jsonify(applicant_count = row_count, applicants = []), 200
        else:
            applicants = list(map(lambda applicant: {
                "userID": applicant[0],
                "name": get_user_name(cur, applicant[0]),
                "date_applied": applicant[1],
                "interview_selected": bool(applicant[2])
            }, rows))
            cur.close()
            return jsonify(applicant_count = row_count, applicants = applicants), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def view_applied_job_posts(mysql):
    userID = request.args.get('userID')
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT jobID, date_applied, interview_selected FROM AppliedJob where userID = %s ORDER BY date_applied DESC", [userID])
        rows = cur.fetchall()
        row_count = cur.rowcount
        if (row_count == 0):
            cur.close()
            return jsonify(applied = row_count, applied_jobs = []), 200
        else:
            applied_jobs = list(map(lambda applied_job: {
                "jobID": applied_job[0],
                "title": get_job_title(cur, applied_job[0]),
                "date_applied": applied_job[1],
                "interview_selected": bool(applied_job[2])
            }, rows))
            cur.close()
            return jsonify(applied = row_count, applied_jobs = applied_jobs), 200
    except Exception as e:
        return jsonify(message=repr(e)), 400

def allowed_file(filename):
    return '.' in filename and \
           get_file_extension(filename) in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower()

def get_user_name(cur, userID):
    cur.execute("SELECT name FROM Users WHERE userID = %s", [userID])
    return cur.fetchone()[0]

def get_applicant_count(cur, jobID):
    cur.execute("SELECT * FROM AppliedJob where jobID = %s", [jobID])
    return cur.rowcount

def get_job_title(cur, jobID):
    cur.execute("SELECT title FROM JobPost WHERE jobID = %s", [jobID])
    return cur.fetchone()[0]

def to_jobs_json(cur, jobs):
    return list(map(lambda job: to_minimum_job_json(cur, job), jobs))

def to_minimum_job_json(cur, job):
    return {
        "jobID": job[0],
        "title": job[1],
        "remote": bool(job[2]),
        "date_created": job[3],
        "company": job[4],
        "applicant_count": get_applicant_count(cur, job[0])
    }

def to_job_json(cur, job):
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
        "date_created": job[10],
        "company": job[11],
        "applicant_count": get_applicant_count(cur, job[0])
    }
