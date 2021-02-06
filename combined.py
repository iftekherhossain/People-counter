import dlib
import cv2
from face_main import Face_utils,Database_Utils
import numpy as np
from tensorflow.keras.models import load_model
import os 
import sqlite3
import array
import pickle
from datetime import datetime
from pytictoc import TicToc
from imutils.video import WebcamVideoStream as webcam
from imutils.video import FPS

#---------for database----------#
#------------------------------------------#
f= Face_utils()
da = Database_Utils('people.db')
da.create_table()
print("table create done")
#------database end------_#
#----------------------------------------#
print("Starting Video.....")
vs_entry = webcam(0).start()
vs_exit = webcam(1).start()
print("Entry Camera found")
print("Loading model.....")
model = load_model("facenet_keras.h5")
cascade_path = "haarcascade_frontalface_default.xml"
#-----------------------------------------------------#
try:
    a = da.read_last_entry()
    print("aaassss",a)
except:
    a=0
    print("aaassss",a)

i=0
try:
    data = da.read_from_db()
    for d in data:
        img_blob = d[1]
        id = d[0]
        #/home/pi/Peple_counter/faces
        da.write_to_file(img_blob,'/faces'+'/'+str(id)+'.jpg')
except:
    print("read_from_db_failed")
temp_database = f.update_temp_database_enter()
p=a
path_proto = 'deploy.prototxt.txt'
path_model = 'res10_300x300_ssd_iter_140000.caffemodel'
net = cv2.dnn.readNetFromCaffe(path_proto, path_model)
#--------------------------------------#
co =0
t = TicToc()
t.tic()
fps = FPS().start()
frames_after_insertion = 100
temp_database = []
last_id = p
entered_entry = []

def entry_func(frame):
    global p
    global temp_database
    entered_people = []
    boxes = f.detect_face_dnn(net,frame,0.7)
    entered_people = list(filter(lambda x:x[2]=='Entered',temp_database))
    #cheak for if the boxes are tuple or not
    check_tuple = type(boxes) is tuple
    if len(boxes)>=1 and not check_tuple:
        for box in boxes:
            x,y,w,h = box[0],box[1],box[2],box[3]
            tup_box = (x,y,w,h)
            
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
            try:
                face = f.return_face(frame,tup_box)
            except:
                cv2.imshow('Entry Camera', frame)
                continue
            real_emd = f.face_embedding(model,face)
            if len(temp_database)==0:
                state = 'Entered'
                enty_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                p+=1
                people = (p,real_emd,state,enty_time,"")
                temp_database.append(people)
                #da.data_entry(p,face,state,enty_time,"")
            else:
                count =0
                for t_d in temp_database:
                    id, emd,entered,entry_time, exit_time = t_d
                    print("ss",f.compare_embeddings(emd,real_emd))
                    if f.compare_embeddings(emd,real_emd)<12:
                        break
                    else:
                        count+=1
                    if count==len(temp_database):
                        state = 'Entered'
                        enty_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        p+=1
                        people = (p,real_emd,state,entry_time,"")
                        temp_database.append(people)
                        #da.data_entry(p,face,state,enty_time,"")
                    else:
                        continue
            print(entered_people)
            cv2.putText(frame, 'People in the room: '+str(len(temp_database)), (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2, cv2.LINE_AA)
            cv2.imshow('Entry Camera', frame)
    else:
        cv2.putText(frame, 'People in the room: '+str(len(entered_people)), (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2, cv2.LINE_AA)
        cv2.imshow('Entry Camera', frame)
    
def exit_func(frame):
    global temp_database
    global p
    exited_person = []
    boxes = f.detect_face_dnn(net,frame,0.5)
    check_tuple = type(boxes) is tuple
    #print(boxes)
    exited_person = list(filter(lambda x:x[2]=='Exited',temp_database))
    if len(boxes)>=1 and not check_tuple:
        for box in boxes:
            #box = boxes[0]
            x,y,w,h = box[0],box[1],box[2],box[3]
            tup_box = (x,y,w,h)
            #print(tup_box)
            
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
            face = f.return_face(frame,tup_box)
            real_emd = f.face_embedding(model,face)
            
            if len(temp_database)==0:
                print("Not possible")
            else:
                count =0
                for w,t_d in enumerate(temp_database):
                    id, emd,entered,entry_time, exit_time = t_d
                    if f.compare_embeddings(emd,real_emd)<12:
                        ti = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        t_d_l = list(t_d)
                        t_d_l[2] = 'Exited'
                        t_d_l[4] = ti
                        t_d_t = tuple(t_d_l)
                        temp_database[w] = t_d_t
                        break
                    else:
                        count+=1
                    if count == len(temp_database):
                        print("Something went wrong")
            cv2.putText(frame, 'People exited: '+str(len(exited_person)), (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2, cv2.LINE_AA)
            cv2.imshow('Exit Camera', frame)
    else:
        cv2.putText(frame, 'People exited: '+str(len(exited_person)), (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2, cv2.LINE_AA)
        cv2.imshow('Exit Camera', frame)
        
if __name__ == '__main__':
    while True:
        frame_entry = vs_entry.read()
        frame_exit = vs_exit.read()

        entry_func(frame_entry)
        exit_func(frame_exit)

        print(temp_database)


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break