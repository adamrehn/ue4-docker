# Determine if we are creating a file filled with zeroes or random bytes
if ($Env:CREATE_RANDOM -ne 1)
{
	Write-Host 'Attempting to create an 8GiB file containing zeroes...';
	fsutil.exe file createnew file 8589934592
}
else
{
	Write-Host 'Attempting to create an 8GiB file containing random bytes...';
	$ErrorActionPreference = 'Stop';
	$writer = [System.IO.File]::OpenWrite('file');
	
	# Write the file in blocks of 1GiB to avoid allocating too much memory in one hit
	$random = new-object Random;
	$blockSize = 1073741824;
	$bytes = new-object byte[] $blockSize;
	for ($i=0; $i -lt 8; $i++)
	{
		$random.NextBytes($bytes);
		$writer.Write($bytes, 0, $blockSize);
	}
	
	$writer.Close();
}
