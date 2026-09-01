from .models import Category, Cart

def global_context(request):
    # Categories for global header/sidebar
    categories = Category.objects.all()

    # Active Cart
    cart = None
    cart_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        if request.session.session_key:
            cart = Cart.objects.filter(session_key=request.session.session_key).first()

    if cart:
        cart_count = cart.total_items

    return {
        'all_categories': categories,
        'cart': cart,
        'cart_item_count': cart_count,
    }
