from tkinter import *
import tkinter as tk
from tkinter import ttk
import pymongo
import os
import copy
from PIL import Image
import numpy as np
import json
import pandas as pd
from cv2 import cv2
from tkinter import filedialog
from deepface import DeepFace
from pathlib import Path
from glob import glob
from datetime import date
import pandas as pd
from bson.objectid import ObjectId
import shutil
import threading

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["mydatabase"]
semester_table = mydb["Semester"]
teacher_table = mydb["Teacher"]
subject_table = mydb["Subject"]
student_table = mydb["Student"]
semesters = []
subjects = []
teachers = []
students = []
attendance_result = []

TEACHER = ""

def deepface_recognition(image1, image2, model_name, model):
    res = DeepFace.verify(image1, image2, model_name = model_name, model = model)
    return res['verified']

class WindowClass():
    def __init__(self, master):
        self.master = master

        self.lbl1 = tk.Label(text = 'Enter Teacher Name')
        self.input1 = tk.Entry()
        self.lbl2 = tk.Label(text = 'Enter Teacher Password')
        self.input2 = tk.Entry(show="*")
        self.btn = tk.Button(text = "Login", command=lambda: self.onLogin())
        self.btn2 = tk.Button(text = "Sign Up", command=lambda: self.onRegister())
        
        self.status = tk.Label(text = "STATUS: NONE")
        self.lbl1.grid(row = 1, column = 1, padx = 10, pady=20)
        self.input1.grid(row = 1, column = 2, padx = 10, pady=20)
        self.lbl2.grid(row = 2, column = 1, padx = 10, pady=20)
        self.input2.grid(row = 2, column = 2, padx = 10, pady=20)
        self.btn.grid(row = 3, column = 2, padx = 10, pady=20)
        self.btn2.grid(row = 3, column = 1, padx = 10, pady=20)
        self.status.grid(row = 5, column = 1, padx = 10, pady=20, columnspan=3)

        self.state = ""

    def onRegister(self):
        toplevel = tk.Toplevel(self.master)
        app = RegApplication(toplevel, self.master)

    def onLogin(self):
        if self.validateCredentials(self.input1.get(),self.input2.get())["Response"]:
            print("Logged in")
            self.status.configure(text="STATUS: Logged In")
            self.status.update()
            teacher_name = self.validateCredentials(self.input1.get(),self.input2.get())["Data"]["name"]

            toplevel = tk.Toplevel(self.master)
            
            path = f"./{teacher_name}"
            if os.path.isdir(path):
                self.state = "normal"
            else:
                self.state = 'disabled'

            # self.master.withdraw()
            app = Application(toplevel, self.master, teacher_name, self.state)
            
        else:
            msg = "Wrong Credentials - Enter correct username and password.!!"
            self.status.configure(text="STATUS: Wrong Credentials!!")
            self.status.update()
            print(msg)

    def validateCredentials(self, username, password):
        
        res = teacher_table.find_one({"name":username, "password":password})
        
        if res is None:
            return {"Response": False}
        else:
            return {"Response": True, "Data":res}

    def get_state(self):
        path = f"./{self.teacher_name}/{self.selection1.get()}"
        if os.path.isdir(path):
            return "normal"
        else:
            return 'disabled'

