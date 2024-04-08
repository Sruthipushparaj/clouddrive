from flask import Flask, render_template, request, redirect, url_for, session, send_file
from azure.storage.blob import BlobServiceClient, BlobClient
import os
import sqlite3
import uuid
app = Flask(__name__)
app.secret_key = '123'

# Initialize SQLite3 database
DATABASE = 'users.db'

def create_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

create_table()

# Azure Blob Storage credentials
AZURE_STORAGE_CONNECTION_STRING ="DefaultEndpointsProtocol=https;AccountName=clouddrivehub;AccountKey=nL2eTiYN/RUh3hEzILDCZhf7YNo4b2ZbbDi5ofPOCgRF9SFsX5uMcgoSD80xQqdc/B8xeTvQVHTx+ASt9cyETg==;EndpointSuffix=core.windows.net"
CONTAINER_PREFIX = "myconnn"


def get_blob_service_client():
    return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

@app.route('/share_file', methods=['POST'])
def share_file():
    if 'username' not in session:
        return redirect(url_for('login'))

    filename = request.form.get('filename')

    # Generate a unique shareable link for the file
    shareable_link = generate_shareable_link(filename)

    # Display the shareable link (this can be improved to store links in a database for later retrieval)
    return render_template('share.html', filename=filename, shareable_link=shareable_link)

def generate_shareable_link(filename):
    # Generate a unique token for the shareable link
    token = str(uuid.uuid4())
    shareable_link = f"https://clouddrivehub.blob.core.windows.net/download/{token}/{filename}"
    return shareable_link
@app.route('/files')
def list_files():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    container_name = CONTAINER_PREFIX + username

    # Create a BlobServiceClient from the connection string
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

    # Get a list of blobs in the container
    blobs = []
    container_client = blob_service_client.get_container_client(container_name)
    for blob in container_client.list_blobs():
        blobs.append(blob.name)

    return render_template('view.html', blobs=blobs)
# Route for retrieving a file from Azure Blob Storage
@app.route('/retrieve/<filename>')
def retrieve_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    container_name = CONTAINER_PREFIX + username

    # Create a BlobServiceClient from the connection string
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        
    # Create a blob client for the container
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)
    
    # Download the file from blob storage
    file_path = f"downloads/{filename}"  # Assuming a directory named "downloads" exists to store downloaded files
    with open(file_path, "wb") as f:
        download_stream = blob_client.download_blob()
        f.write(download_stream.readall())
    
    return send_file(file_path, as_attachment=True)

# Route for deleting a file from Azure Blob Storage
@app.route('/delete/<filename>')
def delete_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    container_name = CONTAINER_PREFIX + username

    # Create a BlobServiceClient from the connection string
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        
    # Create a blob client for the container
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)
    
    # Delete the file from blob storage
    blob_client.delete_blob()

    return redirect(url_for('home'))

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and user[2] == password:  # Check if user exists and password matches
            session['username'] = username
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/upload_file1')
def upload_file1():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))

    file = request.files['file']
    if file:
        username = session['username']
        container_name = CONTAINER_PREFIX + username

        # Create a BlobServiceClient from the connection string
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        
        # Check if container exists, if not, create it
        try:
            blob_service_client.create_container(container_name)
        except:
            pass  # Container already exists
        
        # Create a blob client for the container
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
        
        # Upload the file to the blob
        blob_client.upload_blob(file)

    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        add_user(username, password)
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/about')
def about():
    return render_template('about.html')


def create_contact_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS contact_messages (id INTEGER PRIMARY KEY, name TEXT, email TEXT, message TEXT)')
    conn.commit()
    conn.close()

# Call the function to create the contact table
create_contact_table()

# Modify your /contact route to handle form submission
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Store the message into the database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)', (name, email, message))
        conn.commit()
        conn.close()
        
        # Optionally, you can redirect to a thank you page or render a success message
        return render_template('index.html')
    
    # For GET requests, render the contact form
    return render_template('cont.html')
if __name__ == '__main__':
    app.run(debug=True)

