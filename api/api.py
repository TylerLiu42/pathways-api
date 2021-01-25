from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
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

if __name__ == '__main__':
    app.run(debug=True)
