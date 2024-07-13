import datetime

from flask import Flask, redirect, render_template, request, url_for
from flask_login import login_user, login_required, logout_user, UserMixin, LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import mysql.connector
import hashlib

database = mysql.connector.connect(host='localhost', user='host', password='abcd1234', database='college_portal')
cursor = database.cursor()
app = Flask(__name__)
login_manager = LoginManager(app)
app.config['SECRET_KEY'] = 'bf603aefb078ed6650460e3f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://host:abcd1234@localhost/college_portal'
db = SQLAlchemy(app)


@login_manager.user_loader
def load_user(user_id):
    return user_details.query.get(user_id)


def roles_required(role_required):
    def wrapper(view_function):
        @wraps(view_function)
        def decorator(*args, **kwargs):
            allowed = current_user.is_authenticated
            if not allowed:
                return redirect('/')
            if not current_user.role == role_required:
                role = current_user.role
                return redirect(url_for(f'{role}_home'))
            return view_function(*args, **kwargs)
        return decorator
    return wrapper


class user_details(db.Model, UserMixin):
    name = db.Column(db.String(length=30), nullable=False)
    age = db.Column(db.Integer(), nullable=False)
    user_id = db.Column(db.String(length=10), nullable=False, primary_key=True)
    role = db.Column(db.String(length=10), nullable=False)
    password = db.Column(db.String(length=60), nullable=False)
    current_class = db.Column(db.String(length=10))

    def get_id(self):
        alternative_id = self.user_id
        return alternative_id

    def get_role(self):
        return self.role


def pass_hash(password):
    pass_hashed = hashlib.md5(password.encode('utf-8')).hexdigest()
    return pass_hashed


