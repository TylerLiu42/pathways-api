from flask import request, jsonify, escape
from uuid import uuid4
from enum import Enum
import requests
import datetime

scoreMap = {"Verynegative": -2, "Negative": -1, "Neutral": 0, "Positive": 1, "Verypositive": 2}
f = open("nlp_api_key.txt", "r")
api_key = f.read().replace('\n','')

class ReviewType(Enum):
    JOB = {"ID": "jobID", "TableName": "JobReview"}
    COURSE = {"ID": "courseID", "TableName": "CourseReview"}

def add_review(mysql, review_type: ReviewType):
    review_type_table_name = review_type.value.get("TableName")
    review_type_ID_column = review_type.value.get("ID")
    flagged = False
    review = request.get_json()
    content = escape(review.get('content'))
    userID = review.get('userID')
    typeID = review.get(review_type_ID_column)
    stars = review.get('stars')
    reviewID = uuid4()
    sentiment_scores = requests.post(
        "https://api.deepai.org/api/sentiment-analysis",
        data={
            'text': content,
        },
        headers={'api-key': api_key}
    ).json()
    review_score = getAverageScore(sentiment_scores['output'])
    review = {
        'reviewID': reviewID,
        'author': userID,
        'content': content,
        'stars': stars,
    }
    cur = mysql.connection.cursor()
    if abs(review_score - (int(stars) - 3)) >= 2:
        utc_timestamp = datetime.datetime.utcnow()
        cur.execute(f"INSERT INTO {review_type_table_name} VALUES (%s, %s, %s, %s, UTC_TIMESTAMP(), %s, true, %s)",
        (reviewID, typeID, userID, content, review_score, stars))
        mysql.connection.commit()
        cur.close()
        review['flagged'] = True
        review['date_created'] = utc_timestamp
        return jsonify(message="Created, sentiment does not match rating", review=review), 200
    cur.execute(f"SELECT COUNT(*) from {review_type_table_name} WHERE {review_type_ID_column} = %s", [typeID])
    noOfReviews = cur.fetchone()[0]
    if noOfReviews < 3:
        utc_timestamp = datetime.datetime.now()
        cur.execute(f"INSERT INTO {review_type_table_name} VALUES (%s, %s, %s, %s, UTC_TIMESTAMP(), %s, false, %s)", 
        (reviewID, typeID, userID, content, review_score, stars))
        mysql.connection.commit()
        cur.close()
        review['flagged'] = False
        review['date_created'] = utc_timestamp
        return jsonify(message="Success", review=review), 200
    cur.execute(f"SELECT AVG(sentiment_score) from {review_type_table_name} WHERE {review_type_ID_column} = %s", [typeID])
    current_average_score = cur.fetchone()[0]
    if abs(current_average_score - review_score) > 1.75:
        flagged = True
    utc_timestamp = datetime.datetime.utcnow()
    cur.execute(f"INSERT INTO {review_type_table_name} VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
    (reviewID, typeID, userID, content, utc_timestamp, review_score, flagged, stars))
    mysql.connection.commit()
    cur.close()
    if flagged:
        message="Created, sentiment inconsistent with previous reviews"
    else: 
        message = "Success"
    review['flagged'] = flagged
    review['date_created'] = utc_timestamp
    return jsonify(message=message, review=review), 200

def get_reviews(mysql, review_type: ReviewType):
    review_type_table_name = review_type.value.get("TableName")
    review_type_ID_column = review_type.value.get("ID")
    typeID = request.args.get(review_type_ID_column)
    cur = mysql.connection.cursor()
    cur.execute(f"""SELECT reviewID, name, content, date_created, flagged, stars from {review_type_table_name} JOIN Users USING (userID) 
                WHERE {review_type_ID_column} = %s AND flagged = false ORDER BY date_created DESC""", [typeID])
    non_flagged_rows = cur.fetchall()
    jobReviews = []
    for row in non_flagged_rows:
        jobReviews.append({"reviewID": row[0], "author": row[1], "content": row[2], "date_created": row[3], "flagged": row[4], "stars": row[5]})
    cur.execute(f"""SELECT reviewID, name, content, date_created, flagged, stars from {review_type_table_name} JOIN Users USING (userID) 
                WHERE {review_type_ID_column} = %s AND flagged = true ORDER BY date_created DESC""", [typeID])
    flagged_rows = cur.fetchall()
    for row in flagged_rows:
        jobReviews.append({"reviewID": row[0], "author": row[1], "content": row[2], "date_created": row[3], "flagged": row[4], "stars": row[5]})
    return jsonify(message="Success", jobReviews=jobReviews), 200
    
def getAverageScore(scores):
    total = 0
    for score in scores:
        total += scoreMap[score]
    return total/len(scores)
