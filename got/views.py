# ---------------------------- Librerias de Django -------------------------- #
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views import generic
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.db.models import Count, Q
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.paginator import Paginator
from django.utils import timezone
# from django.contrib import messages

# ---------------------------- Modelos y formularios ------------------------ #
from .models import (
    Asset, System, Ot, Task, Equipo, Ruta, HistoryHour, FailureReport, HistoricalSystem
)
from .forms import (
    RescheduleTaskForm, OtForm, ActForm, FinishTask, SysForm,
    EquipoForm, FinishOtForm, RutaForm, RutActForm, ReportHours,
    ReportHoursAsset, failureForm, RutaUpdateOTForm, EquipoFormUpdate,
    OtFormNoSup, ActFormNoSup
)

# ---------------------------- Librerias auxiliares ------------------------- #
from datetime import timedelta, date
from xhtml2pdf import pisa
from io import BytesIO


# ---------------------------- Main views ------------------------------------#
# ---------------------------- Mis actividades ------------------------------ #
class AssignedTaskByUserListView(LoginRequiredMixin, generic.ListView):

    '''
    Vista 1: consulta para listado de actividades pendientes y enlace directo a
    cada actividad.

    - Supervisores --> listado de actividades pendientes de todos los activos.
                        Boton filtrado por activo.
                        Boton filtrado por responsables
                        Boton para reprogramar.

    - Talleres --> listado de actividades pendientes propias.
                    Boton filtrar por activo.
    
    - Buzos --> Listado de actividades pendientes de sus activos.
                Boton para filtrar por activo.
                Boton para reprogramar.

    - Maquinistas --> Listado de actividades pendientes de su embarcación.
                      Boton para filtrar por responsable. 
                    
    '''

    model = Task
    template_name = 'got/assignedtasks_list_pendient.html'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = self.request.user
        all_users = User.objects.none()

        if current_user.groups.filter(name='super_members').exists():
            all_users = User.objects.all()
        elif current_user.groups.filter(name__in=['maq_members', 'buzos_members']).exists():
            talleres = Group.objects.get(name='serport_members')
            taller_list = list(talleres.user_set.all())
            taller_list.append(current_user)
            all_users = User.objects.filter(id__in=[user.id for user in taller_list])

        asset_id = self.request.GET.get('asset_id')
        worker_id = self.request.GET.get('worker')
        # contexto adicional:
        context['asset'] = Asset.objects.all()
        context['serport_members'] = all_users
        if asset_id:  # Nombre assets para filtrar
            context['selected_asset_name'] = Asset.objects.get(id=asset_id)
            context['asset_id'] = asset_id
        if worker_id:  # Nombre usuarios para filtrar
            worker = User.objects.get(id=worker_id)
            context['worker'] = f'{worker.first_name} {worker.last_name}'
            context['worker_id'] = worker_id

        return context

    def get_queryset(self):
        queryset = Task.objects.filter(ot__isnull=False, start_date__isnull=False)
        current_user = self.request.user

        asset_id = self.request.GET.get('asset_id')
        responsable_id = self.request.GET.get('worker')

        maq_group = Group.objects.get(name='maq_members')
        buzos_group = Group.objects.get(name='buzos_members')
        users_maq = maq_group.user_set.all()
        users_buzos = buzos_group.user_set.all()
        
        # Filtrar actividades por activo y/o usuario.
        if asset_id:
            queryset = queryset.filter(ot__system__asset_id=asset_id)
        if responsable_id:
            queryset = queryset.filter(responsible=responsable_id)

        # Para filtrar actividades para usuarios supervisores.
        if current_user.has_perm("got.can_see_completely"):
            queryset = queryset.filter(finished=False).order_by('start_date')

        # Para filtrar actividades usuarios maquinistas.
        elif current_user in users_maq:
            queryset = queryset.filter(finished=False, ot__system__asset__supervisor=current_user)

        # Para filtrar actividades usuarios buzos.
        elif current_user in users_buzos:
            if current_user.groups.filter(name='santamarta_station').exists():
                queryset = queryset.filter(finished=False, ot__system__asset__area='b', ot__system__location='Santa Marta')
            elif current_user.groups.filter(name='ctg_station').exists():
                queryset = queryset.filter(finished=False, ot__system__asset__area='b', ot__system__location='Cartagena')
            elif current_user.groups.filter(name='guyana_station').exists():
                queryset = queryset.filter(finished=False, ot__system__asset__area='b', ot__system__location='Guyana')
            else:
                queryset = queryset.filter(finished=False, ot__system__asset__area='b')

        # talleres.
        else:
            queryset = queryset.filter(Q(responsible=self.request.user) & Q(finished=False)).order_by('start_date')

        return queryset


