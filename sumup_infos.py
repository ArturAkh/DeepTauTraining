import json

infos = {}
summed_infos = {}

with open("info.json", "r") as f:
    infos = json.load(f)

keys = []

for fpath in infos:
    keys = infos[fpath].keys()
    break

for k in keys:
    summed_infos[k] = sum([info[k] for info in infos.values()])

with open("summed_info.json", "w") as out:
    json.dump(summed_infos, out, indent=2, sort_keys=True)

print "Minimum:",min(summed_infos.values()), "Maximum:", max(summed_infos.values())
