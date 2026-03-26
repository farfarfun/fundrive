import json

from fundrive.drives.pan115 import Pan115Drive

client = Pan115Drive()
client.login()
# print(client.get_file_info("3369824441389168762"))
print(json.dumps(client.get_file_info("3383167882122639641")))
print(json.dumps(client.get_dir_info("3369823279004924710")))
print(json.dumps(client.get_file_list("3369823279004924710")))
print(json.dumps(client.get_dir_list("3369823279004924710")))
print(json.dumps(client.get_file_list("3369823324278241328")))

print(json.dumps(client.get_quota()))
print(json.dumps(client.get_dir_info("3369823275968248606")))

client.download_file("3383167882122639641", save_dir="./")
