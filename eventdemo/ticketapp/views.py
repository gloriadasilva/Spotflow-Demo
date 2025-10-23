import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import os
# Create your views here.

def ticket(request):
    
    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        ticket = request.POST.get("ticket")

        if not ticket :
            messages.info(request, "This field is required")
            return redirect("ticket")
        else:

            try:
                ticket = int(ticket)
                request.session["ticket"] = ticket
                request.session["username"] = username
                request.session["email"] = email

                return redirect("checkout")
            except ValueError:
                messages.info(request, "Invalid input")
                return redirect("ticket")

    return render(request, "ticket.html",)

def checkout(request):
    ticket = request.session.get("ticket")
    username = request.session.get("username")
    email = request.session.get("email")
    price = 1000
    reference = f"ref-{uuid.uuid4()}"
    currency = "NGN"
    callBackUrl = "https://www.algoai.one"
    payload = {
            "reference": reference,
            "amount": ticket * price,
            "currency": "NGN",
            "localCurrency": currency,
            "metadata": {
                "productName": "Tech Workshop 2025",
                "title": "dTechreative Ticket",
            },
            # "callBackUrl": callBackUrl,
            "customer":{
                "email": email,
                "name": username,
            }
    
    }
    API_KEY = "sk_test_3500ece212364e11abd01984afdd67b3"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post("https://api.spotflow.co/api/v1/payments/initialize", json=payload, headers=headers)

    if response.status_code == 200:

        converter = response.json()

        extractData = {
            "reference": converter.get("reference"),
            "checkoutURL": converter.get("checkoutUrl"),
            "status": converter.get("status"),
            "title": converter.get("metadata", {}).get("title"),
            "productName": converter.get("metadata", {}).get("productName"),

        }
        getstatus = extractData["status"]
        request.session["status"] = getstatus

        getreference = extractData["reference"]
        request.session["reference"] = getreference

        return redirect(extractData["checkoutURL"])
    else:
        messages.info(request, "An error occurred.")
        return redirect("ticket")

def verify(request):

    reference = request.GET.get("reference") or request.session.get("reference")
    API_KEY = "sk_test_3500ece212364e11abd01984afdd67b3"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(f" https://api.spotflow.co/api/v1/payments/verify?reference={reference}", headers=headers)

    if response.status_code == 200:
        convertJson = response.json()

        extractResponse = {
            "id": convertJson.get("id",),
            "reference": convertJson.get("reference"),
            "status": convertJson.get("status"),
            "name": convertJson.get("customer", {}).get("name"),
            "email": convertJson.get("customer", {}).get("email"),
            "amount": convertJson.get("amount"),
        }
    else:
        messages.info(request, "An error occurred during verification.")

    username = request.session.get("username")
    ticket = request.session.get("ticket")

    return render(request, "verify.html", { "username": username, "ticket": ticket, "extractResponse": extractResponse, "getstatus": extractResponse.get("status")})