from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .models import Team, ChallengePost, Notification
from .forms import TeamFilterForm
from django.contrib.auth.decorators import login_required
from .forms import ChallengePostForm
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q 
from .forms import ChallengeFilterForm 
from .forms import TeamForm
from django.core.mail import send_mail  
from .models import Post
from django.urls import reverse_lazy,reverse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DeleteView
from django.utils.decorators import method_decorator
from .forms import PostForm
from django.views import View
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your views here.
def register(request):
    form=CreateUserForm()
    
    if request.method =="POST":
        form=CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
    context = {'form':form}
    return render(request,'app/register.html',context)
def loginpage(request):
    if request.user.is_authenticated:
        return redirect('team_list')
    if request.method =="POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username = username, password=password)
        if user is not None:
            login(request,user)
            return redirect('team_list')
        else: messages.info(request,'user or password not correct!')

    
    context = {}
    return render(request,'app/login.html',context) 
def logoutpage(request):
    logout(request)
    return redirect('login')
def home(request):
    if request.user.is_authenticated:
        return redirect('team_list')
    return render(request,'app/base.html')

@login_required
def team_create(request):
    """
    Cho phép người dùng (owner) tạo một đội bóng mới.
    """
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            # Tạo đối tượng Team nhưng chưa lưu vào DB
            team = form.save(commit=False)
            # Gán chủ sở hữu đội là người dùng hiện tại
            team.owner = request.user 
            team.save()
            
            messages.success(request, f"Đội bóng '{team.name}' đã được tạo thành công!")
            # Chuyển hướng về trang danh sách đội hoặc trang chi tiết đội
            return redirect('team_list') # Đảm bảo URL 'team_list' tồn tại
    else:
        form = TeamForm()

    context = {
        'form': form,
        'title': 'Tạo Đội Bóng Mới',
    }
    return render(request, 'app/team_create.html', context)
# View xử lý việc lọc đội
def team_list(request):
    # Bắt đầu với tất cả các đội
    teams = Team.objects.all() 
    
    # Khởi tạo form với dữ liệu từ request GET (dữ liệu lọc)
    form = TeamFilterForm(request.GET) 

    if form.is_valid():
        # Lấy dữ liệu đã làm sạch từ form
        sport_type = form.cleaned_data.get('sport_type')
        location = form.cleaned_data.get('location')
        is_available = form.cleaned_data.get('is_available')
        
        # 🎯 THÊM DÒNG XỬ LÝ LỌC MỚI (US02)
        is_recruiting = form.cleaned_data.get('is_recruiting') 
        # ---------------------------------------------------

        # Xây dựng truy vấn lọc (filter chaining)
        # 1. Lọc theo loại hình sân
        if sport_type:
            teams = teams.filter(sport_type=sport_type)
        
        # 2. Lọc theo khu vực (sử dụng icontains để tìm kiếm linh hoạt)
        if location:
            teams = teams.filter(location__icontains=location)

        # 3. Lọc theo trạng thái sẵn sàng
        if is_available:
            teams = teams.filter(is_available=True)
            
        # 🎯 ÁP DỤNG LỌC US02
        if is_recruiting:
            teams = teams.filter(is_recruiting=True)
            
    context = {
        'form': form, # Danh sách đội đã lọc (hoặc tất cả nếu không lọc)
        'teams': teams,
    }
    return render(request, 'app/team_list.html', context)
@login_required # Chỉ cho phép người dùng đã đăng nhập
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            # 1. Tạm thời lưu form (commit=False)
            new_post = form.save(commit=False)
            
            # 2. Gán tác giả là người dùng hiện tại
            new_post.author = request.user
            
            # 3. Lưu bài đăng vào database
            new_post.save()
            
            # Chuyển hướng đến trang danh sách bài đăng hoặc trang khác
            return redirect(reverse('post_list')) # Giả sử bạn có trang post_list
    else:
        form = PostForm()
    
    context = {'form': form, 'title': 'Đăng tin tìm đội đối thủ'}
    return render(request, 'app/create_post.html', context)

