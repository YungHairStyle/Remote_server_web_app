from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, abort, send_file 
import mimetypes
import datetime
from werkzeug.utils import secure_filename
import os
import shutil
import json


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_change_me")


# --- CONFIG ---


MEDIA_DIR = os.path.abspath('media')
CALENDAR_FILE = os.path.abspath('data/events.json')



def require_api_key():
    if request.headers.get("X-API-KEY") != api_key:
        return jsonify({"error": "Unauthorized"}), 403

@app.route("/api/get-calendar")
def get_calendar():
    require_api_key()
    calendar_path = os.path.join("data", "events.json")
    if not os.path.exists(calendar_path):
        return jsonify({"error": "Calendar not found"}), 404
    with open(calendar_path) as f:
        return jsonify(json.load(f))


@app.route("/api/get-notes")
def list_notes():
    require_api_key()
    notes_dir = os.path.join("files", ".notes")
    txt_files = [
        f for f in os.listdir(notes_dir)
        if f.endswith(".txt") and os.path.isfile(os.path.join(notes_dir, f))
    ]
    notes = {}
    for filename in txt_files:
        with open(os.path.join(notes_dir, filename), "r") as f:
            notes[filename] = f.read()
    return jsonify(notes)

@app.route("/api/get-notes-lycia")
def list_notes_lycia():
    require_api_key()
    notes_dir = os.path.join("files", ".lycia")
    txt_files = [
        f for f in os.listdir(notes_dir)
        if f.endswith(".txt") and os.path.isfile(os.path.join(notes_dir, f))
    ]
    notes = {}
    for filename in txt_files:
        with open(os.path.join(notes_dir, filename), "r") as f:
            notes[filename] = f.read()
    return jsonify(notes)

# --- AUTH ---
@app.before_request
def require_login():
    if request.endpoint and (
        request.path.startswith("/api/")
    ):
        # These are API endpoints: don't require login
        return
    allowed_routes = ['login', 'static', 'media_file', 'favicon', 'guest', 'guest_files']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            return redirect(url_for('home'))  # change to any default page you prefer
        else:
            error = 'Invalid credentials'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# --- HOMEPAGE WITH STATS ---
@app.route('/')
def home():
    total, used, free = shutil.disk_usage("/")
    stats = {
        'total': total // (2**30),
        'used': used // (2**30),
        'free': free // (2**30),
    }
    return render_template('home.html', stats=stats)

