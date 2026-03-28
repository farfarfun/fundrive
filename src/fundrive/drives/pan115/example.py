import json

from fundrive.drives.pan115 import Pan115Drive

client = Pan115Drive()
client.login()


print(json.dumps(client.get_dir_info("3369823275968248606")))
print(json.dumps(client.get_file_info("3394089708692585354")))


def find_file(fid):
    for ff in client.get_all_list(fid=fid):
        if ff["isfile"]:
            print(json.dumps(ff))
        else:
            find_file(ff.fid)


find_file("3369823275968248606")
