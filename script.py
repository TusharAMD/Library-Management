from flask import Flask, render_template, url_for, request, session, redirect
import bcrypt
import pymongo
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
import base64
import requests
import datetime

app = Flask(__name__)
app.secret_key = 'mysecret'
import bcrypt
@app.route('/')
def index():
    if 'username' in session:
        context={}
        context["username"]=session["username"]
        if session['roles'] == "student":
            return render_template('index3.html', context=context)
        else:
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
            collection.insert({'email' : request.form['email'],'name' : request.form['username'], 'password' : hashpass, 'role':request.form['roles']})
            session['username'] = request.form['username']
            session['roles'] = request.form['roles']
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
        
        ###SAVE IMAGE TO IMG BB###

        with open(f"{f.filename}", "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": "c4b63af118f97f88cdeea980cdb4d6c9",
                "image": base64.b64encode(file.read()),
            }
            res = requests.post(url, payload)
            print(res.json()["data"]["url"])
            bookdata["book-image"]=res.json()["data"]["url"]
        
        ### DONE ###
        
        ###STU DATABASE###
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["students"]
        student_details = collection.find_one({"student_email":bookdata["taken-by"]})
        if student_details == None:
            return("This student is not registered")
        elif student_details["how_many_books"]>3:
            return("This student already has 3 books")
        elif student_details["isDefaulter"]==True:
            return("This student is defaulter")
        elif student_details["isactive"]==False:
            return("This student account is banned")
        
        
        collection.update_one({"student_email": bookdata["taken-by"]},{ "$set": { "how_many_books": student_details["how_many_books"]+1} })
        
        ###################
        
        
        ###DATABASE###
        
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["books"]
        collection.insert_one(bookdata)        
        ###OVER###
        
        
    return redirect(url_for('index'))

@app.route('/remove')
def bookdelete():
    return render_template('bookdelete.html')
@app.route('/removeredirect', methods=['POST', 'GET'])
def bookdeleteredirect():
    if request.method == 'POST':
        bookdata={}
        bookdata["book-isbn"]=request.form["book-isbn"]
        
        ###DATABASE###
        
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["books"]
        collection.delete_one(bookdata)        
        ###OVER###
        
        
    return redirect(url_for('index'))

@app.route('/search')
def search():

    #print(request.args.get('messages'),"messages")
    
    if request.args.get('messages') != None:
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["books"]

        context=collection.find({"book-isbn":request.args.get('messages')})
    else:
        ###DATABASE###        
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["books"]
        print(collection.find())
        context=collection.find()
        ###OVER###
    
    return render_template('search.html',context=context)

@app.route('/searchredirect', methods=['POST', 'GET'])
def searchredirect():
    if request.method == 'POST':
        print(request.form['book-isbn'])
    return redirect(url_for('search',messages=request.form['book-isbn']))

@app.route('/update')
def bookupdate():
    return render_template('bookupdate.html')
@app.route('/updateredirect', methods=['POST', 'GET'])
def bookupdateredirect():
    if request.method == 'POST':
        bookdata={}
        print(request.form)
        bookdata["book-name"]=request.form["book-name"]
        bookdata["book-isbn"]=request.form["book-isbn"]
        bookdata["taken-by"]=request.form["taken-by"]
        bookdata["date-taken"]=request.form["date-taken"]
        
        f = request.files['book-image']  
        f.save(f.filename)
        
        ###SAVE IMAGE TO IMG BB###

        with open(f"{f.filename}", "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": "c4b63af118f97f88cdeea980cdb4d6c9",
                "image": base64.b64encode(file.read()),
            }
            res = requests.post(url, payload)
            print(res.json()["data"]["url"])
            bookdata["book-image"]=res.json()["data"]["url"]
        
        ### DONE ###
        
        
        ###STU DATABASE###
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["students"]
        student_details = collection.find_one({"student_email":bookdata["taken-by"]})
        if student_details == None:
            return("This student is not registered")
        elif student_details["how_many_books"]>=3:
            return("This student already has 3 books")
        elif student_details["isDefaulter"]==True:
            return("This student is defaulter")
        elif student_details["isactive"]==False:
            return("This student account is banned")
        
        
        collection.update_one({"student_email": bookdata["taken-by"]},{ "$set": { "how_many_books": student_details["how_many_books"]+1} })
        
        ###################
        
        
        ###DATABASE###
        
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["books"]
        
        myquery = { "book-isbn": bookdata["book-isbn"] }
        newvalues = { "$set": { "book-name": bookdata["book-name"] , "taken-by": bookdata["taken-by"], "date-taken": bookdata["date-taken"]} }

        collection.update_one(myquery, newvalues)
      
        ###OVER###        
    return redirect(url_for('index'))


###### STUDENT MANAGEMENT #######

