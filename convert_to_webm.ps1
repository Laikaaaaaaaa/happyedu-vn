# Script để convert MP4 sang WebM (VP9)
# Yêu cầu: FFmpeg phải được cài đặt

$videoFolder = ".\video"
$ffmpegPath = "$env:USERPROFILE\AppData\Local\ffmpeg\bin\ffmpeg.exe"
$mp4Files = Get-ChildItem -Path $videoFolder -Filter "*.mp4" -File

if (-not (Test-Path $ffmpegPath)) {
    Write-Host "Loi: FFmpeg khong tim thay tai: $ffmpegPath"
    Write-Host "Vui long cai dat FFmpeg truoc"
    exit 1
}

if ($mp4Files.Count -eq 0) {
    Write-Host "Khong tim thay file MP4 nao trong thu muc $videoFolder"
    exit
}

Write-Host "Tim thay $($mp4Files.Count) file MP4 de convert..."
Write-Host ""

foreach ($file in $mp4Files) {
    $inputPath = $file.FullName
    $outputPath = Join-Path -Path $videoFolder -ChildPath "$($file.BaseName).webm"
    
    # Kiểm tra nếu file WebM đã tồn tại
    if (Test-Path $outputPath) {
        Write-Host "OK $($file.Name) = $([System.IO.Path]::GetFileName($outputPath)) (da co)"
        continue
    }
    
    Write-Host "Convert: $($file.Name)"
    Write-Host "   Dung luong: $([math]::Round($file.Length/1MB, 2)) MB"
    
    # Chạy FFmpeg conversion
    & $ffmpegPath -i "$inputPath" -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus -b:a 128k "$outputPath" -y
    
    if ($LASTEXITCODE -eq 0) {
        $newSize = (Get-Item $outputPath).Length
        $reduction = [math]::Round(100 - (($newSize / $file.Length) * 100), 1)
        Write-Host "Thanh cong! Kich thuoc: $([math]::Round($newSize/1MB, 2)) MB (giam $reduction%)"
    } else {
        Write-Host "Loi khi convert!"
    }
    Write-Host ""
}

Write-Host "Hoan thanh!"
