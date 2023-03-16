from flask import Flask, request, jsonify
from flask_uploads import UploadSet, configure_uploads
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template
from flask_cors import CORS, cross_origin
from master_logic import *

app = Flask(__name__)
CORS(app, support_credentials=True)

# define a list of allowed audio and video file extensions
audio_extensions = ('mp3', 'wav')
video_extensions = ('mp4', 'mov')

# configure the upload set to accept audio and video files with the allowed extensions
audio_files = UploadSet('audio', extensions=audio_extensions)
video_files = UploadSet('video', extensions=video_extensions)

# configure Flask-Uploads to save uploaded files to the 'uploads' directory
app.config['UPLOADS_DEFAULT_DEST'] = 'uploads'
configure_uploads(app, (audio_files, video_files))


@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files or 'video' not in request.files:
        return jsonify({'error': 'Missing file(s)'}), 400

    audio_file = request.files['audio']
    video_file = request.files['video']

    # save the files using Flask-Uploads
    audio_filename = audio_files.save(audio_file)
    video_filename = video_files.save(video_file)

    # return the filenames so they can be used later
    return jsonify({'audio': audio_filename, 'video': video_filename}), 200


@app.route('/landing_page', methods=['GET'])
def landing_page():
    name = request.args.get('name')
    video_url = request.args.get('video_url')
    return render_template('index.html', name=name, video_url=video_url)


@app.route('/process', methods=['GET'])
def process():
    audio_filename = request.args.get('audio_filename')
    video_filename = request.args.get('video_filename')
    audio_files = split_audio(audio_filename=audio_filename)
    names_and_audios = audio_mapper(audio_files)
    print("Video Process Started")
    # process_video(names_and_audios=names_and_audios,
    #               video_filename=video_filename)
    print("Video Process Sucess")
    names_and_email = fetch_names_and_email()
    uris = upload_video(names_and_email=names_and_email)

    return jsonify({'messgae': 'Sucess and email sent'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5005)
