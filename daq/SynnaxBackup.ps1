# Makes program stop after encountering an error.
$ErrorActionPreference = "Stop"

$Log_Location = "C:\Path\To\Log\File\name_of_log_file.txt"

$Refresh_Token = "3kbiqaK4vqoAAAAAAAAAAZ9dJtIXNRH1KDJXD1vQhgcm0qtZoE9rhPtTP5Ts-NJk"
$App_Key = "be8l3cgg7vio7am"
$App_Secret = "prwaw7of98rbtfx"
$Folder_To_Compress = "C:\Path\To\Synnax\Data\synnax-deploy\synnax-data"

# Where to store backups locally (temporarily, before uploading!).
# Might want to make a dedicated folder for this. If an error occurs before or while uploading, the zip file won't be removed properly...
$Zip_File_Location = "C:\Path\To\Temporary\Storage\Area"
$Date = Get-Date -Format "MM_dd_yyyy_HHmmss"
$Zip_File_Name = "Backup_1-${Date}.zip"

# Folder in Dropbox that backups will be uploaded to. Do NOT end it in "/".
# Make sure the folder exists. This script will throw an error if the directory does not exist.
$Dropbox_Backup_Folder = "/ENGIN-MASA/Software/Synnax-Backups"

# Overwritten by the GetRootNamespace function.
$Root_Namespace_Id = ""

$Max_Backup_Index = 10


# Makes the log look slightly prettier.
function header {
	$Date = Get-Date -Format "[MM/dd/yyyy]"
	Write-Output "" >> $Log_Location
	Write-Output "NEW BACKUP: $Date" >> $Log_Location
	Write-Output "========================" >> $Log_Location
}


# Logs a message and does not halt the program.
function log {
	Param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
	
	$Timestamp = Get-Date -Format "[MM/dd/yyyy HH:mm:ss]"
	Write-Host "$Timestamp $Message"
	Write-Output "$Timestamp $Message" >> $Log_Location
}


# Logs an error message and halts the program.
function error {
	Param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
	
	log "${Message}: $($Error[0])"
	throw "${Message}: $($Error[0])"
}
	

# Uses the refresh token to generate a valid access token.
function Get-New-Access-Token {
    Param(
        [Parameter(Mandatory=$true)]
        [string]$Refresh_Token,
        [Parameter(Mandatory=$true)]
        [string]$Client_Id,
        [Parameter(Mandatory=$true)]
        [string]$Client_Secret
    )

    $url = "https://api.dropboxapi.com/oauth2/token"
    $body = @{
        grant_type    = "refresh_token"
        refresh_token = $Refresh_Token
        client_id     = $Client_Id
        client_secret = $Client_Secret
    }

    $response = ""
	
	try {
		$response = Invoke-RestMethod -Uri $url -Method Post -ContentType "application/x-www-form-urlencoded" -Body $body
	}
	catch {
		error "An error occured while attempting to receive a new access token using the refresh token"
	}

    return $response.access_token
}


function Get-User-Info {
	Param(
        [Parameter(Mandatory=$true)]
        [string]$Access_Token
	)
	
	$url = "https://api.dropboxapi.com/2/users/get_current_account"
	$headers = @{
        "Authorization" = "Bearer $Access_Token"
		"Content-Type"  = "application/json"
	}
	$body = "null" # no, do not use $null. that throws an error
	
	try {
		$response = Invoke-WebRequest -Uri $url -Method Post -Headers $headers -Body $body
	}
	catch {
		error "An error occured while attempting to get user info"
	}
	
	return $response.Content | ConvertFrom-Json
}


# Extracts the true root directory so the script doesn't just place files in personal folders.
function Get-Root-Namespace-Id {
	Param(
        [Parameter(Mandatory=$true)]
        [string]$Access_Token
	)
	
	$User_Info = Get-User-Info -Access_Token $Dropbox_Access_Token
	return $User_Info.root_info.root_namespace_id
}


