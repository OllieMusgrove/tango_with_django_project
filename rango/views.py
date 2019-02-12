from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

# Import the Category model
from rango.models import Category

def index(request):
    # Query the database for a list of ALL categories currently stored. # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary
    # that will be passed to the template engine.

    category_list = Category.objects.order_by('-likes')[:5]

    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list, 'pages': page_list}

    # Render the response and send it back
    response = render(request, 'rango/index.html', context=context_dict)
    return response

def about(request):
    # html = "Rango says here is the about page." + '<a href="/rango/">Index</a>'
    #return HttpResponse(html)

    # context_dict = {'boldmessage': "This tutorial has been put together by Ollie Musgrove"}
    print(request.method)
    print(request.user)
    return render(request, 'rango/about.html', {})


def show_category(request, category_name_slug):
    # Create a context dictionary which we can pass 
    # to the template rendering engine. 
    context_dict = {}

    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception. 
        category = Category.objects.get(slug=category_name_slug)
        # Retrieve all of the associated pages.
        # Note that filter() will return a list of page objects or an empty list
        pages = Page.objects.filter(category=category)
        
        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from
        # the database to the context dictionary.
        # We'll use this in the template to verify that the category exists. 
        context_dict['category'] = category
    except Category.DoesNotExist:
    # We get here if we didn't find the specified category. 
    # Don't do anything -
    # the template will display the "no category" message for us.
        context_dict['category'] = None
        context_dict['pages'] = None
    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context_dict)

@login_required
def add_category(request):
    form = CategoryForm()

    # A HTTP Post
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # is teh form valid?
        if form.is_valid():
            # save new category to the database
            form.save(commit=True)
            # category saved, give confirmation message
            # most recently added category is on index page so redirect
            return index(request)
        else:
            # if form has errors, print in terminal
            print(form.errors)

    # will handel bad form, new form or no form
    # rendor form with error messages (if any)
    return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None
    
    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()
                return show_category(request, category_name_slug)
        else:
            print(form.errors)
    
    context_dict = {'form':form, 'category': category}
    return render(request, 'rango/add_page.html', context_dict)

def register(request):
    # Lets template know if registration success
    registered = False

    # If a HTTP post we process data
    if request.method == 'POST':
        # Attempt to get data from raw form
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()

            # Hash password with set_password
            user.set_password(user.password)
            user.save()

            # Delay saving the model until ready to avoid integrity problems
            profile = profile_form.save(commit=False)
            profile.user = user

            # If user provides profile pic put in UserProfile model
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            
            # save UserProfile model
            profile.save()
            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    
    return render(request, 'rango/register.html', 
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered})

def user_login(request):
    if request.method == 'POST':
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Use Django's machinery to attempt to see if the username/password is valid
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in. 
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                # An inactive account was used - no logging in
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in. 
            print("Invalid login details: {0}, {1}".format(username, password)) 
            return HttpResponse("Invalid login details supplied.")
    # The request is not a HTTP POST, so display the login form. 
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence blank dictionary object
        return render(request, 'rango/login.html', {})

@login_required
def restricted(request):
    # return HttpResponse("Since you're logged in, you can see this text!")
    return render(request,'rango/restricted.html', {})

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))

