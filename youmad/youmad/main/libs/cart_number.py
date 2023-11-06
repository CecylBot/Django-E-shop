def calculate(request):
    if 'cart' in request.session:
            cart = request.session['cart']
            num_products_in_cart = sum(cart.values()) 
    else:
            num_products_in_cart = 0 
    return num_products_in_cart