@app.route('/', methods=['GET'])
def home_page():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect('/admin_home')
        elif current_user.role == 'mentor':
            return redirect('/mentor_home')
        elif current_user.role == 'student':
            return redirect('/student_home')
    return render_template('main_menu.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect('/admin_home')
        elif current_user.role == 'mentor':
            return redirect('/mentor_home')
        elif current_user.role == 'student':
            return redirect('/student_home')
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        cursor.execute(f"select password from user_details where user_id = '{user_id}' and role = 'admin';")
        data = cursor.fetchone()
        if data is not None:
            pass_data = data[0]
            print(pass_data)
            if pass_data == pass_hash(password):
                attempted_user = user_details.query.get(user_id)
                login_user(attempted_user)
                return redirect('/admin_home')
            else:
                print('Error, wrong password.')
    return render_template('admin/admin_login.html')


@app.route('/admin_home')
@login_required
@roles_required('admin')
def admin_home():
    return render_template('admin/admin_main_menu.html')


@app.route('/admin_home/add_teacher')
@login_required
@roles_required('admin')
def admin_add_teacher():
    return render_template('admin/add_teacher.html')


@app.route('/mentor_login', methods=['GET', 'POST'])
def mentor_login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect('/admin_home')
        elif current_user.role == 'mentor':
            return redirect('/mentor_home')
        elif current_user.role == 'student':
            return redirect('/student_home')
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        cursor.execute(f"select password from user_details where user_id = '{user_id}' and role = 'mentor';")
        data = cursor.fetchone()
        if data is not None:
            pass_data = data[0]
            if pass_data == pass_hash(password):
                attempted_user = user_details.query.get(user_id)
                login_user(attempted_user)
                return redirect('/mentor_home')
            else:
                print('Error, wrong password.')
    return render_template('mentor/mentor_login.html')


@app.route('/mentor_home')
@roles_required('mentor')
def mentor_home():
    cursor.execute(f"select subject, class from teacher_details where teacher_name = '{current_user.name}'")
    data = cursor.fetchall()
    ls_of_data = []
    for i in data:
        ls_of_data.append(i)
    return render_template('mentor/mentor_main_menu.html', data=ls_of_data)


@app.route('/mentor_home/add_student', methods=['GET', 'POST'])
@roles_required('mentor')
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        user_id = request.form['user_id']
        password = pass_hash(request.form['password'])
        class_allotted = request.form['class_allotted']
        cursor.execute(f"insert into user_details values('{name}', {age}, '{user_id}', 'student', '{password}', '{class_allotted}')")
        database.commit()
    return render_template('mentor/add_student.html')


@app.route('/mentor_home/remove_student', methods=['GET', 'POST'])
@roles_required('mentor')
def remove_student():
    if request.method == 'POST':
        name = request.form['name']
        user_id = request.form['user_id']
        cursor.execute(f"delete from user_details where name ='{name}' and user_id = '{user_id}'")
        database.commit()
    return render_template('mentor/remove_student.html')


@app.route('/mentor_home/take_attendance', methods=['GET', 'POST'])
@roles_required('mentor')
def take_attendance():
    cursor.execute(f"select class from teacher_details where teacher_name = '{current_user.name}'")
    data = cursor.fetchall()
    ls_of_data = []
    for i in data:
        ls_of_data.append(i[0])
    if request.method == 'POST':
        return redirect(url_for('take_attendance_class', class_taken=request.form['class']))
    return render_template('mentor/take_attendance.html', data=ls_of_data)


@app.route('/mentor_home/take_attendance/<class_taken>', methods=['GET', 'POST'])
@roles_required('mentor')
def take_attendance_class(class_taken):
    cursor.execute(f"select subject from teacher_details where teacher_name = '{current_user.name}' and class = '{class_taken}'")
    data = cursor.fetchall()
    ls_of_classes = []
    for i in data:
        ls_of_classes.append(i[0])
    cursor.execute(f"select name, user_id from user_details where current_class = '{class_taken}'")
    data = cursor.fetchall()
    ls_of_students = []
    for i in data:
        ls_of_students.append(i)
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    if request.method == 'POST':
        subject = request.form['subject']
        date = request.form['date']
        for i in range(0, len(ls_of_students)):
            status = request.form[f'status_{i}']
            cursor.execute(f"insert into attendance_details values('{date}', '{ls_of_students[i][1]}', '{status}', '{subject}', '{class_taken}')")
            database.commit()
    return render_template('mentor/take_attendance_class.html', subjects=ls_of_classes, students=ls_of_students, length=len(ls_of_students), date=current_date)


@app.route('/mentor_home/review_attendance_records', methods=['GET', 'POST'])
@roles_required('mentor')
def attendance_records():
    cursor.execute(f"select class from teacher_details where teacher_name = '{current_user.name}'")
    data = cursor.fetchall()
    ls_of_data = []
    for i in data:
        ls_of_data.append(i[0])
    if request.method == 'POST':
        return redirect(url_for('review_attendance_records_class', class_taken=request.form['class']))
    return render_template('mentor/review_attendance.html', data=ls_of_data)


@app.route('/mentor_home/review_attendance_records/<class_taken>', methods=['GET', 'POST'])
@roles_required('mentor')
def review_attendance_records_class(class_taken):
    cursor.execute(f"select subject from teacher_details where teacher_name = '{current_user.name}' and class = '{class_taken}'")
    data = cursor.fetchall()
    ls_of_subjects = []
    for i in data:
        ls_of_subjects.append(i[0])
    if request.method == 'POST':
        subject = request.form['subject']
        date = request.form['date']
        cursor.execute(f"select user_id, status from attendance_details where date = '{date}' and class = '{class_taken}' and subject = '{subject}'")
        data = cursor.fetchall()
        data_of_attendance = []
        print(data)
        if not data:
            return render_template('mentor/review_attendance_class.html', s_table='hidden', subjects=ls_of_subjects, s_head='visible')
        else:
            for i in data:
                cursor.execute(f"select name from user_details where user_id = '{i[0]}'")
                data = cursor.fetchall()
                name = data[0][0]
                data_of_attendance.append([name, i[0], i[1]])
            return render_template('mentor/review_attendance_class.html', s_table='visible', subjects=ls_of_subjects, s_head='hidden', data=data_of_attendance)
    return render_template('mentor/review_attendance_class.html', s_table='hidden', subjects=ls_of_subjects, s_head='hidden')


@app.route('/mentor_home/add_marks', methods=['GET', 'POST'])
@roles_required('mentor')
def add_marks():
    cursor.execute(f"select class from teacher_details where teacher_name = '{current_user.name}'")
    data = cursor.fetchall()
    ls_of_data = []
    for i in data:
        ls_of_data.append(i[0])
    if request.method == 'POST':
        return redirect(url_for('add_marks_class', class_taken=request.form['class']))
    return render_template('mentor/add_marks.html', data=ls_of_data)


@app.route('/mentor_home/add_marks/<class_taken>', methods=['GET', 'POST'])
@roles_required('mentor')
def add_marks_class(class_taken):
    return render_template('mentor/add_marks_class.html')


@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect('/admin_home')
        elif current_user.role == 'mentor':
            return redirect('/mentor_home')
        elif current_user.role == 'student':
            return redirect('/student_home')
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        cursor.execute(f"select  password from user_details where user_id = '{user_id}' and role = 'student';")
        data = cursor.fetchone()
        if data is not None:
            pass_data = data[0]
            if pass_data == pass_hash(password):
                attempted_user = user_details.query.get(user_id)
                print(attempted_user.role)
                login_user(attempted_user)
                return redirect('/student_home')
            else:
                print('Error, wrong password.')
    return render_template('student/student_login.html')


@app.route('/student_home')
@login_required
@roles_required('student')
def student_home():
    cursor.execute(f"select teacher_name, subject from teacher_details where class = '{current_user.current_class}'")
    data = cursor.fetchall()
    ls_of_data = []
    for i in data:
        ls_of_data.append(i)
    cursor.execute(f"select subject from teacher_details where class = '{current_user.current_class}'")
    ls_of_subject = cursor.fetchall()
    percentage_attendance = []
    for i in ls_of_subject:
        subject = i[0]
        cursor.execute(f"select status from attendance_details where user_id = '{current_user.user_id}' and class = '{current_user.current_class}' and subject = '{subject}'")
        data = cursor.fetchall()
        total_number_of_classes = len(data)
        if total_number_of_classes == 0:
            percentage_attendance.append([subject, 0])
        else:
            number_days_present = 0
            for j in data:
                for k in j:
                    if k == 'Present':
                        number_days_present += 1
            attendance_percentage = number_days_present / total_number_of_classes
            attendance_percentage = attendance_percentage*100
            percentage_attendance.append([subject, attendance_percentage])

    return render_template('student/student_main_menu.html', data=ls_of_data, a_p=percentage_attendance)


@app.route('/student_home/attendance_records')
@roles_required('student')
def student_attendance_records():
    list_of_attendance = []
    ls_of_subject = []
    cursor.execute(f"select subject from teacher_details where class = '{current_user.current_class}'")
    data = cursor.fetchall()
    for i in data:
        ls_of_subject.append(i[0])
    for i in ls_of_subject:
        subject = i
        cursor.execute(f"select date, status from attendance_details where user_id = '{current_user.user_id}' and class = '{current_user.current_class}' and subject = '{subject}'")
        data = cursor.fetchall()
        total_number_of_classes = len(data)
        if total_number_of_classes == 0:
            list_of_attendance.append(
                [subject, 0, 0, 0, 'None'])
        else:
            number_days_present = 0
            ls_of_status_and_date = []
            for j in data:
                ls = []
                for k in j:
                    if k == 'Present':
                        number_days_present += 1
                    ls.append(k)
                ls_of_status_and_date.append(ls)
            attendance_percentage = number_days_present / total_number_of_classes
            attendance_percentage = attendance_percentage * 100
            ls_of_status_and_date.sort()
            list_of_attendance.append([subject, number_days_present, total_number_of_classes, attendance_percentage, ls_of_status_and_date])

    return render_template('student/student_attendance_records.html', ls=list_of_attendance)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
