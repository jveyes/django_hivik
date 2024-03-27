from django.shortcuts import render, get_object_or_404, redirect

# Autenticacion de usuario y permisos
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User

# Vistas genericas basadas en clases
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views import generic

# Librerias de django para manejo de las URLS
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy

# Modelos y formularios
from .models import (
    Asset, System, Ot, Task, Equipo, Ruta, HistoryHour, FailureReport
)
from .forms import (
    RescheduleTaskForm, OtForm, ActForm, UpdateTaskForm, SysForm,
    EquipoForm, FinishOtForm, RutaForm, RutActForm, ReportHours,
    ReportHoursAsset,
)


# Librerias auxiliares
from datetime import timedelta, date
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.db.models import Q
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from io import BytesIO
from django.conf import settings
from django.db.models import Count
from django.core.paginator import Paginator


# ----------------------------------- Main views -----------------------------#

# Mis actividades
class AssignedTaskByUserListView(LoginRequiredMixin, generic.ListView):
    '''
    Vista generica basada en clases que muestra las actividades en ejecucion
    cada miembro de serport (v1.0)

    v1.1 se le agrega opciones de filtrado por equipos y personal

    '''
    model = Task
    template_name = 'got/assignedtasks_list_pendient_user.html'
    paginate_by = 16

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        info_filter = Asset.objects.all()
        context['asset'] = info_filter

        asset_id = self.request.GET.get('asset_id')
        if asset_id:
            selected_asset = Asset.objects.get(id=asset_id)
            context['selected_asset_name'] = selected_asset.name

        responsable_id = self.request.GET.get('responsable')
        if responsable_id:
            user = User.objects.get(id=responsable_id)
            context['selected_res'] = f'{user.first_name} {user.last_name}'

        serport_group = Group.objects.get(name='serport_members')
        users_in_group = serport_group.user_set.all()

        context['serport_members'] = users_in_group

        for obj in context['task_list']:
            time = obj.men_time
            obj.final_date = obj.start_date + timedelta(days=time)

        return context

    def get_queryset(self):
        queryset = Task.objects.filter(ot__isnull=False)

        asset_id = self.request.GET.get('asset_id')
        responsable_id = self.request.GET.get('responsable')

        maq_group = Group.objects.get(name='maq_members')
        users_maq = maq_group.user_set.all()

        if asset_id:
            queryset = queryset.filter(ot__system__asset_id=asset_id)
        if responsable_id:
            queryset = queryset.filter(responsible=responsable_id)

        if self.request.user.has_perm("got.can_see_completely"):
            queryset = queryset.filter(finished=False).order_by('start_date')
        elif self.request.user in users_maq:
            queryset = queryset.filter(
                finished=False,
                ot__system__asset__supervisor=self.request.user)
        else:
            queryset = queryset.filter(
                Q(responsible=self.request.user) & Q(finished=False)
                ).order_by('start_date')

        return queryset


# Equipos
class AssetsListView(LoginRequiredMixin, generic.ListView):
    '''
    Vista generica para mostrar el listado de los centros de costos (v1.0)
    '''
    model = Asset

    def get_queryset(self):
        queryset = Asset.objects.all()
        area = self.request.GET.get('area')

        # Verifica si el usuario pertenece al grupo 'buzos_members'
        user_groups = self.request.user.groups.values_list('name', flat=True)

        if 'buzos_members' in user_groups:
            # Si pertenece al grupo 'buzos_members', filtra por área 'b'
            queryset = queryset.filter(area='b')

        if area:
            queryset = queryset.filter(area=area)
        return queryset


# Detalle de equipos y listado de sistemas
class AssetsDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Vista generica para mostrar detalle de activos (v1.0)
    '''
    model = Asset

    # Formulario para crear, modificar o eliminar actividades
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sys_form'] = SysForm()

        systems = self.object.system_set.all()
        paginator = Paginator(systems, 10)  # Muestra 10 sistemas por página

        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj

        asset = self.get_object()
        rutas = sorted(
            Ruta.objects.filter(system__asset=asset),
            key=lambda t: t.next_date
            )

        context['rutas'] = rutas

        return context

    def post(self, request, *args, **kwargs):
        asset = self.get_object()
        sys_form = SysForm(request.POST)

        if sys_form.is_valid():
            sys = sys_form.save(commit=False)
            sys.asset = asset
            sys.save()
            return redirect(request.path)
        else:
            return render(
                request,
                self.template_name,
                {'asset': asset, 'sys_form': sys_form}
                )


class SysDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Vista generica para mostrar componentes (v1.2)
    '''
    model = System

    # Formulario para crear, modificar o eliminar actividades
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipo_form'] = EquipoForm()
        context['task_form'] = RutActForm()
        return context

    def post(self, request, *args, **kwargs):
        sys = self.get_object()
        equipo_form = EquipoForm(request.POST, request.FILES)
        task_form = RutActForm(request.POST)

        if equipo_form.is_valid():
            eq = equipo_form.save(commit=False)
            eq.system = sys
            eq.save()
            return redirect(request.path)
        else:
            context = {
                'system': sys,
                'equipo_form': equipo_form,
                'task_form': task_form
                }
            return render(request, self.template_name, context)


class EquipoDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Vista generica para mostrar Equipos con sus rutinas (v3.0)
    '''
    model = Equipo


# Ordenes de trabajo
class OtListView(LoginRequiredMixin, generic.ListView):
    '''
    Vista generica para listado de ordenes de trabajo (v1.0)
    '''
    model = Ot
    paginate_by = 15

    # Formulario para filtrar Ots según descripción
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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
        context['task_form'] = ActForm()
        context['state_form'] = FinishOtForm()

        # Agregar lógica para determinar el estado global de las tareas
        ot = self.get_object()
        all_tasks_finished = ot.task_set.filter(finished=False).exists()
        context['all_tasks_finished'] = not all_tasks_finished

        return context

    def post(self, request, *args, **kwargs):
        ot = self.get_object()
        task_form = ActForm(request.POST, request.FILES)
        state_form = FinishOtForm(request.POST)

        if 'finish_ot' in request.POST and state_form.is_valid():
            ot.state = 'Finalizado'
            ot.save()

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


# Detalle de actividades
class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Detalle de actividades (v1.0)
    '''
    model = Task


@permission_required('got.can_see_completely')
def RutaListView(request):

    assets = Asset.objects.all()

    area_filter = request.GET.get('area_filter')
    if area_filter:
        ruta = sorted(
            Ruta.objects.filter(system__asset__area=area_filter),
            key=lambda t: t.next_date
            )
    else:
        ruta = sorted(Ruta.objects.all(), key=lambda t: t.next_date)

    context = {'ruta_list': ruta, 'assets': assets, 'area_filter': area_filter}
    return render(request, 'got/ruta_list.html', context)


# Equipos
class FailureListView(LoginRequiredMixin, generic.ListView):
    '''
    Vista generica para mostrar el listado de reportes de falla (v1.5)
    '''
    model = FailureReport
    paginate_by = 15


