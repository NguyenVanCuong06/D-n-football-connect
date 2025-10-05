# app/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Lưu ý: UserCreationForm và CreateUserForm phải được chuyển sang app/forms.py

# ==========================================================
# 1. HẰNG SỐ CHUNG (GLOBAL CHO CẢ TEAM VÀ CHALLENGE)
# ==========================================================
# 💡 ĐỊNH NGHĨA Ở CẤP CAO NHẤT ĐỂ TẤT CẢ CÁC MODEL CÓ THỂ TRUY CẬP
SPORT_CHOICES = [
    ('5v5', 'Sân 5 Người'),
    ('7v7', 'Sân 7 Người'),
    # Đã giữ lại các tùy chọn bạn có
]

STATUS_CHOICES = [
    ('open', 'Đang mở (Tìm đối thủ)'),
    ('matched', 'Đã tìm thấy đối thủ'),
    ('closed', 'Đã kết thúc'),
]

# ==========================================================
# 2. MODEL TEAM (Đã hợp nhất tất cả các định nghĩa cũ)
# ==========================================================
class Team(models.Model):
    # Dùng 'owned_teams' cho Model này
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='owned_teams', null=True, blank=True)
    
    # Đã hợp nhất các trường:
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên Đội")
    sport_type = models.CharField(max_length=10, choices=SPORT_CHOICES, default='7v7', verbose_name="Loại Hình Sân")
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="Địa Điểm Hoạt Động")
    # THÊM TRƯỜNG MỚI: is_recruiting
    is_recruiting = models.BooleanField(
        default=False, 
        verbose_name='Đang Tuyển Thành Viên'
    )
    
    # Các trường thêm vào để phục vụ Form Tạo Đội
    city = models.CharField(max_length=100, default='TP. Hồ Chí Minh', verbose_name="Thành phố/Khu vực")
    description = models.TextField(blank=True, verbose_name="Mô tả đội")
    is_looking_for_match = models.BooleanField(default=False, verbose_name="Đang tìm đối thủ?")
    is_available = models.BooleanField(default=True, verbose_name="Sẵn sàng đá giao hữu") # Trường lọc 3
    
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

# ==========================================================
# 3. MODEL CHALLENGEPOST (Bài Đăng Tìm Đối Thủ)
# ==========================================================
class ChallengePost(models.Model):
    # Liên kết bài đăng với đội đăng
    posting_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='challenges', verbose_name="Đội đăng tin")
    
    # Người tạo bài (thường là đội trưởng/admin)
    author = models.ForeignKey(User, on_delete=models.CASCADE) 
    
    # 1. Thông tin cần thiết cho trận đấu
    match_date = models.DateField(verbose_name="Ngày thi đấu")       
    match_time = models.TimeField(verbose_name="Giờ thi đấu")        
    pitch_location = models.CharField(max_length=255, verbose_name="Tên sân/Địa điểm") 

    # 2. Chi tiết yêu cầu và liên hệ
    required_sport_type = models.CharField(max_length=10, choices=SPORT_CHOICES, default='7v7', verbose_name="Loại hình sân yêu cầu") 
    description = models.TextField(verbose_name="Mô tả thêm/Yêu cầu trình độ")       
    
    # Thông tin liên hệ công khai
    contact_phone = models.CharField(max_length=15, verbose_name="Số điện thoại liên hệ")
    contact_name = models.CharField(max_length=100, verbose_name="Tên người liên hệ")
    
    # 3. Trạng thái
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open', verbose_name="Trạng thái")
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Challenge by {self.posting_team.name} on {self.match_date} ({self.status})"

# ==========================================================
# 4. MODEL CUSTOMER (Giữ lại nếu bạn có kế hoạch dùng sau này)
# ==========================================================
class Customer(models.Model):
    # ...
    pass
class Notification(models.Model):
    # Người nhận thông báo
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Người nhận")
    
    # Đối tượng thông báo (ChallengePost)
    challenge_post = models.ForeignKey(
        'ChallengePost', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="Bài đăng liên quan"
    )
    
    # Nội dung thông báo
    message = models.CharField(max_length=255, verbose_name="Nội dung")
    
    # Trạng thái
    is_read = models.BooleanField(default=False, verbose_name="Đã đọc")
    
    # Thời gian tạo
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # Thông báo mới nhất lên đầu

    def __str__(self):
        return f"Thông báo cho {self.user.username}: {self.message[:30]}..."
class Post(models.Model):
    """Mô hình lưu trữ bài đăng tìm đội đối thủ"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Người đăng")
    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Chi tiết trận đấu")
    
    # Thêm các trường cụ thể cho bài đăng tìm đối thủ
    match_time = models.DateTimeField(default=timezone.now,verbose_name="Thời gian thi đấu")
    location = models.CharField(max_length=255,default='Sân bóng chưa xác định', verbose_name="Địa điểm/Sân bóng")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Bài đăng tìm đối thủ"
        verbose_name_plural = "Bài đăng tìm đối thủ"
        ordering = ['-created_at']

    def __str__(self):
        return self.title  
