from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Task, Ot, System, Equipo, Ruta, HistoryHour, FailureReport
    )
from django.contrib.auth.models import User, Group


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


class RescheduleTaskForm(forms.ModelForm):
    '''
    Form 1: reprogramación de actividades
    - "assignedtasks_list_pendient_user.html"
    '''
    news = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label='Novedades'
        )

    class Meta:
        model = Task
        fields = ['start_date', 'news', 'men_time']
        labels = {
            'start_date': 'Fecha de reprogramacion',
            'men_time': 'Tiempo de ejecución (Dias)'
            }
        widgets = {
            'start_date': forms.DateInput(
                format='%d/%m/%Y', attrs={'type': 'date'}
                ),
            }


# Form 3: Actualizar actividad
class UpdateTaskForm(forms.ModelForm):
    '''
    Formulario ubicado en "assignedtasks_list_pendient_user.html"
    '''
    news = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label='Novedades',
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
        queryset=User.objects.none(),  # La queryset se define en __init__
        label='Supervisor',
        widget=forms.Select(attrs={'class': 'form-control'}),
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
            'info_contratista_pdf': forms.FileInput(
                attrs={'class': 'form-control'}
                ),
            'tipo_mtto': forms.Select(attrs={'class': 'form-control'}),
            'system': forms.Select(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        asset = kwargs.pop('asset')
        super().__init__(*args, **kwargs)
        self.fields['system'].queryset = System.objects.filter(asset=asset)
        super_members_group = Group.objects.get(name='super_members')
        self.fields['super'].queryset = super_members_group.user_set.all()


# Form 5: Crear nueva orden de trabajo
class OtFormNoSup(forms.ModelForm):

    class Meta:
        model = Ot
        exclude = ['creations_date', 'num_ot', 'super']
        labels = {
            'description': 'Description',
            'system': 'Sistema',
            'state': 'Estado',
            'tipo_mtto': 'Tipo de mantenimiento',
            'info_contratista_pdf': 'Informe externo'
        }
        widgets = {
            'info_contratista_pdf': forms.FileInput(
                attrs={'class': 'form-control'}
                ),
            'tipo_mtto': forms.Select(attrs={'class': 'form-control'}),
            'system': forms.Select(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
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
            'description': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
                ),
            'evidence': forms.FileInput(attrs={'class': 'form-control'}),
            }

    def __init__(self, *args, **kwargs):
        super(ActForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].required = True


# Form 7: Crear nueva actividad
class ActFormNoSup(forms.ModelForm):

    class Meta:
        model = Task
        exclude = ['ot', 'ruta', 'hse', 'responsible']
        labels = {
            'description': 'Descripción',
            'news': 'Novedades',
            'evidence': 'Evidencia',
            'start_date': 'Fecha de inicio',
            'men_time': 'Tiempo de ejecución (Dias)',
            'finished': 'Finalizado',
        }
        widgets = {
            'start_date': XYZ_DateInput(format=['%Y-%m-%d'],),
            'description': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
                ),
            'evidence': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ActFormNoSup, self).__init__(*args, **kwargs)
        self.fields['start_date'].required = True


class RutActForm(forms.ModelForm):
    responsible = UserChoiceField(
        queryset=User.objects.all(),
        label='Responsable',
        required=False,
    )

    class Meta:
        model = Task
        fields = [
            'responsible',
            'description',
            'procedimiento',
            'suministros',
            'hse'
            ]
        labels = {
            'responsible': 'Responsable(Opcional)',
            'description': 'Descripción',
            'procedimiento': 'Procedimiento',
            'suministros': 'Suministros',
            'hse': 'Precauciones de seguridad',
            }
        widgets = {
            'description': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
                ),
            'procedimiento': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
                ),
            'hse': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
                ),
            'suministros': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
                ),
            'responsible': forms.Select(attrs={'class': 'form-control'}),
            }


# Form 8: Crear/editar nuevo equipo
class EquipoForm(forms.ModelForm):

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if Equipo.objects.filter(code=code).exists():
            raise ValidationError(
                '''Este código ya está en uso. Por favor,
                ingresa un código diferente.'''
                )
        return code

    class Meta:
        model = Equipo
        exclude = ['system', 'horometro', 'prom_hours']
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
            'manual_pdf': 'Manual',
            'tipo': 'tipo de equipo:',
            'initial_hours': 'Horas iniciales (si aplica)'
            }
        widgets = {
            'date_inv': XYZ_DateInput(format=['%Y-%m-%d'],),
            'feature': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
                ),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'manual_pdf': forms.FileInput(attrs={'class': 'form-control'}),
            }


