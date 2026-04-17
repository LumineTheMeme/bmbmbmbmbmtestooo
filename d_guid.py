import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../step2')))

from read_guid import read_guid

CSV_INPUT = 'd_download.csv'
CSV_OUTPUT = 'br_mods.csv'

def main():
    if not os.path.exists(CSV_INPUT):
        print(f"[!] 找不到输入文件: {CSV_INPUT}")
        return

    with open(CSV_INPUT, 'r', encoding='utf-8') as f_in, \
         open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f_out:

        reader = csv.reader(f_in)
        writer = csv.writer(f_out)

        for row in reader:
            if len(row) < 3:
                print(f"[!] 跳过格式错误行: {row}")
                continue

            index, url, local_path = row[0].strip(), row[1].strip(), row[2].strip()
            try:
                guid = read_guid(local_path)
            except Exception as e:
                print(f"[×] 读取 GUID 失败: {local_path} - {e}")
                guid = ''

            writer.writerow([index, url, local_path, guid])

    print(f"[✓] 已生成: {CSV_OUTPUT}")

if __name__ == '__main__':
    main()
