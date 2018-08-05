#!/usr/bin/env python3
import shutil, subprocess, sys, ue4cli
from os.path import join

# Query ue4cli for the UE4 version string and the root directory of the UE4 source tree
ue4 = ue4cli.UnrealManagerFactory.create()
versionMinor = int(ue4.getEngineVersion('minor'))
engineRoot = ue4.getEngineRoot()

# Runs a command from the root of the UE4 source tree
def run(command):
	subprocess.run(command, shell=False, cwd=engineRoot, check=True)

# We only need to rebuild SDL2 for 4.20.0 and newer
if versionMinor < 20:
	print('Detected UE4 version {}, skipping rebuild of SDL2.'.format(ue4.getEngineVersion()), file=sys.stderr)
	run('mkdir /tmp/sdl')
	sys.exit(0)

# Retrieve the dependency files for SDL and Vulkan
run([
	'./Engine/Build/BatchFiles/Linux/GitDependencies.sh',
	'--prompt',
	'--exclude=AMD',
	'--exclude=AndroidPermission',
	'--exclude=ANGLE',
	'--exclude=Binaries',
	'--exclude=Breakpad',
	'--exclude=Build',
	'--exclude=CEF3',
	'--exclude=Content',
	'--exclude=coremod',
	'--exclude=CryptoPP',
	'--exclude=Documentation',
	'--exclude=DotNetZip',
	'--exclude=elftoolchain',
	'--exclude=Expat',
	'--exclude=Extras',
	'--exclude=FakeIt',
	'--exclude=FBX',
	'--exclude=FeaturePacks',
	'--exclude=ForsythTriOO',
	'--exclude=FreeType2',
	'--exclude=glslang',
	'--exclude=GoogleARCore',
	'--exclude=GoogleInstantPreview',
	'--exclude=GoogleTest',
	'--exclude=GoogleVR',
	'--exclude=HarfBuzz',
	'--exclude=hlslcc',
	'--exclude=ICU',
	'--exclude=IntelEmbree',
	'--exclude=IntelISPCTexComp',
	'--exclude=IntelTBB',
	'--exclude=IOS',
	'--exclude=jemalloc',
	'--exclude=Kiss_FFT',
	'--exclude=Leap',
	'--exclude=libcurl',
	'--exclude=libOpus',
	'--exclude=libPhonon',
	'--exclude=libPNG',
	'--exclude=libSampleRate',
	'--exclude=libstrophe',
	'--exclude=libWebSockets',
	'--exclude=Licenses',
	'--exclude=llvm',
	'--exclude=MCPP',
	'--exclude=MikkTSpace',
	'--exclude=mtlpp',
	'--exclude=NVIDIA',
	'--exclude=nvtesslib',
	'--exclude=nvTextureTools',
	'--exclude=nvTriStrip',
	'--exclude=Oculus',
	'--exclude=Ogg',
	'--exclude=OneSky',
	'--exclude=OpenAL',
	'--exclude=openexr',
	'--exclude=OpenSSL',
	'--exclude=OpenSubdiv',
	'--exclude=OpenVR',
	'--exclude=Perforce',
	'--exclude=PLCrashReporter',
	'--exclude=Plugins',
	'--exclude=Programs',
	'--exclude=PhysX',
	'--exclude=PhysX3',
	'--exclude=Qualcomm',
	'--exclude=rd_route',
	'--exclude=ResonanceAudioApi',
	'--exclude=Runtime',
	'--exclude=Samples',
	'--exclude=SpeedTree',
	'--exclude=Steamworks',
	'--exclude=Templates',
	'--exclude=TVOS',
	'--exclude=VHACD',
	'--exclude=Vorbis',
	'--exclude=WebRTC',
	'--exclude=Windows',
	'--exclude=zlib'
])

# Copy the Vulkan headers into the location that the SDL2 build script looks for them
run(['mkdir', join(engineRoot, 'Engine/Source/ThirdParty/Vulkan/Linux')])
run(['cp', '-R', join(engineRoot, 'Engine/Source/ThirdParty/Vulkan/Include'), join(engineRoot, 'Engine/Source/ThirdParty/Vulkan/Linux/include')])

# Rebuild SDL2
run(['./Engine/Source/ThirdParty/SDL2/build.sh'])

# Copy the built files to the destination directory (used by the Dockerfile for copying from the builder image)
buildDir = join(engineRoot, 'Engine/Source/ThirdParty/SDL2/SDL-gui-backend/lib/Linux/x86_64-unknown-linux-gnu')
shutil.copytree(buildDir, '/tmp/sdl')