@login_required # Chỉ cho phép người dùng đã đăng nhập tạo bài đăng
def post_challenge(request):
    """
    Xử lý việc đăng tin tìm đối thủ (ChallengePost).
    Chỉ cho phép người dùng chọn các đội mà họ sở hữu.
    """
    
    # 1. Kiểm tra điều kiện tiên quyết: Người dùng phải có ít nhất một đội
    # Giả sử bạn muốn dùng 'team_create' là URL tạo đội.
    if not request.user.owned_teams.exists():
        messages.warning(request, "Bạn cần tạo một đội trước khi đăng tin tìm đối thủ!")
        return redirect('team_create') 

    if request.method == 'POST':
        # 2. Xử lý POST: Truyền request.POST VÀ request.user vào Form
        form = ChallengePostForm(request.POST, user=request.user)
        
        if form.is_valid():
            challenge_post = form.save(commit=False)
            
            # Gán các trường bắt buộc
            challenge_post.author = request.user
            challenge_post.status = 'open' 
            
            challenge_post.save()

            
            # =========================================================
            # PHẦN MỚI: TẠO THÔNG BÁO TRONG ỨNG DỤNG
            # =========================================================
            # Lấy tất cả người dùng trừ người vừa đăng bài
            other_users = User.objects.exclude(id=request.user.id)
            
            # Định nghĩa nội dung
            message = f"⚽ Đội {challenge_post.posting_team.name} vừa đăng tin tìm đối thủ ở {challenge_post.pitch_location} vào {challenge_post.match_time}!"
            
            # Tạo thông báo cho từng người dùng (hoặc nên dùng bulk_create nếu số lượng lớn)
            notifications_to_create = []
            for user in other_users:
                notifications_to_create.append(
                    Notification(
                        user=user, 
                        challenge_post=challenge_post, 
                        message=message
                    )
                )
            
            # Lưu tất cả thông báo vào database
            Notification.objects.bulk_create(notifications_to_create)

            messages.success(request, "Đăng tin tìm đối thủ thành công! Thông báo đã được gửi đến người dùng.")
            # =========================================================

            return redirect('challenge_list') 
    else:
        # 3. Xử lý GET: Hiển thị form trống
        # Truyền user vào form để kích hoạt logic lọc đội
        form = ChallengePostForm(user=request.user)
        
    context = {'form': form}
    return render(request, 'app/post_challenge.html', context)
def challenge_list(request):
    # Chỉ lấy các tin đang mở
    challenges = ChallengePost.objects.filter(status='open').order_by('match_date', 'match_time')
    
    form = ChallengeFilterForm(request.GET)
    
    if form.is_valid():
        sport_type = form.cleaned_data.get('required_sport_type')
        location = form.cleaned_data.get('pitch_location')
        date_start = form.cleaned_data.get('match_date_start')
        
        # 1. Lọc theo Loại hình sân
        if sport_type:
            challenges = challenges.filter(required_sport_type=sport_type)
            
        # 2. Lọc theo Khu vực/Sân (Tìm kiếm một phần)
        if location:
            challenges = challenges.filter(pitch_location__icontains=location)
            
        # 3. Lọc theo Ngày bắt đầu
        if date_start:
            challenges = challenges.filter(match_date__gte=date_start) # Lớn hơn hoặc bằng ngày này
            
    context = {
        'challenges': challenges,
        'title': 'Danh sách Tin Tìm Đối Thủ',
        'filter_form': form, # Truyền form lọc vào template
    }
    return render(request, 'app/challenge_list.html', context)
def challenge_detail(request, pk):
    """
    Hiển thị chi tiết của một bài đăng tìm đối thủ cụ thể.
    """
    # Sử dụng get_object_or_404 để trả về 404 nếu không tìm thấy bài đăng
    challenge = get_object_or_404(ChallengePost, pk=pk)
    
    context = {
        'challenge': challenge,
        'title': f"Chi tiết Thách đấu: {challenge.posting_team.name}",
    }
    return render(request, 'app/challenge_detail.html', context)
def about(request):
    """Xử lý yêu cầu cho trang Giới Thiệu."""
    return render(request, 'app/about.html', {})
