import pandas as pd
import sys

if len(sys.argv) != 3:
	print('Syntax: python convert.py <path to input csv file> <path to output directory>')
	exit(1)

df_path = sys.argv[1]
output_dir = sys.argv[2]

df = pd.read_csv(df_path, encoding="utf-8", header=None)

final_dfs = {}
device_group = df.groupby(0)
for device_key in device_group.groups.keys():
	param_dfs = {}
	device_df = device_group.get_group(device_key)
	device_df = device_df.drop(device_df.columns[[0]], axis=1)

	param_group = device_df.groupby(1)
	for param_key in param_group.groups.keys():
		print(f'Detected {device_key}/{param_key}')
		param_df = param_group.get_group(param_key)
		param_df = param_df.drop(param_df.columns[[0]], axis=1)
		param_df.columns = ["Time", "Data", "Unit"]
		param_dfs[param_key] = param_df

	final_dfs[device_key] = param_dfs

print()

code_conversions = {
	"eRep": {
		"curr": "Target Current"
	},
	"edwr": {
		"g1pres": "Chamber Pressure",
		"g1gas": "Chamber Gas"
	},
	"uwGen": {
		"isOn": "Microwave Generator Active",
		"volt": "Microwave Generator Voltage",
		"ignite": "Microwave Generator Ignite",
		"conPwr": "Microwave Generator Control Power",
		"auto": "Microwave Generator Automatic Mode",
		"setpoint": "Microwave Generator Setpoint",
		"forPwr": "Microwave Generator Forward Power",
		"revPwr": "Microwave Generator Reverse Power",
		"curr": "Microwave Generator Current",
		"temp": "Microwave Generator Temperature"
	}
}

for device_key, device_dict in final_dfs.items():
	for param_key, param_df in device_dict.items():
		param_df.to_csv(f'{output_dir}/{code_conversions[device_key][param_key]}.csv', encoding="utf-8", index=False)
		print(f'Saved "{code_conversions[device_key][param_key]}.csv" file')