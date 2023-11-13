from sqlalchemy import create_engine, Column, Integer, String, Text, Date, exc # To handle exceptions while querying
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi import FastAPI, Response, status
from pydantic import BaseModel, parse_obj_as
from typing import Optional, List
import json, os, datetime, requests, pickle
from dotenv import load_dotenv

# To run use the below command from the same directory which has courseregistrationservice.py
# uvicorn courseregistrationservice:app --port 8082 --reload 
# The Swagger API documentation is hosted at http://localhost:8082/docs 

Base = declarative_base()
class Batch(Base):
    __tablename__ = 'courseBatch'

    id = Column(Integer(), primary_key=True)
    courseid = Column(Integer(), nullable=False)
    start_date = Column(String(50), nullable=False)
    end_date = Column(String(50), nullable=False)
    professor = Column(String(100), nullable=False)

class BatchSchema(BaseModel):
    # model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    courseid: int   
    start_date: str
    end_date:str
    professor:str

    class Config:
        orm_mode = True

class Registration(Base):
    __tablename__ = 'courseRegistration'

    id = Column(Integer(), primary_key=True)
    userid = Column(Integer(), nullable=False)
    courseid = Column(Integer(), nullable=False)
    batchid = Column(Integer(), nullable=False)
    registration_date = Column(String(100), nullable=False)
    payment_mode = Column(String(20), nullable=False)
    payment_status = Column(String(20), nullable=False)

class RegistrationSchema(BaseModel):
    # model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    userid: int  
    courseid: int
    batchid: int   
    registration_date: str
    payment_mode:str
    payment_status:str

    class Config:
        orm_mode = True

#Read the environment variables
print("Loading Environment Variables")
load_dotenv('.env')
app = FastAPI()

USER_SERVICE_URL = os.environ['UserServiceBaseURL']
COURSE_SERVICE_URL = os.environ['CourseServiceBaseURL']

#Construct the DB Connection URL using environment variable
url = URL.create( drivername=os.environ['DB_Driver'], username=os.environ['DB_Username'], password=os.environ['DB_Password'], host=os.environ['DB_Host'], database=os.environ['Database'])
engine = create_engine(url)
print("Connecting to database")
connection = engine.connect()
print("Connection successful ")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


@app.get('/batches')
def getAllBatches(response: Response):
    batches = session.query(Batch).all()

    if len(batches) == 0: #No batches exists return appropraite HTTPS response
        response.status_code = status.HTTP_200_OK 
        retString = "No batches exists in the course batch database"
        json_string = '{"message": "' + retString + '"}'
        return json.loads(json_string)
    else:
        batch_list = parse_obj_as(List[BatchSchema], batches)
        response.status_code = status.HTTP_200_OK
        return batch_list

@app.get('/batches/{u_id}')
def get_batch(u_id: int, response: Response):
    batches = session.query(Batch).filter(Batch.id == u_id).all()
    if len(batches) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND 
        retString = "Batch with id " + str(u_id) + " does not exists in the course batch database"
        json_string = '{"message": "' + retString + '"}'
        return json.loads(json_string)
    else:
        batch_list  = parse_obj_as(List[BatchSchema], batches)
        response.status_code = status.HTTP_200_OK
        return batch_list

@app.delete('/batches/{u_id}',status_code=202)
def delete_batch(u_id: int):
    try:
        retValue = session.query(Batch).filter(Batch.id==u_id).delete()

        if retValue == 0:
            retString = "batch with batch id " + str(u_id) + " does not exists"
            json_string = '{"message": "' + retString + '"}'
            return json.loads(json_string)
        else:
            session.commit()
            retString = "batch with batch id " + str(u_id) + " deleted successfully"
            json_string = '{"message": "' + retString + '"}'
            return json.loads(json_string)
    except:
        session.rollback()
        print('Exception occurred while deleting')

@app.post('/batches', status_code=201)
def new_batch(batchObj: BatchSchema, response: Response):
    batches = session.query(Batch).all()
    #Call the course service to check if course id exists
    try:
        end_point =  COURSE_SERVICE_URL + "/courses/" + str(batchObj.courseid)
        print("Before adding batch Communicating with course service at the endpoint:: " + end_point)
        response = requests.get(end_point)
        if response.status_code == 200:
            print("Successfully validated the course " + str(batchObj.courseid) + " exists in course service")
        else:
            print("course service returned with Status " + str(response.status_code) + " and response text as " + response.text)
            response.status_code = status.HTTP_400_BAD_REQUEST
            retString = "Course with Course id " + str(batchObj.courseid)+ " does not exists in course service"
            json_string = '{"message": "' + retString + '"}'
            return json.loads(json_string)
    except Exception as e:
         print(e)
         print("Error: Failed to communicate with the course service server. Ensure that the server is running")
         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR 
         retString = "Exception occured communicating with course service"
         json_string = '{"message": "' + retString + '"}'
         return json.loads(json_string)


    if len(batches) == 0:
        u_id = 1
    else:
        max_id = 1
        for u in batches:
            if u.id > max_id:
                max_id = u.id
        u_id = max_id + 1

    new_batch = Batch(
        id=u_id,
        courseid = batchObj.courseid,
        start_date = batchObj.start_date,
        end_date = batchObj.end_date,
        professor=batchObj.professor
    )

    try:
        session.add(new_batch)
        session.commit()
        return BatchSchema.from_orm(new_batch)
    
    except exc.IntegrityError:
        session.rollback()
        print("Exception Occured")
        return "Unable to add duplicate values"
    
