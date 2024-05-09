from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from audio import hide_file_in_audio_util, extract_file_from_audio_util
from image import hide_file_in_img_util, extract_file_from_img_util
import numpy as np
import wave
from PIL import Image
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import io


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/')
def home():
    return 'Welcome'


@app.route('/audiohide', methods=['POST'])
def audiohide():
    try:
        required_files = ['secret', 'pubKey', 'audio']
        for field in required_files:
            if field not in request.files:
                return jsonify({"error": f"Missing file: {field}", "done": False}), 400

        # Extracting values from JSON request
        secret_file = request.files['secret']
        pub_key_file = request.files['pubKey']
        audio_file = request.files['audio']

        file_name = secret_file.filename.encode()
        file_data = secret_file.read()

        # Convert PEM data to public key object
        public_key_pem = pub_key_file.read()
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        # Open the audio
        audio = wave.open(audio_file, mode='rb')

        # Process the data
        output = hide_file_in_audio_util(
            audio, file_data, file_name, public_key)

        with io.BytesIO() as wav_io:
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setparams(audio.getparams())
                wav_file.writeframes(output)

            wav_bytes = wav_io.getvalue()

        aud_byte = io.BytesIO(wav_bytes)

        return send_file(
            aud_byte,
            as_attachment=True,
            download_name="",
            mimetype='audio/wav',
        ), 200

    except Exception as err:
        return jsonify({"error": f"error occurred: {str(err)}", "done": False}), 500


@app.route('/imagehide', methods=['POST'])
def imagehide():
    try:
        if 'output' not in request.form:
            return jsonify({"error": f"Missing required field: 'output'", "done": False}), 400

        required_files = ['secret', 'pubKey', 'image']
        for field in required_files:
            if field not in request.files:
                return jsonify({"error": f"Missing file: {field}", "done": False}), 400

        # Extracting values from JSON request
        secret_file = request.files['secret']
        pub_key_file = request.files['pubKey']
        image_file = request.files['image']
        output_name = request.form['output']

        # processing the secret file
        file_name = secret_file.filename.encode()
        file_data = secret_file.read()

        # Convert PEM data to public key object
        public_key_pem = pub_key_file.read()
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )

        # Open the image
        image = Image.open(image_file)
        image_name = image_file.filename

        # Process the data
        output, host_format = hide_file_in_img_util(
            image, image_name, file_data, file_name, public_key)

        img_io = io.BytesIO()

        output.save(img_io, host_format)
        img_io.seek(0)

        if host_format == 'PNG':
            mimetype = 'image/png'
        elif host_format == 'TIFF':
            mimetype = 'image/tiff'
        elif host_format == 'BMP':
            mimetype = 'image/bmp'
        elif host_format == 'TGA':
            mimetype = 'image/x-targa'
        else:
            mimetype = 'image/png'

        return send_file(
            img_io,
            as_attachment=True,
            download_name=output_name,
            mimetype=mimetype,
        ), 200

    except Exception as err:
        return jsonify({"error": f"error occurred: {str(err)}", "done": False}), 500


@app.route('/audioextract', methods=['POST'])
def audioextract():
    try:
        required_fields = ['passphrase', 'output']
        for field in required_fields:
            if field not in request.form:
                return jsonify({"error": f"Missing required field: {field}", "done": False}), 400

        required_files = ['priKey', 'audio']
        for file in required_files:
            if file not in request.files:
                return jsonify({"error": f"Missing file: {file}", "done": False}), 400

        # Extracting values from JSON request
        pri_key_file = request.files['priKey']
        audio_file = request.files['audio']
        output_name = request.form['output']
        passphrase = request.form['passphrase']

        private_key_pem = pri_key_file.read()
        # Convert PEM data to public key object
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=passphrase.encode(),
            backend=default_backend()
        )

        # Open the audio
        audio = wave.open(audio_file, mode='rb')

        # Process the data
        output, filename = extract_file_from_audio_util(audio, private_key)

        text = output.decode("utf-8")
        output_name = output_name or filename

        return jsonify({
            "data": text,
            "filename": output_name,
            "done": True
        }), 200

    except Exception as err:
        return jsonify({"error": f"error occurred: {str(err)}", "done": False}), 500


@app.route('/imageextract', methods=['POST'])
def imageextract():
    try:
        required_fields = ['passphrase', 'output']
        for field in required_fields:
            if field not in request.form:
                return jsonify({"error": f"Missing required field: {field}", "done": False}), 400

        required_files = ['priKey', 'image']
        for file in required_files:
            if file not in request.files:
                return jsonify({"error": f"Missing file: {file}", "done": False}), 400

        # Extracting values from JSON request
        pri_key_file = request.files['priKey']
        image_file = request.files['image']
        output_name = request.form['output']
        passphrase = request.form['passphrase']

        private_key_pem = pri_key_file.read()
        # Convert PEM data to public key object
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=passphrase.encode(),
            backend=default_backend()
        )

        # Open the audio
        image = Image.open(image_file)

        output, filename = extract_file_from_img_util(image, private_key)
        text = output.decode("utf-8")

        output_name = output_name or filename
        return jsonify({
            "data": text,
            "filename": output_name,
            "done": True
        }), 200

    except Exception as err:
        return jsonify({"error": f"error occurred: {str(err)}", "done": False}), 500


# Run the Flask application on port 8000
if __name__ == '__main__':
    app.run(debug=True, port=8000)
