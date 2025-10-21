import syauto

config = syauto.Config()

print("config load")
config.load("config/test.json")

print("config view")
config.view()

print("type check")
config.validate(type_check=True, list_check=False, checksum_check=False, manual_check=False)
print("list check")
config.validate(type_check=False, list_check=True, checksum_check=False, manual_check=False)
print("checksum check")
config.validate(type_check=False, list_check=False, checksum_check=True, manual_check=False)
print("manual check")
config.validate(type_check=False, list_check=False, checksum_check=False, manual_check=True)

