import csv
import os
import shutil
import requests
import sys
import argparse
from multiprocessing import Process, Lock, Manager, Queue, current_process
from read_guid import read_guid
import hashlib

CSV_INPUT = 'd_url.csv'
CSV_OUTPUT = 'd_download.csv'
TMP_DIR = 'tmp'

def format_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

def compute_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"[×] 读取失败: {file_path} - {e}")
        return None

def setup_dirs():
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR, exist_ok=True)

def init_output_csv():
    if not os.path.exists(CSV_OUTPUT):
        with open(CSV_INPUT, 'r', encoding='utf-8') as fin, \
             open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as fout:
            reader = csv.reader(fin)
            writer = csv.writer(fout)
            for row in reader:
                while len(row) < 7:
                    row.append('')
                writer.writerow(row)

def load_completed_indexes():
    completed = set()
    with open(CSV_OUTPUT, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 7 and row[5] and row[6]:  # guid 和 md5 不为空
                completed.add(row[0].strip())
    return completed

def update_csv_line(filename, index, updated_row, lock: Lock):
    with lock:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))

            i = int(index) - 1
            if 0 <= i < len(rows):
                row = rows[i]
                while len(row) < 7:
                    row.append('')
                row[5] = updated_row[5]
                row[6] = updated_row[6]
                rows[i] = row
            else:
                print(f"[×] 无效 index: {index}")

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
        except Exception as e:
            print(f"[×] 更新 CSV 行失败: index={index} - {e}")

def worker(task_queue: Queue, lock: Lock, total_downloaded):
    while True:
        try:
            task = task_queue.get(timeout=1)
        except:
            break

        if task is None:
            break

        index, url, filename, time_str, size = task
        tmp_filename = os.path.join(TMP_DIR, f"{index}.zipmod")

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            with open(tmp_filename, 'wb') as f:
                local_bytes = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        local_bytes += len(chunk)
                        if local_bytes >= 1024 * 1024:  # Update every 1MB
                            with lock:
                                total_downloaded.value += local_bytes
                                current_total = total_downloaded.value
                            local_bytes = 0
                            sys.stdout.write(f"\r[*] Total Downloaded: {format_size(current_total)}    ")
                            sys.stdout.flush()

                if local_bytes > 0:
                    with lock:
                        total_downloaded.value += local_bytes
                        current_total = total_downloaded.value

            guid = read_guid(tmp_filename)
            md5 = compute_md5(tmp_filename)

            updated_row = [index, url, filename, time_str, size, guid, md5]
            update_csv_line(CSV_OUTPUT, index, updated_row, lock)

            with lock:
                current_total = total_downloaded.value
            print(f"\r[✓] {current_process().name} 下载完成: {tmp_filename} | Session Total: {format_size(current_total)}    ")
            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)

        except Exception as e:
            print(f"[×] {current_process().name} 下载失败: {filename} - {e}")
            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)

def main():
    parser = argparse.ArgumentParser(description="Download mod metadata and extract GUID/MD5")
    parser.add_argument("-d", "--download", action="store_true", help="Perform the actual downloads")
    parser.add_argument("-t", "--threads", type=int, default=5, help="Number of worker threads (default: 5)")
    args = parser.parse_args()

    # Ensure output CSV exists for comparison
    if not os.path.exists(CSV_OUTPUT):
        init_output_csv()
    
    completed = load_completed_indexes()
    
    pending_tasks = []
    with open(CSV_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 5:
                index = row[0].strip()
                if index not in completed:
                    pending_tasks.append(row)

    print(f"[*] Found {len(pending_tasks)} pending downloads.")

    if not args.download:
        if len(pending_tasks) > 0:
            print("[!] Use -d flag to start downloading.")
        return

    if not pending_tasks:
        print("[✓] All metadata is already up to date.")
        return

    setup_dirs()
    
    manager = Manager()
    lock = Lock()
    total_downloaded = manager.Value('Q', 0)
    task_queue = manager.Queue()
    
    for row in pending_tasks:
        index = row[0].strip()
        url = row[1].strip()
        filename = row[2].strip()
        time_str = row[3].strip()
        size = row[4].strip()
        task_queue.put((index, url, filename, time_str, size))

    print(f"[*] Starting download process with {args.threads} workers...")

    processes = []
    try:
        for i in range(args.threads):
            p = Process(target=worker, args=(task_queue, lock, total_downloaded), name=f"Worker-{i+1}")
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

    except KeyboardInterrupt:
        print("\n[!] 收到 Ctrl+C，强制终止所有子进程...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
        print("[!] 所有任务已中断并退出。")
        sys.exit(1)

if __name__ == '__main__':
    main()
