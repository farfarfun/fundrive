import json

from fundrive.drives.pan115 import Pan115Drive

client = Pan115Drive()
client.login()
# print(client.get_file_info("3369824441389168762"))
print(client.get_file_info("3369823279004924710"))
print(json.dumps(client.get_quota()))

client.download_file("3369823322608908330", save_dir="./")


print(json.dumps(client.get_dir_info("3369823322608908330")))
