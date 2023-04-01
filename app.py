from flask import Flask,render_template,request,session
from flask_mysqldb import MySQL
import base64
app = Flask(__name__)
app.secret_key = 'secret'

app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'diba_manager_proj'

mysql=MySQL(app)

@app.route('/')
def hello_world():
    return render_template('html.html')

@app.route('/upload', methods=['POST'])
def upload():

    file = request.files['file']
    # name = request.form['name']
    # description = request.form['description']
    mimetype = file.mimetype
    # data = file.read()
    cursor = mysql.connection.cursor()
    email=session['email']

    # Convert file data to base64 string
    # encoded_data = base64.b64encode(data).decode('utf-8')

    # Insert file into database
    cursor.execute("""
        INSERT INTO reports(email,file)
        VALUES (%s, %s)
    """, (email, mimetype))
    mysql.connection.commit()
    cursor.close()

    return 'File uploaded successfully'

@app.route('/login', methods=['POST'])
def login():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        
        #Store the data in session
        session['email'] = email
        session['password'] = password

        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT * FROM user_login WHERE email=%s and password=%s''',(email,password))
        result=cursor.fetchone()

        print(result)
        mysql.connection.commit()
        cursor.close()
        if result:       
            return render_template("dashboard.html",session=session)
        else:
            return "invalid credentials"

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']
    cnfpass = request.form['cnfpass']

    session['email'] = email
    session['password'] = password

    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT email FROM user_login''')
    tuple_email=cursor.fetchall()
    list_email=[]

    for i in tuple_email:
        if i:
            list_email.append(i[0])
   
    print(list_email)   
    if password==cnfpass :
        if email not in list_email:

            cursor.execute('''INSERT INTO user_login(email,password) values(%s,%s)''',(email,password))
            mysql.connection.commit()
            cursor.close()
            return f"Signup Successfully {email}"
        else:
            return "email already registered"
    else:
        return "passwords didnot matched"

if __name__ == '__main__':
    app.run()
