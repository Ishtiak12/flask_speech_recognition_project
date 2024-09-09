from flask import Flask, request, render_template, send_file, jsonify
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

app = Flask(__name__)

# Folder to save uploaded MP3 files
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to recognize speech from the uploaded audio file
def recognize_speech(audio_file):
    # Load the audio file (convert to WAV format)
    audio = AudioSegment.from_mp3(audio_file)

    # Export the audio as a WAV file
    wav_temp_file = os.path.join(app.config['UPLOAD_FOLDER'], 'temp.wav')
    audio.export(wav_temp_file, format='wav')

    # Load the WAV file and split it into chunks on silence
    audio = AudioSegment.from_wav(wav_temp_file)
    chunks = split_on_silence(audio, min_silence_len=500, silence_thresh=-40)

    recognizer = sr.Recognizer()
    recognized_text = []

    # Recognize speech in each chunk
    for i, chunk in enumerate(chunks):
        chunk_file = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_chunk_{i}.wav')
        chunk.export(chunk_file, format='wav')

        with sr.AudioFile(chunk_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language='bn-BD')  # Use 'bn-BD' for Bangla
                recognized_text.append(text)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand the audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")

    # Join recognized text from all chunks
    final_text = " ".join(recognized_text)
    return final_text

# Route for file upload and speech recognition (HTML form)
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded!', 400
        file = request.files['file']

        if file.filename == '':
            return 'No selected file!', 400
        
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            recognized_text = recognize_speech(file_path)
            output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'bangla_text.txt')
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(recognized_text)

            return send_file(output_file_path, as_attachment=True, download_name='bangla_text.txt')

    return render_template('index.html')

# API Endpoint for file upload and speech recognition
@app.route('/api/upload', methods=['POST'])
def api_upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded!'}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file!'}), 400
    
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        recognized_text = recognize_speech(file_path)
        output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'bangla_text.txt')
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(recognized_text)

        return send_file(output_file_path, as_attachment=True, mimetype='text/plain', download_name='bangla_text.txt')

    return jsonify({'error': 'Failed to process file!'}), 500

if __name__ == '__main__':
    app.run(debug=True)

