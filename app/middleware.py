from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class QuickCartAuthRoleMiddleware:
    """
    Middleware to enforce strict bidirectional session isolation and role-based access:
    1. Authenticated Admin/Staff users are strictly kept within /admin-panel/*
       (redirecting attempts to visit guest or customer storefront pages back to /admin-panel/).
    2. Non-staff / Customer users / Guests are strictly blocked from accessing any /admin-panel/* route.
    3. Active sessions visiting /accounts/login/ or /accounts/signup/ are redirected to their respective panels.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Whitelist static assets, media, api endpoints, and logout
        is_exempt = (
            path.startswith('/static/') or
            path.startswith('/media/') or
            path.startswith('/api/') or
            path == reverse('accounts:logout')
        )

        if not is_exempt:
            if request.user.is_authenticated:
                is_admin = request.user.is_staff or getattr(request.user, 'role', '') == 'admin'

                # 1. Admin Session Isolation: Admin stays strictly in /admin-panel/*
                if is_admin:
                    if not path.startswith('/admin-panel/'):
                        return redirect('admin_dashboard')

                # 2. Customer Session Isolation: Customer cannot access login/signup or admin routes
                else:
                    if path in [reverse('accounts:login'), reverse('accounts:signup')]:
                        return redirect('customer:orders')
                    if path.startswith('/admin-panel/'):
                        messages.error(request, "Access Denied: Administrative privileges required.")
                        return redirect('customer:orders')

            # 3. Guest User Access: Guests cannot access /admin-panel/*
            else:
                if path.startswith('/admin-panel/'):
                    messages.warning(request, "Please log in with administrator credentials.")
                    return redirect(f"{reverse('accounts:login')}?next={path}")

        response = self.get_response(request)
        return response
