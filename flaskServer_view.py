#terminate job->find job dir
#reads PID
#kills job

import os, controller
# Render HTML templates and access data sent by POST
# using the request object from flask. Redirect and url_for
# will be used to redirect the user once the upload is done
# and send_from_directory will send/show on the
# browser the file that the user just uploaded
from flask import Flask, render_template, request, url_for, send_from_directory, make_response, abort, jsonify
from werkzeug import secure_filename
from werkzeug.contrib.fixers import ProxyFix

# Initialize the Flask application
app = Flask(__name__)

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that are acceptable to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['xml'])

app.wsgi_app = ProxyFix(app.wsgi_app)

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/')
def index():
    return render_template('index.html')

# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded file
    file = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file

        filearg = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        #queue job
        newtest = controller.JobRunner(filearg)
        jobID = newtest.queueJob()

        print "newjob scheduled: " + str(jobID)

        #import redirect
        #return redirect(url_for('uploaded_file',filename=filename))
        return jsonify( { 'JobID': jobID } ), 200
    return jsonify( { 'code':'400', 'error': 'File extension not allowed' } ), 400

# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it one the browser, so if the user uploads
# an image, that image is going to be show after the upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/<jobID>', methods = ['DELETE'])
def abortJob(jobID):
    #DEBUG print "attempting abort job: " + jobID
    job = controller.JobRunner()
    job.abortJob(jobID)
    return jsonify( { 'success': 'Check for print stmt' } ), 200

@app.route('/jobs', methods=['GET'])
def getAllStatus():
    alljobs = controller.JobRunner()
    tasks = alljobs.getstatus()
    return jsonify( { 'success': 'Check for print stmt', 'jobs': tasks } ), 200

@app.route('/jobs/<jobID>', methods=['GET'])
def getStatus(jobID):
    newtest = controller.JobRunner()
    task = newtest.getstatus(jobID=jobID)
    #DEBUG print "get jobID status"
    return jsonify( { 'success': 'Check for print stmt', 'status': task } ), 200

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        debug=True
    )
