from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RecordForm
from .models import Record


def healthcheck(request):
    return HttpResponse("pong", content_type="text/plain")


def record_list(request):
    records = Record.objects.all()
    return render(request, "main/list.html", {"records": records})


def record_create(request):
    form = RecordForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Запись добавлена.")
            return redirect("main:list")
        messages.error(request, "Проверьте поля формы.")
        return render(request, "main/edit.html", {"form": form}, status=400)
    return render(request, "main/edit.html", {"form": form})


def record_edit(request, pk):
    record = get_object_or_404(Record, pk=pk)
    form = RecordForm(request.POST or None, instance=record)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены.")
            return redirect("main:list")
        messages.error(request, "Проверьте поля формы.")
        return render(request, "main/edit.html", {"form": form, "record": record}, status=400)
    return render(request, "main/edit.html", {"form": form, "record": record})


def record_delete(request, pk):
    record = get_object_or_404(Record, pk=pk)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Запись удалена.")
        return redirect("main:list")
    return render(request, "main/remove.html", {"record": record})
