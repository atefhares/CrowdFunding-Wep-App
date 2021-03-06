from datetime import timedelta
import datetime
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseNotFound
from .models import UserProfile
import re
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.template.loader import get_template
from django.utils import timezone
import random
import string
import pytz


def validate_string(name_field):
    if name_field == '':
        return True
    else:
        return False


def validate_password(password_field):
    PASS_REJEX = re.compile(r"^.{8,}$")
    if not PASS_REJEX.match(password_field):
        return True
    else:
        return False


def validate_email(email_field):
    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
    if not EMAIL_REGEX.match(email_field):    #لو مش بيماتش هترجع ترووووووو
        return True
    else:
        return False


def validate_mobile_phone(phone_number):
    PHONE_REJEX = re.compile(r"^01[012][0-9]{8}")
    if not PHONE_REJEX.match(phone_number):
        return True
    else:
        return False


# Create your views here.
def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        validate_string(first_name)
        if validate_string(first_name):
            messages.error(request, "First Name Is Required")

        last_name = request.POST['last_name']
        validate_string(last_name)
        if validate_string(last_name):
            messages.error(request, "Last Name Is Required")

        email = request.POST['email']
        validate_email(email)
        if validate_email(email):
            messages.error(request, "Invalid Email Format:example@domain.com")

        phone_number = request.POST['phone_number']
        validate_mobile_phone(phone_number)
        if validate_mobile_phone(phone_number):
            messages.error(request, "Phone Number Must Be 11 digits starts with 010 or 011 or 012")

        birth_date = request.POST['birth_date']

        password = request.POST['password']
        validate_password(password)
        if validate_password(password):
            messages.error(request, "Password Must Be At Least 8 Character")
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            if User.objects.filter(email=email).exists():
                messages.error(request, "This Email already exists")

                return redirect('register')
            elif not validate_email(email) and not validate_mobile_phone(phone_number) and not validate_string(first_name) and not validate_string(last_name) and not validate_password(password):
                if birth_date == '':
                    profile = UserProfile(
                        phone_number=phone_number,
                        key = random_string_generator(size=45), 
                        )
                else:
                        profile = UserProfile(
                        phone_number=phone_number,
                        birth_date= birth_date,
                        key = random_string_generator(size=45), 
                        )
                user = User.objects.create_user(
                    username=email,
                    first_name=first_name,
                    email=email,
                    password=password,
                    last_name=last_name,

                )
                user.active = False
                profile.time_stamp = datetime.datetime.now()
                profile.expires = profile.time_stamp + datetime.timedelta(hours=24)
                # profile.expires = datetime.datetime.now()
                profile.user = user

                if send_activation(user, profile,is_registered = False):
                    profile.save()

                messages.success(request, '<strong>Success</strong><br>Registered, Successfully!',
                                 extra_tags='contains_html')
                messages.info(request,
                              """<strong>Info</strong><br>
                              <p>
                              An activation mail is sent to you.
                              once you verify your mail, You can login.<br>
                              Note: This mail will be expired after 24 hours.</p>
                              """,
                              extra_tags='contains_html'
                              )
                # return render(request, 'RegisteredSucceccfully.html', context)
                return redirect('login')
        else:
            messages.error(request, "Passwords don't match")
            return redirect('register')
    return render(request, 'accounts/register.html')


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def send_activation(user, profile,is_registered):  # responsoble for sending the mail
    is_sent = False

    # send_email(subject,message,from_email,recipient_list,html_message)
    context = {
        'key': profile.key,
        'email': user.email,
        'username': user.first_name
    }
    html_ = get_template("accounts/verify.html").render(context)
    txt_ = get_template("accounts/verify.txt").render(context)
    mail_subject = 'Verification Mail'
    mail_sender = 'crowdfundingwebapp@gmail.com'
    mail_reciever = [user.email]
    verify_forget_password_txt_ = get_template("accounts/verify_forget_password.txt").render(context)
    verify_forget_password_html_ = get_template("accounts/verify_forget_password.html").render(context)
    if is_registered == False:
        send_email = send_mail(
            mail_subject,
            txt_,
            mail_sender,
            mail_reciever,
            html_message=html_,
        )
    else:
        send_email = send_mail(
            mail_subject,
            verify_forget_password_txt_,
            mail_sender,
            mail_reciever,
            verify_forget_password_html_
        )
    is_sent = True
    return is_sent


def is_expired(expiration_date):   #returns true if the user is expired
    utc = pytz.UTC
    now_date = datetime.datetime.now().replace(tzinfo=utc)
    expiration_date = expiration_date.replace(tzinfo=utc)
    if now_date >= expiration_date:
        return True
    else:
        return False


def activate(request, key):
    try:
        user_profile = UserProfile.objects.get(key=key)
    except(UserProfile.DoesNotExist, OverflowError, ValueError, TypeError):
        user_profile = None
        return HttpResponseNotFound('<h1>Error:404<br>Page not found</h1>')
        # return render(request, 'accounts/verify.html')
    expires = user_profile.expires
    if user_profile is not None and is_expired(expires) == False:
        if not user_profile.once_activation:
            user_profile.once_activation = True
            user_profile.is_active = True
            user_profile.save()
            messages.success(request, "Your mail is successfully activated.")
            return render(request, "accounts/login.html")

        elif user_profile.once_activation == True and user_profile.is_active == True:
            messages.info(request, "Your email is already activated")
            return render(request, 'accounts/login.html')
    else:
        return HttpResponseNotFound('<h1>Error<br>Page not found</h1>')
        # return render(request, 'accounts/verify.html')