# Form 8: Crear/editar nuevo equipo
class EquipoFormUpdate(forms.ModelForm):

    class Meta:
        model = Equipo
        exclude = ['system', 'horometro', 'prom_hours']
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
            'manual_pdf': 'Manual',
            'tipo': 'tipo de equipo:',
            'initial_hours': 'Horas iniciales (si aplica)'
            }
        widgets = {
            'date_inv': XYZ_DateInput(format=['%Y-%m-%d'],),
            'feature': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
                ),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'manual_pdf': forms.FileInput(attrs={'class': 'form-control'}),
            }


#  Form 9: Crear/editar nueva ruta
class RutaForm(forms.ModelForm):

    def clean(self):
        cleaned_data = super().clean()
        control = cleaned_data.get('control')
        equipo = cleaned_data.get('equipo')

        if control == 'h' and not equipo:
            self.add_error(
                'equipo',
                'Seleccionar un equipo es obligatorio para el control en horas'
                )
        return cleaned_data

    def clean_frecuency(self):
        frecuency = self.cleaned_data['frecuency']

        if frecuency < 0:
            raise forms.ValidationError(
                'El valor de la frecuencia no puede ser 0.'
                )
        return frecuency

    class Meta:
        model = Ruta
        exclude = ['system', 'code']
        labels = {
            'name': 'Codigo interno',
            'frecuency': 'Frecuencia',
            'intervention_date': 'Fecha ultima intervención',
            'dependencia': 'Dependencia'
            }
        widgets = {
            'intervention_date': XYZ_DateInput(format=['%Y-%m-%d'],),
            }

    def __init__(self, *args, **kwargs):
        system = kwargs.pop('system')
        super(RutaForm, self).__init__(*args, **kwargs)
        self.fields['equipo'].queryset = Equipo.objects.filter(system=system)
        self.fields['ot'].queryset = Ot.objects.filter(system__asset=system.asset)
        self.fields['dependencia'].queryset = Ruta.objects.filter(system=system).exclude(code=self.instance.code if self.instance else None)


class ReportHours(forms.ModelForm):
    def clean_hour(self):
        hour = self.cleaned_data['hour']
        if hour < 0 or hour > 24:
            raise forms.ValidationError(
                'El valor de horas debe estar entre 0 y 24.'
                )
        return hour

    class Meta:
        model = HistoryHour
        fields = ['hour', 'report_date']
        labels = {
            'hour': 'Horas',
            'report_date': 'Fecha'
        }
        widgets = {'report_date': XYZ_DateInput(format=['%Y-%m-%d'],), }


class ReportHoursAsset(forms.ModelForm):
    def clean_hour(self):
        hour = self.cleaned_data['hour']
        if hour < 0 or hour > 24:
            raise forms.ValidationError(
                'El valor de horas debe estar entre 0 y 24.'
                )
        return hour

    class Meta:
        model = HistoryHour
        fields = ['hour', 'report_date', 'component']
        labels = {
            'hour': 'Horas',
            'report_date': 'Fecha',
            'component': 'Componente',
        }
        widgets = {'report_date': XYZ_DateInput(format=['%Y-%m-%d'],), }

    def __init__(self, *args, **kwargs):
        asset = kwargs.pop('asset')
        super().__init__(*args, **kwargs)
        self.fields['component'].queryset = Equipo.objects.filter(
            system__asset=asset,
            tipo='r'
            )


# Form : Crear nuevo reporte de falla
class failureForm(forms.ModelForm):

    critico_choices = [
        (True, 'Sí'),
        (False, 'No'),
    ]

    critico = forms.ChoiceField(
        choices=critico_choices,
        widget=forms.RadioSelect(attrs={'class': 'radioOptions'}),
        label='¿El equipo/sistema que presenta la falla es crítico?',
        initial=False,
        required=False,
    )

    impact = forms.MultipleChoiceField(
        choices=FailureReport.IMPACT,
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'custom-checkbox'}
        ),
        required=False,
        label='Impacto',
    )

    class Meta:
        model = FailureReport
        exclude = ['reporter', 'related_ot', 'closed']
        labels = {
            'equipo': 'Equipo que presenta la falla',
            'critico': '¿Equipo/sistema que presenta la falla es critico?',
            'description': 'Descripción detallada de falla presentada',
            'impact': 'Seleccione las areas afectadas por la falla',
            'causas': 'Describa las causas probable de la falla',
            'suggest_repair': 'Reparación sugerida',
            'evidence': 'Evidencia',
            }
        widgets = {
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}),
            'causas': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}),
            'suggest_repair': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}),
            'evidence': forms.FileInput(attrs={'class': 'form-control'}),
        }


class RutaUpdateOTForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        asset_id = kwargs.pop('asset_id')
        super().__init__(*args, **kwargs)
        self.fields['ot'].queryset = Ot.objects.filter(
            system__asset_id=asset_id)

    class Meta:
        model = Ruta
        fields = ['ot']
