from django import forms
from .models import Point, Image, Document
from django.forms.formsets import formset_factory

class PointForm(forms.ModelForm):
    class Meta:
        model = Point

class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('image',)

    def save(self, point):
        img = super(ImageForm, self).save(commit=False)
        img.point = point
        img.save()
        return img

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('doc',)

    def save(self, point):
        doc = super(DocumentForm, self).save(commit=False)
        doc.point = point
        doc.save()
        return doc


class ImageFormSet(formset_factory(ImageForm)):
    def save(self, point):
        # NB returning a list, not an iterator,
        # otherways f.save() will NOT be evauated !!
        return [f.save(point) for f in self]

class DocumentFormSet(formset_factory(DocumentForm)):
    def save(self, point):
        # NB returning a list, not an iterator,
        # otherways f.save() will NOT be evauated !!
        return [f.save(point) for f in self]
    

