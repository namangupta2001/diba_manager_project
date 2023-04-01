from flask import Flask,render_template,request,session, make_response
from flask_mysqldb import MySQL
import base64
app = Flask(__name__)
app.debug=True
app.secret_key = 'secret'

app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'diba_manager_proj'

mysql=MySQL(app)


@app.route('/view_reports')
def view_reports():
    # email=session['email']
    cur = mysql.connection.cursor()

    cur.execute('SELECT pp,fast,date FROM reports WHERE email = %s', ("soumil",))
    tuple_reports=cur.fetchall()
    print(tuple_reports)

    return render_template("view_reports.html",items=tuple_reports)

@app.route('/')
def hello_world():
    return render_template('html.html')

@app.route('/view')
def view():
    email = "anurag"
    cur = mysql.connection.cursor()
    cur.execute('SELECT email,file FROM reports WHERE email = %s', (email,))
    email, file = cur.fetchone()
    cur.close()
    content_type = 'application/pdf'

    # create response with file data and content type
    response = make_response(file)
    response.headers['Content-Type'] = content_type 
    response.headers['Content-Disposition'] = 'inline; filename=' + email
    return response




@app.route('/upload', methods=['POST'])
def upload():

    file = request.files['file']
    # name = request.form['name']
    # description = request.form['description']
    filename=file.filename
    file = file.read()
   
    # data = file.read()
    cursor = mysql.connection.cursor()
    email=session['email']
 
    cursor.execute("""INSERT INTO reports(email,file) VALUES (%s, %s)""", (email, file))
    mysql.connection.commit()
    cursor.close()

    return f'File {filename}uploaded successfully'

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
