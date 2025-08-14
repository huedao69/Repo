# Auto Content System — VN Maritime (Safe Mode)

Tự động thu thập tin tức hàng hải Việt Nam → GPT tóm tắt (có trích dẫn) → **đưa lên WordPress ở trạng thái Pending** để bạn duyệt tay. Có lớp **kiểm duyệt an toàn** (blacklist + AI policy).

## Nhanh gọn để chạy
1) `cp .env.example .env` rồi điền:
   - `OPENAI_API_KEY=`
   - `WORDPRESS_BASE_URL=` (vd: https://yourdomain.com)
   - `WORDPRESS_USERNAME=` (user Editor dành riêng, ví dụ api-bot)
   - `WORDPRESS_APP_PASSWORD=` (Application Password của user đó)
2) Kiểm tra nguồn trong `app/scraper/sources.yaml` (đã cắm sẵn hàng hải VN).
3) Chạy một vòng: `python -m app.main --once` (hoặc dùng Docker/GitHub Actions).

## Safe Mode
- `app/config/safety.yaml`:
  - `publish_mode: pending` (giữ trạng thái Pending)
  - `require_citations: true`
  - `blacklist:` các từ khoá nhạy cảm
- Lớp kiểm duyệt sẽ phân loại: **OK/REVIEW/BLOCK**.
  - BLOCK → chuyển **draft** (không công khai).
  - OK/REVIEW → **pending** để bạn duyệt.

## Lưu ý pháp lý
- Tôn trọng robots.txt/TOS.
- Chỉ tóm tắt và luôn **trích dẫn nguồn**.
- Tránh các chủ đề cấm theo pháp luật và chính sách nền tảng.
