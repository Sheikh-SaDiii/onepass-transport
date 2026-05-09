from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Wallet, Transaction


@login_required
def wallet(request):
    w, _ = Wallet.objects.get_or_create(user=request.user)
    txs = request.user.transactions.all()[:50]
    return render(request, "payments/wallet.html", {"wallet": w, "transactions": txs})


@login_required
def topup(request):
    if request.method == "POST":
        amount = Decimal(request.POST.get("amount") or "0")
        method = request.POST.get("method", "card")
        if amount <= 0:
            messages.error(request, "Enter a valid amount.")
            return redirect("payments:wallet")
        w, _ = Wallet.objects.get_or_create(user=request.user)
        w.balance += amount
        w.save()
        Transaction.objects.create(
            user=request.user,
            amount=amount,
            kind="credit",
            method="topup",
            note=f"Top-up via {method}",
        )
        messages.success(request, f"৳{amount} added to your wallet.")
    return redirect("payments:wallet")
