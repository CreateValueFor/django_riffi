# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Folders(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'folders'


class Musics(models.Model):
    created_date_time = models.DateTimeField(blank=True, null=True)
    folder = models.ForeignKey(Folders, models.DO_NOTHING, blank=True, null=True)
    id = models.BigAutoField(primary_key=True)
    modified_date_time = models.DateTimeField(blank=True, null=True)
    owner = models.ForeignKey('Users', models.DO_NOTHING, db_column='owner', blank=True, null=True)
    title = models.CharField(max_length=50)
    description = models.TextField()
    raw_fileurl = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'musics'


class Sources(models.Model):
    download_cnt = models.IntegerField(blank=True, null=True)
    id = models.BigAutoField(primary_key=True)
    music = models.ForeignKey(Musics, models.DO_NOTHING, blank=True, null=True)
    session = models.CharField(max_length=50)
    fileurl = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sources'


class Users(models.Model):
    created_date_time = models.DateTimeField(blank=True, null=True)
    id = models.BigAutoField(primary_key=True)
    modified_date_time = models.DateTimeField(blank=True, null=True)
    genre = models.CharField(max_length=20, blank=True, null=True)
    job = models.CharField(max_length=20, blank=True, null=True)
    nickname = models.CharField(max_length=20, blank=True, null=True)
    o_auth_key = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'users'
