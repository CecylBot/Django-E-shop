from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail

from .models import *
from django.template.loader import get_template
from django.http import JsonResponse, HttpResponseRedirect
import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY
import os
import pdfkit 
from .libs import search_products,cart_number,stripeFunctions

#Views:
#Index
class IndexView(View):
    """
    View for handling user registration and new member creation.
    """
    template_name = 'main/home.html'
    
    def get(self, request):
        """
        Displays the index page.

        Args:
            request: HTTP request object.

        Returns:
            Rendered template response.
        """
        products = Products.objects.filter(size__quantity__gt=0).distinct()
        
        num_products_in_cart = cart_number.calculate(request)
      
        return render(request, self.template_name,{'products':products,'num_products_in_cart':num_products_in_cart})

    



#Search Results
class searchResults(View):
    """
    View for handling adding to cart
    """
    template_name = 'main/searchResultsView.html'
    
    def get(self, request):
       
        """
        Displays the Search results View.

        Args:
            request: HTTP request object.

        Returns:
            Rendered template response.
        """
        num_products_in_cart = cart_number.calculate(request)
        if "q" in request.GET:
            query=request.GET.get("q")
            results=search_products.results(query)
        else:
            query=""
            results=[]
        return render(request, self.template_name,{'num_products_in_cart':num_products_in_cart,"results":results,"query":query})

   


#Product View

class ProductView(View):
    """
    View for handling adding to cart
    """
    template_name = 'main/productView.html'
    
    def get(self, request,id):
       
        """
        Displays the product View.

        Args:
            request: HTTP request object.

        Returns:
            Rendered template response.
        """
        
        
        num_products_in_cart = cart_number.calculate(request)
        product=Products.objects.get(id=id)
        discounted_price = product.price * (1 - product.discount / 100)
        sizes = Size.objects.filter(product=product).exclude(quantity=0)
        images=Image.objects.filter(product=product)
        if AdminInformations.objects.all()[0].DPH == True:
            product.price+=(product.price*(AdminInformations.objects.all()[0].dph_size / 100))
            discounted_price+=(discounted_price*(AdminInformations.objects.all()[0].dph_size / 100))
        return render(request, self.template_name,{'product':product,'sizes':sizes,'images':images,'discounted_price':discounted_price,'num_products_in_cart':num_products_in_cart})

 #Checkout

class Checkout(View):
    """
    View for handling user registration and new member creation.
    """
    template_name = 'main/checkout.html'
    
    def get(self, request):
        """
        Displays the index page.

        Args:
            request: HTTP request object.

        Returns:
            Rendered template response.
        """
        cart = request.session.get('cart', {}) 
        price=0  
        
        for size_id, quantity in cart.items():
        
            size = Size.objects.get(id=size_id)
                
            price += size.product.price*(1 - size.product.discount / 100)*quantity

        if AdminInformations.objects.all()[0].DPH == True:
            price+=(price*(AdminInformations.objects.all()[0].dph_size / 100))
        price=round(price, 2)
        return render(request, self.template_name,{'price': price})
#Cart
class ViewCart(View):
    """
    View for handling user registration and new member creation.
    """
    template_name = 'main/cart.html'
    
    def get(self, request):
        """
        Displays the index page.

        Args:
            request: HTTP request object.

        Returns:
            Rendered template response.
        """
        cart = request.session.get('cart', {}) 
        items = []  
    
        for size_id, quantity in cart.items():
            try:
                size = Size.objects.get(id=size_id)
                product_name = size.product.name
            
                max_quantity = size.quantity
                price = size.product.price*(1 - size.product.discount / 100)*quantity
                if AdminInformations.objects.all()[0].DPH == True:
                    price+=(price*(AdminInformations.objects.all()[0].dph_size / 100))
                price = round(price, 2)
                items.append({'product': product_name, 'size': size, 'quantity': quantity,'price':price,'max_quantity':max_quantity})
            except Size.DoesNotExist:
                pass
        
        return render(request, self.template_name,{'cart_items': items})

#Succesful Order

class SuccesfulOrder(View):
    """
    View for handling user registration and new member creation.
    """
    template_name = 'main/succesful-order.html'
    
    def get(self, request,id):
        """
        Displays the index page.

        Args:
            request: HTTP request object.

        Returns:
            Rendered template response.
        """
        order=Order.objects.get(id=id)

        items=OrderItem.objects.filter(order=order)
        
        return render(request, self.template_name,{'order_items': items,'order':order})

#Json Responses

def AddToCart(request):
    if request.GET:
        
        size_id = request.GET.get('size')
        quantity = int(request.GET.get('quantity'))

       
        if 'cart' not in request.session:
            request.session['cart'] = {}

        cart = request.session['cart']

        if size_id in cart:
           
            cart[size_id] += quantity
        else:
            
            cart[size_id] = quantity

        request.session.modified = True 
        product=Size.objects.get(id=size_id).product.id
        return JsonResponse({'success': True})

    return JsonResponse({'success': False})
        
