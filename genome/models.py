from django.db import models


# Create your models here.
class TxtFiles(models.Model):
    file1 = models.FileField(upload_to="txt_files1/%Y/%m")
    file2 = models.FileField(upload_to="txt_files2/%Y/%m")
    acc_f1 = models.CharField(max_length=255, null=True, blank=True)
    acc_f2 = models.CharField(max_length=255, null=True, blank=True)
    results_f1 = models.TextField(null=True, blank=True)
    results_f2 = models.TextField(null=True, blank=True)
    img_f1 = models.FileField(upload_to="img_f1/%Y/%m", null=True, blank=True)
    img_f2 = models.FileField(upload_to="img_f2/%Y/%m", null=True, blank=True)

    def __str__(self):
        return str(self.id)
