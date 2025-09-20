#!/usr/bin/env python3
"""
Video80s Web API - Flask server with web interface
"""
import os
import sys
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from flask import Flask, request, jsonify, render_template, send_file, flash, redirect, url_for
from flask_cors import CORS

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.video_processor import VideoProcessor
from src.youtube_uploader import YouTubeUploader
from src.json_storage import JsonStorageHandler
from config import VIDEO_CONFIG, YOUTUBE_CONFIG, setup_directories

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'video80s_secret_key_change_in_production'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB limit

# Enable CORS for API endpoints
CORS(app)

# Setup directories
setup_directories()

# Global variables for tracking jobs
processing_jobs = {}
upload_jobs = {}


class JobStatus:
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


def create_job_id():
    """Generate unique job ID"""
    return str(uuid.uuid4())


def allowed_file(filename, extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


# ================================
# Web Interface Routes
# ================================

@app.route('/')
def index():
    """Main web interface"""
    return render_template('index.html')


@app.route('/upload')
def upload_page():
    """Upload page"""
    return render_template('upload.html')


@app.route('/status')
def status_page():
    """Status page"""
    return render_template('status.html')


@app.route('/direct-upload')
def direct_upload_page():
    """Direct upload page"""
    return render_template('direct_upload.html')


# ================================
# API Routes - Video Processing
# ================================

@app.route('/api/process-video', methods=['POST'])
def process_video_api():
    """API endpoint for video processing"""
    try:
        # Check if video file is present
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not allowed_file(video_file.filename, ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'webm']):
            return jsonify({'error': 'Invalid file format. Supported: mp4, avi, mov, mkv, wmv, webm'}), 400
        
        # Create job
        job_id = create_job_id()
        
        # Save uploaded file
        filename = secure_filename(video_file.filename)
        unique_filename = f"{job_id}_{filename}"
        input_path = os.path.join(VIDEO_CONFIG['input_folder'], unique_filename)
        video_file.save(input_path)
        
        # Get processing options
        background_style = request.form.get('background_style', 'blur')
        auto_upload = request.form.get('auto_upload', 'false').lower() == 'true'
        
        # Create output filename
        output_filename = f"processed_{unique_filename.rsplit('.', 1)[0]}.mp4"
        output_path = os.path.join(VIDEO_CONFIG['output_folder'], output_filename)
        
        # Initialize processing job
        processing_jobs[job_id] = {
            'id': job_id,
            'status': JobStatus.PENDING,
            'input_file': unique_filename,
            'output_file': output_filename,
            'progress': 0,
            'message': 'Job queued',
            'created_at': datetime.now().isoformat(),
            'auto_upload': auto_upload,
            'background_style': background_style
        }
        
        # Start processing in background
        import threading
        thread = threading.Thread(target=process_video_background, args=(job_id, input_path, output_path, background_style, auto_upload))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'accepted',
            'message': 'Video processing started'
        })
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum size: 1GB'}), 413
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def process_video_background(job_id, input_path, output_path, background_style, auto_upload):
    """Background video processing"""
    try:
        # Update job status
        processing_jobs[job_id]['status'] = JobStatus.PROCESSING
        processing_jobs[job_id]['message'] = 'Processing video...'
        processing_jobs[job_id]['progress'] = 10
        
        # Create video processor
        processor = VideoProcessor(
            input_video=input_path,
            logo_path=VIDEO_CONFIG['logo_path'],
            banner_path=VIDEO_CONFIG['banner_path'],
            output_path=output_path,
            background_style=background_style,
            banner_intro_path=VIDEO_CONFIG['banner_intro_path'],
            banner_outro_path=VIDEO_CONFIG['banner_outro_path']
        )
        
        processing_jobs[job_id]['progress'] = 30
        processing_jobs[job_id]['message'] = 'Adding logo and banners...'
        
        # Process video
        result = processor.process_video()
        
        if result['status'] == 'success':
            processing_jobs[job_id]['status'] = JobStatus.COMPLETED
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['message'] = 'Video processing completed'
            processing_jobs[job_id]['result'] = result
            processing_jobs[job_id]['download_url'] = f'/api/download/{os.path.basename(output_path)}'
            
            # Auto upload if requested
            if auto_upload:
                upload_to_youtube_background(job_id, output_path)
        else:
            processing_jobs[job_id]['status'] = JobStatus.FAILED
            processing_jobs[job_id]['message'] = f"Processing failed: {result.get('error_message', 'Unknown error')}"
        
        # Clean up input file
        if os.path.exists(input_path):
            os.remove(input_path)
            
    except Exception as e:
        processing_jobs[job_id]['status'] = JobStatus.FAILED
        processing_jobs[job_id]['message'] = f"Processing error: {str(e)}"


# ================================
# API Routes - Direct YouTube Upload
# ================================

