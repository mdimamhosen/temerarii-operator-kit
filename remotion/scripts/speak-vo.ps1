Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = -2
$synth.Volume = 85
try {
  $voices = $synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo }
  $prefer = $voices | Where-Object { $_.Name -match 'Zira|Jenny|Aria|Female' } | Select-Object -First 1
  if ($prefer) { $synth.SelectVoice($prefer.Name) }
} catch {}

$lines = @(
  'Seven checks. About seventy minutes.',
  'We measure refrigerant charge against spec, and the reading stays on screen.',
  'Outdoor coil cleaned. Real dirt, real hose. No theatrics.',
  'This is the part that usually goes. Capacitor tested under load.',
  'Temperature split across the evaporator, next to the manufacturer spec.',
  'One hundred twenty nine dollars. You keep the readings.',
  'Book when you are ready. northgate home slash book.'
)

$out = Join-Path $PSScriptRoot '..\public\vo.wav'
$synth.SetOutputToWaveFile($out)
foreach ($line in $lines) {
  $synth.Speak($line)
  Start-Sleep -Milliseconds 350
}
$synth.Dispose()
Write-Host "wrote $out"
Get-Item $out | Format-List FullName, Length
