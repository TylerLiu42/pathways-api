from uuid import uuid4
from flask import request, jsonify

def create_course(mysql):
    courseID = uuid4()
    course = request.get_json()
    author = course.get('author')
    title = course.get('title')
    quizzes = course.get('quizzes')
    video_links = course.get('videos')
    description = course.get('description')
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Course VALUES (%s, %s, %s, %s, %s, UTC_TIMESTAMP())", (courseID, author, title, description, ','.join(video_links)))
    mysql.connection.commit()
    for quizID, quiz in enumerate(quizzes):
        for questionID, questionInfo in quiz.items():
            cur.execute("INSERT INTO Quiz VALUES (%s, %s, %s, %s, %s)", (questionID, quizID, courseID, questionInfo['answer'], questionInfo['question']))
            mysql.connection.commit()
            for optionID, option in enumerate(questionInfo['options']):
                cur.execute("INSERT INTO QuestionOption VALUES (%s, %s, %s, %s, %s)", (questionID, optionID, courseID, quizID, option))
                mysql.connection.commit()
    cur.close()
    return jsonify(message="Success", courseID=courseID), 200

def start_quiz(mysql):
    request_body = request.get_json()
    userID = request_body['userID']
    courseID = request_body['courseID']
    quizID = request_body['quizID']
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM CourseUser WHERE userID = %s AND courseID = %s AND quizID = %s", (userID, courseID, quizID))
    row_count = cur.fetchone()[0]
    if row_count == 1:
        return jsonify(message="Quiz already started/completed"), 405
    cur.execute("INSERT INTO CourseUser (userID, courseID, quizID, completed) VALUES (%s, %s, %s, false)", (userID, courseID, quizID))
    mysql.connection.commit()
    cur.close()
    return jsonify(message="Success"), 200
    
def submit_quiz(mysql):
    request_body = request.get_json()
    userID = request_body['userID']
    courseID = request_body['courseID']
    quizID = request_body['quizID']
    cur = mysql.connection.cursor()
    cur.execute("SELECT questionID, answer FROM Quiz WHERE quizID = %s AND courseID = %s", (quizID, courseID))
    answer_map = to_map(cur.fetchall())
    correctQuestions = 0
    graded_questions = []
    for questionID, user_answer in request_body['submission'].items():
        if answer_map[questionID] == user_answer:
            correctQuestions += 1
            graded_questions.append({"questionID": questionID, "correct": True})
        else:
            graded_questions.append({"questionID": questionID, "correct": False, "correctAnswer": answer_map[questionID]})
    cur.execute("""UPDATE CourseUser SET completed = true, grade = %s WHERE userID = %s AND courseID = %s 
                AND quizID = %s""", (correctQuestions/len(answer_map), userID, courseID, quizID))
    mysql.connection.commit()
    cur.close()
    return jsonify(message="Quiz submitted", grade=correctQuestions/len(answer_map), graded_questions=graded_questions), 200
    
def to_map(rows):
    map = {}
    for row in rows:
        map[row[0]] = row[1]
    return map

def get_videos(mysql):
    cur = mysql.connection.cursor()
    courseID = request.args.get('courseID')
    cur.execute("SELECT videos, courseTitle FROM Course WHERE CourseID = %s", [courseID])
    row = cur.fetchone()
    video_links = row[0].split(',')
    return jsonify(video_links=video_links, courseTitle=row[1]), 200

def get_quizzes(mysql):
    cur = mysql.connection.cursor()
    courseID = request.args.get('courseID')
    cur.execute("SELECT courseID, quizID, questionID FROM Quiz WHERE courseID = %s ORDER BY quizID", [courseID])
    rows = cur.fetchall()
    quizzes = []
    questionIDs = []
    currentQuizID = rows[0][1]
    for i, row in enumerate(rows):
        if row[1] != currentQuizID:
            quizzes.append({"quizID": currentQuizID, "questionIDs": questionIDs})
            questionIDs = []
            currentQuizID = row[1]
            questionIDs.append(row[2])
        elif i == len(rows)-1:
            questionIDs.append(row[2])
            quizzes.append({"quizID": currentQuizID, "questionIDs": questionIDs})
        else:
            questionIDs.append(row[2])
    cur.execute("SELECT courseTitle FROM Course WHERE CourseID = %s", [courseID])
    row = cur.fetchone()
    cur.close()
    return jsonify(quizzes=quizzes, courseTitle=row[0]), 200
    
