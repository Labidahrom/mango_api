from django.db import models


class CallHistoryGolangVersion(models.Model):
    id = models.BigAutoField(primary_key=True)
    entry_id = models.CharField(max_length=50)
    napravlenie = models.CharField(max_length=50)
    data_postupil = models.DateField(null=True)
    time_postupil = models.TimeField(null=True)
    date_time_postupil = models.DateTimeField(null=True)
    gruppa = models.CharField(max_length=100, null=True)
    dlitelnost = models.CharField(max_length=10, null=True)
    tel_kto_zvonil = models.CharField(max_length=100, null=True)
    komu_zvonil = models.CharField(max_length=100, null=True)
    tel_komu_zvonil = models.CharField(max_length=100, null=True)
    kuda_zvonil = models.CharField(max_length=100, null=True)
    komment_k_nomeru = models.CharField(max_length=100, null=True)
    data_okonchania_razgovora = models.DateField(null=True)
    time_okonchania_razgovora = models.TimeField(null=True)
    recording_id = models.CharField(max_length=60, null=True)

    class Meta:
        db_table = 'call_history_golang_version'

    def __str__(self):
        return self.entry_id


class CallRecordingGolangVersion(models.Model):
    id = models.OneToOneField(
        CallHistoryGolangVersion,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='recordings'
    )
    date = models.DateField(null=True)
    recording = models.BinaryField(null=True)


    class Meta:
        db_table = 'call_recording_golang_version'

    def __str__(self):
        return self.id


class GroupGolangVersion(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=300)

    class Meta:
        db_table = 'group_golang_version'

    def __str__(self):
        return self.name


class OperatorGolangVersion(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    group = models.CharField(max_length=100, null=True, blank=True)
    telegram_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'operator_golang_version'

    def __str__(self):
        return self.name


class PhoneGolangVersion(models.Model):
    number = models.CharField(primary_key=True, max_length=100)
    comment = models.CharField(max_length=100, null=True, blank=True)
    schema_id = models.IntegerField()

    class Meta:
        db_table = 'phone_golang_version'

    def __str__(self):
        return self.number


class DistributionSchemaGolangVersion(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'distribution_schema_golang_version'

    def __str__(self):
        return self.name
