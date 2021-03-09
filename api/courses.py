from uuid import uuid4
from flask import request, jsonify

def create_course(mysql):
    courseID = uuid4()
    course = request.get_json()
    author = course.get('author')
    title = course.get('title')
    quizzes = course.get('quizzes')
    video_links = course.get('videos')
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Course VALUES (%s, %s, %s, %s)", (courseID, author, title, ','.join(video_links)))
    mysql.connection.commit()
    for quizID, quiz in enumerate(quizzes):
        for questionID, questionInfo in quiz.items():
            cur.execute("INSERT INTO Quiz VALUES (%s, %s, %s, %s, %s)", (questionID, quizID, courseID, questionInfo['answer'], questionInfo['question']))
            mysql.connection.commit()
            for optionID, option in enumerate(questionInfo['options']):
                cur.execute("INSERT INTO QuestionOption VALUES (%s, %s, %s, %s, %s)", (questionID, optionID, courseID, quizID, option))
                mysql.connection.commit()
    cur.close()
    return jsonify(message="Success"), 200

def start_course(mysql):
    request_body = request.get_json()
    userID = request_body['userID']
    courseID = request_body['courseID']
    quizID = request_body['quizID']
    cur = mysql.connection.cursor()
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
    for questionID, user_answer in request_body['submission'].items():
        if answer_map[questionID] == user_answer:
            correctQuestions += 1
    cur.execute("""UPDATE CourseUser SET completed = true, grade = %s WHERE userID = %s AND courseID = %s 
                AND quizID = %s""", (correctQuestions/len(answer_map), userID, courseID, quizID))
    mysql.connection.commit()
    cur.close()
    return jsonify(message="Quiz submitted", grade=correctQuestions/len(answer_map)), 200
    
def to_map(rows):
    map = {}
    for row in rows:
        map[row[0]] = row[1]
    return map

def get_videos(mysql):
    cur = mysql.connection.cursor()
    courseID = request.args.get('courseID')
    cur.execute("SELECT videos FROM Course WHERE CourseID = %s", [courseID])
    video_links = cur.fetchone()[0].split(',')
    return jsonify(video_links=video_links), 200

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
    cur.close()
    return jsonify(quizzes=quizzes), 200
    
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
    cur.close()
    return jsonify(questions=response), 200
    
def get_courses(mysql):
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT courseID, name, courseTitle from Course JOIN Users ON Course.courseAuthorID = Users.userID")
    rows = cur.fetchall()
    courses = {}
    for row in rows:
        courses[row[0]] = {"author": row[1], "title": row[2]}
    cur.close()
    return jsonify(courses=courses), 200

def get_progress(mysql):
    cur = mysql.connection.cursor()
    userID = request.args.get('userID')
    cur.execute("SELECT courseID, quizID, completed, grade FROM CourseUser WHERE userID = %s ORDER BY courseID", [userID])
    rows = cur.fetchall()
    response = []
    course_map = {}
    completed = 0
    totalQuizzes = 0
    gradeSum = 0
    for i, row in enumerate(rows):
        if row[0] not in course_map:
            course_map[row[0]] = {"completed": 0, "totalQuizzes": 1, "gradeSum": 0}
            if row[2]:
                course_map[row[0]]["completed"] += 1
                course_map[row[0]]["gradeSum"] += row[3]
        else:
            if row[2]:
                course_map[row[0]]["completed"] += 1
                course_map[row[0]]["gradeSum"] += row[3]
            course_map[row[0]]["totalQuizzes"] += 1
    for key, value in course_map.items():
        response.append(
            {"courseID": key, "progress": float(value["completed"]/value["totalQuizzes"]), "avgGrade": float(value["gradeSum"]/value["completed"])}
        )
    cur.close()
    return jsonify(courseProgress=response), 200
    