@app.route('/api/direct-upload', methods=['POST'])
def direct_upload_api():
    """API endpoint for direct YouTube upload"""
    try:
        # Check if video file is present
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not allowed_file(video_file.filename, ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'webm']):
            return jsonify({'error': 'Invalid file format'}), 400
        
        # Create job
        job_id = create_job_id()
        
        # Save uploaded file
        filename = secure_filename(video_file.filename)
        unique_filename = f"{job_id}_{filename}"
        video_path = os.path.join(VIDEO_CONFIG['input_folder'], unique_filename)
        video_file.save(video_path)
        
        # Get metadata
        title = request.form.get('title', Path(filename).stem)
        description = request.form.get('description', f'Video uploaded via Video80s API\n\nOriginal filename: {filename}\n\n#Video #YouTube')
        tags = request.form.get('tags', 'Video,Upload').split(',')
        privacy = request.form.get('privacy', 'public')
        
        # Initialize upload job
        upload_jobs[job_id] = {
            'id': job_id,
            'status': JobStatus.PENDING,
            'filename': filename,
            'title': title,
            'progress': 0,
            'message': 'Upload queued',
            'created_at': datetime.now().isoformat()
        }
        
        # Start upload in background
        import threading
        thread = threading.Thread(target=upload_to_youtube_background, args=(job_id, video_path, title, description, tags, privacy))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'accepted',
            'message': 'Upload started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def upload_to_youtube_background(job_id, video_path, title=None, description=None, tags=None, privacy='public'):
    """Background YouTube upload"""
    try:
        # Update job status
        if job_id not in upload_jobs:
            upload_jobs[job_id] = {
                'id': job_id,
                'status': JobStatus.PENDING,
                'progress': 0,
                'message': 'Upload starting...',
                'created_at': datetime.now().isoformat()
            }
        
        upload_jobs[job_id]['status'] = JobStatus.PROCESSING
        upload_jobs[job_id]['message'] = 'Connecting to YouTube...'
        upload_jobs[job_id]['progress'] = 10
        
        # Auto-generate metadata if not provided
        if not title:
            title = Path(video_path).stem
        if not description:
            description = f"Video uploaded via Video80s API\n\n#Video #YouTube"
        if not tags:
            tags = ['Video', 'Upload']
        
        # Create uploader
        uploader = YouTubeUploader(
            client_secrets_file=YOUTUBE_CONFIG['client_secrets_file'],
            credentials_file=YOUTUBE_CONFIG['credentials_file']
        )
        
        upload_jobs[job_id]['progress'] = 30
        upload_jobs[job_id]['message'] = 'Uploading to YouTube...'
        
        # Upload video
        result = uploader.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy
        )
        
        if result['status'] == 'success':
            upload_jobs[job_id]['status'] = JobStatus.COMPLETED
            upload_jobs[job_id]['progress'] = 100
            upload_jobs[job_id]['message'] = 'Upload completed successfully'
            upload_jobs[job_id]['result'] = result
        else:
            upload_jobs[job_id]['status'] = JobStatus.FAILED
            upload_jobs[job_id]['message'] = f"Upload failed: {result.get('message', 'Unknown error')}"
        
        # Clean up file
        if os.path.exists(video_path):
            os.remove(video_path)
            
    except Exception as e:
        upload_jobs[job_id]['status'] = JobStatus.FAILED
        upload_jobs[job_id]['message'] = f"Upload error: {str(e)}"


# ================================
# API Routes - Job Status
# ================================

@app.route('/api/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status"""
    # Check in processing jobs
    if job_id in processing_jobs:
        return jsonify(processing_jobs[job_id])
    
    # Check in upload jobs
    if job_id in upload_jobs:
        return jsonify(upload_jobs[job_id])
    
    return jsonify({'error': 'Job not found'}), 404


@app.route('/api/jobs', methods=['GET'])
def get_all_jobs():
    """Get all jobs"""
    all_jobs = {}
    all_jobs.update({f"process_{k}": v for k, v in processing_jobs.items()})
    all_jobs.update({f"upload_{k}": v for k, v in upload_jobs.items()})
    
    # Sort by created_at
    sorted_jobs = dict(sorted(all_jobs.items(), key=lambda x: x[1]['created_at'], reverse=True))
    
    return jsonify(sorted_jobs)


# ================================
# API Routes - File Operations
# ================================

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download processed video"""
    file_path = os.path.join(VIDEO_CONFIG['output_folder'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/files')
def list_files():
    """List available files"""
    output_files = []
    if os.path.exists(VIDEO_CONFIG['output_folder']):
        for filename in os.listdir(VIDEO_CONFIG['output_folder']):
            if filename.endswith(('.mp4', '.avi', '.mov')):
                file_path = os.path.join(VIDEO_CONFIG['output_folder'], filename)
                file_info = {
                    'filename': filename,
                    'size': os.path.getsize(file_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    'download_url': f'/api/download/{filename}'
                }
                output_files.append(file_info)
    
    return jsonify(output_files)


# ================================
# Health Check
# ================================

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


# ================================
# Error Handlers
# ================================

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("🚀 Starting Video80s API Server...")
    print("📺 Web interface: http://localhost:5000")
    print("🔧 API endpoints: http://localhost:5000/api/")
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Set to False in production
        threaded=True
    )