@app.get('/registrations')
def getAllRegistrations(response: Response):
    registrations = session.query(Registration).all()
  
    if len(registrations) == 0: #No batches exists return appropraite HTTPS response
        response.status_code = status.HTTP_200_OK 
        retString = "No registrations exists in the registration database"
        json_string = '{"message": "' + retString + '"}'
        return json.loads(json_string)
    else:
        registration_list = parse_obj_as(List[RegistrationSchema], registrations)
        response.status_code = status.HTTP_200_OK
        return registration_list

@app.get('/registrations/{u_id}')
def get_registration(u_id: int, response: Response):
    registrations = session.query(Registration).filter(Registration.id == u_id).all()
    if len(registrations) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND 
        retString = "Registration with id " + str(u_id) + " does not exists in the registration database"
        json_string = '{"message": "' + retString + '"}'
        return json.loads(json_string)
    else:
        registration_list  = parse_obj_as(List[RegistrationSchema], registrations)
        response.status_code = status.HTTP_200_OK
        return registration_list

@app.delete('/registrations/{u_id}',status_code=202)
def delete_registration(u_id: int):
    try:
        retValue = session.query(Registration).filter(Registration.id==u_id).delete()

        if retValue == 0:
            retString = "registration with registration id " + str(u_id) + " does not exists"
            json_string = '{"message": "' + retString + '"}'
            return json.loads(json_string)
        else:
            session.commit()
            retString = "registration with registration id " + str(u_id) + " deleted successfully"
            json_string = '{"message": "' + retString + '"}'
            return json.loads(json_string)
    except:
        session.rollback()
        print('Exception occurred while deleting')

@app.post('/registrations', status_code=201)
def new_registration(registrationObj: RegistrationSchema):
    registrations = session.query(Registration).all()

    # Validating that user exists in user service before registering the user
    try:
        end_point =  USER_SERVICE_URL + "/users/" + str(registrationObj.userid)
        print("Before Registration Communicating with user service at the endpoint:: " + end_point)
        response = requests.get(end_point)
        if response.status_code == 200:
            print("Successfully validated the user " + str(registrationObj.userid) + " exists in user service")
        else:
            print("user service returned with status " + str(response.status_code) + " and response text as " + response.text)
            response.status_code = status.HTTP_400_BAD_REQUEST
            retString = "User with user id " + str(registrationObj.userid) +" does not exists in user service"
            json_string = '{"message": "' + retString + '"}'
            return json.loads(json_string)
    except Exception as e:
         print(e)
         print("Error: Failed to communicate with the user service server. Ensure that the server is running")
         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR 
         retString = "Exception occured communicating with user service"
         json_string = '{"message": "' + retString + '"}'
         return json.loads(json_string)

    # Validating that course exists in course service before registering the user
    try:
        end_point =  COURSE_SERVICE_URL + "/courses/" + str(registrationObj.courseid)
        print("Before Registration Communicating with course service at the endpoint:: " + end_point)
        response = requests.get(end_point)
        if response.status_code == 200:
            print("Successfully validated the course " + str(registrationObj.courseid) + " exists in course service")
        else:
            print("course service returned with status " + str(response.status_code) + " and response text as " + response.text)
            response.status_code = status.HTTP_400_BAD_REQUEST
            retString = "Course with Course id " + str(registrationObj.courseid)+ " does not exists in course service"
            json_string = '{"message": "' + retString + '"}'
            return json.loads(json_string)
    except Exception as e:
         print(e)
         print("Error: Failed to communicate with the course service server. Ensure that the server is running")
         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR 
         retString = "Exception occured communicating with course service"
         json_string = '{"message": "' + retString + '"}'
         return json.loads(json_string)

    if len(registrations) == 0:
        u_id = 1
    else:
        max_id = 1
        for u in registrations:
            if u.id > max_id:
                max_id = u.id
        u_id = max_id + 1

    new_registration = Registration(
        id=u_id,
        userid = registrationObj.userid,
        courseid = registrationObj.courseid,
        batchid = registrationObj.batchid,
        registration_date = registrationObj.registration_date,
        payment_mode=registrationObj.payment_mode,
        payment_status=registrationObj.payment_status,
    )

    try:
        session.add(new_registration)
        session.commit()
        return RegistrationSchema.from_orm(new_registration)
    
    except exc.IntegrityError:
        session.rollback()
        print("Exception Occured")
        return "Unable to add duplicate values"


    