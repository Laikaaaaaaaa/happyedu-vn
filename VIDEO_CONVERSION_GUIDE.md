# Hướng Dẫn Convert Video sang WebM (VP9)

## 🎯 Tại sao chuyển sang WebM?

- ✅ Nén tốt hơn MP4 (giảm 30-50% dung lượng)
- ✅ Codec VP9 tối ưu cho web
- ✅ Hỗ trợ trên hầu hết các trình duyệt hiện đại
- ✅ Không cần sử dụng LFS

## 📋 Yêu Cầu

1. **FFmpeg** - Công cụ xử lý video
   - Tải từ: https://ffmpeg.org/download.html
   - Hoặc dùng Chocolatey: `choco install ffmpeg`
   - Hoặc dùng Windows Package Manager: `winget install FFmpeg.FFmpeg`

## 🚀 Các Bước

### 1. Cài đặt FFmpeg (nếu chưa có)

**Cách 1: Dùng Chocolatey (nếu đã cài)**
```powershell
choco install ffmpeg -y
```

**Cách 2: Dùng Windows Package Manager**
```powershell
winget install FFmpeg.FFmpeg
```

**Cách 3: Tải từ trang chính thức**
- Vào https://ffmpeg.org/download.html
- Tải phiên bản Windows dùng được (full build)
- Giải nén và thêm vào PATH

### 2. Xác minh FFmpeg đã cài đặt

```powershell
ffmpeg -version
```

### 3. Convert các file MP4 sang WebM

**Cách nhanh nhất: Chạy script**
```powershell
cd "C:\Users\abc23\OneDrive\Máy tính\Student Protect"
.\convert_to_webm.ps1
```

**Cách thủ công: Convert từng file**
```powershell
# Mở PowerShell tại thư mục project
cd "C:\Users\abc23\OneDrive\Máy tính\Student Protect"

# Convert với VP9 codec (chất lượng cao, file nhỏ)
ffmpeg -i "video/videoplayback.mp4" -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus -b:a 128k "video/videoplayback.webm"
ffmpeg -i "video/videoplayback (1).mp4" -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus -b:a 128k "video/videoplayback (1).webm"
ffmpeg -i "video/videoplayback (2).mp4" -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus -b:a 128k "video/videoplayback (2).webm"
ffmpeg -i "video/videoplayback (3).mp4" -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus -b:a 128k "video/videoplayback (3).webm"
ffmpeg -i "video/videoplayback (4).mp4" -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus -b:a 128k "video/videoplayback (4).webm"
```

## ⚙️ Giải Thích Command

```
ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus -b:a 128k output.webm
```

- `-i input.mp4` - File đầu vào
- `-c:v libvpx-vp9` - Codec video VP9 (tốt nhất cho web)
- `-crf 30` - Chất lượng (0-63, thấp hơn = tốt hơn, mặc định 31)
- `-b:v 0` - Bitrate video tự động (tối ưu)
- `-c:a libopus` - Codec âm thanh Opus (tốt nhất)
- `-b:a 128k` - Bitrate âm thanh 128kbps
- `output.webm` - File đầu ra

## 📊 Dung Lượng So Sánh (Ước Tính)

| Format | Codec | Dung Lượng | Ghi Chú |
|--------|-------|-----------|--------|
| MP4 | H.264 | 100% | Gốc |
| WebM | VP9 | 40-60% | Nén tốt |
| WebM (VP8) | VP8 | 50-70% | Nhanh hơn VP9 |

## 🔧 Tuỳ Chọn Tối Ưu Hóa

**Nếu muốn chất lượng cao hơn (file lớn hơn):**
```powershell
ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf 25 -b:v 0 -c:a libopus output.webm
```

**Nếu muốn file nhỏ hơn (chất lượng thấp hơn):**
```powershell
ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf 35 -b:v 0 -c:a libopus -b:a 96k output.webm
```

**Nếu muốn encode nhanh hơn (dùng VP8 thay vì VP9):**
```powershell
ffmpeg -i input.mp4 -c:v libvpx -crf 30 -b:v 0 -c:a libopus output.webm
```

## ✅ Kiểm Tra Kết Quả

Sau khi convert xong:

1. Kiểm tra file WebM đã tồn tại
2. Mở `prevent_violence.html` trong trình duyệt
3. Video sẽ tự động phát

## 🐛 Xử Lý Sự Cố

**Lỗi: "ffmpeg is not recognized"**
- FFmpeg chưa được cài đặt
- Hoặc chưa thêm vào PATH
- Giải pháp: Cài đặt lại FFmpeg và chọn "Add to PATH"

**Lỗi: "File not found"**
- Đảm bảo đang chạy PowerShell từ thư mục project
- Hoặc dùng đường dẫn tuyệt đối

**Convert quá chậm**
- Dùng VP8 thay VP9 (nhanh hơn nhưng file lớn hơn một chút)
- Hoặc tăng `-crf` thành 35-40

## 📝 Lưu Ý

- Quá trình convert có thể mất vài phút tùy dung lượng file
- File WebM sẽ được lưu trong cùng thư mục `video/`
- File MP4 gốc có thể xóa sau khi xác minh WebM hoạt động
- HTML đã được cập nhật để dùng file `.webm`

## 🎬 Hỗ Trợ Trình Duyệt

WebM với VP9 được hỗ trợ trên:
- ✅ Chrome/Edge 29+
- ✅ Firefox 28+
- ✅ Opera 16+
- ⚠️ Safari: Không hỗ trợ (dùng MP4 fallback)

Để hỗ trợ Safari, bạn có thể thêm fallback:
```html
<video>
  <source src="video.webm" type="video/webm" />
  <source src="video.mp4" type="video/mp4" />
  Trình duyệt của bạn không hỗ trợ video.
</video>
```

---

**Cần giúp? Liên hệ hoặc chạy: `powershell .\convert_to_webm.ps1`**
