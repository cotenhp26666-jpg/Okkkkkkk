
from flask import Flask, request, jsonify
import subprocess
import os
import random
import json
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
scheduler = BackgroundScheduler(daemon=True)

BASE_DIR = "/root/denvkl"  # Đường dẫn chứa các file .py trên VPS

API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'bot_secret_key_12345')


SCRIPT_CALL_DIRECT = ["lenhcall1.py", "lenhcall.py", "lenhmoi1.py", "lenhmoi5.py"]

SCRIPT_SPAM_DIRECT = ["lenhmoi5.py", "lenhmoi.py", "lenhspam1.py", "07.py"]

SCRIPT_FREE = ["08.py", "06.py"]

TIMEOUT_MAP = {
    'full': 1200,   # 20 phút
    'vip': 180,     # 3 phút
    'sms': 180,     # 3 phút
    'spam': 300,    # 5 phút
    'call': 300,    # 5 phút
    'free': 100,    # ~1.6 phút
    'tiktok': 3600, # 60 phút
    'ngl': 3600     # 60 phút
}


USER_PROCESSES = {}
PROCESS_LOCK = threading.Lock()

def chay_script(command, user_id=None, timeout=None, command_type=None):
    try:
        if not command or not user_id:
            return False, None

        if command_type:
            timeout = TIMEOUT_MAP.get(command_type, 180)
        else:
            timeout = timeout or 180

        with PROCESS_LOCK:
            user_procs = USER_PROCESSES.get(user_id, [])
            alive_procs = []
            for p in user_procs:
                if p.poll() is None:
                    alive_procs.append(p)
            USER_PROCESSES[user_id] = alive_procs

            if len(alive_procs) >= 10:
                return False, None

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
            start_new_session=True,
            cwd=BASE_DIR
        )

        with PROCESS_LOCK:
            if user_id not in USER_PROCESSES:
                USER_PROCESSES[user_id] = []
            USER_PROCESSES[user_id].append(process)

        def kill_after_timeout():
            time.sleep(timeout)
            try:
                if process.poll() is None:
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
            except:
                pass

        timer = threading.Thread(target=kill_after_timeout, daemon=True)
        timer.start()

        return True, process.pid
    except Exception as e:
        return False, None


@app.route('/execute', methods=['POST'])
def execute():
    try:
        # *** ADD THESE 6 LINES ***qq
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "data": {"error": "Thiếu xác thực"}}), 401
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        if token != API_SECRET_KEY:
            return jsonify({"success": False, "data": {"error": "Xác thực không hợp lệ"}}), 401
                
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "data": {"error": "Không có dữ liệu"}}), 400

        command_type = data.get("command_type")
        phone_numbers = data.get("phone_numbers", [])
        user_id = str(data.get("user_id", "0"))
        requested_script = data.get("script_name")  # Script cụ thể từ bot (nếu có)
        rounds = data.get("rounds")

        if not command_type or not phone_numbers:
            return jsonify({"success": False, "data": {"error": "Thiếu command_type hoặc phone_numbers"}}), 400

        supported_types = {"call", "spam", "free"}
        if command_type not in supported_types:
            return jsonify({"success": False, "data": {"error": f"Không hỗ trợ loại: {command_type}"}}), 400

        if not requested_script:
            return jsonify({"success": False, "data": {"error": "Bot chưa truyền script_name"}}), 400

        success_count = 0
        pids = []
        script_name = requested_script

        # Xác định round_value
        if command_type in ["free", "call", "spam"]:
            round_value = rounds if rounds else 2
        else:
            round_value = None

        for phone in phone_numbers:

            if round_value:
                cmd = f"python3 {os.path.join(BASE_DIR, script_name)} {phone} {round_value}"
            else:
                cmd = f"python3 {os.path.join(BASE_DIR, script_name)} {phone}"

            success, pid = chay_script(cmd, user_id, command_type=command_type)
            if success:
                success_count += 1
                pids.append(pid)

        if success_count > 0:
            return jsonify({
                "success": True,
                "data": {
                    "message": f"Chạy {success_count} script thành công",
                    "pids": pids,
                    "script": script_name,
                    "command_type": command_type
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "data": {"error": "Không thể chạy script"}
            }), 500

    except Exception as e:
        return jsonify({"success": False, "data": {"error": str(e)}}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "OK"}), 200


def cleanup_dead_processes():
    with PROCESS_LOCK:
        for user_id in list(USER_PROCESSES.keys()):
            alive_procs = []
            for p in USER_PROCESSES[user_id]:
                if p.poll() is None:
                    alive_procs.append(p)
            USER_PROCESSES[user_id] = alive_procs
            if not alive_procs:
                del USER_PROCESSES[user_id]
    print(" 🧹 Dọn dẹp process chết")

if __name__ == '__main__':
    print("🚀 API Server khởi động...")
    scheduler.add_job(cleanup_dead_processes, 'interval', minutes=20, id='cleanup_processes')
    scheduler.start()
    print("📅 Các nhiệm vụ đã lên lịch đã bắt đầu:")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
