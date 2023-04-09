from flask import Flask,render_template,request,session, make_response,render_template_string
from flask_mysqldb import MySQL
import PyPDF2
import re
import io
import io
import base64
import matplotlib.pyplot as plt
from datetime import datetime
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
     
            pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(file))
            text = ''
            for page in range(pdf_reader.getNumPages()):
                text += pdf_reader.getPage(page).extractText()

            hb_pattern ='HbA1c\s+\(GLYCOSYLATED HEMOGLOBIN\), \(HPLC\)[\n ]+BLOOD[\n ]+Method : HPLC METHOD[\n ]+(\d+\.\d+)\n'
            hb_match = re.search(hb_pattern, text)
            if hb_match:
                hb_value = float(hb_match.group(1))
                return hb_value
              
            else:
                print("HbA1c value not found")


@app.route('/chart')
def chart():
    email=session['email']
    cur = mysql.connection.cursor()
    cur.execute('SELECT DATE(date) as date, pp,fast,HbA1C FROM reports WHERE email = %s ', (email,))
    chart_data = cur.fetchall()
    cur.close()
    # print(chart_data)
    x_data=[]
    y1_data=[]
    y2_data=[]
    y3_data=[]

    for i in chart_data:
        x_data.append(str(i[0]))
        y1_data.append(i[1])
        y2_data.append(i[2])
        y3_data.append(i[3])
    # dates = ['2022-01-01', '2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01']
    # x_data = [datetime.strptime(date, '%Y-%m-%d').date() for date in x_data]
    print(x_data)
    # y_data = [20, 10, 30, 15, 25]
    
    # Create a line chart using matplotlib
    fig, ax = plt.subplots()
    ax.plot(x_data, y1_data)
    ax.set_xlabel('Dates')
    ax.set_ylabel('Values of PP')
    # Save the chart to a bytes buffer
    buffer = io.BytesIO()
    fig.set_size_inches(10, 6) 
    fig.canvas.print_png(buffer)
    buffer.seek(0)

    # Encode the bytes buffer as base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Generate the HTML template for the chart
    html = """
     <html>
        <head>
            <title>Line Chart</title>
            <style>
                .chart-container {
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="chart-container">
                <h1>PP Line Chart</h1>
                <img src="data:image/png;base64,{{ image_base64 }}">
            </div>
        </body>
    </html>
    """

    # Render the HTML template with the chart data
    return render_template_string(html, image_base64=image_base64)

@app.route('/view_reports')
def view_reports():
    email=session['email']
    cur = mysql.connection.cursor()
    cur.execute('SELECT date,pp,fast,HbA1C FROM reports WHERE email = %s', (email,))
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
 
    cursor.execute("""INSERT INTO reports(email,file,pp,fast,HbA1C) VALUES (%s, %s,%s,%s,%s)""", (email,file,pp,fast,hb_value))
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
