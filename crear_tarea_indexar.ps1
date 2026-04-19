$python  = 'C:\Python314\python.exe'
$script  = 'L:\JusticiaArgentina\indexar_todo.py'
$wd      = 'L:\JusticiaArgentina'

$action   = New-ScheduledTaskAction -Execute $python -Argument $script -WorkingDirectory $wd
$trigger  = New-ScheduledTaskTrigger -Daily -At '21:05'
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 23) -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName    'JusticiaAR_Indexar' `
    -Description 'Indexa SAIJ + InfoLeg en Qdrant Cloud. Retoma desde checkpoint. Reinicia diario a medianoche UTC.' `
    -Action      $action `
    -Trigger     $trigger `
    -Settings    $settings `
    -RunLevel    Highest `
    -Force | Out-Null

Write-Host "Tarea 'JusticiaAR_Indexar' registrada. Proxima ejecucion: 21:05 hora local (00:05 UTC)."
Get-ScheduledTask -TaskName 'JusticiaAR_Indexar' | Select-Object TaskName, State
