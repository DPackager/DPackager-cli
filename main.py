import sys
import json
from pathlib import Path
import requests
import os
import zipfile

cmd_args = sys.argv
supported_args = ['--install', '--init', '--uninstall', '--check-dependencies', '--run']

dpackagerEndpoint = "http://127.0.0.1"

def add_to_package_json(packageName, packageVersion):
	packageFile = Path("package.json")
	if packageFile.is_file() == False: print('ERROR: package.json file not found'); exit()
	else:
		with open('package.json', 'r') as pkgFileR:
			content = pkgFileR.read()
			pkgFileR.close()

		with open('package.json', 'w') as pkgFileW:
			inputJson = json.loads(content)
			inputJson["dependencies"] = inputJson["dependencies"] | {
				packageName: {
					"version": packageVersion
				}
			}
			json.dump(inputJson, pkgFileW, sort_keys=True, indent=4)
			pkgFileW.close()

try:
	cmd_args[1]
except:
	print('ERROR: No arguments')
	exit()

if cmd_args[1] not in supported_args:
	print(f'Unknown command: {cmd_args[1]}')
else:
	for i, arg in enumerate(cmd_args):
		if arg == "--run":
			scriptToRun = cmd_args[2]
			with open('package.json', 'r') as pkgFileR:
				content = pkgFileR.read()
				inputJson = json.loads(content)

				for script in inputJson['scripts']:
					if script == scriptToRun:
						os.system(inputJson['scripts'][script])


		if arg == "--check-dependencies":
			with open('package.json', 'r') as pkgFileR:
				content = pkgFileR.read()
				inputJson = json.loads(content)

				#print(inputJson['dependencies'])
				#print(inputJson['dependencies']['example']['version'])

				packagesNotFound = 0
				packagesNotAvailable = 0
				packagesNoUpgrade = 0
				packagesUpgraded = 0

				for dependency in inputJson['dependencies']:
					packageName = dependency
					packageVersion = inputJson['dependencies'][dependency]['version']

					packageRequested = requests.get(dpackagerEndpoint + f"/api/v1/package/{packageName}/{packageVersion}/package-info.json")
					if packageRequested.status_code == 404:
						packagesNotFound = packagesNotFound + 1
						print(f'INFO: Package not found: {packageName}')

					if packageRequested.status_code == 403:
						packagesNotAvailable = packagesNotFound + 1
						print(f'INFO: Package {packageName} was blocked or not available to all')

					if packageRequested.status_code == 200:
						packageRequestedVersion = packageRequested.json()['version']

						if packageRequestedVersion == packageVersion:
							packagesNoUpgrade = packagesNoUpgrade + 1
							print(f'INFO: Upgrade/Downgrade not required for {packageName}')
						else:
							packagesUpgraded = packagesUpgraded + 1
							print(f'INFO: Upgrade/Downgrade required for {packageName}')

				print()
				print(f'Packages upgrade required: {packagesUpgraded}')
				print(f'Packages upgrade not required: {packagesNoUpgrade}')
				print(f'Packages not found: {packagesNotFound}')
				print(f'Packages not available: {packagesNotAvailable}')

					# os.mkdir(f'./packages/{packageName}')
					# with open(f"./packages/{packageName}/" + package.json()["downloadURLFileName"], 'wb') as packageFileOutput:
					# 	packageFileOutput.write(file.content)
					# 	packageFileOutput.close()

		if arg == "--install":
			packageName = cmd_args[2]
			try:
				packageVersion = cmd_args[3]
			except:
				print('WARN: Version was not specified. Installing latest')
				packageVersion = "latest"

			steps = 5

			print(f'[1/{steps}] Checking package is exists...')

			package = requests.get(dpackagerEndpoint + f"/api/v1/package/{packageName}/{packageVersion}/package-info.json")

			if package.status_code == 404: print('[1/4] ERROR: Package not found'); exit()
			if package.status_code == 403: print('[1/4] ERROR: Package was blocked or not available to all'); exit()

			print(f'[2/{steps}] Adding to package.json')

			add_to_package_json(packageName, packageVersion)

			print(f'[3/{steps}] Downloading package...')
            #print(f'[3.1/{steps}] Downloading main file from {package.json()["downloadURL"]}...')

			file = requests.get(package.json()["downloadURL"].replace('DPACKAGER_ENDPOINT', dpackagerEndpoint))
			os.mkdir(f'./packages/{packageName}')
			with open(f"./packages/{packageName}/" + package.json()["downloadURLFileName"], 'wb') as packageFileOutput:
				packageFileOutput.write(file.content)
				packageFileOutput.close()

			if package.json()["downloadURLFileName"].endswith('.zip'):
                #print(f'[3.2/{steps}] This is a zip archive. Unzipping...')
				src = zipfile.ZipFile(f'./packages/{packageName}/{package.json()["downloadURLFileName"]}')
				src.extractall(f'./packages/{packageName}')
				src.close()

			print(f'[4/{steps}] Running setup.py...')
			os.system(f'python ./packages/{packageName}/setup.py')

			print(f'[5/{steps}] Package sucessfully installed!')


		if arg == "--init":
			print("This utility helps you create a package.json file.")
			print("This file is needed for packages, version control and many other things.")
			print()
			packageName = input('Package name> ')
			packageVersion = input('Package version (1.0.0)> ')
			packageAuthor = input('Package author> ')
			tags = input('Tags> ')
			mainFile = input('Main file (main.py)> ')
			repository = input('Repository> ')
			license = input('License (MIT License)> ')

			# Default values
			if packageVersion == "": packageVersion = "1.0.0"
			if mainFile == "": mainFile = "main.py"
			if license == "": license = "MIT License"

			outputJson = json.dumps(
				{
					"name": packageName,
					"version": packageVersion,
					"author": packageAuthor,
					"tags": tags,
					"main": mainFile,
					"repository": repository,
					"license": license,
					"scripts": {},
					"dependencies": {},
					"devDependencies": {}
				}
			, sort_keys=True, indent=4)

			print(outputJson)
			print()
			thisisok = input('This is OK? (yes)> ')
			if thisisok == "": thisisok = "yes"

			if thisisok == 'yes':
				with open('package.json', 'w') as pkgFile:
					pkgFile.write(outputJson)
					pkgFile.close()
				os.mkdir('packages')