# Uploads the file at Source_File_Path on the local machine to Target_File_Path in Dropbox.
function Send-To-Dropbox {
    Param(
        [Parameter(Mandatory=$true)]
        [string]$Dropbox_Access_Token,
        [Parameter(Mandatory=$true)]
        [string]$Source_File_Path,
        [Parameter(Mandatory=$true)]
        [string]$Target_File_Path
    )

	$url = "https://content.dropboxapi.com/2/files/upload"
	$headers = @{
        "Authorization" = "Bearer $Dropbox_Access_Token"
		"Dropbox-API-Arg" = '{ "path": "' + $Target_File_Path + '", "mode": "add", "autorename": true, "mute": false }'
        "Content-Type" = "application/octet-stream"
		"Dropbox-API-Path-Root" = '{".tag": "root", "root": "' + $Root_Namespace_Id + '"}'
	}
	

    $response = ""
	
	try {
		$response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -InFile $Source_File_Path
	}
	catch {
		error "An error occured while attempting to upload the file ${Source_File_Path} onto Dropbox as ${Target_File_Path}"
	}
	
	log "Uploaded the file ${Source_File_Path} onto Dropbox as ${Target_File_Path}"

    # return $response
}


# Returns a list of Dropbox files.
function Get-Dropbox-Files {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Dropbox_Access_Token,
        [Parameter(Mandatory=$true)]
        [string]$Dropbox_Folder
    )
	
	$url = "https://api.dropboxapi.com/2/files/list_folder"
	
	$headers = @{
        "Authorization" = "Bearer $Dropbox_Access_Token"
        "Content-Type" = "application/json"
		"Dropbox-API-Path-Root" = '{".tag": "root", "root": "' + $Root_Namespace_Id + '"}'
    }

    $body = @{
        path = $Dropbox_Folder
        recursive = $false
    } | ConvertTo-Json -Depth 10
	
	$response = ""

	try {
		$response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body
	}
	catch {
		error "An error occured while attempting to get the files in the Dropbox folder ${Dropbox_Folder}"
	}
	
    return $response.entries
}


# Delete a file from Dropbox.
function Delete-Dropbox-File {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Dropbox_Access_Token,
        [Parameter(Mandatory=$true)]
        [string]$File_To_Delete
    )
	
	$url = "https://api.dropboxapi.com/2/files/delete_v2"
	
	$headers = @{
        "Authorization" = "Bearer $Dropbox_Access_Token"
        "Content-Type" = "application/json"
		"Dropbox-API-Path-Root" = '{".tag": "root", "root": "' + $Root_Namespace_Id + '"}'
    }

    $body = @{ path = $File_To_Delete } | ConvertTo-Json
	
	$response = ""

	try {
		$response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body
	}
	catch {
		error "An error occured while attempting to delete the Dropbox file ${File_To_Delete}"
	}
	
	# return $response
}


# Technically doesn't rename. Moves the file at Old_Path to New_Path.
function Rename-Dropbox-File {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Dropbox_Access_Token,
        [Parameter(Mandatory=$true)]
        [string]$Old_Path,
        [Parameter(Mandatory=$true)]
        [string]$New_Path
    )
	
	$url = "https://api.dropboxapi.com/2/files/move_v2"
	$headers = @{
        "Authorization" = "Bearer $Dropbox_Access_Token"
        "Content-Type" = "application/json"
		"Dropbox-API-Path-Root" = '{".tag": "root", "root": "' + $Root_Namespace_Id + '"}'
    }
    $body = @{
        from_path = $Old_Path
        to_path = $New_Path
    } | ConvertTo-Json -Depth 10

    $response = ""
	
	try {
		$response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body
	}
	catch {
		error "An error occured while attempting to rename the Dropbox file ${Old_Path} into ${New_Path}"
	}

    # return $response
}


