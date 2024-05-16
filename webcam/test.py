from flask import Flask, render_template, request, redirect, jsonify
import os
import face_recognition
from PIL import Image
import math
import cv2
import numpy as np
import shutil

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
        id = request.form['id']
        return redirect(f'/success/{name}/{id}')
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




stack=[]


# Function to save the value of 'a' to a file
def save_a_value(a):
    with open('a_value.txt', 'w') as f:
        f.write(str(a))

# Function to load the value of 'a' from a file
def load_a_value():
    if os.path.exists('a_value.txt'):
        with open('a_value.txt', 'r') as f:
            return int(f.read())
    else:
        return 1  # Default value if the file doesn't exist

a = load_a_value()  # Load the value of 'a' from a file
print("Initial value of 'a':", a)

@app.route('/capture', methods=['POST'])
def capture():
    global stack, a

    # Get the captured image from the request
    captured_image = request.files['image']

    # Save the captured image to a folder
    captured_image.save('static/captured.jpg')

    # Load the captured image for face recognition
    captured_image = face_recognition.load_image_file('static/captured.jpg')
    captured_encoding = face_recognition.face_encodings(captured_image)

    if len(captured_encoding) > 0:
        # Compare the captured image with known faces
        face_distances = face_recognition.face_distance(known_faces, captured_encoding[0])
        confidence_values = [face_confidence(d) for d in face_distances]
        best_confidence = np.max(confidence_values)

        print("Best confidence:", best_confidence)

        if best_confidence >= 85:
            # Redirect to success page if the best confidence value is greater than or equal to 90
            return jsonify({'redirect_url': '/recognized'})
        else:
            stack.append(a)
            s = str(stack[-1])
            print("Value of s:", s)
            # Save the captured face image to the "faces" folder
            captured_image_path = os.path.join(KNOWN_FACES_DIR, f"unknown_{s}.jpg")
            a += 1
            save_a_value(a)  # Save the updated value of 'a' to a file
            print("Updated value of 'a':", a)

            # Convert the image to RGB using OpenCV
            captured_image_rgb = cv2.cvtColor(captured_image, cv2.COLOR_BGR2RGB)

            # Save the image
            cv2.imwrite(captured_image_path, captured_image_rgb)

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
    # Run Flask app with port forwarding using Serveo.net
    import subprocess
    subprocess.Popen(['ssh', '-R', '80:localhost:5667', 'serveo.net'])
    app.run(host='0.0.0.0', port=5667, debug=True)
