import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "duata_kingbawl_exclusive_key"

# --- DATABASE CONFIG (AUTOMATIC PATH) ---
# He lai hian i folder hmun a hmu lawk anga, 'instance' folder a zawng nghal ang
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'office.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload folder setup
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False) # NH, BRTF, STAFFS
    designation = db.Column(db.String(100), nullable=True) 
    image = db.Column(db.String(100), nullable=True, default='default_staff.png') 
    files = db.relationship('ProjectFile', backref='folder', cascade="all, delete-orphan", lazy=True)

class ProjectFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    file_no = db.Column(db.String(100), nullable=True)
    filename = db.Column(db.String(100), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)

# --- ROUTES ---

@app.route('/')
def index():
    if 'user' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    u_input = request.form.get('username')
    p_input = request.form.get('password')
    
    user = User.query.filter_by(username=u_input).first()
    
    if user and user.password == p_input:
        session['user'] = user.username
        return redirect(url_for('dashboard'))
    return render_template('login.html', error="Username emaw Password a dik lo")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/category/<cat_type>')
def category_page(cat_type):
    if 'user' not in session: return redirect(url_for('index'))
    folders = Folder.query.filter_by(category=cat_type).all()
    if cat_type == 'STAFFS':
        return render_template('staffs.html', folders=folders)
    template = 'nh.html' if cat_type == 'NH' else 'brtf.html'
    return render_template(template, folders=folders, category=cat_type)

@app.route('/add_folder/<cat_type>', methods=['POST'])
def add_folder(cat_type):
    if 'user' not in session: return redirect(url_for('index'))
    name = request.form.get('folder_name')
    if name:
        new_folder = Folder(name=name, category=cat_type)
        db.session.add(new_folder)
        db.session.commit()
    return redirect(url_for('category_page', cat_type=cat_type))

@app.route('/add_staff', methods=['POST'])
def add_staff():
    if 'user' not in session: return redirect(url_for('index'))
    name = request.form.get('staff_name')
    desig = request.form.get('designation')
    file = request.files.get('staff_image')
    img_name = 'default_staff.png'
    if file and file.filename != '':
        img_name = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_name))
    new_staff = Folder(name=name, category='STAFFS', designation=desig, image=img_name)
    db.session.add(new_staff)
    db.session.commit()
    return redirect(url_for('category_page', cat_type='STAFFS'))

@app.route('/folder_detail/<int:id>')
def folder_detail(id):
    if 'user' not in session: return redirect(url_for('index'))
    folder = Folder.query.get_or_404(id)
    files = ProjectFile.query.filter_by(folder_id=id).all()
    if folder.category == 'STAFFS':
        return render_template('folder_detail_staffs.html', folder=folder, files=files)
    template = 'folder_detail_nh.html' if folder.category == 'NH' else 'folder_detail_brtf.html'
    return render_template(template, folder=folder, files=files)

@app.route('/upload_file/<int:folder_id>', methods=['POST'])
def upload_file(folder_id):
    if 'user' not in session: return redirect(url_for('index'))
    p_name = request.form.get('project_name')
    f_no = request.form.get('file_no')
    file = request.files.get('file')
    if file:
        fname = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        new_f = ProjectFile(project_name=p_name, file_no=f_no, filename=fname, folder_id=folder_id)
        db.session.add(new_f)
        db.session.commit()
    return redirect(url_for('folder_detail', id=folder_id))

@app.route('/view_file/<filename>')
def view_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete_file/<int:file_id>/<int:folder_id>')
def delete_file(file_id, folder_id):
    if 'user' not in session: return redirect(url_for('index'))
    f = ProjectFile.query.get(file_id)
    db.session.delete(f)
    db.session.commit()
    return redirect(url_for('folder_detail', id=folder_id))

@app.route('/delete_folder/<int:id>/<cat_type>')
def delete_folder(id, cat_type):
    if 'user' not in session: return redirect(url_for('index'))
    f = Folder.query.get(id)
    db.session.delete(f)
    db.session.commit()
    return redirect(url_for('category_page', cat_type=cat_type))

@app.route('/settings')
def settings():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template('setting.html')

@app.route('/update_password', methods=['POST'])
def update_password():
    if 'user' not in session: return redirect(url_for('index'))
    current_p = request.form.get('current_password')
    new_p = request.form.get('new_password')
    confirm_p = request.form.get('confirm_password')
    user = User.query.filter_by(username=session['user']).first()
    if user and user.password == current_p:
        if new_p == confirm_p:
            user.password = new_p
            db.session.commit()
            return render_template('setting.html', success="Password successfully updated!")
        else:
            return render_template('setting.html', error="New passwords do not match!")
    else:
        return render_template('setting.html', error="Current password is incorrect!")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="LA_BRANCH").first():
            admin = User(username="LA_BRANCH", password="LABranch")
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)