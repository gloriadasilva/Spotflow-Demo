import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
from django.conf import settings
# Create your views here.

# for webhook

import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

import hmac
import hashlib

def ticket(request):
    
    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        ticket = request.POST.get("ticket")

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
    ticket = request.session.get("ticket") # retriev the num
    username = request.session.get("username") # re
    email = request.session.get("email")
    price = 1000
    amount = price * ticket
    reference = f"ref-{uuid.uuid4()}"
    currency = "NGN"
    payload = {
            "reference": reference,
            "amount": amount,
            "currency": "NGN",
            "localCurrency": currency,
            "metadata": {
                "productName": "Tech Workshop 2025",
                "title": "dTechreative Ticket",
            },
            "callBackUrl": "https://spotflow-demo.onrender.com/verify/",
            "customer":{
                "email": email,
                "name": username,
            }
    
    }
    # SPOTFLOW_API_KEY = "sk_test_3500ece212364e11abd01984afdd67b3"
    #  sk_test_3500ece212364e11abd01984afdd67b3
    headers = {
        "Authorization": f"Bearer {settings.SPOTFLOW_API_KEY}",
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
        "Authorization": f"Bearer {settings.SPOTFLOW_API_KEY}",
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

@csrf_exempt
def webhook (request):
    if request.method == "POST":
        secretKey = "sk_test_3500ece212364e11abd01984afdd67b3"
        signature = request.headers.get("x-spotflow-signature")
        payload = request.body
        payloadString = json.dumps(payload, separators=(',', ':'))

        computed_signature = hmac.new(
          secretKey.encode(),
          payloadString.encode(),
          hashlib.sha512
       ).hexdigest()
       
        print("=== WEBHOOK DEBUG ===")
        print("Received Signature:", signature)
        print("Computed Signature:", computed_signature)
        print("Payload:", payload.decode("utf-8"))
        print("=====================")


        # if not hmac.compare_digest(computed_signature, signature):
            # return JsonResponse({"status": "forbidden"}, status=403)

        try:
            payload = json.loads(request.body)
            eventType = payload.get("event")
            data = payload.get("data", {})
            if eventType == "payment_successful":
                reference = data.get("reference")
                amount = data.get("amount")
                print("Payment sucessful with ID", reference, "Amount", amount)
            elif eventType == "payment_failed":
                reference = data.get("reference")
                print("Payment failed with ID", reference)
            return JsonResponse({"status": "success"}, status=200)
        except Exception as e:
            print("Error processing webhook", e)
            return JsonResponse({"status": "error"}, status=400)
    return JsonResponse({"status": "Method not allowed"}, status=405)