from flask import Flask, render_template, request, redirect, jsonify
import os
import face_recognition
from PIL import Image
import math
import cv2
import numpy as np
import shutil
import sqlite3

app = Flask(__name__)

# Path to the known faces directory
KNOWN_FACES_DIR = 'faces'

# Load the known faces and their names
known_faces = []
known_names = []

for filename in os.listdir(KNOWN_FACES_DIR):
    file_path = os.path.join(KNOWN_FACES_DIR, filename)
    if os.path.isfile(file_path):
        image = face_recognition.load_image_file(file_path)
        encoding = face_recognition.face_encodings(image)[0]
        known_faces.append(encoding)
        known_names.append(os.path.splitext(filename)[0])

# Create table to store ID and name
conn = sqlite3.connect('face_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS face_data
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, user_id TEXT)''')
conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/success/<name>/<id>')
def success(name, id):
    return render_template('success.html', name=name, id=id)

@app.route('/failure', methods=['GET', 'POST'])
def failure():
    if request.method == 'POST':
        name = request.form['name']
        user_id = request.form['id']
        
        # Insert ID and name into the database
        conn = sqlite3.connect('face_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO face_data (name, user_id) VALUES (?, ?)", (name, user_id))
        conn.commit()
        conn.close()
        
        return redirect(f'/success/{name}/{user_id}')
    return render_template('failure.html')

def face_confidence(face_distance, face_match_threshold=0.6):
    range_val = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range_val * 2.0)

    if face_distance > face_match_threshold:
        return round(linear_val * 100, 2)
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return round(value, 2)

@app.route('/recognized')
def recognized():
    return render_template('recognized.html')

a = 1

@app.route('/capture', methods=['POST'])
def capture():
    global a
    # Get the captured image from the request
    captured_image = request.files['image']
    name = request.form['name']
    user_id = request.form['id']

    # Save the captured image to a folder
    image_filename = f"{name}_{user_id}.jpg"
    captured_image_path = os.path.join(KNOWN_FACES_DIR, image_filename)
    captured_image.save(captured_image_path)

    # Load the captured image for face recognition
    captured_image = face_recognition.load_image_file(captured_image_path)
    captured_encoding = face_recognition.face_encodings(captured_image)

    print(len(captured_encoding))

    if len(captured_encoding) > 0:
        # Compare the captured image with known faces
        face_distances = face_recognition.face_distance(known_faces, captured_encoding[0])
        confidence_values = [face_confidence(d) for d in face_distances]
        best_confidence = np.max(confidence_values)

        print(best_confidence)

        if best_confidence >= 90:
            # Redirect to success page if the best confidence value is greater than or equal to 90
            return jsonify({'redirect_url': '/recognized'})
        else:
            # Add the captured face image to known faces
            new_encoding = captured_encoding[0]
            known_faces.append(new_encoding)
            known_names.append(f"unknown_{len(known_faces)}")

            # Redirect to failure page
            return jsonify({'redirect_url': '/failure'})
    else:
        # No face detected in the captured image, redirect to failure page
        return jsonify({'redirect_url': '/failure'})


if __name__ == '__main__':
    app.run(debug=True)