@app.route('/addstu')
def stuadd():
    return render_template('stuadd.html')
@app.route('/addsturedirect', methods=['POST', 'GET'])
def stuaddredirect():
    if request.method == 'POST':
        studata={}
        print(request.form)
        studata["student_name"]=request.form["student_name"]
        studata["student_id"]=request.form["student_id"]
        studata["student_class"]=request.form["student_class"]
        studata["student_email"]=request.form["student_email"]
        studata["how_many_books"]=0
        studata["countViolation"]=0
        studata["isDefaulter"]=False
        studata["isactive"]=True
        
        f = request.files['student_image']  
        f.save(f.filename)
        
        ###SAVE IMAGE TO IMG BB###

        with open(f"{f.filename}", "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": "c4b63af118f97f88cdeea980cdb4d6c9",
                "image": base64.b64encode(file.read()),
            }
            res = requests.post(url, payload)
            print(res.json()["data"]["url"])
            studata["student_image"]=res.json()["data"]["url"]
        
        ### DONE ###
        
        ###DATABASE###
        
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["students"]
        collection.insert_one(studata)        
        ###OVER###
        
        
    return redirect(url_for('index'))


@app.route('/allstudents')
def searchstu():

    #print(request.args.get('messages'),"messages")
    
    if request.args.get('messages') != None:
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["students"]

        context=collection.find({"student_id":request.args.get('messages')})

        print(context,"context")
    else:
        ###DATABASE###        
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["students"]
        print(collection.find())
        context=collection.find()
        ###OVER###
    
    return render_template('searchstu.html',context=context)

@app.route('/searchsturedirect', methods=['POST', 'GET'])
def searchsturedirect():
    if request.method == 'POST':
        print(request.form['studentid'])
    return redirect(url_for('searchstu',messages=request.form['studentid']))
    
    
    
######### updateStudent ############    

@app.route('/updateStudent')
def updateStudent():
    
    return render_template('updateStudent.html')
@app.route('/updateStudentredirect', methods=['POST', 'GET'])
def updateStudentredirect():
    if request.method == 'POST':
        studata={}
        print(request.form)
        studata["student_name"]=request.form["student_name"]
        studata["student_id"]=request.form["student_id"]
        studata["student_class"]=request.form["student_class"]
        studata["student_email"]=request.form["student_email"]
        studata["how_many_books"]=request.form["how_many_books"]
        studata["countViolation"]=int(request.form["countViolation"])
        studata["isDefaulter"]=eval(request.form["isDefaulter"])
        studata["isactive"]=eval(request.form["isactive"])
        
        f = request.files['student_image']  
        f.save(f.filename)
        
        ###SAVE IMAGE TO IMG BB###

        with open(f"{f.filename}", "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": "c4b63af118f97f88cdeea980cdb4d6c9",
                "image": base64.b64encode(file.read()),
            }
            res = requests.post(url, payload)
            print(res.json()["data"]["url"])
            studata["student_image"]=res.json()["data"]["url"]
        
        ### DONE ###
        
        ###DATABASE###
        
        client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        db = client['Library']
        collection = db["students"]
        myquery = { "student_email": studata["student_email"] }
        newvalues = { "$set": studata }

        collection.update_one(myquery, newvalues)        
        ###OVER###
        
        
    return redirect(url_for('index'))
    
@app.route('/sendReminders')
def reminders():
     client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.wonbr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
     db = client['Library']
     collection = db["books"]
     collection2 = db["students"]
     allbooks = collection.find()
     for ele in allbooks:
        #print(ele)
        
        timedelta = datetime.datetime.now() - datetime.datetime.strptime(ele["date-taken"], "%Y-%m-%d")
        
        x = collection2.find_one({"student_email":ele['taken-by']})
        
        try:
            if timedelta.days >= 12 and timedelta.days < 15:
                print(collection2.find_one({"student_email":ele['taken-by']}))
                
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
                       <h3>Your Book Due date is near'''+"\n"+str(f"Book Name {ele['book-name']}")+''''</h3>
                       </div>
                    </body>
                </html>
                ''', subtype='html')
                message['Subject'] = f"Book Name {ele['book-name']}"
                message['From'] = "infomailtva@gmail" 
                message['To'] = ele['taken-by']
                s.send_message(message)
                #### Email Done ####
                collection2.update_one({"student_email":ele['taken-by']},{ "$set": { "isDefaulter": True } })
            elif timedelta.days >= 15:
                collection2.update_one({"student_email":ele['taken-by']},{ "$set": { "countViolation": x["countViolation"]+1 } })
            if x["countViolation"] >=3:
                collection2.update_one({"student_email":ele['taken-by']},{ "$set": { "isactive": False}})
        except:
            pass
        
     return("ok")

if __name__ == '__main__':
    
    app.run(debug=True)