# Detalle de actividades
class FailureDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Detalle de reportes de falla (v1.0)
    '''
    model = FailureReport

# ------------------------------------- Formularios -------------------------#


@permission_required('got.can_see_completely')
def reschedule_task(request, pk):
    '''
    Vista formulario para reprogramar actividades (v1.0)
    '''
    act = get_object_or_404(Task, pk=pk)

    time = act.men_time
    final_date = act.start_date + timedelta(days=time)

    if request.method == 'POST':
        form = RescheduleTaskForm(request.POST, instance=act)

        if form.is_valid():
            act.start_date = form.cleaned_data['start_date']
            act.news = form.cleaned_data['news']
            act.men_time = form.cleaned_data['men_time']
            act.save()
            return HttpResponseRedirect(reverse('got:my-tasks'))

    else:
        # proposed_reschedule_date = date.today() + timedelta(weeks=1)
        form = RescheduleTaskForm(instance=act)

    context = {'form': form, 'task': act, 'final_date': final_date}
    return render(request, 'got/task_reschedule.html', context)


class OtCreate(CreateView):
    '''
    Vista formulario para crear ordenes de trabajo (v1.0)
    '''
    model = Ot
    form_class = OtForm
    http_method_names = ['get', 'post']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        asset_id = self.kwargs.get('pk')
        asset = Asset.objects.get(pk=asset_id)
        kwargs['asset'] = asset
        return kwargs


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


class OtUpdate(UpdateView):
    '''
    Vista formulario para actualizar ordenes de trabajo (v1.0)
    '''
    model = Ot
    form_class = OtForm
    http_method_names = ['get', 'post']

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


class TaskCreate(CreateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = Task
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


class TaskUpdate(UpdateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = Task
    form_class = ActForm
    template_name = 'got/task_form.html'
    http_method_names = ['get', 'post']


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


class SysDelete(DeleteView):
    '''
    Vista formulario para eliminar actividades
    '''
    model = System

    success_url = reverse_lazy('got:ot-list')

    def get_success_url(self):
        asset_code = self.object.asset.id
        kwargs = {'pk': asset_code}
        success_url = reverse_lazy('got:asset-detail', kwargs)
        return success_url


class EquipoUpdate(UpdateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = Equipo
    form_class = EquipoForm
    template_name = 'got/equipo_form.html'
    http_method_names = ['get', 'post']


class SysUpdate(UpdateView):
    '''
    Vista formulario para actualizar una actividad
    '''
    model = System
    form_class = SysForm


class EquipoDelete(DeleteView):
    '''
    Vista formulario para eliminar actividades
    '''
    model = Equipo

    def get_success_url(self):
        sys_code = self.object.system.id
        success_url = reverse_lazy('got:sys-detail', kwargs={'pk': sys_code})
        return success_url


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


class RutaDelete(DeleteView):
    '''
    Vista formulario para eliminar actividades
    '''
    model = Ruta

    def get_success_url(self):
        sys_code = self.object.system.id
        success_url = reverse_lazy('got:sys-detail', kwargs={'pk': sys_code})
        return success_url


# Reportes
@permission_required('got.can_see_completely')
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


def finish_task(request, pk):
    '''
    Vista formulario para finalizar actividades (v1.1)
    '''
    act = get_object_or_404(Task, pk=pk)

    time = act.men_time
    final_date = act.start_date + timedelta(days=time)

    if request.method == 'POST':
        form = UpdateTaskForm(request.POST, request.FILES)

        if form.is_valid():
            act.news = form.cleaned_data['news']
            act.finished = form.cleaned_data['finished']
            act.save()
            return HttpResponseRedirect(reverse('got:my-tasks'))

    else:
        form = UpdateTaskForm()

    context = {'form': form, 'task': act, 'final_date': final_date}
    return render(request, 'got/task_finish_form.html', context)


@permission_required('got.can_see_completely')
def indicadores(request):

    area_filter = request.GET.get('area', None)

    top_assets = Asset.objects.annotate(
        num_ots=Count('system__ot')).order_by('-num_ots')[:5]
    ots_per_asset = [asset.num_ots for asset in top_assets]
    asset_labels = [asset.name for asset in top_assets]

    labels = ['Preventivo', 'Correctivo', 'Modificativo']

    if area_filter:
        ots = len(Ot.objects.filter(
            creation_date__month=3,
            creation_date__year=2024,
            system__asset__area=area_filter
            ))
        ot_finish = len(Ot.objects.filter(
            creation_date__month=3,
            creation_date__year=2024, state='f',
            system__asset__area=area_filter))
        preventivo = len(Ot.objects.filter(
            creation_date__month=3,
            creation_date__year=2024,
            tipo_mtto='p',
            system__asset__area=area_filter
            ))
        correctivo = len(Ot.objects.filter(
            creation_date__month=3,
            creation_date__year=2024,
            tipo_mtto='c',
            system__asset__area=area_filter
            ))
        modificativo = len(Ot.objects.filter(
            creation_date__month=3,
            creation_date__year=2024,
            tipo_mtto='m',
            system__asset__area=area_filter
            ))

    else:
        ots = len(Ot.objects.filter(
            creation_date__month=3, creation_date__year=2024))
        ot_finish = len(Ot.objects.filter(
            creation_date__month=3, creation_date__year=2024, state='f'))
        preventivo = len(Ot.objects.filter(
            creation_date__month=3, creation_date__year=2024, tipo_mtto='p'))
        correctivo = len(Ot.objects.filter(
            creation_date__month=3, creation_date__year=2024, tipo_mtto='c'))
        modificativo = len(Ot.objects.filter(
            creation_date__month=3, creation_date__year=2024, tipo_mtto='m'))

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


@permission_required('got.can_see_completely')
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

    # Copiar las Task de la Ruta a la nueva OT
    for task in ruta.task_set.all():
        Task.objects.create(
            ot=nueva_ot,
            responsible=task.responsible,
            description=task.description,
            procedimiento=task.procedimiento,
            hse=task.hse,
            suministros=task.suministros,
            news=task.news,
            evidence=task.evidence,
            start_date=date.today(),
            men_time=1,
            finished=False,  # Suponiendo que quieres que estén abiertas
        )

    # Actualizar el campo OT de la Ruta con la nueva OT
    ruta.ot = nueva_ot
    ruta.save()

    # Redirige a la vista de detalle de la nueva OT
    return redirect('got:ot-detail', pk=nueva_ot.pk)
