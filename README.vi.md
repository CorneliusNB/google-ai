# ePlus AI Toolkit — Tiếng Việt

<!-- Source README.md git-blob: 66dc72117e92b338bad604c5fd83517588cf878a -->

[English](README.md) · **Tiếng Việt** · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md)


> **Tài liệu gốc:** [README tiếng Anh](README.md). Nội dung bên dưới được diễn đạt bằng tiếng Việt để dễ theo dõi, đồng thời giữ nguyên các lệnh, điều kiện và lưu ý an toàn. Khi thông tin khác với chương trình thực tế, hãy ưu tiên kiểm tra mã nguồn và tài liệu gốc.

**ePlus AI Toolkit** giúp bạn kiểm tra các ưu đãi Google AI Pro được hiển thị qua Google One và Google Play trên thiết bị Android. Công cụ chạy trên **Windows và macOS**: Windows sử dụng PowerShell, còn macOS sử dụng Terminal (zsh/bash). Cả giao diện Textual lẫn chế độ dòng lệnh đều dùng chung bộ xử lý Python, ADB và Frida.

![Giao diện ePlus AI Toolkit](https://github.com/user-attachments/assets/f16cde7e-022f-43bc-97fe-310012b0a5d3)

> [!CAUTION]
> **Đây không phải công cụ chính thức của Google và có thể phát sinh chi phí.** Ở các bước **2–5**, công cụ có thể mở trang thanh toán Google Play và tự nhấn **Subscribe**. Ưu đãi xuất hiện trong danh sách, mức giá đầu tiên bằng 0 hoặc thông báo đã gửi yêu cầu thanh toán **không có nghĩa là** bạn đủ điều kiện, được dùng miễn phí hay đã gia hạn thành công. Trước khi thực hiện, hãy kiểm tra đúng tài khoản, khoản tiền phải trả ngay, mức phí những kỳ sau và ngày gia hạn trong **Google Play**. Dừng công cụ không hủy được giao dịch đã gửi.

> [!NOTE]
> **Xác thực thẻ có thể tạm giữ tiền dù hóa đơn Google Play hiển thị 0 USD.** Bạn có thể thấy khoản **giữ tiền chờ xử lý khoảng 3 USD** (hoặc mức khác) để xác thực thẻ. **3 USD chỉ là mức tham khảo, không phải phí cố định của Google hoặc bằng chứng đã thanh toán gói đăng ký.** Khoản tạm giữ có thể làm giảm số dư khả dụng; theo Google, lệnh xác thực này không phải giao dịch mua hàng và thường được giải tỏa trong **1–14 ngày làm việc**, tùy ngân hàng. Nếu tiền được hạch toán thành khoản trừ thực tế hoặc lệnh giữ tiền còn tồn tại sau 14 ngày làm việc, hãy liên hệ ngân hàng và Google Payments. [Nguồn chính thức của Google Play](https://support.google.com/googleplay/answer/6224192?hl=en).

## Tuyên bố miễn trừ trách nhiệm

ePlus AI Toolkit là dự án độc lập, **không thuộc và không được Google, Google One, Google Play, NetEase hay MuMuPlayer tài trợ hoặc xác nhận**. Phần mềm được cung cấp theo hiện trạng, không bảo đảm bạn sẽ nhận được ưu đãi, đăng ký thành công hoặc chạy được trên mọi thiết bị. Việc chuẩn bị môi trường có thể thay đổi cấu hình Android, Frida hoặc mạng. Chỉ dùng với tài khoản và thiết bị bạn sở hữu hoặc được phép sử dụng, đồng thời tuân thủ điều khoản liên quan. Đọc thêm [tuyên bố miễn trừ trách nhiệm](DISCLAIMER.md) và [hướng dẫn an toàn](SECURITY.md).

## 1. Chuẩn bị

**Chọn hướng dẫn phù hợp với hệ điều hành đang dùng.** Trên Mac, bạn không cần cài hay chạy PowerShell.

| Thành phần | Windows | macOS |
| --- | --- | --- |
| Terminal | **PowerShell 5.1 trở lên** | **Terminal** với zsh hoặc bash |
| Python | **3.10 trở lên**, dùng lệnh `python` | **3.10 trở lên**, dùng `python3`; công cụ tự tạo môi trường `.venv` |
| Git | Git for Windows | Git từ Xcode Command Line Tools hoặc Homebrew |
| Android | Thiết bị hoặc máy ảo đã bật root và ADB; hướng dẫn của dự án hỗ trợ **MuMuPlayer cho Windows** | Thiết bị Android có root hoặc máy ảo tương thích; **MuMuPlayer Pro cho Mac** chỉ phù hợp với Apple Silicon, không hỗ trợ Intel Mac |
| Ứng dụng Android | Google Play Store và Google One, đã đăng nhập đúng tài khoản | Tương tự trên thiết bị Android bạn sử dụng |
| ADB | Công cụ có thể tìm hoặc tải Android SDK Platform-Tools | Cần cài riêng, chẳng hạn `brew install android-platform-tools`; kiểm tra bằng `adb devices` |
| Frida | **16.5.9**; trình thiết lập Windows có thể chuẩn bị khi cần | **16.5.9** trong `.venv`; vẫn phải kiểm tra khả năng tương thích với Android |
| Lệnh khởi chạy | `.\run-all.ps1` | `sh run-macos.sh` hoặc `ePlus-AI-Toolkit.command` |

Dù dùng Windows hay macOS, bạn vẫn cần một môi trường Android đã thiết lập đúng và có quyền truy cập. Mã nguồn hỗ trợ các bước 0–5 trên macOS, nhưng **chưa xác minh được quy trình thanh toán trên Mac/MuMu thực tế**. Xem hướng dẫn riêng cho [Windows](docs/INSTALLATION.md) và [macOS](docs/MACOS-PREVIEW.md).

### Yêu cầu trên Windows

- Cài Windows, PowerShell **5.1 trở lên** và Python **3.10 trở lên**.
- Tự cài MuMuPlayer, khởi động máy ảo Android và bật root cùng ADB.
- Cài Google Play Store và Google One trong Android, rồi đăng nhập tài khoản cần kiểm tra.
- Chuẩn bị kết nối ADB và Frida **16.5.9** tương thích. Công cụ có thể hỗ trợ tìm và cài các thành phần này, **nhưng không tự cài MuMuPlayer**.

### Bước 1 — Cài MuMuPlayer

Tải MuMuPlayer từ [trang chính thức của NetEase](https://www.mumuplayer.com/download/) và chọn phiên bản Windows. Không nên tải từ các trang chia sẻ không rõ nguồn gốc.

Sau khi cài đặt, hãy bật quyền root và ADB cho máy ảo. Kiểm tra Google Play Store và Google One đã có sẵn, sau đó đăng nhập đúng tài khoản bạn muốn kiểm tra ưu đãi.

Bạn có thể xem thêm [hướng dẫn cài đặt kèm hình ảnh trên GitHub Wiki](https://github.com/hoangsvit/google-ai/wiki/Install).

## 2. Cài và khởi động

**Bước 2 — Tải và chạy công cụ trên Windows.** Mở PowerShell trong thư mục dự định lưu mã nguồn.

Mở PowerShell:

```powershell
git clone https://github.com/hoangsvit/google-ai.git
cd google-ai
.\run-all.ps1
```

Nếu bạn đã tải mã nguồn về máy từ trước:

```powershell
git pull --ff-only
.\run-all.ps1
```

Chạy lệnh **không kèm tham số** sẽ mở giao diện **Textual** thay vì tự bắt đầu thanh toán. Khi bắt đầu kiểm tra, chương trình có thể tự chuẩn bị Textual, ADB và Frida. Thường **không cần** chạy `setup_env.py` trước. Bước chuẩn bị có thể thay đổi công cụ, proxy/mạng và cấu hình máy ảo.

Nếu ADB có trong PATH, kiểm tra kết nối:

```powershell
adb devices
```

Thiết bị phải ở trạng thái `device`, không phải `offline` hoặc `unauthorized`. Nếu không tìm thấy ADB, xem [hướng dẫn xử lý lỗi](docs/DETAILED-GUIDE.md).

### Phương án thay thế: sử dụng bản phát hành khi gặp lỗi

Nếu phiên bản mới nhất chạy từ source gặp lỗi, bạn có thể thử **bản phát hành đã công bố** tại [GitHub Releases](https://github.com/hoangsvit/google-ai/releases). Chọn một phiên bản, đọc ghi chú phát hành và tải gói Windows **nếu có file đính kèm**. Nếu chỉ có **Source code (zip)** do GitHub cung cấp, hãy tải ZIP, giải nén, mở PowerShell ngay trong thư mục đã giải nén rồi chạy:

```powershell
.\run-all.ps1
```

**Source code (zip) chỉ là mã nguồn, không phải tệp `.exe` hoặc bộ cài đã dựng sẵn.** Nên giữ bản phát hành trong **thư mục riêng**, không chép đè lên bản source đang dùng. Bản phát hành cũ có thể chưa chứa những bản sửa lỗi mới và vẫn cần Windows, Python, MuMuPlayer, ADB/Frida cùng các lưu ý về thanh toán. Nếu lỗi vẫn xảy ra, xem [hướng dẫn khắc phục](docs/DETAILED-GUIDE.md) hoặc [tạo Issue](https://github.com/hoangsvit/google-ai/issues).

## macOS — Cài đặt và khởi chạy

Trên **macOS**, cài **Git**, **Python 3.10+** và **Android SDK Platform-Tools (ADB)** (Homebrew: `brew install android-platform-tools`). Kết nối thiết bị Android có root và Google Play Store/Google One, hoặc máy ảo Android tương thích. **MuMuPlayer Pro trên Mac hỗ trợ Apple Silicon**; Mac Intel cần thiết bị hoặc máy ảo khác.

Mở **Terminal** và chạy:

```sh
git clone https://github.com/hoangsvit/google-ai.git
cd google-ai
adb devices
sh run-macos.sh
```

Lệnh `sh run-macos.sh` mở cùng giao diện Textual với **Steps 0–5**. `--check` kiểm tra môi trường (có thể thay đổi cấu hình), `--list` chỉ liệt kê ưu đãi, và `--step 2` chỉ mở TUI với Step 2 được chọn — **không tự thanh toán**. Các Steps 2–5 có thể phát sinh phí thật và yêu cầu xác nhận riêng. **Chưa kiểm thử giao dịch trên Mac/MuMu thực tế.** Xem [hướng dẫn Mac chi tiết](docs/MACOS-PREVIEW.md).

## Kiểm tra kết nối Android và xem ưu đãi (Windows + macOS)

Trên bảng điều khiển có hai chức năng kiểm tra được phát triển từ hướng dẫn cấu hình Android và danh sách ưu đãi của dự án gốc:

- **Diagnose Android connection — Kiểm tra kết nối Android:** Xác định ADB đã có trên máy hay chưa, liệt kê thiết bị Android đã cấp quyền kết nối, đọc kiến trúc ABI, kiểm tra ứng dụng Google One và phiên bản Frida trên máy tính. Tùy hệ điều hành, công cụ sẽ hướng dẫn thiết lập bằng PowerShell/MuMu trên Windows hoặc Terminal/Homebrew trên macOS. Chức năng này **không tự cài phần mềm, kết nối hay khởi động lại máy ảo, chạy Frida hoặc thực hiện thanh toán**. Tuy nhiên, lệnh `adb devices` có thể khởi động ADB server trên máy.
- **Check Device & Offers (Step 1) — Kiểm tra thiết bị và ưu đãi:** Dùng quy trình Android/Frida hiện có để lấy danh sách ưu đãi rồi hiển thị trong **Offer Explorer** bên dưới Live Status. Màn hình chỉ cho biết mã sản phẩm, mã ưu đãi, kỳ thanh toán đầu tiên và việc giá kỳ đầu có bằng 0 hay không. Công cụ **không hiển thị** offer token, purchase token, thông tin tài khoản đầy đủ hoặc dữ liệu thẻ. Khác với tính năng chẩn đoán kết nối, bước này có thể thiết lập lại một số thành phần Android nên **không hoàn toàn chỉ đọc**.

**Giá kỳ đầu bằng 0 không đồng nghĩa với việc được dùng miễn phí hoặc gia hạn thành công.** Step 1 chỉ truy vấn danh sách của ba mã sản phẩm `g1.2tb.ai.subs_variant`, `g1.play.2tb.ai` và `g1.2tb.ai`; các bước 2–5 vẫn truy vấn đúng ưu đãi dành cho từng bước. Vì báo cáo Android chưa có đủ thông tin về những kỳ thanh toán tiếp theo, Offer Explorer đánh dấu giá tương lai là **chưa được xác minh**. Hãy đối chiếu các điều khoản và số tiền thực tế ngay trong Google Play.

## 3. Sử dụng giao diện

Chọn **Check Device & Offers** để thực hiện **Step 1 — Available offers**, truy vấn ưu đãi **không khởi tạo checkout**. Theo dõi **Live Status**, mở **Show technical details** khi cần và kiểm tra tài khoản trong Google Play. Việc không có log mới trong 30 giây chỉ là cảnh báo thiếu hoạt động, **không phải kết luận treo**.

Step 1 chỉ liệt kê ưu đãi, không chủ động mua hàng; nhưng preflight bên dưới vẫn có thể tải/sửa ADB hoặc Frida và đổi cấu hình máy ảo/mạng. **Step 0 — Environment cũng có thể thay đổi cấu hình cục bộ**, không phải tác vụ hoàn toàn chỉ đọc. Sidebar hiển thị sáu bước; các ô Android Device/Google Account lấy từ đầu ra thật, che định danh tài khoản. Liên kết ghi công tác giả gốc và người duy trì có thể bấm trong terminal hỗ trợ.

Mục **Advanced: Run by step** gồm:

| Chế độ | Chức năng |
| --- | --- |
| **One step only** | Chỉ chạy một bước được chọn từ 0 đến 5 |
| **From selected step** | Bắt đầu chuỗi có hướng dẫn từ Step 2–5 |
| **All: Steps 2–5** | Bắt đầu chuỗi từ Step 2; Step 5 là tùy chọn |

| Bước | Vai trò | Rủi ro |
| --- | --- | --- |
| **0 — Environment** | Kiểm tra/chuẩn bị Android, ADB và Frida | Không checkout, nhưng có thể đổi cấu hình |
| **1 — Available offers** | Truy vấn ưu đãi | Không checkout, nhưng preflight có thể đổi môi trường |
| **2 — Pro 12 months** | Thử ưu đãi gốc 12 tháng | **Có thể thanh toán thật** |
| **3 — Pro +6 months** | Thử cập nhật gói | **Có thể thanh toán thật** |
| **4 — Pro +6 months (second)** | Thử cập nhật lần tiếp | **Có thể thanh toán thật** |
| **5 — Optional +6 months** | Thử ưu đãi tùy chọn | **Có thể thanh toán thật** |

Tên 12/6 tháng là **tên lịch sử của các bước**, không phải cam kết được cộng thêm thời hạn. Nếu đã có gói đang hoạt động, **không chạy lại Step 2**.

Trước **mỗi bước checkout trên TUI**, cần phê duyệt riêng. Khi công cụ báo đã thử gửi checkout, hãy xác minh gói đang hoạt động, số tiền và ngày gia hạn tại [Google Play Subscriptions](https://play.google.com/store/account/subscriptions). Chỉ chọn **Verified in Google Play → Next** sau khi bạn đã tự xác minh trong Google Play. **Công cụ không thể tự xác nhận giao dịch đã thành công.**

Trong khi một bước đang chạy, các nút **Check Device & Offers**, Run, chọn chế độ và chọn Step đều bị khóa để không chạy chồng. Help và log kỹ thuật vẫn dùng được. Chỉ hiển thị **Next** khi kết quả checkout cho phép người dùng kiểm chứng trong chuỗi có hướng dẫn; lỗi hoặc trạng thái không rõ ràng không cho phép tiếp tục.

**Stop/Exit:** Step 0–1 có thể yêu cầu dừng tiến trình cục bộ. Với Step 2–5, **Stop after this step** ngăn chạy bước tiếp theo, **không ép dừng giao dịch đang xử lý**. **Q / Exit** sẽ đợi bước thanh toán hiện tại kết thúc. **D** mở/đóng log kỹ thuật; **R** chạy chế độ đã chọn.

## 4. PowerShell CLI (nâng cao)

**Chỉ dành cho Windows.** Các lệnh PowerShell không áp dụng cho macOS; Mac dùng `run-macos.sh` và [hướng dẫn riêng](docs/MACOS-PREVIEW.md). Khi truyền tham số tường minh, launcher chạy CLI thay vì mở Textual TUI.

**Kiểm tra, không mua hàng:**

```powershell
.\run-all.ps1 -Step 1
.\run-all.ps1 -Step 1 -Debug
.\run-all.ps1 -Step 0
.\run-all.ps1 -Cli
```

Log kỹ thuật nằm trong §logs/§, còn báo cáo phiên chạy mới nhất nằm ở §ultra0-report/§. **Không công khai log hoặc báo cáo thô** chứa email, token và thông tin thanh toán. §setup_env.py§ và [§tools/windows/setup-environment.bat§](tools/windows/setup-environment.bat) chỉ là công cụ khắc phục lỗi hoặc sửa môi trường, không phải bước cài đặt bắt buộc trước dashboard.

**Các lệnh sau có thể kích hoạt thanh toán thật:**

```powershell
.\run-all.ps1 -Step 2
.\run-all.ps1 -Step 3
.\run-all.ps1 -Step 4
.\run-all.ps1 -Step 5
```

Khác với TUI, chạy một bước riêng bằng `-Step 2..5` **không có thêm hộp thoại phê duyệt trong PowerShell**. Chỉ thực hiện khi thực sự có ý định checkout và đã xem điều khoản.

Chuỗi có xác nhận từng giai đoạn:

```powershell
.\run-all.ps1 -AllStages
.\run-all.ps1 -AllStages -StartStep 3
```

CLI dùng **1 = Continue, 2 = End run, 0 = Stop**. Tự kiểm tra kết quả trong Google Play trước khi chuyển bước. `-StartStep 3` không xác minh các bước trước đã thành công.

Chọn thiết bị hoặc tài khoản dự kiến:

```powershell
.\run-all.ps1 -Step 1 -Serial emulator-5554
.\run-all.ps1 -AllStages -Email "account@gmail.com"
```

Chỉ sử dụng serial thực tế từ ADB. Tránh `-Force` vì nó bỏ qua bước kiểm tra khớp tài khoản, **không** vượt qua điều kiện ưu đãi hay giới hạn thanh toán của Google.

## 5. Kết quả và xử lý lỗi

- **Không tìm thấy MuMu/ADB:** kiểm tra máy ảo, root, ADB và trạng thái kết nối.
- **Lỗi Frida:** mở log và kiểm tra phiên bản **16.5.9**/khả năng tương thích Android.
- **Không có ưu đãi:** mở Google One/Play Store, rồi chạy lại **Step 1**.
- **Sai tài khoản:** xác nhận đúng hồ sơ Google Play, không bỏ qua xác minh.
- **Checkout đã gửi nhưng chưa xác nhận:** không coi là gia hạn; kiểm tra trực tiếp Google Play trước khi thử lại.
- **§already_subscribed§ hoặc §ineligible§:** dừng lại, không thử các bước thanh toán khác khi chưa xác minh.
- **Lỗi Unicode trên Windows:** cập nhật repository; launcher duy trì cấu hình UTF-8 khi chuyển log qua pipe.
- **Đã gửi yêu cầu checkout:** đó chỉ là thao tác cố gắng gửi, **không phải xác nhận đã kích hoạt hoặc gia hạn**.
- **Lỗi bảo mật thanh toán (ví dụ OR-REH-04):** dừng các bước thanh toán, kiểm tra thông báo bảo mật chính thức.

Nhật ký chạy được lưu trong `logs/`, còn báo cáo nằm trong `ultra0-report/`. **Không chia sẻ log/report chưa ẩn email, token hoặc dữ liệu thanh toán**. CI chỉ kiểm thử tĩnh/mock, không kiểm chứng mua hàng thật. **khả năng tương thích checkout trên Mac/MuMu thực tế chưa được xác minh**.

## Hỗ trợ cộng đồng và dự án liên quan

Nếu gặp vấn đề khi cài đặt hoặc sử dụng ePlus AI Toolkit, hãy truy cập [bài đăng hỗ trợ trên Telegram ePlus](https://t.me/eplus_news/29) để liên lạc, trao đổi kinh nghiệm và nhờ cộng đồng hỗ trợ. Với lỗi kỹ thuật có thể tái hiện, bạn cũng có thể [tạo GitHub Issue](https://github.com/hoangsvit/google-ai/issues). **Không chia sẻ mật khẩu, mã OTP/2FA, offer/purchase token, log chưa che thông tin cá nhân hoặc dữ liệu thẻ thanh toán.** Đây là hỗ trợ cộng đồng, không phải kênh hỗ trợ chính thức của Google.

**Không tham gia được chương trình Google AI Pro?** Bạn có thể tham khảo [Muse Invite Hub](https://github.com/ePlus-DEV/muse-invite-hub), một dự án khác của ePlus.DEV để [tìm kiếm hoặc chia sẻ mã mời Muse](https://muse.eplus.dev/). **Muse là dịch vụ riêng**, mã mời Muse **không kích hoạt và không thay thế** quyền đăng ký Google AI Pro. Mã mời có thể hết lượt hoặc bị giới hạn theo khu vực/tài khoản.

## Cấu trúc mã nguồn

Các tệp khởi chạy và mô-đun Python chính vẫn nằm tại thư mục gốc để bảo đảm tương thích với các hướng dẫn hiện có. Trên Windows dùng `run-all.ps1`, còn trên macOS dùng `run-macos.sh`.

| Đường dẫn | Vai trò |
| --- | --- |
| `run-all.ps1` | Khởi chạy giao diện Textual và chế độ CLI trên Windows |
| `run-macos.sh`, `ePlus-AI-Toolkit.command`, `macos_runner.py` | Khởi chạy và điều phối các bước 0–5 trên Mac; chưa xác minh thanh toán trên thiết bị thật |
| `tui.py`, `tui_core.py`, `ultra0.py`, `setup_env.py`, `device_selector.py`, `query_sku.py` | Các mô-đun Python đang được sử dụng |
| [`tools/windows/`](tools/windows/README.md) | Công cụ thiết lập Windows thủ công, chỉ dùng khi cần |
| [`legacy/windows/`](legacy/windows/README.md) | Các tệp .bat cũ; một số sử dụng `--force` để bỏ qua bước đối chiếu tài khoản, có thể **phát sinh phí thật**. Nên dùng launcher được duy trì |
| `scripts/`, `assets/` | Tiện ích hỗ trợ và tài nguyên Android/Frida |
| `tests/`, `.github/workflows/`, `docs/` | Bộ kiểm thử, GitHub Actions và tài liệu |

## Tài liệu và đóng góp

[README tiếng Anh](README.md) · [Wiki Install](https://github.com/hoangsvit/google-ai/wiki/Install) · [Hướng dẫn kỹ thuật](docs/DETAILED-GUIDE.md) · [Các bước gốc](docs/ORIGINAL-STEPS.md) · [Disclaimer](DISCLAIMER.md) · [Bảo mật](SECURITY.md) · [Đóng góp](CONTRIBUTING.md) · [Thông báo bản quyền](THIRD_PARTY_NOTICES.md)

Bạn cũng có thể tham khảo [cấu trúc dự án](docs/PROJECT.md), [cách dùng dashboard và CLI](docs/USAGE.md), [an toàn thanh toán](docs/SAFETY.md), [lưu ý tác giả](docs/AUTHOR-NOTES.md) và [hướng dẫn AI agent](AGENTS.md). GitHub Actions kiểm tra Python, PowerShell, Textual và các tình huống mô phỏng Frida/Billing; **không thực hiện giao dịch Google Play thật**. CI thành công không chứng minh thiết bị tương thích hoặc tài khoản đủ điều kiện.

## Ghi công

**Tác giả gốc:** [@gylive](https://github.com/gylive) — [google-ultra](https://github.com/gylive/google-ultra). **Người duy trì:** [David Nguyen (@hoangsvit)](https://github.com/hoangsvit) / [ePlus.DEV](https://eplus.dev). Giữ nguyên thông báo MIT của tác giả gốc trong [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); giấy phép này không mặc nhiên áp dụng cho các đóng góp mới không liên quan. [Danh sách người đóng góp](https://github.com/hoangsvit/google-ai/graphs/contributors).

[Trung tâm tài liệu](docs/README.md) · [Tài liệu tham khảo cũ (tiếng Việt)](docs/i18n/README.vi.md) · [An toàn thanh toán](docs/SAFETY.md)
