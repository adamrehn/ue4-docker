# escape=`
ARG BASETAG
FROM mcr.microsoft.com/windows/servercore:${BASETAG}
SHELL ["cmd", "/S", "/C"]

# Add a sentinel label so we can easily identify intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Write an 8GiB file in blocks of 1GiB to avoid allocating too much memory in one hit
RUN powershell "`
	$ErrorActionPreference = 'Stop';`
	$writer = [System.IO.File]::OpenWrite('file');`
	`
	$random = new-object Random;`
	$blockSize = 1073741824;`
	$bytes = new-object byte[] $blockSize;`
	for ($i=0; $i -lt 8; $i++)`
	{`
		$random.NextBytes($bytes);`
		$writer.Write($bytes, 0, $blockSize);`
	}`
	`
	$writer.Close();`
	"
