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
    return jsonify(message="Post created"), 200

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
    cur = mysql.connection.cursor()
    cur.execute("""SELECT Users.name, score, title, date_created from 
        ForumPost JOIN Users ON ForumPost.author = Users.userID where topic = %s 
        order by date_created desc limit %s, %s""", (topic, int(index), int(limit)))
    rows = cur.fetchall()
    response = []
    for row in rows:
        post = {'authorName': row[0], 'score': row[1], 'title': row[2], 'date_created': row[3]}
        response.append(post)
    cur.close()
    return jsonify(response), 200

def get_single_post(mysql):
    postID = request.args.get('id')
    cur = mysql.connection.cursor()
    cur.execute("SELECT content from ForumPost where postID = %s", [postID])
    row = cur.fetchall()
    return jsonify(content = row[0][0]), 200

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
        
