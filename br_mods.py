import os
import csv
from logger import get_logger
from paths import get_resource_path

logger = get_logger(__name__)

def update_paths_in_csv(csv_filename, base_url, local_base_path):
    try:
        if not os.path.exists(csv_filename):
            raise FileNotFoundError(f"The file {csv_filename} does not exist.")
        
        updated_rows = []
        with open(csv_filename, mode='r', newline='', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            header = next(reader)  # Read the header
            updated_rows.append(header)
            
            for row in reader:
                if len(row) == 2:
                    local_path = row[1]
                    # Convert local path to URL path
                    remote_path = convert_to_remote_path(local_path, base_url, local_base_path)
                    row[1] = remote_path
                    updated_rows.append(row)
        
        # Write the updated rows back to the CSV file
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(updated_rows)
        
        logger.info(f"[rename] Paths updated in {csv_filename}")
    except Exception as e:
        logger.error(f"[rename] An error occurred: {e}", exc_info=True)

def convert_to_remote_path(local_path, base_url, local_base_path):
    try:
        if local_path.startswith(local_base_path):
            relative_path = local_path[len(local_base_path):].replace("\\", "/").lstrip("/")
            remote_path = f"{base_url}/{relative_path}"
            return remote_path
        else:
            logger.warning(f"[rename] Path does not start with base path: {local_path}")
            return local_path
    except Exception as e:
        logger.error(f"[rename] Error converting path: {e}")
        return local_path

def br_mods():
    try:
        csv_filename = get_resource_path('step3', 'd_download.csv')
        if not os.path.exists(csv_filename):
            raise FileNotFoundError(f"The file {csv_filename} does not exist.")
        
        guid_map = {}
        with open(csv_filename, mode='r', newline='', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                if len(row) == 7:
                    index, url, name, time, size, guid, md5 = row
                    guid_map[guid] = url
        return guid_map
    except Exception as e:
        logger.error(f"[br_mods] An error occurred: {e}", exc_info=True)
        return {}

# Example usage
if __name__ == "__main__":
    csv_filename = "br_mods.csv"
    base_url = "https://sideload.betterrepack.com/download/AISHS2"
    local_base_path = "D:\\HoneySelect2_ArcticFox\\BBManager\\mods"
    
    update_paths_in_csv(csv_filename, base_url, local_base_path)
