from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def inbox(request):
    notifs = request.user.notifications.all()
    return render(request, "notifications/inbox.html", {"notifs": notifs})


@login_required
def mark_all_read(request):
    request.user.notifications.update(is_read=True)
    return redirect("notifications:inbox")
