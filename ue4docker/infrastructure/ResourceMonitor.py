import datetime, humanfriendly, os, psutil, shutil, threading, time
from .DockerUtils import DockerUtils

class ResourceMonitor(threading.Thread):
	
	def __init__(self, logger, interval):
		'''
		Creates a resource monitor with the specified configuration
		'''
		super().__init__()
		self._logger = logger
		self._interval = interval
		self._lock = threading.Lock()
		self._shouldStop = False
	
	def stop(self):
		'''
		Stops the resource monitor thread
		'''
		
		# Set the flag to instruct the resource monitor loop to stop
		with self._lock:
			self._shouldStop = True
		
		# Wait for the resource monitor thread to complete
		if self.is_alive() == True:
			self.join()
	
	def run(self):
		'''
		The resource monitor loop itself
		'''
		
		# Determine which filesystem the Docker daemon uses for storing its data directory
		dockerInfo = DockerUtils.info()
		rootDir = dockerInfo['DockerRootDir']
		
		# If we cannot access the Docker data directory (e.g. when the daemon is in a Moby VM), don't report disk space
		reportDisk = os.path.exists(rootDir)
		
		# Sample the CPU usage using an interval of 1 second the first time to prime the system
		# (See: <https://psutil.readthedocs.io/en/latest/#psutil.cpu_percent>)
		psutil.cpu_percent(1.0)
		
		# Loop until asked to stop
		while True:
			
			# Check that the thread has not been asked to stop
			with self._lock:
				if self._shouldStop == True:
					return
			
			# Format the timestamp for the current time in ISO 8601 format (albeit without the "T" separator)
			isoTime = datetime.datetime.now().replace(microsecond=0).isoformat(' ')
			
			# We format data sizes using binary units (KiB, MiB, GiB, etc.)
			formatSize = lambda size: humanfriendly.format_size(size, binary=True, keep_width=True)
			
			# Format the current quantity of available disk space on the Docker data directory's filesystem
			diskSpace = formatSize(shutil.disk_usage(rootDir).free) if reportDisk == True else 'Unknown'
			
			# Format the current quantity of available system memory
			physicalMemory = formatSize(psutil.virtual_memory().free)
			virtualMemory = formatSize(psutil.swap_memory().free)
			
			# Format the current CPU usage levels
			cpu = psutil.cpu_percent()
			
			# Report the current levels of our available resources
			self._logger.info('[{}] [Available disk: {}] [Available memory: {} physical, {} virtual] [CPU usage: {:.2f}%]'.format(
				isoTime,
				diskSpace,
				physicalMemory,
				virtualMemory,
				cpu
			), False)
			
			# Sleep until the next sampling interval
			time.sleep(self._interval)
