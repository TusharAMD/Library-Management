from flask import Flask, render_template, url_for, request, session, redirect
import bcrypt
import pymongo
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage

app = Flask(__name__)
import bcrypt
@app.route('/')
def index():
    if 'username' in session:
        
        context={}
        context["username"]=session["username"]
        return render_template('index2.html', context=context)
    return render_template('index.html')

@app.route('/loginpage')
def loginpage():
    return render_template('login.html')
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))  

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["Librarian"]

        login_user = collection.find_one({'name' : request.form['username']})

        if login_user:
            if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                return redirect(url_for('index'))

        return 'Invalid username/password combination'

@app.route('/registerpage', methods=['POST', 'GET'])
def registerpage():
    return render_template('register.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["Librarian"]
        
        existing_user = collection.find_one({'name' : request.form['username']})

        if existing_user is None:
        
            ### Send Email ###
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login("infomailtva@gmail.com", "@#password123")
            message = EmailMessage()
            message.set_content('''\
            <!DOCTYPE html>
            <html>
                <body>
                   <div style="background-color:black;color:white;">
                   <h3>Your password is '''+str(request.form["password"])+'''</h3>
                   </div>
                </body>
            </html>
            ''', subtype='html')
            message['Subject'] = f'Your Password for User {request.form["username"]}'
            message['From'] = "infomailtva@gmail" 
            message['To'] = request.form["email"]
            s.send_message(message)
            #### Email Done ####
            
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            collection.insert({'email' : request.form['email'],'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        
        return 'That username already exists!'

    return render_template('register.html')


@app.route('/add')
def bookadd():
    return render_template('bookadd.html')
@app.route('/addredirect', methods=['POST', 'GET'])
def bookaddredirect():
    if request.method == 'POST':
        bookdata={}
        print(request.form)
        bookdata["book-name"]=request.form["book-name"]
        bookdata["book-isbn"]=request.form["book-isbn"]
        bookdata["taken-by"]=request.form["taken-by"]
        bookdata["date-taken"]=request.form["date-taken"]
        
        f = request.files['book-image']  
        f.save(f.filename)
        
        ###DATABASE###
        
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["books"]
        collection.insert_one(bookdata)
        
        
        ###OVER###
        
        
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)