class RegApplication:
    def __init__(self, master, mainwnd):
        self.master = master
        self.mainwnd = mainwnd
        self.subjects = self.get_subjects()

        self.lbl1 = tk.Label(self.master, text = 'Enter Teacher Name: ')
        self.inputTeacher = tk.Entry(self.master)
        self.lbl2 = tk.Label(self.master, text = 'Enter Password: ')
        self.inputPassword = tk.Entry(self.master, show="*")

        self.selection1 = ttk.Combobox(self.master, state = 'readonly')
        self.selection1['values'] = list(self.subjects.keys())
        self.selection1.current(0)

        self.registerButton = tk.Button(self.master, text = 'Register', width = 20,\
            command=lambda: self.onRegister(self.subjects, self.selection1.get(), self.inputTeacher.get(), self.inputPassword.get()))
        self.quitButton = tk.Button(self.master, text = 'Back', width = 20, command = self.close_windows)

        self.lbl1.grid(row = 2, column = 1, padx = 10, pady=20)
        self.inputTeacher.grid(row = 2, column = 2, padx = 10, pady=20)
        self.lbl2.grid(row = 3, column = 1, padx = 10, pady=20)
        self.inputPassword.grid(row = 3, column = 2, padx = 10, pady=20)
        self.selection1.grid(row = 4, column = 1, padx = 10, pady=20, columnspan=3)
        self.registerButton.grid(row = 5, column= 1, padx = 10, pady=20, columnspan=3)
        self.quitButton.grid(row = 6, column= 1, padx = 10, pady=20, columnspan=3)

    def get_subjects(self):
        new_sub = {}
        with open("subjects.json","r") as f:
            data = json.load(f)

        for i in data['values']:
            new_sub[i["name"]] = i["_id"]

        return new_sub
        
    def onRegister(self, new_sub, subject, name, password):

        with open("teachers.json","r") as f:
            data = json.load(f)

        new_teachers = copy.deepcopy(data)
        flag = True
        response = ""

        for ind, row in enumerate(data["values"]):
            if row["name"] == name and password == password and new_sub[subject] in row["subjects"]:
                response = "Subject Already Registered"
                flag = False
                break
            
            if row["name"] == name and password == password and new_sub[subject] not in row["subjects"]:
                new_teachers["values"][ind]["subjects"].append(new_sub[subject])
                response = "Teacher registered with the subject"
                flag = False
                break
                
        if flag:
            if len(new_teachers["values"]) == 0:
                new_id = 0
            else:
                new_id = new_teachers["values"][-1]["_id"] + 1
            new_teachers["values"].append({"_id": new_id, "name": name, "password": password, "subjects": [new_sub[subject]]})
            response = "Teacher registered with the subject"
            flag = False
        
        with open("teachers.json","w") as f:
            json.dump(new_teachers, f)

        teacher_table.delete_many({})
        teacher_table.insert_many(new_teachers["values"])

        print(response)

    def close_windows(self):
        self.master.destroy()

