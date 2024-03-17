from django import forms
from django.core.exceptions import ValidationError
from .models import Task, Ot, System, Equipo, Ruta, HistoryHour
from django.contrib.auth.models import User
import datetime


class UserChoiceField(forms.ModelChoiceField):
     '''
     Objeto widget para desplegar nombre y apellido de los usuarios
     '''
     def label_from_instance(self, obj):
          return f'{obj.first_name} {obj.last_name}'


class XYZ_DateInput(forms.DateInput):
     '''
     Objeto para desplegar calendario en fechas de formularios
     '''
     input_type = 'date'

     def __init__(self, **kwargs):
          kwargs['format'] = '%Y-%m-%d'
          super().__init__(**kwargs)
    

# Form 2: Reprogramar actividades 
class RescheduleTaskForm(forms.ModelForm):
        '''
        Formulario ubicado en "assignedtasks_list_pendient_user.html"
        '''
        news = forms.CharField(
            widget=forms.Textarea(attrs={'rows': 4}),
        	required=False,
            label = 'Novedades'
        )

        def clean_start_date(self):
               data = self.cleaned_data['start_date']
               if data < datetime.date.today():
                    raise ValidationError('Fecha invalida')
               return data
        class Meta:
            model = Task
            fields = ['start_date', 'news', 'men_time']
            labels = {
                  'start_date': 'Fecha de reprogramacion',
                  'men_time': 'Tiempo de ejecución (Dias)'
                }
            help_text = {
                 'news': 'Motivo de la reprogramación'
            }
            widgets = {
                 'start_date': forms.DateInput(attrs={'type': 'date'}),
            }
            

# Form 3: Actualizar actividad 
class UpdateTaskForm(forms.ModelForm):
        '''
        Formulario ubicado en "assignedtasks_list_pendient_user.html"
        '''
        news = forms.CharField(
          widget=forms.Textarea(attrs={'rows': 4}),
        	required=False,
          label = 'Novedades'
        )
        class Meta:
            model = Task
            fields = ['news', 'evidence', 'finished']
            labels = {
                  'news': 'Novedades',
                  'evidence': 'Evidencia',
                  'finished': 'Finalizar'
                }
            widgets = {
            'responsible': forms.Select(attrs={'class': 'form-control'}),
            'evidence': forms.FileInput(attrs={'class': 'form-control'}),
        }


# Form 4: Crear nuevo sistema
class SysForm(forms.ModelForm):
     '''
     v2.1
     '''
     class Meta:
          model = System
          exclude = ['asset',]
          labels = {
                'name': 'Sistema',
                'gruop': 'Grupo',
                'location': 'Ubicación',
                'state': 'Estado'
          }


# Form 5: Crear nueva orden de trabajo
class OtForm(forms.ModelForm):
     super = UserChoiceField(
          queryset=User.objects.all(), label='Supervisor',
     )

     class Meta:
          model = Ot
          exclude = ['creations_date', 'num_ot']
          labels = {
               'description': 'Description',
               'system': 'Sistema',
               'state': 'Estado',
               'tipo_mtto': 'Tipo de mantenimiento',
               'info_contratista_pdf': 'Informe externo'
          }
          widgets = {
               'super': forms.Select(attrs={'class': 'form-control'}),
               'info_contratista_pdf': forms.FileInput(attrs={'class': 'form-control'}),
          }

     def __init__(self, *args, **kwargs):
          asset = kwargs.pop('asset')
          super().__init__(*args, **kwargs)
          self.fields['system'].queryset = System.objects.filter(asset=asset)


# Form 6: Finalizar actividad
class FinishOtForm(forms.Form):
     finish = forms.BooleanField(
          widget=forms.HiddenInput(),
          required=False,
          initial=True,
     )


# Form 7: Crear nueva actividad
class ActForm(forms.ModelForm):
     responsible = UserChoiceField(
          queryset=User.objects.all(),
          label='Responsable',
     )

     class Meta:
          model = Task
          exclude = ['ot', 'ruta', 'hse']
          labels = {
               'description': 'Descripción',
               'news': 'Novedades',
               'evidence': 'Evidencia',
               'start_date': 'Fecha de inicio',
               'men_time': 'Tiempo de ejecución (Dias)',
               'finished': 'Finalizado',
          }
          widgets = {
               'responsible': forms.Select(attrs={'class': 'form-control'}),
               'start_date': XYZ_DateInput(format=['%Y-%m-%d'],),
               'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
               'evidence': forms.FileInput(attrs={'class': 'form-control'}),
          }

     
class RutActForm(forms.ModelForm):
     responsible = UserChoiceField(
          queryset=User.objects.all(),
          label='Responsable',
          required=False,
     )

     class Meta:
          model = Task
          fields = ['responsible', 'description', 'procedimiento', 'suministros', 'hse']
          labels = {
               'responsible': 'Responsable(Opcional)',
               'description': 'Descripción',
               'procedimiento': 'Procedimiento',
               'suministros': 'Suministros',
               'hse': 'Precauciones de seguridad',
          }
          widgets = {
               'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
               'procedimiento': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
               'hse': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
               'suministros': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
               'responsible': forms.Select(attrs={'class': 'form-control'}),
          }


# Form 8: Crear/editar nuevo equipo
class EquipoForm(forms.ModelForm):

     class Meta:
          model = Equipo
          exclude = ['system', 'horometro']
          labels = {
               'name': 'Nombre',
               'date_inv': 'Fecha de ingreso al inventario',
               'code': 'Codigo interno',
               'model': 'Modelo',
               'serial': '# Serial',
               'marca': 'Marca',
               'fabricante': 'Fabricante',
               'feature': 'Caracteristicas',
               'imagen': 'Imagen',
               'manual_pdf': 'Manual'
          }
          widgets = {
            'date_inv': XYZ_DateInput(format=['%Y-%m-%d'],),
            'feature': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'manual_pdf': forms.FileInput(attrs={'class': 'form-control'}),
          }


#  Form 9: Crear/editar nueva ruta
class RutaForm(forms.ModelForm):

     class Meta:
          model = Ruta
          exclude = ['system', 'code']
          labels = {
               'name': 'Codigo interno',
               'frecuency': 'Frecuencia',
               'intervention_date': 'Fecha ultima intervención'
          }
          widgets = {
            'intervention_date': XYZ_DateInput(format=['%Y-%m-%d'],),
          }
     
     def __init__(self, *args, **kwargs):
          system = kwargs.pop('system')
          super().__init__(*args, **kwargs)
          self.fields['equipo'].queryset = Equipo.objects.filter(system=system)


class ReportHours(forms.ModelForm):
     def clean_hour(self):
          hour = self.cleaned_data['hour']
          if hour < 0 or hour > 24:
               raise forms.ValidationError('El valor de horas debe estar entre 0 y 24.')
          return hour
     
     class Meta:
          model = HistoryHour
          fields = ['hour', 'report_date']
          labels = {
               'hour': 'Horas',
               'report_date': 'Fecha'
          }
          widgets = {
            'report_date': XYZ_DateInput(format=['%Y-%m-%d'],),
          }