def get_size_quantity(request):
    
    size_id = request.GET.get("size")
    size = Size.objects.get(id=size_id)
    quantity = size.quantity
    if 'cart'  in request.session:
        cart = request.session.get('cart', {})

        if size_id in cart:
          
            quantity_in_cart = cart[size_id]
            quantity-=quantity_in_cart
        
    return JsonResponse({"quantity": quantity})



def update_cart(request):
    if request.method == 'GET':
        size_id = request.GET.get('size')
        new_quantity = int(request.GET.get('new_quantity'))
        
        cart = request.session.get('cart', {})
        print(new_quantity)
        if new_quantity == 0:
            print("delete")
            if size_id in cart:
                del cart[size_id]
             
     
        else:
            cart[size_id] = new_quantity

      
        request.session['cart'] = cart
        request.session.modified = True
      
        return JsonResponse({"quantity": new_quantity})

    return JsonResponse({"quantity": new_quantity})





def get_shipping_rates(request):
    shipping_data = {}
    countries = Shipping.objects.all()
    for country in countries:
        methods = ShippingMethod.objects.filter(country=country)
        shipping_data[country.country] = {}
        for method in methods:
            shipping_data[country.country][method.name] = method.price
    return JsonResponse(shipping_data)





def Charge(request):
    data = json.loads(request.body.decode('utf-8'))
    amount =int(data.get('price') * 100)
    customer_identifier = data.get('customer_identifier')  # Unique identifier for the customer or session
    
    stripe.api_key = settings.STRIPE_SECRET_KEY

    customer=stripeFunctions.get_create_customer(customer_identifier)
    existing_payment_intent = stripeFunctions.retrieve_existing_payment_intent(customer)

    if existing_payment_intent and existing_payment_intent.status not in ['succeeded']:
        # Update the existing payment intent with the new amount
       
        existing_payment_intent = stripe.PaymentIntent.modify(
            existing_payment_intent.id,
            amount=amount,
        )
        return JsonResponse({'client_secret': existing_payment_intent.client_secret})

    # If no existing payment intent, create a new one
    payment_intent = stripe.PaymentIntent.create(
        amount=amount,
        currency='eur',
        customer=customer,  # Use the customer identifier to associate with the customer
        automatic_payment_methods={'enabled': True}
    )
    
    return JsonResponse({'client_secret': payment_intent.client_secret})


    
   

def CreateOrder(request):
 
    mail = request.POST.get('mail')
    country = request.POST.get('country')
    print(country)
    shipping_name=request.POST.get('shipping_method')
    country_id= Shipping.objects.get(country=country)
    shipping_method = ShippingMethod.objects.get(country=country_id,name=shipping_name)
    
    first_name = request.POST.get('firstname')
    last_name = request.POST.get('lastname')
    city = request.POST.get('city')
    street = request.POST.get('street')
    postal_code = request.POST.get('postalcode')
    phone = request.POST.get('phone')
    order = Order.objects.create(
        mail=mail,
        customer_first_name=first_name,
        customer_last_name=last_name,
        country=country,
        phone=phone,
        city=city,
        street=street,
        zip_address=postal_code,
        shipping_method=shipping_method)
    order.save()
    cart = request.session.get('cart', {})
    for size_id, Quantity in cart.items():
        
        size = Size.objects.get(id=size_id)
        orderitem=OrderItem.objects.create(
        order=order,
        product_and_size=size,
        quantity=Quantity
        )
        orderitem.save()
        size.quantity-=Quantity
        size.save()
        
        if 'cart' in request.session:
            del request.session['cart']
        request.session.modified = True
        


    return JsonResponse({'success': True,'order':order.id})
    




def invoice(request):

    order = Order.objects.get(id=29)

    order.order_price = order.get_order_total()
    orderId = order.id
    invoice_number = 2000000 + int(orderId)
    try:
        SupplierInformations = AdminInformations.objects.all()[0]
    except:
        SupplierInformations = ""
    orderItems = OrderItem.objects.filter(order=orderId)
    
    for item in orderItems:
        item.discounted_price = item.product_and_size.product.price * (1 - item.product_and_size.product.discount / 100)
        if AdminInformations.objects.all()[0].DPH == True:
            item.dph=(SupplierInformations.dph_size / 100)*item.product_and_size.product.price
            item.price_with_dph=item.product_and_size.product.price+  (SupplierInformations.dph_size / 100) * item.product_and_size.product.price
 
    shipping_method = order.shipping_method
    return render(request, 'main/invoice-form.html', {"order": order,
        "orderItems": orderItems,
        "invoice_number": invoice_number,
        "shipping_method": shipping_method,
        "SupplierInformations": SupplierInformations,})


