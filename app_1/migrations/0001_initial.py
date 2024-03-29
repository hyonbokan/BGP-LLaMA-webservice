# Generated by Django 4.2.9 on 2024-03-11 03:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("isbn", models.CharField(max_length=150)),
                ("qty", models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Playlist",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("playlist_name", models.CharField(max_length=200)),
                ("playlist_url", models.CharField(max_length=250)),
                (
                    "slug",
                    models.SlugField(blank=True, default="", max_length=250, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Userquery",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("query", models.CharField(max_length=200)),
                ("llmodel", models.CharField(max_length=150, null=True)),
                ("maxlength", models.IntegerField(null=True)),
                ("topk", models.IntegerField(null=True)),
                ("prompt_template", models.CharField(max_length=250, null=True)),
                ("reply", models.CharField(max_length=500)),
                (
                    "slug",
                    models.SlugField(blank=True, default="", max_length=600, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Video",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("vid_id", models.CharField(max_length=25)),
                ("title", models.CharField(max_length=100)),
                ("videourl", models.CharField(max_length=100)),
                ("description", models.CharField(max_length=2000, null=True)),
                (
                    "slug",
                    models.SlugField(blank=True, default="", max_length=150, null=True),
                ),
                (
                    "featured_image",
                    models.ImageField(null=True, upload_to="Media/featured_img"),
                ),
                (
                    "plist",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="app_1.playlist",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Playlistvideos",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "playlist",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app_1.playlist"
                    ),
                ),
                (
                    "video",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="app_1.video"
                    ),
                ),
            ],
        ),
    ]
