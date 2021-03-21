from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from review import ReviewType
import forum
import resource_scraper
import job
import review
import courses
import sys
app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

f = open("pw.txt", "r")
pw = f.read().replace('\n','')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = pw
app.config['MYSQL_DB'] = 'pathways'

mysql = MySQL(app)

@app.route('/api/signup', methods=['POST'])
def sign_up():
    user = request.get_json() 
    user_id = user.get('userID')
    role = user.get('role')
    if role not in ['applicant', 'employer', 'mentor']:
        return jsonify(created=False, message="Incorrect user role."), 400
    name = user.get('name')
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Users VALUES (%s, %s, %s)", (user_id, name, role))
        mysql.connection.commit()
    except:
        cur.close()
        return jsonify(created=False, message="User already exists."), 400
    if role == 'employer':
        company = user.get('company')
        if company is None:
            cur.close()
            return jsonify(created=False, message="No company specified"), 400
        cur.execute("INSERT INTO Employer VALUES (%s, %s)", (user_id, company))
        mysql.connection.commit()
    cur.close()
    return jsonify(created=True), 200

@app.route('/api/user_exists', methods=['GET'])
def user_exists():
    user_id = request.args.get('userID')
    cur = mysql.connection.cursor()
    cur.execute("SELECT role from Users where userID = %s", [user_id])
    exists = not cur.rowcount == 0
    if exists:
        row = cur.fetchall()
        cur.close()
        return jsonify(exists=exists, role=row[0][0]), 200
    cur.close()
    return jsonify(exists=exists, role=""), 200

@app.route('/api/forum_post', methods=['POST'])
def create_forum_post():
    return forum.create_forum_post(mysql)

@app.route('/api/forum_reply', methods=['POST'])
def create_forum_reply():
    return forum.create_forum_reply(mysql)

@app.route('/api/posts', methods=['GET'])
def get_posts():
    return forum.get_posts(mysql)

@app.route('/api/single_post', methods=['GET'])
def get_single_post():
    return forum.get_single_post(mysql)

@app.route('/api/replies', methods=['GET'])
def get_replies():
    return forum.get_replies(mysql)

@app.route('/api/vote', methods=['POST'])
def vote():
    return forum.vote(mysql)

@app.route('/api/resources', methods=['POST'])
def resources():
    return resource_scraper.get_resources()

@app.route('/api/get_single_job_post', methods=['GET'])
def get_single_job_post():
    return job.get_single_job_post(mysql)

@app.route('/api/view_my_job_posts', methods=['GET'])
def view_my_job_posts():
    return job.view_my_job_posts(mysql)

@app.route('/api/get_job_posts', methods=['GET'])
def get_job_posts():
    return job.get_job_posts(mysql)

@app.route('/api/create_job_post', methods=['POST'])
def create_job_post():
    return job.create_job_post(mysql)

@app.route('/api/delete_job_post', methods=['DELETE'])
def delete_job_post():
    return job.delete_job_post(mysql)

@app.route('/api/apply_job_post', methods=['POST'])
def apply_job_post():
    return job.apply_job_post(mysql)

@app.route('/api/view_job_applicants', methods=['GET'])
def view_job_applicants():
    return job.view_job_applicants(mysql)

@app.route('/api/select_applicant_for_interview', methods=['POST'])
def select_applicant_for_interview():
    return job.select_applicant_for_interview(mysql)

@app.route('/api/view_applied_job_posts', methods=['GET'])
def view_applied_job_posts():
    return job.view_applied_job_posts(mysql)

@app.route('/api/applicant_resume', methods=['GET'])
def get_applicant_resume():
    return job.get_applicant_resume(mysql)

@app.route('/api/add_job_review', methods=['POST'])
def add_job_review():
    return review.add_review(mysql, ReviewType.JOB)

@app.route('/api/job_reviews', methods=['GET'])
def get_job_reviews():
    return review.get_reviews(mysql, ReviewType.JOB)

@app.route('/api/add_course_review', methods=['POST'])
def add_course_review():
    return review.add_review(mysql, ReviewType.COURSE)

@app.route('/api/course_reviews', methods=['GET'])
def get_course_reviews():
    return review.get_reviews(mysql, ReviewType.COURSE)

@app.route('/api/add_course', methods=['POST'])
def add_course():
    return courses.create_course(mysql)

@app.route('/api/start_quiz', methods=['POST'])
def start_quiz():
    return courses.start_quiz(mysql)

@app.route('/api/submit_quiz', methods=['POST'])
def submit_quiz():
    return courses.submit_quiz(mysql)

@app.route('/api/quizzes', methods=['GET'])
def get_quizzes():
    return courses.get_quizzes(mysql)

@app.route('/api/questions', methods=['GET'])
def get_questions():
    return courses.get_questions(mysql)

@app.route('/api/courses', methods=['GET'])
def get_courses():
    return courses.get_courses(mysql)

@app.route('/api/individual_course', methods=['GET'])
def get_course():
    return courses.get_course(mysql)

@app.route('/api/progress', methods=['GET'])
def get_progress():
    return courses.get_progress(mysql)

@app.route('/api/videos', methods=['GET'])
def get_videos():
    return courses.get_videos(mysql)

@app.route('/api/mentor_courses', methods=['GET'])
def get_mentor_courses():
    return courses.get_mentor_courses(mysql)

if __name__ == '__main__':
    app.run(debug=True)