class Reschedule_task(UpdateView):

    '''
    Funcionalidad para reprogramar actividades.
    Supervisores, buzos y maquinistas.
    '''

    model = Task
    form_class = RescheduleTaskForm
    template_name = 'got/task_reschedule.html'
    success_url = reverse_lazy('got:my-tasks')

    def form_valid(self, form):
        return super().form_valid(form)
    

class Finish_task(UpdateView):

    '''
    Funcionalidad para reprogramar actividades
    '''

    model = Task
    form_class = FinishTask
    template_name = 'got/task_finish_form.html'
    http_method_names = ['get', 'post']
    success_url = reverse_lazy('got:my-tasks')

    def form_valid(self, form):
        return super().form_valid(form)


# ---------------------------- Activos (Assets) ---------------------------- #
class AssetsListView(LoginRequiredMixin, generic.ListView):

    '''
    Vista 2: consulta del listado de activos(Assets) de cada area (barcos,
    buceo, oceanografía, vehiculos, locativo y apoyo).

    - Supervisores tendran acceso al listado completo de cada area.

    - Grupo de buzos tendra acceso solo a los equipo de buceo.

    - Maquinistas/talleres no tendran acceso a esta vista.
    '''

    model = Asset
    paginate_by = 15

    def get_queryset(self):
        queryset = Asset.objects.all()

        area = self.request.GET.get('area')
        user_groups = self.request.user.groups.values_list('name', flat=True)

        if 'buzos_members' in user_groups:
            queryset = queryset.filter(area='b')
        if area:
            queryset = queryset.filter(area=area)

        return queryset


