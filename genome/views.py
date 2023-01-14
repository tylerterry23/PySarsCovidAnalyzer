import base64
import os
import shutil

from django.conf import settings
from django.shortcuts import render
from django.views import View
from django.contrib import messages
from .models import TxtFiles
from .local import main_local
from .global_algo import main_global
from django.core.files.storage import FileSystemStorage
from datetime import date


# Create your views here.
class UploadTxt(View):
    def get(self, request, *args, **kwargs):
        return render(request, "home_upload.html")

    def post(self, request, *args, **kwargs):
        a_value = request.POST.get("algo")
        algo = a_value
        file1 = request.FILES.get("file1", False)
        file2 = request.FILES.get("file2", False)

        currentDate = date.today()
        today = currentDate.strftime('%m/%d/%Y').replace("/0", "/")
        if today[0] == '0':
            today = today[1:]

        filename1 = ""
        filename2 = ""

        if algo == "Global":
            global_or_local = "Global Alignment Result"
        elif algo == "":
            global_or_local = "Local Alignment Result"
        elif algo == "select":
            messages.error(request, "Please Select Algorithm")
            return render(request, "home_upload.html")

        if file1:
            filename1 = file1.name
            if not filename1.endswith('.txt'):
                messages.error(request, "Please Select A .txt File")
                return render(request, "home_upload.html")

        if file2:
            filename2 = file2.name
            if not filename2.endswith('.txt'):
                messages.error(request, "Please Select A .txt File")
                return render(request, "home_upload.html")

        if file1 is False or file2 is False:
            messages.error(request, "Please Select Files")
            return render(request, "home_upload.html")

        created = TxtFiles.objects.create(
            file1=file1,
            file2=file2
        )
        created.save()

        local_result1, local_result2, local_result3, local_result4_score, result5_p_similarity, local_image_data = main_local(
            created.file1.path, created.file2.path, algo)
        # main_global(created.file1.path, created.file2.path, algo)

        shutil.rmtree(os.path.join(settings.MEDIA_ROOT), ignore_errors=False, onerror=None)
        created.delete()

        context = {
            "file1_name": filename1,
            "file2_name": filename2,
            "local_result1": local_result1,
            "local_result2": local_result2,
            "local_result3": local_result3,
            "local_result4_score": local_result4_score,
            "local_image_data": local_image_data,
            "global_or_local": global_or_local,
            "today": today,
            "algo": algo,
            "result5_p_similarity": result5_p_similarity,
        }

        return render(request, "results.html", context=context)


# Trim each line to only be x characters long
def truncate_lines(text, characters_show):
    return '\n'.join([line[:characters_show] for line in text.splitlines()])