def get_questions(mysql):
    cur = mysql.connection.cursor()
    courseID = request.args.get('courseID')
    quizID = request.args.get('quizID')
    cur.execute("""SELECT questionID, option_string, question_string FROM Quiz JOIN QuestionOption USING (quizID, questionID, courseID) 
                WHERE quizID = %s AND courseID = %s ORDER BY questionID ASC""", (quizID, courseID))
    rows = cur.fetchall()
    response = []
    options = []
    currentQuestionID = rows[0][0]
    question_string = rows[0][2]
    for i, row in enumerate(rows):
        if row[0] != currentQuestionID:
            response.append({"questionID": currentQuestionID, "question_string": question_string, "options": options})
            currentQuestionID = row[0]
            options = []
            options.append(row[1])
            question_id = row[1]
            question_string = row[2]
        elif i == len(rows) - 1:
            options.append(row[1])
            response.append({"questionID": row[0], "question_string": row[2], "options": options})
        else:
            options.append(row[1])
    cur.execute("SELECT courseTitle FROM Course WHERE CourseID = %s", [courseID])
    row = cur.fetchone()
    cur.close()
    return jsonify(questions=response, courseTitle=row[0]), 200
    
def get_courses(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""SELECT DISTINCT courseID, name, courseTitle, date_created from Course 
                JOIN Users ON Course.courseAuthorID = Users.userID ORDER BY date_created DESC""")
    rows = cur.fetchall()
    courses = {}
    for row in rows:
        courses[row[0]] = {"author": row[1], "title": row[2], "date_created": row[3]}
    cur.close()
    return jsonify(courses=courses), 200

def get_course(mysql):
    cur = mysql.connection.cursor()
    courseID = request.args.get('courseID')
    cur.execute("""SELECT courseTitle, date_created, description, name, videos, count(distinct QuizID) 
                FROM Course LEFT JOIN Quiz using (CourseID) JOIN Users ON Course.courseAuthorID = Users.userID 
                WHERE courseID = %s""", [courseID])
    row = cur.fetchone()
    noOfVideos = len(row[4].split(","))
    response = {"courseTitle": row[0], "date_created": row[1], "description": row[2], "author": row[3], 
                "videoCount": noOfVideos, "quizCount": row[5]}
    cur.close()
    return jsonify(course=response), 200

def get_progress(mysql):
    cur = mysql.connection.cursor()
    userID = request.args.get('userID')
    cur.execute("""SELECT courseID, quizID, completed, grade, courseTitle FROM CourseUser 
                JOIN Course USING (courseID) WHERE userID = %s ORDER BY courseID""", [userID])
    rows = cur.fetchall()
    response = []
    course_map = {}
    completed = 0
    gradeSum = 0
    for i, row in enumerate(rows):
        if row[0] not in course_map:
            cur.execute("SELECT COUNT(DISTINCT quizID) FROM Quiz WHERE courseID = %s", [row[0]])
            totalQuizzes = cur.fetchone()[0]
            course_map[row[0]] = {"completed": 0, "totalQuizzes": totalQuizzes, "gradeSum": 0, "courseTitle": row[4]}
            if row[2]:
                course_map[row[0]]["completed"] += 1
                course_map[row[0]]["gradeSum"] += row[3]
        else:
            if row[2]:
                course_map[row[0]]["completed"] += 1
                course_map[row[0]]["gradeSum"] += row[3]
    for key, value in course_map.items():
        response.append(
            {"courseID": key, 
             "courseTitle": value["courseTitle"], 
             "progress": float(value["completed"]/value["totalQuizzes"]), 
             "avgGrade": float(value["gradeSum"]/value["completed"])}
        )
    cur.close()
    return jsonify(courseProgress=response), 200

def get_mentor_courses(mysql):
    cur = mysql.connection.cursor()
    userID = request.args.get('userID')
    cur.execute("SELECT courseID, courseTitle, date_created FROM Course WHERE courseAuthorId = %s", [userID])
    rows = cur.fetchall()
    courses = []
    for row in rows:
        courses.append({"courseID": row[0], "courseTitle": row[1], "date_created": row[2]})
    cur.close()
    return jsonify(mentorCourses=courses), 200