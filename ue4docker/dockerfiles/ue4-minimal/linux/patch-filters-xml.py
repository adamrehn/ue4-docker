#!/usr/bin/env python3
import os, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

filtersXml = sys.argv[1]
code = readFile(filtersXml)

# Add missing SetupDotnet.sh in Unreal Engine 5.0.0-early-access-1
# See https://github.com/adamrehn/ue4-docker/issues/171#issuecomment-853918412
# and https://github.com/EpicGames/UnrealEngine/commit/a18824057e6cd490750a10b59af29ca10b3d67d9
dotnet = 'Engine/Binaries/ThirdParty/DotNet/Linux/...'
setup_dotnet = 'Engine/Build/BatchFiles/Linux/SetupDotnet.sh'
if dotnet in code and setup_dotnet not in code:
	code = code.replace(dotnet, f'{dotnet}\n{setup_dotnet}')

writeFile(filtersXml, code)