def find_nearby_fields(request):
    """
    Xử lý tìm kiếm sân bóng gần vị trí người dùng.
    """
    # *** ĐÂY LÀ NƠI BẠN CẦN THỰC HIỆN LOGIC: ***
    # 1. Gửi yêu cầu đến API Maps/DB để lấy dữ liệu sân gần MY_LOCATION.
    # 2. Xử lý kết quả (tên, địa chỉ, khoảng cách, rating).
    # 3. Truyền kết quả vào context.
    
    # Dữ liệu mẫu (thay thế bằng dữ liệu thực từ DB/API)
    fields = [
        {'name': 'Sân bóng Đại học GTVT', 'distance': '1.1 km', 'rating': 4.3, 'address': 'Láng Thượng, Đống Đa'},
        {'name': 'Sân Bóng Hoàng Cầu', 'distance': '1.2 km', 'rating': 3.9, 'address': '42 P. Hoàng Cầu'},
        # ... thêm các sân khác
    ]
    
    context = {
        'field_list': fields,
        'search_query': 'sân bóng gần vị trí tôi',
        # 'map_data': ... (Nếu bạn có dữ liệu để hiển thị bản đồ)
    }
    
    return render(request, 'app/find_nearby_fields.html', context)
def is_admin_or_staff(user):
    return user.is_active and user.is_staff

# -----------------
# 1. DANH SÁCH BÀI ĐĂNG CỦA NGƯỜI DÙNG
# -----------------
@method_decorator(user_passes_test(is_admin_or_staff), name='dispatch')
class AdminPostListView(LoginRequiredMixin, ListView):
    """Hiển thị tất cả bài đăng cho Admin"""
    model = Post
    template_name = 'app/admin_post_list.html' # Template sẽ tạo ở B3
    context_object_name = 'posts'
    paginate_by = 10


# -----------------
# 2. XÁC NHẬN XÓA (Delete View)
# -----------------
@method_decorator(user_passes_test(is_admin_or_staff), name='dispatch')
class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Hiển thị trang xác nhận xóa bài đăng"""
    model = Post
    template_name = 'app/admin_post_delete.html' # Template sẽ tạo ở B3
    success_url = reverse_lazy('admin_post_list') # Quay lại trang danh sách sau khi xóa

    # Override hàm get_object để đảm bảo chỉ có admin mới thấy
    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs['pk'])
def team_list_view(request):
    """
    Hiển thị danh sách các bài đăng (Post) tìm đối thủ.
    """
    # Lấy tất cả bài đăng để hiển thị
    posts = Post.objects.all().order_by('-created_at')
    
    context = {
        'posts': posts,
        'title': 'Danh sách các đội đang tìm đối thủ'
    }
    
    # Bạn cần tạo file template 'app/post_list.html' cho view này
    return render(request, 'app/post_list.html', context)
class TeamListView(View): 
    def get(self, request):
        # Bắt đầu với tất cả đội
        teams = Team.objects.all()
        
        # Lấy tham số lọc từ URL (GET parameters)
        field_type_filter = request.GET.get('field_type')
        location_query = request.GET.get('location')
        
        # ⚠️ LẤY THAM SỐ LỌC MỚI (US02)
        recruiting_filter = request.GET.get('is_recruiting')

        # ÁP DỤNG CÁC BỘ LỌC
        if field_type_filter:
            teams = teams.filter(field_type=field_type_filter)
            
        if location_query:
            teams = teams.filter(location__icontains=location_query) 

        # 🎯 ÁP DỤNG LỌC US02
        if recruiting_filter == 'on': # Nếu checkbox được chọn
            teams = teams.filter(is_recruiting=True)
            
        context = {
            'teams': teams,
            # Truyền lại trạng thái lọc để form giữ được giá trị
            'selected_field_type': field_type_filter,
            'selected_location': location_query,
            'is_recruiting_checked': recruiting_filter == 'on', # Thêm trạng thái checkbox
            # Giả sử bạn có list field_types để hiển thị dropdown
            'field_types': Team.FIELD_TYPE_CHOICES, 
        }
        
        return render(request, 'app/team_list.html', context)



