from django.contrib import admin
from mango_api import models




class GroupGolangVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class OperatorGolangVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', "group")


class CallHistoryGolangVersionAdmin(admin.ModelAdmin):
    list_display = ('entry_id', 'napravlenie', 'date_time_postupil', 'napravlenie')


admin.site.register(models.CallHistoryGolangVersion, CallHistoryGolangVersionAdmin)
admin.site.register(models.CallRecordingGolangVersion)
admin.site.register(models.OperatorGolangVersion, OperatorGolangVersionAdmin)
admin.site.register(models.PhoneGolangVersion)
admin.site.register(models.GroupGolangVersion, GroupGolangVersionAdmin)
admin.site.register(models.DistributionSchemaGolangVersion)