class Application:

    def __init__(self, master, mainwnd, teacher_name, state):
        self.master = master
        self.mainwnd = mainwnd
        self.filename = ""
        self.teacher_name = teacher_name
        self.FLAG = True
        TEACHER = teacher_name
        self.mainwnd.withdraw()

        self.lbl1 = tk.Label(self.master, text = 'Teacher Name: ')
        self.lbl1.grid(row = 2, column = 1, padx = 10, pady=20)
        self.lbl2 = tk.Label(self.master, text = f'{self.teacher_name}')
        self.lbl2.grid(row = 2, column = 2, padx = 10, pady=20)

        self.lbl3 = tk.Label(self.master, text = 'Subject List')
        self.lbl3.grid(row = 3, column = 1, padx = 10, pady=20)
        self.selection1 = ttk.Combobox(self.master, state = 'readonly')
        
        # Subject List
        self.selection1['values'] = self.get_subjects(self.teacher_name)
        self.selection1.current(0)
        self.selection1.grid(row = 3, column = 2, padx = 10)

        self.LoadBtn = tk.Button(self.master, text = "Load Images", command = lambda: self.insert_student(self.teacher_name, self.selection1.get()))
        self.LoadBtn.grid(row = 3, column = 3, padx = 10)

        self.b = threading.Thread(name='background', target=self.mark_attendance, args=(self.teacher_name,))
        self.b.daemon = True

        self.btn3 = tk.Button(self.master, text = "Mark Attendance", state=state, width = 20, command = self.b.start)
        self.btn3.grid(row = 4, column = 1, padx = 10, pady=20)

        self.btn4 = tk.Button(self.master, text = "Clear Subject Students", width = 20, command=lambda: self.clear_subject_students(self.selection1.get()))
        self.btn4.grid(row = 4, column = 2, padx = 10, pady=20)

        self.logoutButton = tk.Button(self.master, text = 'Log Out', width = 20, command = self.logout_profile)
        self.logoutButton.grid(row = 4, column= 3, padx = 10, pady=20)

        self.quitButton = tk.Button(self.master, text = 'Quit', width = 20, command = self.close_windows)
        self.quitButton.grid(row = 6, column= 2, padx = 10, pady=20)

        self.status = tk.Label(self.master, text = "STATUS: NONE")
        self.status.grid(row = 8, padx = 10, pady=20, column=0, columnspan=3)

    def get_subjects(self, teacher_name):
        res = teacher_table.find_one({"name":teacher_name})
        res = subject_table.find({"_id":{"$in":res['subjects']}})
        subject_names = [i['name'] for i in res]
        return subject_names

    def take_picture(self):
        print("Taking Picture")
        camera = cv2.VideoCapture(0)

        for _ in range(30):
            _, image = camera.read()

        cv2.imwrite('test_img.png', image)
        del(camera)
        self.status.configure(text="STATUS: Test Image Saved")
        self.status.update()
        print("Picture Taken")


    def insert_student(self, teacher_name, subject_name):

        self.filename = filedialog.askopenfilenames(title='Choose a file')

        for path in self.filename:
            try:
                
                img = Image.open(path)
                img_name = path.split("/")[-1]
                name = img_name.split(".")[0].split("_")[1]
                reg_id = img_name.split(".")[0].split("_")[0]
                dirName = os.getcwd() + "/" + str(teacher_name) + "/" + str(subject_name)
                
                try:
                    if not os.path.isdir(dirName):
                        os.makedirs(dirName)
                except FileExistsError:
                    print("Error while creating directory.")  

                new_path = dirName + "/" + img_name
                img.save(new_path)
                self.btn3['state'] = 'normal'

                # Check if student already exist or not
                x = student_table.find_one({"name":name},{"_id":1})
                student_id = ObjectId()
                if not x:
                    #---------------------------------------------------------------------------#

                    x = subject_table.find_one({"name":subject_name},{"_id":0, "semester_id":1})
                    x = semester_table.find_one({"_id":x["semester_id"]}, {"_id":0, "code":1})
                    # reg_id = str(np.random.randint(1000,10000)) + "-" + x['code']

                    
                    student = {"registration_id":reg_id, "name": name, "image": new_path}
                    x = student_table.insert_one(student)

                    print("Student Id: ", x.inserted_id)
                    student_id = x.inserted_id

                    #---------------------------------------------------------------------------#
                else:
                    student_id = x["_id"]

                myquery = {"name":subject_name}
                newvalues = { "$push": { "enrolled_students": student_id } }
                subject_table.update_one(myquery, newvalues)

            except Exception as e:
                print("Student Insertion Failed ", e)

        self.status.configure(text="STATUS: Images inserted successfully.")
        self.status.update()


    def clear_subject_students(self, subject_name):

        self.FLAG = False
        
        try:
            myquery = {"name":subject_name}

            result = subject_table.find_one(myquery)
            student_ids = result['enrolled_students']
            students = student_table.find({"_id":{"$in": student_ids}})
            student_img_names = [i['image'].split("/")[-1] for i in students]

            newvalues = { "$set": { "enrolled_students": [] } }
            subject_table.update_one(myquery, newvalues)

            myquery = { "_id": {"$in": student_ids} }
            student_table.delete_many(myquery)

            filepath =  f"./{self.teacher_name}/{subject_name}"
            try:
                shutil.rmtree(filepath)
            except OSError:
                os.remove(filepath)

            print("Subject Students Cleared From Database")
            self.status.configure(text="STATUS: Subject data cleared from database.")
            self.status.update()
        except:
            print("Error: Students cannot be cleared for this subject")

    def recognize_face(self, teacher_name, subject_name):

        model_name = "Facenet"
        result = {"date":str(date.today()),"name":"","attendance":"Absent", "subject":subject_name, \
            "teacher":teacher_name, "semester":"", "registration_id": ""}

        model = DeepFace.build_model(model_name)

        test_image = "./test_img.png"

        try:
            if (Path.cwd() / teacher_name / subject_name).exists():
                img_path = f"./{teacher_name}/{subject_name}/*"
                
                test_images = glob(img_path)
                
                if test_images:
                    for img in test_images:

                        mark_attendance = deepface_recognition(img, test_image, model_name, model)
                        if mark_attendance:

                            x = subject_table.find_one({"name":subject_name},{"_id":0, "semester_id":1})
                            x = semester_table.find_one({"_id":x["semester_id"]}, {"_id":0, "code":1})

                            result["semester"] = x["code"]
                            result["name"] = img.split("/")[-1].split(".")[0].split("_")[1] # New Change
                            x = student_table.find_one({"name":result['name']},{"_id":0, "registration_id":1})
                            result["registration_id"] = x['registration_id']
                            result["attendance"] = "Present"
                            result["subject"] = subject_name
                            result["teacher"] = teacher_name
                            break

                    attendance_result.append(result)
                    print("Face Recognized")
                    self.status.configure(text="STATUS: Face Recognized.")
                    self.status.update()
            else:
                print("Load images in database")
                self.status.configure(text="STATUS: Load Images in Database.")
                self.status.update()
        except Exception as e:
            print("Something went wrong. - ", e)

    def mark_attendance(self, teacher_name):

        subject_name = self.selection1.get()

        while(self.FLAG):
            try:
                self.take_picture()
                self.recognize_face(teacher_name, subject_name)
                
                print("Attendance Result: ",attendance_result[-1])
                if attendance_result[-1]["name"] != "":
                    filename = f"./{teacher_name}/{subject_name}/attendance_sheet.csv"

                    dataframe = pd.DataFrame.from_dict({k:[v] for k,v in attendance_result[-1].items()})

                    column_titles = ['date','registration_id','semester','name','subject', 'teacher', 'attendance']
                    dataframe = dataframe[column_titles]
                    header = True
                    if os.path.isfile(filename):
                        mode = 'a'
                        header = False
                    else:
                        mode = 'w'

                    print("=========================")
                    print(attendance_result)
                    print("=========================")

                    if header or self.record_not_exist(attendance_result[-1]['registration_id'],filename):
                        with open(filename, mode=mode) as f:
                            dataframe.to_csv(f, header=header, index=False)

                        print("Attendance Marked")
                        self.status.configure(text="STATUS: Attendance Marked.")
                        self.status.update()
                    else:
                        print("Attendance Already Marked")
                        self.status.configure(text="STATUS: Attendance Already Marked.")
                        self.status.update()
                else:
                    print("Unknown Person")
                    self.status.configure(text="STATUS: Unknown Person")
                    self.status.update()
            except Exception as e:
                self.FLAG = False
                print("ERROR: No image in the database - Load the images", e)
                self.status.configure(text="STATUS: No image in the database - Load the images")
                self.status.update()
                

    def record_not_exist(self, reg_id, filename):
        data = pd.read_csv(filename)
        regs = list(data["registration_id"])
        if int(reg_id) in regs:
            return False
        else:
            return True

    def logout_profile(self):
        
        self.FLAG = False
        self.master.withdraw()
        self.mainwnd.deiconify()
        # self.master.destroy()

        print("Logged out")

    def close_windows(self):
        try:
            self.FLAG = False
            data = {"values": []}
            with open("teachers.json","w") as f:
                json.dump(data,f)
            teacher_table.delete_many({})
            student_table.delete_many({})

            subjects = [i for i in subject_table.find({})]
            new_subjects = []
            for subject in subjects:
                subject['enrolled_students'] = []
                new_subjects.append(subject)
            subject_table.delete_many({})
            subject_table.insert_many(new_subjects)

            # path = f"./{self.teacher_name}"
            # shutil.rmtree(path)
            # os.remove("./attendance_sheet.csv")
            lst = ['enrolled','semesters.json','teachers.json','main.py','subjects.json']
            files = [i.replace("./","") for i in glob("./*")]
            residue = [i for i in files if i not in lst]
            for file in residue:
                path = f"./{file}"
                if os.path.isfile(file):
                    os.remove(path)
                elif os.path.isdir(file):
                    shutil.rmtree(path)

            self.master.quit()
        except:
            self.master.quit()

