import os
import uuid
import logging
from werkzeug.utils import secure_filename

# Define upload configurations
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {
    'images': {'jpg', 'jpeg', 'png', 'gif'},
    'documents': {'pdf', 'doc', 'docx', 'txt'},
    'vouchers': {'pdf', 'jpg', 'jpeg', 'png'}
}

def init_upload_folders():
    """Initialize upload directories"""
    folders = ['photos', 'id_photos', 'vouchers', 'documents']
    for folder in folders:
        path = os.path.join(UPLOAD_FOLDER, folder)
        if not os.path.exists(path):
            os.makedirs(path)

def allowed_file(filename, file_type='documents'):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

def generate_unique_filename(filename):
    """Generate unique filename to prevent conflicts"""
    if filename:
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_name = str(uuid.uuid4())
        return f"{unique_name}.{ext}" if ext else unique_name
    return None

def save_file(file, subfolder, file_type='documents'):
    """Save uploaded file and return filename"""
    if file and file.filename:
        if allowed_file(file.filename, file_type):
            filename = secure_filename(file.filename)
            unique_filename = generate_unique_filename(filename)
            
            # Create subfolder if it doesn't exist
            folder_path = os.path.join(UPLOAD_FOLDER, subfolder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            file_path = os.path.join(folder_path, unique_filename)
            file.save(file_path)
            return unique_filename
    return None

def save_multiple_files(files, subfolder, file_type='documents'):
    """Save multiple files and return list of filenames"""
    saved_files = []
    for file in files:
        if file and file.filename:
            filename = save_file(file, subfolder, file_type)
            if filename:
                saved_files.append(filename)
    return saved_files

def delete_file(filename, subfolder):
    """Delete a file from uploads directory"""
    if filename:
        file_path = os.path.join(UPLOAD_FOLDER, subfolder, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError:
                return False
    return False

def get_file_path(filename, subfolder):
    """Get full path to uploaded file"""
    if filename:
        return os.path.join(UPLOAD_FOLDER, subfolder, filename)
    return None

# Initialize upload folders when module is imported
init_upload_folders()
