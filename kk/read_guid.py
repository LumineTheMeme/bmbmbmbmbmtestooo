import zipfile
import os
import xml.etree.ElementTree as ET

def read_guid(file_path):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_path} does not exist.")
        
        if not zipfile.is_zipfile(file_path):
            raise ValueError(f"{file_path} is not a valid zip file.")
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            if 'manifest.xml' not in zip_ref.namelist():
                raise ValueError(f"{file_path} does not contain manifest.xml.")
            
            with zip_ref.open('manifest.xml') as manifest_file:
                content = manifest_file.read().decode('utf-8')
                root = ET.fromstring(content)
                guid = root.find('guid').text
                return guid
    except Exception as e:
        print(f"[load_zipmods] Warning: {e}")
        return None

# Example usage
if __name__ == "__main__":
    test_zipmod_path = "test.zipmod"
    
    guid = read_guid(test_zipmod_path)
    if guid:
        print(f"[load_zipmods] Extracted GUID: {guid}")
    else:
        print("[load_zipmods] Failed to extract GUID.")