def threaded_start():
    root = tk.Tk()
    root.title("Attendance System")
    root.geometry("380x250")
    cls = WindowClass(root)
    root.mainloop()

def on_closing():
    try:
        data = {"values": []}
        with open("teachers.json","w") as f:
            json.dump(data,f)
        teacher_table.delete_many({})
        student_table.delete_many({})

        subjects = [i for i in subject_table.find({})]
        new_subjects = []
        for subject in subjects:
            subject['enrolled_students'] = []
            new_subjects.append(subject)
        subject_table.delete_many({})
        subject_table.insert_many(new_subjects)
        # os.remove("./attendance_sheet.csv")

        lst = ['enrolled','semesters.json','teachers.json','main.py','subjects.json']
        files = [i.replace("./","") for i in glob("./*")]
        residue = [i for i in files if i not in lst]
        for file in residue:
            path = f"./{file}"
            print("aya tha")
            if os.path.isfile(file):
                print("file ha")
                os.remove(path)
            elif os.path.isdir(file):
                print("dir ha")
                shutil.rmtree(path)

        root.destroy()
    except:
        root.destroy()

if __name__ == "__main__":

    for path in ["subjects", "semesters", "teachers"]:
        file_path = path + ".json"
        with open(file_path, "r") as file:
            x = json.load(file)
            
            if path == "subjects":
                subjects = x["values"]
            elif path == "semesters":
                semesters = x["values"]
            elif path == "teachers":
                teachers = x["values"]
            elif path == "students":
                students = x["values"]
                
    try:
        semester_table.insert_many(semesters)
        subject_table.insert_many(subjects)
        teacher_table.insert_many(teachers)
        print("Data Loaded")
    except:
        print("Data Already Loaded")


    root = tk.Tk()
    root.title("Attendance System")
    root.geometry("380x250")
    cls = WindowClass(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
    