def reset_password(request, key):
    try:
        user_profile = UserProfile.objects.get(key=key)
    except(UserProfile.DoesNotExist, OverflowError, ValueError, TypeError):
        user_profile = None
        return HttpResponseNotFound('<h1>Error:404<br>Page not found</h1>')
    
    if user_profile is not None and not is_expired(user_profile.expires) and user_profile.once_activation == False:
        context = {
            'key' : user_profile.key,
            'email' : user_profile.user.email
        }
        user_profile.once_activation = True
        user_profile.save()
        return render(request,'accounts/reset_password.html',context)
    else:
        return HttpResponseNotFound('<h1>Error:404<br>Page not found</h1>')


def submit_password_new_value(request,key):
    try:
        user_profile = UserProfile.objects.get(key=key)
        user = user_profile.user 
        print(user_profile.user.email)
    except(UserProfile.DoesNotExist, OverflowError, ValueError, TypeError):
        user_profile = None
        return HttpResponseNotFound('<h1>Error:404<br>Page not found</h1>')
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if validate_password(password):
            messages.error("Password Must Be At Least 8 Characters.")
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            user.set_password(password)
            user_profile.is_active = True
            user_profile.once_activation = True
            user.save()
            user_profile.save()
            messages.success(request,"<strong>Success: </strong>Password Updated Sucessfully!",extra_tags='contains_html')
            return render(request, 'accounts/login.html')
        else:
            messages.error(request,"Passwords Don't Match")
    else:
        return redirect(request,'accounts/reset_password.html')





def resend_activation_email(request,email):
    expired_user_profile = UserProfile.objects.get(user__email= email)
    expired_user = User.objects.get(email= email)
    send_activation(expired_user,expired_user_profile)
    messages.success(request, "<strong>Success:</strong>Verification email is successfully sent, <br>Once you verfiy your email you can login!",extra_tags='contains_html')
    expired_user_profile.time_stamp = datetime.datetime.now()
    expired_user_profile.expires = expired_user_profile.time_stamp + datetime.timedelta(hours=24)
    expired_user_profile.save()
    return render(request, 'accounts/login.html')

def login(request):
    if request.method == 'POST':
        email = request.POST['login_email']
        password = request.POST['login_password']

        email_validation_result = validate_email(email)
        if email_validation_result:
            messages.error(request, "Invalid Email")

        password_validation_result = validate_password(password)
        if password_validation_result:
            messages.error(request, "Password Must Be More Than Or Equal 8 Characters")
        user = auth.authenticate(username=email, password=password)

        try:
            user_profie = UserProfile.objects.get(user__email=email)
        except(UserProfile.DoesNotExist, OverflowError, ValueError, TypeError):
            messages.error(request, "Invalid Credentials")
            user = None
            return render(request, 'accounts/login.html')
        if user is not None and user_profie.is_active == True:
            auth.login(request, user)
            return redirect('/')
        elif user is not None and user_profie.is_active == False:
            expired_user_profile = UserProfile.objects.get(user__email=email)
            is_user_expired = is_expired(expired_user_profile.expires)
            if  is_user_expired == False:
                messages.error(request,"Sorry, This email is not activated yet!")
                messages.info(request,"<strong>Info:</strong> Please, Check your email inbox and activate your account.",extra_tags='contains_html')
            else:
                email = user.email
                messages.error(request, "This email is not activated yet,<br> If your activation email is expired,"+
                                        'Please <a id="resend_email" href="http://localhost:8000/accounts/resend_activation_email/{}">ClickHere</a>'.format(email),
                                        extra_tags='contains_html'
                )
            return render(request, 'accounts/login.html')
        else:
            messages.error(request, "Invalid Credentials")
            return render(request, 'accounts/login.html')

    else:
        return render(request, 'accounts/login.html')
def text_message():
    str =  "<strong>Info: </strong>If provided email is a registered email ID on CrowdFunding,<br> you will receive an email with instructions on how to reset your password. <br> In case you didn't receive this email, you need to create a new account."
    return str
def forget_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        email_after_validation = validate_email(email)

        if not email_after_validation:
            try:
                user = User.objects.get(email = email)
            except(User.DoesNotExist, OverflowError, ValueError, TypeError):
                user = None
                messages.info(request,text_message(),extra_tags= 'contains_html')
                return render(request, 'accounts/forget_password.html')
            profile = UserProfile.objects.get(user__email= email)
            if user is not None:
                send_activation(user,profile,True)

                profile.time_stamp = datetime.datetime.now()
                profile.expires = profile.time_stamp + datetime.timedelta(hours=24)
                profile.is_active = False
                profile.once_activation = False
                profile.save()
                messages.info(request,text_message(),extra_tags='contains_html')
                return render(request, 'accounts/login.html')
        
        else:
            messages.error(request, "Invalid Email Format:example@domain.com")
            return render(request, 'accounts/forget_password.html')


    else:
        return render(request, 'accounts/forget_password.html')        




# def logout(request):
#     return redirect(request, 'acounts/index.html')