@app.route('/save_note', methods=['POST'])
def save_note():
    if request.is_json:
        data = request.get_json()
        note = data.get('content', '').strip()

        if not note:
            return jsonify({"error": "Note content is empty"}), 400

        notes_dir = os.path.join(os.getcwd(), 'files/.notes')
        os.makedirs(notes_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"note_{timestamp}.txt"
        filepath = os.path.join(notes_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(note)

        return jsonify({"message": "Note saved successfully"}), 200
    else:
        return jsonify({"error": "Request must be JSON"}), 415
    
@app.route('/save_note_lycia', methods=['POST'])
def save_note_lycia():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    note = data.get('content', '').strip()

    if not note:
        return jsonify({"error": "Note content is empty"}), 400

    # Hidden directory inside 'files'
    notes_dir = os.path.join(os.getcwd(), 'files', '.lycia')
    os.makedirs(notes_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"note_{timestamp}.txt"
    filepath = os.path.join(notes_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(note)

    return jsonify({"message": "Note saved successfully"}), 200


# --- CALENDAR ---
@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/api/events', methods=['GET', 'POST'])
def events():
    if request.method == 'GET':
        if os.path.exists(CALENDAR_FILE):
            with open(CALENDAR_FILE) as f:
                return jsonify(json.load(f))
        return jsonify([])
    elif request.method == 'POST':
        try:
            events = request.json
            os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
            with open(CALENDAR_FILE, 'w') as f:
                json.dump(events, f)
            return jsonify({"status": "saved"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400


# --- MEDIA GALLERY ---
@app.route('/media', defaults={'subpath': ''})
@app.route('/media/<path:subpath>')
def media(subpath):
    abs_path = os.path.join(MEDIA_DIR, subpath)

    if not os.path.exists(abs_path):
        return abort(404)

    # List folders and files
    folders = []
    files = []

    for item in os.listdir(abs_path):
        full_item_path = os.path.join(abs_path, item)
        if os.path.isdir(full_item_path):
            folders.append(item)
        elif item.lower().endswith(('.jpg', '.jpeg', '.png', '.mp4')):
            files.append(item)

    folders.sort()
    files.sort()

    return render_template(
        'media.html',
        current_folder=subpath,
        folders=folders,
        files=files
    )

@app.route('/media_file/<path:filename>')
def media_file(filename):

    directory = os.path.join(MEDIA_DIR, os.path.dirname(filename))
    file = os.path.basename(filename)
    if not os.path.isfile(os.path.join(directory, file)):
        return abort(404)
    return send_from_directory(directory, file)

# --- FILE MANAGER ---
FILE_DIR = os.path.abspath('files')
ALLOWED_PREVIEW = ('.txt', '.pdf')

# --- List files and folders ---
@app.route('/files', defaults={'subpath': ''})
@app.route('/files/<path:subpath>')
def file_manager(subpath):
    abs_path = os.path.join(FILE_DIR, subpath)
    os.makedirs(abs_path, exist_ok=True)

    # List folders and files
    folders = [f for f in os.listdir(abs_path) if os.path.isdir(os.path.join(abs_path, f)) and not f.startswith('.')]
    files = [f for f in os.listdir(abs_path) if os.path.isfile(os.path.join(abs_path, f)) and not f.startswith('.')]

    return render_template('files.html', folders=folders, files=files, current_folder=subpath)

# --- Upload file ---
@app.route('/files/upload', defaults={'subpath': ''}, methods=['POST'])
@app.route('/files/upload/<path:subpath>', methods=['POST'])
def upload_file(subpath):
    abs_path = os.path.join(FILE_DIR, subpath)
    os.makedirs(abs_path, exist_ok=True)

    file = request.files.get('file')
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(abs_path, filename))

    return redirect(url_for('file_manager', subpath=subpath))

# --- View file ---
@app.route('/files/view/<path:subpath>')
def view_file(subpath):
    filepath = os.path.join(FILE_DIR, subpath)
    if os.path.splitext(filepath)[1].lower() in ALLOWED_PREVIEW and os.path.exists(filepath):
        return send_file(filepath)
    return "Preview not supported for this file type.", 415

# --- Download file ---
@app.route('/files/download/<path:subpath>')
def download_file(subpath):
    filepath = os.path.join(FILE_DIR, subpath)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found.", 404

# --- Delete file ---
@app.route('/files/delete/<path:subpath>', methods=['POST'])
def delete_file(subpath):
    filepath = os.path.join(FILE_DIR, subpath)
    if os.path.exists(filepath) and os.path.isfile(filepath):
        os.remove(filepath)
    parent = os.path.dirname(subpath)
    return redirect(url_for('file_manager', subpath=parent))

# --- Create folder ---
@app.route('/files/create_folder/<path:subpath>', methods=['POST'])
def create_folder(subpath):
    abs_path = os.path.join(FILE_DIR, subpath)
    folder_name = request.form.get('folder_name', '').strip()
    if folder_name:
        os.makedirs(os.path.join(abs_path, folder_name), exist_ok=True)
    return redirect(url_for('file_manager', subpath=subpath))

# --- Delete folder ---
@app.route('/files/delete_folder/<path:subpath>', methods=['POST'])
def delete_folder(subpath):
    folder_path = os.path.join(FILE_DIR, subpath)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
    parent = os.path.dirname(subpath)
    return redirect(url_for('file_manager', subpath=parent))


GUEST_DIR = os.path.abspath('guest')

@app.route('/guest')
def guest():
    cv_filename = "Resume.pdf"  # only filename
    return render_template('guest.html', cv_filename=cv_filename)

@app.route('/guest_files/<filename>')
def guest_files(filename):
    return send_from_directory(GUEST_DIR, filename)


# --- RUN ---
#if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=4999)
