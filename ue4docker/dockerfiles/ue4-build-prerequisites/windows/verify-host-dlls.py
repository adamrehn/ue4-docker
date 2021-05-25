import glob, os, sys, win32api


# Adapted from the code in this SO answer: <https://stackoverflow.com/a/7993095>
def getDllVersion(dllPath):
	info = win32api.GetFileVersionInfo(dllPath, '\\')
	return '{:d}.{:d}.{:d}.{:d}'.format(
		info['FileVersionMS'] // 65536,
		info['FileVersionMS'] % 65536,
		info['FileVersionLS'] // 65536,
		info['FileVersionLS'] % 65536
	)


# Print the host and container OS build numbers
print('Host OS build number:      {}'.format(sys.argv[1]))
print('Container OS build number: {}'.format(sys.getwindowsversion().build))
sys.stdout.flush()

# Verify each DLL file in the directory specified by our command-line argument
dlls = glob.glob(os.path.join(sys.argv[2], '*.dll'))
for dll in dlls:
	
	# Attempt to retrieve the version number of the DLL
	dllName = os.path.basename(dll)
	try:
		dllVersion = getDllVersion(dll)
	except Exception as err:
		print('\nError: could not read the version string from the DLL file "{}".'.format(dllName), file=sys.stderr)
		print('Please ensure the DLLs copied from the host are valid DLL files.', file=sys.stderr)
		print('\nError details:', file=sys.stderr)
		print(err, file=sys.stderr)
		sys.exit(1)
	
	# Print the DLL details
	print('Found host DLL file "{}" with version string "{}".'.format(dllName, dllVersion))
	sys.stdout.flush()
	
	# Determine if the container OS will load the DLL
	try:
		handle = win32api.LoadLibrary(dll)
		win32api.FreeLibrary(handle)
	except Exception as err:
		print('\nError: the container OS cannot load the DLL file "{}".'.format(dllName), file=sys.stderr)
		print('This typically indicates that the DLL is from a newer version of Windows.', file=sys.stderr)
		print('Please ensure the DLLs copied from the host match the container OS version.', file=sys.stderr)
		print('\nError details:', file=sys.stderr)
		print(err, file=sys.stderr)
		sys.exit(1)
