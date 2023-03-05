$dlls = (Get-ChildItem "C:\GatheredDLLs\*.dll")
foreach ($dll in $dlls)
{
	$filename = $dll.Name
	$existing = (Get-ChildItem "C:\Windows\System32\${filename}" -ErrorAction SilentlyContinue)
	if ($existing)
	{
		[Console]::Error.WriteLine("${filename} already exists in System32 in the target base image, excluding it from the list of DLL files to copy.")
		Remove-Item $dll
	}
}
