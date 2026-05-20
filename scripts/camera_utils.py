import os

def find_camera_index(keyword="Jupiter"):
    base_path = "/sys/class/video4linux"
    if not os.path.exists(base_path):
        return 0

    devices = sorted(os.listdir(base_path))
    for device in devices:
        name_path = os.path.join(base_path, device, "name")
        if os.path.exists(name_path):
            with open(name_path, "r") as f:
                device_name = f.read().strip()
                if keyword.lower() in device_name.lower():
                    return int(device.replace("video", ""))
    return 0