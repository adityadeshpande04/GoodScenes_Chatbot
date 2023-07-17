from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import requests
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
from enum import Enum
from twilio.rest import Client


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:itnabadapasswordkyuchaiye@db.loqxgclpchetzcdaqssm.supabase.co:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class SessionState(Enum):
    GREETING = 'GREETING'
    ASK_CITY = 'ASK_CITY'
    ASK_ACTIVITY = 'ASK_ACTIVITY'
    ASK_BUDGET = 'ASK_BUDGET'
    ASK_PEOPLE_COUNT = 'ASK_PEOPLE_COUNT'
    PDF = 'PDF'
    END='END'


class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_num = db.Column(db.String(50))
    session = db.Column(db.Enum(SessionState))
    is_active=db.Column(db.Boolean,default=True)
    city=db.Column(db.String(50))


class bookings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_num = db.Column(db.String(50))
    location=db.Column(db.String(100))
    category = db.Column(db.Integer, db.ForeignKey('experiences.num'))
    budget = db.Column(db.Float)
    created = db.Column(db.Date, default=datetime.utcnow)
    num_people=db.Column(db.Integer)
    is_done=db.Column(db.Boolean,default=False)

class experiences(db.Model):
    num=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))

@app.route('/bot', methods=['GET', 'POST'])
def bot():
    GREETING_MSG="Hello there! Welcome to GoodScenes, where extraordinary team experiences come to life. Where are you based out of?"
    NON_OPERATIONAL_MSG="We are currently operational only in Bengaluru and we promise we will be operational in your city soon. We shall notify you soon!"
    ASK_BUDGET_MSG="Sure thing! To make sure we find the perfect fit, please share your maximum budget"
    CATALOG_MSG= '''Got it! We'll curate a collection of experiences that match your budget and preferences. One of our team members will be in touch with you soon. 🤝 \nIn the meanwhile would you like to check out catalogue of our most loved experiences? 😍 '''
    CATALOG_LINK="https://drive.google.com/uc?export=download&id=1FwsPrdpYy2ACIde2igqtk8SCLf_mEE4K"
    ASK_NUM_PEOPLE_MSG="How many of you?"
    ENTER_VALID_NUM="Please Enter a Valid Number"
    ENTER_VALID_LOC="Please enter a valid location 😊"
    ENTER_NUM_TILL_7_ERROR="Please enter a number between 1 and 7"
    NO_PROBLEM_MSG="No Problem!"
    SOMETHING_WENT_WRONG_MSG="Oops! Looks like something went wrong. Please send a Hi 👋 to get started"
    categories=experiences.query.all()
    CATEGORY_LIST=[category.num for category in categories]

    incoming_msg = request.values.get('Body', '').lower()
    phone_number = request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()
    account_sid=request.values.get('AccountSid','')

    def check_active_user(num):
        if (user.query.filter_by(phone_num=num).first() is None or user.query.filter_by(phone_num=num).first().is_active==False ):
            return False
        else:
            return True

    def insert_user(num):
        if (check_active_user(num) == False):
            if(user.query.filter_by(phone_num=num).first() is None):
                newU = user(phone_num=request.values.get('From'),session=SessionState.ASK_CITY,is_active=True)
                db.session.add(newU)   
            else:
                user.query.filter_by(phone_num=num).first().session=SessionState.ASK_CITY
                user.query.filter_by(phone_num=num).first().is_active=True
            newUU = bookings(phone_num=request.values.get('From'))
            db.session.add(newUU)
            db.session.commit()
    
    def check_location_validity(user_location):
        api_key = "AIzaSyBsGb--wjjdIRsHSwkNi-_ct0sxoyt_JaU"
        our_location = "Bengaluru"
        flag="Invalid"
        url = f"https://maps.googleapis.com/maps/api/geocode/json?key={api_key}&address={user_location}"
        response = requests.get(url)
        data=response.json()
        if(len(data['results'])>0):
            if our_location in data['results'][0]['formatted_address']:
                flag="Bangalore"
            else:
                flag="Not Bangalore"
        return flag
        

    def greet_user():
        response = GREETING_MSG
        msg.body(response)
        insert_user(phone_number)
    

    def fetch_categories():
        categories=experiences.query.order_by(experiences.num).all()
        list_of_categories="Awesome, What kind of activities are you interested in?\n\nHere are some popular categories to choose from:\n"
        list_of_categories+=''.join([f"{category.num}. {category.name}\n" for category in categories])
        list_of_categories+='\nFor example if you are interested in activity 3 then enter 3.'
        return list_of_categories
    

    def show_category():
        curr_booking=bookings.query.filter_by(phone_num=phone_number,is_done=False).first()
        if(check_location_validity(incoming_msg)!="Invalid"):
            curr_user=user.query.filter_by(phone_num=phone_number).first()
            curr_user.city=incoming_msg
            if check_location_validity(incoming_msg)=="Bangalore":
                response=fetch_categories()
                msg.body(response)
                user.query.filter_by(phone_num=phone_number).first().session=SessionState.ASK_ACTIVITY
            else:
                response= NON_OPERATIONAL_MSG  
                msg.body(response)
                curr_user.is_active=False
                curr_booking.is_done=True
            curr_booking.location=incoming_msg
            db.session.commit()  
        else:
            response=ENTER_VALID_LOC    
            msg.body(response)


    def ask_budget():
        category_num=int(incoming_msg)
        if category_num in CATEGORY_LIST:
            curr_booking=bookings.query.filter_by(phone_num=phone_number,is_done=False).first()
            curr_booking.category=category_num
            db.session.commit()
            response= ASK_BUDGET_MSG
            msg.body(response)
            user.query.filter_by(phone_num=phone_number).first().session=SessionState.ASK_BUDGET
            db.session.commit()
        else:
            response=ENTER_NUM_TILL_7_ERROR
            msg.body(response)


    def ask_num_people():
        if incoming_msg.isdigit():
            curr_booking=bookings.query.filter_by(phone_num=phone_number,is_done=False).first()
            curr_booking.budget=float(incoming_msg)
            db.session.commit()
            response=ASK_NUM_PEOPLE_MSG
            msg.body(response)
            user.query.filter_by(phone_num=phone_number).first().session=SessionState.ASK_PEOPLE_COUNT
            db.session.commit()
        else:
            response=ENTER_VALID_NUM
            msg.body(response)


    def ask_catalog():
        if incoming_msg.isdigit():
            curr_booking=bookings.query.filter_by(phone_num=phone_number,is_done=False).first()
            curr_booking.num_people=int(incoming_msg)
            db.session.commit()
            response= CATALOG_MSG
            msg.body(response)
            curr_user=user.query.filter_by(phone_num=phone_number).first()
            curr_user.session=SessionState.PDF
            db.session.commit()
        else:
            response=ENTER_VALID_NUM
            msg.body(response)


    def send_catalog():
        if 'yes' in incoming_msg:
            msg.media(CATALOG_LINK)
        else:
            response=NO_PROBLEM_MSG
            msg.body(response)
        curr_user=user.query.filter_by(phone_num=phone_number).first()
        curr_user.session=SessionState.END
        curr_user.is_active=False
        curr_booking=bookings.query.filter_by(phone_num=phone_number,is_done=False).first().is_done=True
        db.session.commit()



    if user.query.filter_by(phone_num=phone_number).first() is None or user.query.filter_by(phone_num=phone_number).first().is_active==False:
        greet_user()

    elif user.query.filter_by(phone_num=phone_number).first().is_active==True  and user.query.filter_by(phone_num=phone_number).first().session==SessionState.ASK_CITY:
        show_category()

    elif user.query.filter_by(phone_num=phone_number).first().is_active==True and user.query.filter_by(phone_num=phone_number).first().session==SessionState.ASK_ACTIVITY:
        ask_budget()  

    elif user.query.filter_by(phone_num=phone_number).first().is_active==True and  user.query.filter_by(phone_num=phone_number).first().session==SessionState.ASK_BUDGET:
        ask_num_people()

    elif user.query.filter_by(phone_num=phone_number).first().is_active==True and  user.query.filter_by(phone_num=phone_number).first().session==SessionState.ASK_PEOPLE_COUNT:
        ask_catalog()  
         
    elif user.query.filter_by(phone_num=phone_number).first().is_active==True and  user.query.filter_by(phone_num=phone_number).first().session==SessionState.PDF:
        send_catalog()    
    else:
        msg.body(SOMETHING_WENT_WRONG_MSG)
    return str(resp)

# @app.route('/send_message', methods=['POST'])
# def send_message():
#     phone_number = request.form.get('phone_number')
#     message = request.form.get('message')
    
#     # Use the Twilio client to send the custom message to the user
#     client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
#     message = client.messages.create(
#         body=message,
#         from_=+14155238886,
#         to=phone_number
#     )
    
#     return "Message sent successfully"


if __name__ == '__main__':
    app.debug = True
    app.run(port=4000)