# Remove all files in Dropbox_Backup_Folder that are not named "Backup_[index]-[timestamp]", where index is less than Max_Backup_Index.
function Delete-Extra-Backups {
	param (
        [Parameter(Mandatory=$true)]
        [string]$Dropbox_Access_Token,
        [Parameter(Mandatory=$true)]
        [string]$Dropbox_Folder,	
        [Parameter(Mandatory=$true)]
        [int]$Max_Backup_Index
	)
	
	$files = Get-Dropbox-Files -Dropbox_Access_Token $Dropbox_Access_Token -Dropbox_Folder $Dropbox_Folder
	
	foreach ($file in $files) {
		log "Saw $($file.name) when deleting extra backups"
		if ($file.name -match "Backup_(\d+)-(.+)") {
			$index = [int]$Matches[1]
			if ($index -lt $Max_Backup_Index) {
				log "Kept $($file.name): index $index was less than max index $Max_Backup_Index"
			}
			else {
				Delete-Dropbox-File -Dropbox_Access_Token $Dropbox_Access_Token -File_To_Delete $file.path_lower
				log "Deleted $($file.name): index $index was greater than or equal to max index $Max_Backup_Index"
			}
		}
		else {
			Delete-Dropbox-File -Dropbox_Access_Token $Dropbox_Access_Token -File_To_Delete $file.path_lower
			log "Deleted $($file.name): file named poorly"
		}
	}
}


# Make room for a new "Backup_1_[timestamp]" by incrementing existing backups in Dropbox_Backup_Folder by 1.
# Technically there might be a collision if two backups have the same timestamps, down to the second. I think I'd cry if that happened.
function Rename-Existing-Backups {
	param (
        [Parameter(Mandatory=$true)]
        [string]$Dropbox_Access_Token,
        [Parameter(Mandatory=$true)]
        [string]$Dropbox_Folder,
        [Parameter(Mandatory=$true)]
        [int]$Max_Backup_Index
	)
	
	$files = Get-Dropbox-Files -Dropbox_Access_Token $Dropbox_Access_Token -Dropbox_Folder $Dropbox_Folder
	
	foreach ($file in $files) {
		log "Saw $($file.name) when renaming existing backups"
		if ($file.name -match "Backup_(\d+)-(.+)") {
			$index = [int]$Matches[1]
			if ($index -le $Max_Backup_Index) {
				$renamed = "Backup_$($index + 1)-$($Matches[2])"
				Rename-Dropbox-File -Dropbox_Access_Token $Dropbox_Access_Token -Old_Path $file.path_lower -New_Path "${Dropbox_Backup_Folder}/${renamed}"
				log "Renamed $($file.name) to ${renamed}"
			}
			else {
				log "Ignored $($file.name): index $($Matches[1]) was larger than max index $Max_Backup_Index"
			}
		}
		else {
			log "Ignored $($file.name): file named poorly"
		}
	}
	
}

# Print header to the log.
header

# Get an access token using the refresh token.
$Dropbox_Access_Token = Get-New-Access-Token -Refresh_Token $Refresh_Token -Client_Id $App_Key -Client_Secret $App_Secret

# Get the true root to place files in.
$Root_Namespace_Id = Get-Root-Namespace-Id -Access_Token $Dropbox_Access_Token

# Squish all the data into a zip file.
$Zip_File_Path = "${Zip_File_Location}\$Zip_File_Name"
Compress-Archive $Folder_To_Compress $Zip_File_Path -Force

# Make room for the new file.
Delete-Extra-Backups -Dropbox_Access_Token $Dropbox_Access_Token -Dropbox_Folder $Dropbox_Backup_Folder -Max_Backup_Index $Max_Backup_Index
Rename-Existing-Backups -Dropbox_Access_Token $Dropbox_Access_Token -Dropbox_Folder $Dropbox_Backup_Folder -Max_Backup_Index $Max_Backup_Index

# Upload the zip file to Dropbox.
$Dropbox_File_Path = "${Dropbox_Backup_Folder}/$Zip_File_Name"
Send-To-Dropbox -Dropbox_Access_Token $Dropbox_Access_Token -Source_File_Path $Zip_File_Path -Target_File_Path $Dropbox_File_Path

# Clean up the zip file we made.
Remove-Item $Zip_File_Path