from flask import Flask, request
from flask_mysqldb import MySQL 
import sys
app = Flask(__name__)

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
    if role != 'applicant' and role != 'employer' and role != 'mentor':
        return "Invalid role", 400
    name = user.get('name')
    cur = mysql.connection.cursor()
    cur.execute("SELECT userID from Users where userID = %s", [user_id])
    users = cur.fetchall()
    print('rowcount: ' + str(cur.rowcount), file=sys.stderr)
    if (cur.rowcount == 0):
        print(role, len(role), file=sys.stderr)
        cur.execute("INSERT INTO Users VALUES (%s, %s, %s)", (user_id, name, role))
        mysql.connection.commit()
        cur.close()
        return "Created new user", 200
    cur.close()
    return "User already exists", 403
    
if __name__ == '__main__':
    app.run(debug=True)