from flask import Flask,render_template,request,session, make_response,jsonify
from flask_mysqldb import MySQL
import PyPDF2
import re
import io

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

def extract_hba1c(file):
        # filename=file.filename
        # extension = os.path.splitext(filename)[1]
        # if extension == '.pdf':
            # Load PDF file
            pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(file))
            text = ''
            for page in range(pdf_reader.getNumPages()):
                text += pdf_reader.getPage(page).extractText()
        # elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        #     # Perform OCR on image file
        #     image = cv2.imdecode(numpy.frombuffer(file.read(), numpy.uint8), cv2.IMREAD_UNCHANGED)
        #     text = pytesseract.image_to_string(image)
        # else:
        #     print("Unsupported file format")

        # Find HbA1c value from OCR output
            hb_pattern ='HbA1c\s+\(GLYCOSYLATED HEMOGLOBIN\), \(HPLC\)[\n ]+BLOOD[\n ]+Method : HPLC METHOD[\n ]+(\d+\.\d+)\n'
            hb_match = re.search(hb_pattern, text)
            if hb_match:
                hb_value = float(hb_match.group(1))
                return hb_value
              
            else:
                print("HbA1c value not found")


@app.route('/view_reports')
def view_reports():
    email=session['email']
    cur = mysql.connection.cursor()
    cur.execute('SELECT date,pp,fast FROM reports WHERE email = %s', (email,))
    tuple_reports=cur.fetchall()
    # print(tuple_reports)
    return render_template("view_reports.html",items=tuple_reports,session=session)

@app.route('/')
def hello_world():
    return render_template('html.html')

@app.route('/view', methods=['POST'])
def view():
    email = session['email']
    date = request.form['view']
    cur = mysql.connection.cursor()
    cur.execute('SELECT email,file FROM reports WHERE email = %s AND date=%s', (email,date))
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
    pp = request.form['pp']
    fast = request.form['fast']
    filename=file.filename
    file = file.read()
    
    ##passing the file to db
    hb_value=extract_hba1c(file)
  
 
    cursor = mysql.connection.cursor()
    email=session['email']
 
    cursor.execute("""INSERT INTO reports(email,file,pp,fast) VALUES (%s, %s,%s,%s)""", (email,file,pp,fast))
    mysql.connection.commit()
    cursor.close()

    return f'File {filename}uploaded successfully {str(hb_value)}'

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

        # print(result)
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
   
    # print(list_email)   
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
