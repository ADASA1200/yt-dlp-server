from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import threading

app = Flask(__name__)
DOWNLOAD_DIR = '/tmp/downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

tasks = {}

def do_download(task_id, url):
    try:
        out_path = os.path.join(DOWNLOAD_DIR, task_id)
        os.makedirs(out_path, exist_ok=True)
        ydl_opts = {
            'outtmpl': os.path.join(out_path, '%(title)s.%(ext)s'),
            'format': 'bestvideo[height<=720]+bestaudio/best',
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            filename = filename.rsplit('.', 1)[0] + '.mp4'
            tasks[task_id] = {'status': 'done', 'file': filename, 'title': info.get('title', 'video')}
    except Exception as e:
        tasks[task_id] = {'status': 'error', 'error': str(e)}

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'חסר url'}), 400
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'processing'}
    threading.Thread(target=do_download, args=(task_id, url)).start()
    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def status(task_id):
    return jsonify(tasks.get(task_id, {'status': 'not_found'}))

@app.route('/file/<task_id>')
def get_file(task_id):
    task = tasks.get(task_id)
    if not task or task['status'] != 'done':
        return jsonify({'error': 'לא מוכן'}), 404
    return send_file(task['file'], as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