# Detalle assets y listado de sistemas
class AssetDetailView(LoginRequiredMixin, generic.DetailView):

    '''
    Información de activo y relaciones con sus sistemas y sus rutinas.

    - template name: asset_detail.html

    - Supervisores:
        Crear nueva OT.
        Crear/editar/eliminar sistema.
        Reporte total de horas.
        Reportar fallas.

    - Maquinistas y buzos:
        Reporte total de horas.
        Reportar fallas.
    '''

    model = Asset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.get_object()

        rotativos = Equipo.objects.filter(
            system__asset=asset, tipo='r').exists()

        # Filtrar sistemas basado en el grupo de usuario
        if self.request.user.groups.filter(name='santamarta_station').exists():
            systems = asset.system_set.filter(location='Santa Marta')
            sys = asset.system_set.filter(location='Santa Marta').exclude(state='x')
        elif self.request.user.groups.filter(name='ctg_station').exists():
            systems = asset.system_set.filter(location='Cartagena')
            sys = asset.system_set.filter(location='Cartagena').exclude(state='x')
        elif self.request.user.groups.filter(name='guyana_station').exists():
            systems = asset.system_set.filter(location='Guyana')
            sys = asset.system_set.filter(location='Guyana').exclude(state='x')
        else:
            systems = asset.system_set.all()
            sys = asset.system_set.exclude(state='x')

        rutas = sorted(Ruta.objects.filter(system__in=sys), key=lambda t: t.next_date)
        # Limitar a mostrar 10 sistemas
        paginator = Paginator(systems, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        paginator_rutas = Paginator(rutas, 20)
        page_number_rutas = self.request.GET.get('page_rutas')
        page_obj_rutas = paginator_rutas.get_page(page_number_rutas)

        context['sys_form'] = SysForm()
        context['page_obj'] = page_obj
        context['page_obj_rutas'] = page_obj_rutas
        context['rotativos'] = rotativos

        return context

    def post(self, request, *args, **kwargs):
        asset = self.get_object()
        sys_form = SysForm(request.POST)
        # Formulario para crear nuevo sistema
        if sys_form.is_valid():
            sys = sys_form.save(commit=False)
            sys.asset = asset
            sys.save()
            return redirect(request.path)
        else:
            context = {'asset': asset, 'sys_form': sys_form}
            return render(request, self.template_name, context)


# ---------------------------- Systems -------------------------------------- #
class SysDetailView(LoginRequiredMixin, generic.DetailView):

    '''
    Información de consulta para listado de equipos detallado de cada sistema
    creado.

    - Supervisores:
        Crear/editar/eliminar componente.
        Reporte de horas de equipos rotativos.

    - Maquinistas y buzos:
        Reporte de horas de equipos rotativos.
    '''

    model = System

    # Formulario para crear, modificar o eliminar actividades
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['equipo_form'] = EquipoForm()
    #     return context

    # def post(self, request, *args, **kwargs):
    #     sys = self.get_object()
    #     equipo_form = EquipoForm(request.POST, request.FILES)

    #     if equipo_form.is_valid():
    #         eq = equipo_form.save(commit=False)
    #         eq.system = sys
    #         eq.save()
    #         return redirect(request.path)
    #     else:
    #         context = {
    #             'system': sys,
    #             'equipo_form': equipo_form,
    #             }
    #         return render(request, "got/system_detail.html", context)


class SysDelete(DeleteView):
    '''
    Vista formulario para eliminar sistemas
    '''
    model = System

    def get_success_url(self):
        asset_code = self.object.asset.id
        success_url = reverse_lazy(
            'got:asset-detail', kwargs={'pk': asset_code})
        return str(success_url)


class SysUpdate(UpdateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = System
    form_class = SysForm

# ---------------------------- Equipos ---------------------------- #

class EquipoCreateView(CreateView):
    model = Equipo
    form_class = EquipoForm
    template_name = 'got/equipo_form.html'

    def form_valid(self, form):
        form.instance.system = System.objects.get(pk=self.kwargs['pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('got:sys-detail', kwargs={'pk': self.object.system.pk})

class EquipoUpdate(UpdateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = Equipo
    form_class = EquipoFormUpdate
    template_name = 'got/equipo_form.html'
    http_method_names = ['get', 'post']


class EquipoDelete(DeleteView):
    '''
    Vista formulario para eliminar actividades
    '''
    model = Equipo

    def get_success_url(self):
        sys_code = self.object.system.id
        success_url = reverse_lazy('got:sys-detail', kwargs={'pk': sys_code})
        return success_url

# ---------------------------- Failure Report ---------------------------- #

class FailureListView(LoginRequiredMixin, generic.ListView):

    '''
    Información de activo y relaciones con sus sistemas y sus rutinas.

    - template name: asset_detail.html

    - Supervisores:
        Crear nueva OT.
        Crear/editar/eliminar sistema.
        Reporte total de horas.
        Reportar fallas.

    - Maquinistas y buzos:
        Reporte total de horas.
        Reportar fallas.
    '''

    model = FailureReport
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()

        # Comprueba si el usuario es parte del grupo 'maq_members'
        if self.request.user.groups.filter(name='maq_members').exists():
            # Obtén el/los asset(s) supervisado(s) por el usuario
            supervised_assets = Asset.objects.filter(
                supervisor=self.request.user)

            queryset = queryset.filter(
                equipo__system__asset__in=supervised_assets)
        elif self.request.user.groups.filter(name='buzos_members').exists():
            # Obtén el/los asset(s) supervisado(s) por el usuario
            supervised_assets = Asset.objects.filter(
                area='b')

            queryset = queryset.filter(
                equipo__system__asset__in=supervised_assets)

        return queryset


class FailureReportForm(LoginRequiredMixin, CreateView):

    '''
    Formulario para reportar fallas en los equipos de activo.
    '''

    model = FailureReport
    form_class = failureForm
    http_method_names = ['get', 'post']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset_id = self.kwargs.get('asset_id')
        asset = get_object_or_404(Asset, pk=asset_id)
        context['asset_main'] = asset
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        asset_id = self.kwargs.get('asset_id')
        asset = get_object_or_404(Asset, pk=asset_id)
        form.fields['equipo'].queryset = Equipo.objects.filter(
            system__asset=asset
        )
        return form

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        self.object = form.save()  # Guarda el objeto y lo mantiene en self.object

        # Preparar el contexto para la plantilla de correo
        context = {
            'reporter': self.object.reporter,
            'moment': self.object.moment,
            'equipo': self.object.equipo,
            'description': self.object.description,
            'causas': self.object.causas,
            'suggest_repair': self.object.suggest_repair,
            'impact': self.object.impact,
            'critico': self.object.critico,
            'report_url': self.request.build_absolute_uri(self.object.get_absolute_url()),
        }

        # Renderizar la plantilla de correo
        email_body = render_to_string('got/failure_report_email.txt', context)

        # Obtener correos de super miembros
        super_members_group = Group.objects.get(name='super_members')
        super_members_emails = super_members_group.user_set.values_list('email', flat=True)

        # Preparar y enviar el correo
        email = EmailMessage(
            subject='Nuevo Reporte de Falla',
            body=email_body,
            from_email=settings.EMAIL_HOST_USER,
            to=list(super_members_emails),
        )

        # Adjuntar imagen de evidencia si está presente
        if self.object.evidence:
            email.attach_file(self.object.evidence.path)

        email.send()

        return super(FailureReportForm, self).form_valid(form)



class FailureDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Detalle de reportes de falla (v1.0)
    '''
    model = FailureReport


class FailureReportUpdate(LoginRequiredMixin, UpdateView):

    '''
    Formulario para reportar fallas en los equipos de activo.
    '''

    model = FailureReport
    form_class = failureForm
    http_method_names = ['get', 'post']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.get_object().equipo.system.asset
        context['asset_main'] = asset
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        asset = self.get_object().equipo.system.asset
        form.fields['equipo'].queryset = Equipo.objects.filter(
            system__asset=asset)
        return form

    def form_valid(self, form):
        return super().form_valid(form)


@permission_required('got.can_see_completely')
def crear_ot_failure_report(request, fail_id):
    fail = get_object_or_404(FailureReport, pk=fail_id)
    nueva_ot = Ot(
        description=f"Mantenimiento por reporte de falla #{fail.id}",
        state='x',  # Ejecución
        super=request.user,
        tipo_mtto='c',
        system=fail.equipo.system,
    )
    nueva_ot.save()

    # Actualizar el campo OT de la Ruta con la nueva OT
    fail.related_ot = nueva_ot
    fail.save()

    # Redirige a la vista de detalle de la nueva OT
    return redirect('got:ot-detail', pk=nueva_ot.pk)


# --------------------------- Ordenes de trabajo --------------------------- #
class OtListView(LoginRequiredMixin, generic.ListView):
    '''
    Vista generica para listado de ordenes de trabajo (v1.0)
    '''
    model = Ot
    paginate_by = 15

    # Formulario para filtrar Ots según descripción
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.groups.filter(name='buzos_members').exists():
            # Limitar a los asset que tienen en área el valor de 'b'
            info_filter = Asset.objects.filter(area='b')
        else:
            # Todos los asset para usuarios que no son parte de buzos_members
            info_filter = Asset.objects.all()
        context['asset'] = info_filter

        super_group = Group.objects.get(name='super_members')
        users_in_group = super_group.user_set.all()
        context['super_members'] = users_in_group

        return context

    def get_queryset(self):
        queryset = Ot.objects.all()
        state = self.request.GET.get('state')
        asset_id = self.request.GET.get('asset_id')
        responsable_id = self.request.GET.get('responsable')
        keyword = self.request.GET.get('keyword')

        if self.request.user.groups.filter(name='maq_members').exists():
            # Obtén el/los asset(s) supervisado(s) por el usuario
            supervised_assets = Asset.objects.filter(
                supervisor=self.request.user)
            queryset = queryset.filter(system__asset__in=supervised_assets)
        elif self.request.user.groups.filter(name='buzos_members').exists():
            # Obtén el/los asset(s) supervisado(s) por el usuario
            supervised_assets = Asset.objects.filter(
                area='b')

            # Filtra los reportes de falla cuyos equipos pertenecen a un
            # sistema que a su vez pertenece a un asset supervisado por
            # el usuario
            queryset = queryset.filter(system__asset__in=supervised_assets)

        if state:
            queryset = queryset.filter(state=state)

        if keyword:
            queryset = Ot.objects.filter(description__icontains=keyword)
            return queryset

        if asset_id:
            queryset = queryset.filter(system__asset_id=asset_id)
        if responsable_id:
            queryset = queryset.filter(super=responsable_id)

        return queryset


# Detalle de orden de trabajo - generalidades, listado de actividades y reporte
class OtDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Detalle de ordenes de trabajo (v1.0)
    '''
    model = Ot

    # Formulario para crear, modificar o eliminar actividades
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.groups.filter(name='super_members').exists():
            context['task_form'] = ActForm()
        else:
            context['task_form'] = ActFormNoSup()
        context['state_form'] = FinishOtForm()

        # Agregar lógica para determinar el estado global de las tareas
        ot = self.get_object()
        all_tasks_finished = ot.task_set.filter(finished=False).exists()
        context['all_tasks_finished'] = not all_tasks_finished

        try:
            failure_report = ot.failure_report
        except FailureReport.DoesNotExist:
            failure_report = None

        context['failure_report'] = failure_report

        try:
            ruta_asociada = ot.ruta_set.first()  # Asume que hay una relación inversa llamada 'ruta_set'
        except AttributeError:
            ruta_asociada = None

        # Si hay una ruta asociada, agregar su ID al contexto
        if ruta_asociada:
            context['ruta_id'] = ruta_asociada
        else:
            context['ruta_id'] = None

        return context

    def actualizar_rutas_dependientes(self, ruta):
        ruta.intervention_date = timezone.now()
        ruta.save()
        if ruta.dependencia is not None:
            self.actualizar_rutas_dependientes(ruta.dependencia)

    def post(self, request, *args, **kwargs):
        ot = self.get_object()
        if request.user.groups.filter(name='super_members').exists():
            task_form = ActForm(request.POST, request.FILES)
        else:
            task_form = ActFormNoSup(request.POST, request.FILES)

        state_form = FinishOtForm(request.POST)

        if 'finish_ot' in request.POST and state_form.is_valid():
            ot.state = 'f'
            ot.save()

            rutas_relacionadas = Ruta.objects.filter(ot=ot)
            for ruta in rutas_relacionadas:
                self.actualizar_rutas_dependientes(ruta)

            # Verificar y cerrar el reporte de falla relacionado, si existe
            if hasattr(ot, 'failure_report'):
                ot.failure_report.closed = True
                ot.failure_report.save()

            supervisor = ot.system.asset.supervisor
            if supervisor and supervisor.email:
                supervisor_email = supervisor.email

                # Enviar correo electrónico al finalizar la OT
                subject = f'Orden de Trabajo {ot.num_ot} Finalizada'
                message = render_to_string(
                    'got/ot_finished_email.txt', {'ot': ot}
                    )
                from_email = settings.EMAIL_HOST_USER
                to_email = supervisor_email

                email = EmailMessage(
                    subject, message, from_email, [to_email]
                    )

                # Adjuntar el PDF al correo
                pdf_content_dynamic = self.generate_pdf_content(ot)
                pdf_filename_dynamic = f'OT_{ot.num_ot}_Detalle.pdf'
                email.attach(
                    pdf_filename_dynamic,
                    pdf_content_dynamic,
                    'application/pdf'
                    )

                # Adjuntar el PDF almacenado en el campo info_contratista_pdf
                if ot.info_contratista_pdf:
                    pdf_filename_stored = f'OT_{ot.num_ot}_Contratista.pdf'
                    email.attach(
                        pdf_filename_stored,
                        ot.info_contratista_pdf.read(),
                        'application/pdf'
                        )

                email.send()

            return redirect(ot.get_absolute_url())

        elif 'submit_task' in request.POST and task_form.is_valid():
            act = task_form.save(commit=False)
            act.ot = ot
            if isinstance(task_form, ActFormNoSup):
                act.responsible = request.user
            act.save()
            return redirect(act.get_absolute_url())

        context = {'ot': ot, 'task_form': task_form, 'state_form': state_form}

        return render(request, self.template_name, context)

    def generate_pdf_content(self, ot):
        '''
        Función para generar el contenido del PDF
        '''
        template_path = 'got/pdf_template.html'
        context = {'ot': ot}
        template = get_template(template_path)
        html = template.render(context)
        pdf_content = BytesIO()

        pisa.CreatePDF(html, dest=pdf_content)

        return pdf_content.getvalue()


class OtCreate(CreateView):
    '''
    Vista formulario para crear ordenes de trabajo (v1.0)
    '''
    model = Ot
    http_method_names = ['get', 'post']

    def get_form_class(self):
        if self.request.user.groups.filter(name='super_members').exists():
            return OtForm
        else:
            return OtFormNoSup

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        asset_id = self.kwargs.get('pk')
        asset = Asset.objects.get(pk=asset_id)
        kwargs['asset'] = asset
        return kwargs

    def form_valid(self, form):
        ot = form.save(commit=False)
        if isinstance(form, OtFormNoSup):
            ot.super = self.request.user
        ot.save()
        return redirect('got:ot-detail', pk=ot.pk)


class OtUpdate(UpdateView):
    '''
    Vista formulario para actualizar ordenes de trabajo (v1.0)
    '''
    model = Ot
    http_method_names = ['get', 'post']

    def get_form_class(self):
        if self.request.user.groups.filter(name='super_members').exists():
            return OtForm
        else:
            return OtFormNoSup

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Obtener la instancia actual de la orden de trabajo
        ot_instance = self.get_object()
        kwargs['asset'] = ot_instance.system.asset
        return kwargs


class OtDelete(DeleteView):
    '''
    Vista formulario para confirmar eliminacion de ordenes de trabajo (v1.0)
    '''
    model = Ot
    success_url = reverse_lazy('got:ot-list')


# --------------------------- Actividades --------------------------- #
class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Detalle de actividades (v1.0)
    '''
    model = Task


class TaskUpdate(UpdateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = Task
    template_name = 'got/task_form.html'
    http_method_names = ['get', 'post']

    def get_form_class(self):
        if self.request.user.groups.filter(name='super_members').exists():
            return ActForm
        else:
            return ActFormNoSup


# Para rutinas
class TaskCreate(CreateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = Task
    http_method_names = ['get', 'post']
    form_class = RutActForm

    def form_valid(self, form):
        # Obtener el valor del parámetro pk desde la URL
        pk = self.kwargs['pk']

        # Obtener el objeto System relacionado con el pk
        ruta = get_object_or_404(Ruta, pk=pk)

        # Establecer el valor del campo system en el formulario
        form.instance.ruta = ruta
        form.instance.finished = False

        # Llamar al método form_valid de la clase base
        return super().form_valid(form)

    def get_success_url(self):
        task = self.object
        # Redirigir a la vista de detalle del objeto recién creado
        return reverse('got:sys-detail', args=[task.ruta.system.id])


class TaskDelete(DeleteView):
    '''
    Vista formulario para eliminar actividades
    '''
    model = Task
    success_url = reverse_lazy('got:ot-list')


class TaskUpdaterut(UpdateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = Task
    form_class = RutActForm
    template_name = 'got/task_form.html'
    http_method_names = ['get', 'post']

    def get_success_url(self):
        # Obtén el ID del sistema al que pertenece la tarea eliminada
        sys_id = self.object.ruta.system.id
        # Retorna la URL de detalle del sistema con el ID correspondiente
        return reverse_lazy('got:sys-detail', kwargs={'pk': sys_id})


class TaskDeleterut(DeleteView):
    '''
    Vista formulario para eliminar actividades
    '''
    model = Task

    def get_success_url(self):
        # Obtén el ID del sistema al que pertenece la tarea eliminada
        sys_id = self.object.ruta.system.id
        # Retorna la URL de detalle del sistema con el ID correspondiente
        return reverse_lazy('got:sys-detail', kwargs={'pk': sys_id})

    def get(self, request, *args, **kwargs):
        context = {'task': self.get_object()}
        return render(request, 'got/task_confirm_delete.html', context)


# --------------------------- Rutinas --------------------------- #
class RutaListView(LoginRequiredMixin, generic.ListView):
    model = Ruta
    paginate_by = 15
    template_name = 'got/ruta_list.html'
    context_object_name = 'ruta_list'

    def get_queryset(self):

        area_filter = self.request.GET.get('area_filter')
        if area_filter:
            queryset = sorted(Ruta.objects.filter(system__asset__area=area_filter).exclude(system__state='x'), key=lambda t: t.next_date)
        else:
            queryset = sorted(Ruta.objects.exclude(system__state='x'), key=lambda t: t.next_date)
        return queryset

    def get_context_data(self, **kwargs):
        """
        Agrega assets y area_filter al contexto.
        """
        context = super(RutaListView, self).get_context_data(**kwargs)
        context['assets'] = Asset.objects.all()
        context['area_filter'] = self.request.GET.get('area_filter')
        return context


class RutaCreate(CreateView):
    '''
    Vista formulario para crear ordenes de trabajo (v1.0)
    '''
    model = Ruta
    form_class = RutaForm

    def form_valid(self, form):
        # Obtener el valor del parámetro pk desde la URL
        pk = self.kwargs['pk']

        # Obtener el objeto System relacionado con el pk
        system = get_object_or_404(System, pk=pk)

        # Establecer el valor del campo system en el formulario
        form.instance.system = system

        # Llamar al método form_valid de la clase base
        return super().form_valid(form)

    def get_success_url(self):
        ruta = self.object
        # Redirigir a la vista de detalle del objeto recién creado
        return reverse('got:sys-detail', args=[ruta.system.id])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['system'] = System.objects.get(pk=self.kwargs['pk'])
        return kwargs


class RutaUpdate(UpdateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = Ruta
    form_class = RutaForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['system'] = self.object.system
        return kwargs


class RutaUpdateOT(UpdateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = Ruta
    form_class = RutaUpdateOTForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Obtener la instancia actual de la orden de trabajo
        instance = self.get_object()
        kwargs['asset'] = instance.system.asset
        return kwargs


class RutaDelete(DeleteView):
    '''
    Vista formulario para eliminar actividades
    '''
    model = Ruta

    def get_success_url(self):
        sys_code = self.object.system.id
        success_url = reverse_lazy('got:sys-detail', kwargs={'pk': sys_code})
        return success_url


@login_required
def crear_ot_desde_ruta(request, ruta_id):
    ruta = get_object_or_404(Ruta, pk=ruta_id)
    nueva_ot = Ot(
        description=f"Rutina de mantenimiento con código {ruta.name}",
        state='x',  # Ejecución
        super=request.user,
        tipo_mtto='p',
        system=ruta.system,
    )
    nueva_ot.save()

    def copiar_tasks_y_actualizar_ot(ruta, ot):
        for task in ruta.task_set.all():
            Task.objects.create(
                ot=ot,
                responsible=task.responsible,
                description=task.description,
                procedimiento=task.procedimiento,
                hse=task.hse,
                suministros=task.suministros,
                news=task.news,
                evidence=task.evidence,
                start_date=timezone.now().date(),
                men_time=1,
                finished=False,
            )

        ruta.ot = ot
        ruta.save()

        # Llamada recursiva para rutas dependientes
        if ruta.dependencia:
            copiar_tasks_y_actualizar_ot(ruta.dependencia, ot)

    # Llamar a la función auxiliar con la ruta inicial y la OT recién creada
    copiar_tasks_y_actualizar_ot(ruta, nueva_ot)
    return redirect('got:ot-detail', pk=nueva_ot.pk)

# Reportes
def report_pdf(request, num_ot):
    '''
    Funcion para crear reportes pdf
    '''
    ot_info = Ot.objects.get(num_ot=num_ot)
    template_path = 'got/pdf_template.html'
    context = {'ot': ot_info}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="orden_de_trabajo.pdf'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@login_required
def indicadores(request):

    m = 4

    area_filter = request.GET.get('area', None)

    # top_assets = Asset.objects.annotate(num_ots=Count('system__ot')).order_by('-num_ots')[:5]
    assets = Asset.objects.annotate(num_ots=Count('system__ot'))
    if area_filter:
        assets = assets.filter(area=area_filter)
    top_assets = assets.order_by('-num_ots')[:5]
    ots_per_asset = [asset.num_ots for asset in top_assets]
    asset_labels = [asset.name for asset in top_assets]

    labels = ['Preventivo', 'Correctivo', 'Modificativo']

    if area_filter:
        ots = len(Ot.objects.filter(
            creation_date__month=m,
            creation_date__year=2024,
            system__asset__area=area_filter
            ))

        ot_finish = len(Ot.objects.filter(
            creation_date__month=m,
            creation_date__year=2024, state='Finalizado',
            system__asset__area=area_filter))

        preventivo = len(Ot.objects.filter(
            creation_date__month=m,
            creation_date__year=2024,
            tipo_mtto='p',
            system__asset__area=area_filter
            ))
        correctivo = len(Ot.objects.filter(
            creation_date__month=m,
            creation_date__year=2024,
            tipo_mtto='c',
            system__asset__area=area_filter
            ))
        modificativo = len(Ot.objects.filter(
            creation_date__month=m,
            creation_date__year=2024,
            tipo_mtto='m',
            system__asset__area=area_filter
            ))

    else:
        ots = len(Ot.objects.filter(
            creation_date__month=m, creation_date__year=2024))
        ot_finish = len(Ot.objects.filter(
            creation_date__month=m, creation_date__year=2024, state='f'))

        preventivo = len(Ot.objects.filter(
            creation_date__month=m, creation_date__year=2024, tipo_mtto='p'))
        correctivo = len(Ot.objects.filter(
            creation_date__month=m, creation_date__year=2024, tipo_mtto='c'))
        modificativo = len(Ot.objects.filter(
            creation_date__month=m, creation_date__year=2024, tipo_mtto='m'))

    if ots == 0:
        ind_cumplimiento = 0
        data = 0
    else:
        ind_cumplimiento = round((ot_finish/ots)*100, 2)
        data = [
            round((preventivo/ots)*100, 2), round((correctivo/ots)*100, 2),
            round((modificativo/ots)*100, 2)
            ]

    context = {
        'ind_cumplimiento': ind_cumplimiento,
        'data': data,
        'labels': labels,
        'ots': ots,
        'ots_asset': ots_per_asset,
        'asset_labels': asset_labels,
        'ots_finished': ot_finish,
    }
    return render(request, 'got/indicadores.html', context)


# reporte de horas
@login_required
def reporthours(request, component):

    hours = HistoryHour.objects.filter(component=component)[:30]
    equipo = get_object_or_404(Equipo, pk=component)

    if request.method == 'POST':
        # Si se envió el formulario, procesarlo
        form = ReportHours(request.POST)
        if form.is_valid():
            # Guardar el formulario si es válido
            instance = form.save(commit=False)
            instance.component = equipo
            instance.reporter = request.user
            instance.save()
            return redirect(request.path)
    else:
        # Si es una solicitud GET, mostrar el formulario vacío
        form = ReportHours()

    context = {
        'form': form,
        'horas': hours,
        'component': equipo
    }

    return render(request, 'got/hours.html', context)


@login_required
def reportHoursAsset(request, asset_id):

    asset = get_object_or_404(Asset, pk=asset_id)

    if request.method == 'POST':
        # Si se envió el formulario, procesarlo
        form = ReportHoursAsset(request.POST, asset=asset)
        if form.is_valid():
            # Guardar el formulario si es válido
            instance = form.save(commit=False)
            instance.reporter = request.user
            instance.save()
            return redirect(request.path)
    else:
        form = ReportHoursAsset(asset=asset)

    hours = HistoryHour.objects.filter(component__system__asset=asset)[:30]

    context = {
        'form': form,
        'horas': hours,
        'asset': asset,
    }

    return render(request, 'got/hours_asset.html', context)


class HistorialCambiosView(generic.TemplateView):
    template_name = 'got/historial_cambios.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modelo1'] = FailureReport.history.all()
        context['modelo2'] = Ot.history.all()
        context['modelo3'] = Ruta.history.all()
        context['modelo4'] = Task.history.all()
        context['modelo5'] = System.history.all()
        # Agrega tantos contextos como modelos tengas
        return context


class BitacoraView(generic.TemplateView):
    template_name = 'got/bitacora.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset_id = self.kwargs.get('asset_id')
        asset = get_object_or_404(Asset, pk=asset_id)
        
        ots = Ot.objects.filter(system__asset=asset).order_by('-creation_date')
        
        # Fetching all historical records for systems related to this asset
        # history_items = HistoricalSystem.objects.filter(asset_id=asset_id, history_change_reason__contains="location change")
        history_items = System.history.filter(asset_id=asset_id, history_change_reason__contains="location change")


        # Combining and sorting all items for display
        combined_items = list(ots) + list(history_items)
        combined_items.sort(key=lambda x: x.history_date if hasattr(x, 'history_date') else x.creation_date, reverse=True)

        context['combined_items'] = combined_items
        context['asset'] = asset
        return context