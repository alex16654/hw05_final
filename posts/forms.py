from django import forms
from django.forms import Textarea

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'group': 'Имя группы',
            'text': 'Текст',
        }
        help_texts = {
            'group': 'Группу можно выбрать здесь',
            'text': 'Текст вводить здесь',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Комментарий'}
        widgets = {'text': Textarea(attrs={"rows": 2})}
