# OCR Tool

Ứng dụng web trích xuất văn bản từ ảnh và PDF bằng **PaddleOCR**, chạy trong Docker (Linux container) để tránh các vấn đề tương thích trên Windows CPU.

---

## Tính năng

- Upload ảnh hoặc PDF qua giao diện kéo thả
- **Tự động nhận diện ngôn ngữ** — OCR lần đầu với model English, detect ngôn ngữ, re-run nếu cần
- Hỗ trợ 10 ngôn ngữ: Việt, Anh, Trung (Giản/Phồn thể), Nhật, Hàn, Pháp, Đức, Ả Rập, Hindi
- Điều chỉnh DPI cho PDF (72–600, mặc định 200)
- Sao chép kết quả hoặc tải về `.txt`
- Xử lý bất đồng bộ — theo dõi tiến trình theo thời gian thực

## Định dạng hỗ trợ

| Loại | Định dạng |
|------|-----------|
| Ảnh  | JPG, JPEG, PNG, BMP, TIFF, TIF, WEBP |
| Tài liệu | PDF (nhiều trang) |

Giới hạn upload: **50 MB**

---

## Chạy với Docker

### Yêu cầu

- Docker Desktop (Windows) với WSL2 backend
- Không cần cài Python hay Poppler trên máy host

### Build và chạy

```bash
docker build -t ocr-app .
docker run -d -p 5000:5000 --name ocr-container ocr-app
```

Mở trình duyệt tại `http://localhost:5000`

### Dừng và xoá container

```bash
docker stop ocr-container
docker rm ocr-container
```

### Chạy lại (không cần build lại)

```bash
docker start ocr-container
```

### Rebuild sau khi sửa code

```bash
docker stop ocr-container && docker rm ocr-container
docker build -t ocr-app .
docker run -d -p 5000:5000 --name ocr-container ocr-app
```

---

## Cấu trúc dự án

```
ocr/
├── app.py            # Flask server, API endpoints, job management
├── ocr_engine.py     # OCREngine class, language detection
├── Dockerfile        # Linux container với PaddleOCR + Poppler
├── .dockerignore
├── templates/
│   └── index.html    # Single-page UI
└── uploads/          # Tạm thời — file tự xoá sau khi OCR xong
```

---

## API

### `POST /upload`

Upload file và bắt đầu OCR.

**Form data:**

| Field | Kiểu   | Mặc định | Mô tả |
|-------|--------|----------|-------|
| `file` | File  | —        | File ảnh hoặc PDF |
| `lang` | string | `vi`   | Ngôn ngữ: `auto`, `vi`, `en`, `ch`, `chinese_cht`, `japan`, `korean`, `fr`, `german`, `arabic`, `hindi` |
| `dpi`  | int    | `200`  | DPI khi render PDF (72–600) |

**Response:**
```json
{ "job_id": "abc123", "filename": "document.pdf" }
```

---

### `GET /status/<job_id>`

Lấy trạng thái và kết quả của job.

**Response (đang xử lý):**
```json
{ "status": "processing", "filename": "document.pdf" }
```

**Response (hoàn tất):**
```json
{
  "status": "done",
  "text": "Nội dung văn bản...",
  "page_count": 3,
  "char_count": 1247,
  "detected_lang": "vi",
  "detected_lang_name": "Tiếng Việt"
}
```

**Trạng thái job:**

| Status | Ý nghĩa |
|--------|---------|
| `queued` | Đang chờ xử lý |
| `loading_model` | Đang tải model PaddleOCR |
| `processing` | Đang nhận dạng văn bản |
| `done` | Hoàn tất |
| `error` | Thất bại (kèm `error`, `trace`) |

---

## Tại sao dùng Docker?

PaddleOCR trên **Windows CPU** gặp lỗi `oneDNN / PIR executor` không khắc phục được:

```
NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support
[pir::ArrayAttribute<pir::DoubleAttribute>]
```

Docker chạy Linux container → tránh hoàn toàn vấn đề này, PaddleOCR hoạt động bình thường.

---

## Lưu ý

- Lần chạy đầu tiên sau khi start container: model PaddleOCR tải về ~100-300MB, mất 30–60 giây
- Model được cache trong RAM — các lần sau nhanh hơn nhiều
- File upload bị xoá ngay sau khi OCR xong
- Kết quả job được giữ trong bộ nhớ 1 giờ rồi tự xoá
- Chạy hoàn toàn offline sau lần tải model đầu tiên

## Stack

| Component | Version |
|-----------|---------|
| PaddleOCR | 2.9.1   |
| PaddlePaddle | 3.0.0 (CPU) |
| Flask     | 3.1.0   |
| pdf2image | 1.17.0  |
| Poppler   | apt (Debian trixie) |
| langdetect | latest |
| Python    | 3.11    |
| Base image | python:3.11-slim |
