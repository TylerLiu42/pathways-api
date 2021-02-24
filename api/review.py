from flask import request, jsonify, escape
from uuid import uuid4
import requests

scoreMap = {"Verynegative": -2, "Negative": -1, "Neutral": 0, "Positive": 1, "Verypositive": 2}
f = open("nlp_api_key.txt", "r")
api_key = f.read().replace('\n','')

def add_job_review(mysql):
    flagged = False
    review = request.get_json()
    content = escape(review.get('content'))
    userID = review.get('userID')
    jobID = review.get('jobID')
    reviewID = uuid4()
    sentiment_scores = requests.post(
        "https://api.deepai.org/api/sentiment-analysis",
        data={
            'text': content,
        },
        headers={'api-key': api_key}
    ).json()
    review_score = getAverageScore(sentiment_scores['output'])
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) from JobReview WHERE jobID = %s", (jobID))
    noOfReviews = cur.fetchone()[0]
    if noOfReviews < 3:
        cur.execute("INSERT INTO JobReview VALUES (%s, %s, %s, %s, UTC_TIMESTAMP(), %s, false)", (reviewID, jobID, userID, content, review_score))
        mysql.connection.commit()
        cur.close()
        return jsonify(message="Success", flagged=False), 200
    cur.execute("SELECT AVG(sentiment_score) from JobReview WHERE jobID = %s", (jobID))
    current_average_score = cur.fetchone()[0]
    if abs(current_average_score - review_score) > 1.75:
        flagged = True
    cur.execute("INSERT INTO JobReview VALUES (%s, %s, %s, %s, UTC_TIMESTAMP(), %s, %s)", (reviewID, jobID, userID, content, review_score, flagged))
    mysql.connection.commit()
    cur.close()
    return jsonify(message="Success", flagged=flagged), 200

def get_job_reviews(mysql):
    jobID = request.args.get('jobID')
    cur = mysql.connection.cursor()
    cur.execute("""SELECT name, content, date_created, flagged from JobReview JOIN Users USING (userID) 
                WHERE jobID = %s ORDER BY date_created DESC""", (jobID))
    rows = cur.fetchall()
    jobReviews = []
    for row in rows:
        jobReviews.append({"author": row[0], "content": row[1], "date_created": row[2], "flagged": row[3]})
    return jsonify(message="Success", jobReviews=jobReviews), 200
    
def getAverageScore(scores):
    total = 0
    for score in scores:
        total += scoreMap[score]
    return total/len(scores)
    
    