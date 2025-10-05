from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Team
from .models import ChallengePost,SPORT_CHOICES, STATUS_CHOICES
from .models import Post 
from django.contrib.auth import get_user_model
# Create your models here.
#change form register django
class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','first_name','last_name','password1','password2']
class TeamFilterForm(forms.Form):
    # Lấy các lựa chọn từ Model Team
        SPORT_CHOICES_WITH_EMPTY = [('', '--- Chọn loại hình sân ---')] + SPORT_CHOICES 

    # 1. Lọc theo loại hình sân
        sport_type = forms.ChoiceField(   
        choices=SPORT_CHOICES_WITH_EMPTY,
        required=False,
        label='Loại hình sân',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # 2. Lọc theo khu vực
        location = forms.CharField(
        max_length=100,
        required=False,
        label='Khu vực/Sân',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập khu vực'})
    )

    # 3. Lọc theo trạng thái sẵn sàng
        is_available = forms.BooleanField(
        required=False,
        label='Đội sẵn sàng tham gia',
    )
        # 🎯 THÊM TRƯỜNG NÀY (US02)
is_recruiting = forms.BooleanField(
        required=False,
        label='Đang Tuyển Thành Viên:',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
# 💡 FORM MỚI DÙNG ĐỂ LỌC DANH SÁCH BÀI ĐĂNG
class ChallengeFilterForm(forms.Form):
    # Lọc theo loại hình sân (5v5, 7v7, 11v11)
        SPORT_CHOICES_WITH_EMPTY = [('', '--- Loại hình sân ---')] + SPORT_CHOICES
        required_sport_type = forms.ChoiceField(
        choices=SPORT_CHOICES_WITH_EMPTY,
        required=False,
        label='Loại hình sân',
        widget=forms.Select(attrs={'class': 'form-control form-select-sm'})
    )
    
    # Lọc theo khu vực/sân
        pitch_location = forms.CharField(
        required=False,
        label='Khu vực/Sân',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Nhập tên sân hoặc khu vực'})
    )
    
    # Lọc theo ngày (ví dụ: chỉ muốn xem các trận trong tuần này)
        match_date_start = forms.DateField(
        required=False,
        label='Từ ngày',
        widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'})
    )
class ChallengePostForm(forms.ModelForm):
    # Vì user có thể sở hữu nhiều đội, bạn phải chọn đội nào sẽ đăng bài
    # Sử dụng queryset rỗng, chúng ta sẽ điền nó trong view
    posting_team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        label="Đội đăng bài",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    def __init__(self, *args, **kwargs):
        # Lấy user được truyền từ view (xem app/views.py)
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

        # 🎯 Lọc trường posting_team
        if user and user.is_authenticated:
            # Giả định: Team Model có related_name là owned_teams
            self.fields['posting_team'].queryset = user.owned_teams.all() 
        else:
            # Nếu không đăng nhập, không có đội nào để chọn
            self.fields['posting_team'].queryset = self.fields['posting_team'].queryset.none()
            
            
        # Áp dụng widget cho Date và Time fields (Đã sửa lại để code gọn gàng hơn)
        self.fields['match_date'].widget = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        self.fields['match_time'].widget = forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})


    class Meta:
        model = ChallengePost
        # Loại bỏ author, status, date_posted (sẽ được điền tự động trong view)
        fields = ['posting_team', 'match_date', 'match_time', 'pitch_location', 
                  'required_sport_type', 'description']
        
        # Thêm widgets để form sử dụng Bootstrap classes và các loại input phù hợp
        widgets = {
            'match_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'match_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'pitch_location': forms.TextInput(attrs={'class': 'form-control'}),
            'required_sport_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),

            # 💡 WIDGETS MỚI CHO THÔNG TIN LIÊN HỆ
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên người đại diện'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại (VD: 090xxxxxxx)'}),
        }
# 💡 THÊM TEAMFORM MỚI
class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        # Chọn các trường người dùng cần điền khi tạo đội
        # Loại bỏ trường 'owner' vì nó được gán tự động trong view
        fields = ['name', 'sport_type', 'city', 'description', 'is_looking_for_match'] 
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên đội bóng'}),
            'sport_type': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Thành phố hoặc khu vực'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Mô tả ngắn về đội...'}),
            'is_looking_for_match': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Tên Đội',
            'sport_type': 'Loại Hình Sân',
            'city': 'Khu Vực',
            'description': 'Mô Tả Đội',
            'is_looking_for_match': 'Sẵn sàng tham gia?',
        }
class PostForm(forms.ModelForm):
    # Định nghĩa các trường bạn muốn người dùng nhập
    title = forms.CharField(label='Tiêu đề bài đăng', max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    content = forms.CharField(label='Yêu cầu & Chi tiết trận đấu', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    location = forms.CharField(label='Địa điểm/Sân bóng', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Sử dụng DateTimeInput cho thời gian thi đấu
    match_time = forms.DateTimeField(
        label='Thời gian thi đấu', 
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'location', 'match_time']