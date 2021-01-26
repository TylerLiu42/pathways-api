import uuid
import sys
from uuid import uuid4
from flask import request, jsonify, escape

def create_forum_post(mysql):
    postID = uuid4()
    post = request.get_json() 
    topic = post.get('topic')
    author = post.get('author')
    title = post.get('title')
    content = escape(post.get('content'))
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO ForumPost VALUES (%s, %s, 0, %s, %s, NOW(), %s)", (postID, topic, author, title, content))
    mysql.connection.commit()
    cur.close()
    return jsonify(message="Post created", post_url="/forum/%s/%s" %(topic, postID)), 200

def create_forum_reply(mysql):
    replyID = uuid4()
    reply = request.get_json()
    postID = reply.get('postID')
    author = reply.get('author')
    content = escape(reply.get('content'))
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO ForumReply VALUES (%s, %s, %s, 0, NOW(), %s)", (replyID, postID, author, content))
    mysql.connection.commit()
    cur.close()
    return jsonify(message="Reply created"), 200

def get_posts(mysql):
    index = request.args.get('index')
    limit = request.args.get('limit') 
    topic = request.args.get('topic')
    userID = request.args.get('userID')
    cur = mysql.connection.cursor()
    cur.execute("""SELECT Users.name, score, title, date_created, postID from 
        ForumPost JOIN Users ON ForumPost.author = Users.userID where topic = %s 
        order by date_created desc limit %s, %s""", (topic, int(index), int(limit)))
    rows = cur.fetchall()
    response = []
    for row in rows:
        cur.execute("SELECT rating from PostRating where userID = %s and postID = %s", (userID, row[4]))
        if cur.rowcount == 0:
            userVoted = ''
        else:
            userVoted = cur.fetchall()[0][0]
        post = {'authorName': row[0], 'rating': {'score': row[1], "userVoted": userVoted}, 'title': row[2], 'date_created': row[3]}
        response.append(post)
    cur.execute("SELECT COUNT(PostID) from ForumPost where topic = %s", [topic])
    totalRows = cur.fetchall()[0][0]
    cur.close()
    return jsonify(posts=response, totalPosts=totalRows), 200

def get_single_post(mysql):
    postID = request.args.get('id')
    cur = mysql.connection.cursor()
    cur.execute("SELECT title, score, author, content, date_created from ForumPost where postID = %s", [postID])
    row = cur.fetchall()
    if (len(row) == 1):
        return jsonify(title=row[0][0], score=row[0][1], author=row[0][2], content=row[0][3], date_created=row[0][4]), 200
    return jsonify(message="Could not find post."), 400

def get_replies(mysql):
    postID = request.args.get('postID')
    cur = mysql.connection.cursor()
    cur.execute("""SELECT Users.name, score, date_created, content from 
        ForumReply JOIN Users ON ForumReply.author = Users.userID where postID = %s order by date_created desc""", [postID])
    rows = cur.fetchall()
    response = []
    for row in rows:
        reply = {'authorName': row[0], 'score': row[1], 'date_created': row[2], 'content': row[3]}
        response.append(reply)
    cur.close()
    return jsonify(response), 200

def vote_post():
    #WIP
    payload = request.get_json()
    userID = payload.get('userID')
    postID = payload.get('postID')
    rating = payload.get('rating')
    if rating.lower() != 'up' and rating.lower != 'down':
        return jsonify(message="Invalid rating"), 400
    cur = mysql.connection.cursor()
    
    if rating.lower() == 'up':
        cur.execute("UPDATE Posts SET score = score + 1 WHERE postID = %s", [postID])
    else:
        cur.execute("UPDATE Posts SET score = score - 1 WHERE postID = %s", [postID])
    
