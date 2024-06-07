# ---------------------------- Librerias de Django -------------------------- #
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.db.models import Count, Q, Min, OuterRef, Subquery, F, ExpressionWrapper, DateField
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views import View


# ---------------------------- Modelos y formularios ------------------------ #
from .models import (
    Asset, System, Ot, Task, Equipo, Ruta, HistoryHour, FailureReport, Image, Operation, Location, Document,
    Megger, Solicitud, Suministro, Item
)
from .forms import (
    RescheduleTaskForm, OtForm, ActForm, FinishTask, SysForm, EquipoForm, FinishOtForm, RutaForm, RutActForm, ReportHours,
    ReportHoursAsset, failureForm,EquipoFormUpdate, OtFormNoSup, ActFormNoSup, UploadImages, OperationForm, LocationForm,
    DocumentForm, SolicitudForm, SuministroFormset
)

# ---------------------------- Librerias auxiliares ------------------------- #
from datetime import timedelta, date
from xhtml2pdf import pisa
from io import BytesIO
import itertools
from django.db.models import ExpressionWrapper, F, DateField, DurationField
from django.db.models.functions import ExtractMonth, ExtractYear
from datetime import datetime


# ---------------------------- Main views ------------------------------------#
# ---------------------------- Mis actividades ------------------------------ #
class AssignedTaskByUserListView(LoginRequiredMixin, generic.ListView):

    model = Task
    template_name = 'got/assignedtasks_list_pendient.html'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        current_user = request.user
        if current_user.groups.filter(name='gerencia').exists():
            return redirect('got:operation-list')

        return super().dispatch(request, *args, **kwargs)

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
        context['assets'] = Asset.objects.all()
        context['serport_members'] = all_users
        if asset_id:  # Nombre assets para filtrar
            context['selected_asset_name'] = Asset.objects.get(abbreviation=asset_id)
            context['asset_id'] = asset_id
        if worker_id:  # Nombre usuarios para filtrar
            worker = User.objects.get(id=worker_id)
            context['worker'] = f'{worker.first_name} {worker.last_name}'
            context['worker_id'] = worker_id

        context['solicitud_form'] = SolicitudForm()
        context['suministro_formset'] = SuministroFormset(queryset=Suministro.objects.none())
        context['all_items'] = Item.objects.all()

        return context
    
    def post(self, request, *args, **kwargs):
        solicitud_form = SolicitudForm(request.POST)
        suministro_formset = SuministroFormset(request.POST)
        if solicitud_form.is_valid() and suministro_formset.is_valid():
            solicitud = solicitud_form.save(commit=False)
            solicitud.solicitante = request.user
            solicitud.save()
            suministro_formset.instance = solicitud
            suministro_formset.save()
            return redirect('got:my-tasks')
        return self.get(request, *args, **kwargs)


    def get_queryset(self):
        queryset = Task.objects.filter(ot__isnull=False, start_date__isnull=False)
        current_user = self.request.user

        asset_id = self.request.GET.get('asset_id')
        responsable_id = self.request.GET.get('worker')

        maq_group = Group.objects.get(name='maq_members')
        buzos_group = Group.objects.get(name='buzos_members')
        users_maq = maq_group.user_set.all()
        users_buzos = buzos_group.user_set.all()
        
        if asset_id:
            queryset = queryset.filter(ot__system__asset_id=asset_id)
        if responsable_id:
            queryset = queryset.filter(responsible=responsable_id)

        if current_user.has_perm("got.can_see_completely"):
            queryset = queryset.filter(finished=False).order_by('start_date')

        elif current_user in users_maq:
            queryset = queryset.filter(finished=False, ot__system__asset__supervisor=current_user)

        elif current_user in users_buzos:
            if current_user.groups.filter(name='santamarta_station').exists():
                queryset = queryset.filter(finished=False, ot__system__asset__area='b', ot__system__location='Santa Marta')
            elif current_user.groups.filter(name='ctg_station').exists():
                queryset = queryset.filter(finished=False, ot__system__asset__area='b', ot__system__location='Cartagena')
            elif current_user.groups.filter(name='guyana_station').exists():
                queryset = queryset.filter(finished=False, ot__system__asset__area='b', ot__system__location='Guyana')
            else:
                queryset = queryset.filter(finished=False, ot__system__asset__area='b')

        else:
            queryset = queryset.filter(Q(responsible=self.request.user) & Q(finished=False)).order_by('start_date')

        return queryset


from .forms import SolicitudAssetForm

def create_solicitud_asset(request, asset_id):
    asset = get_object_or_404(Asset, pk=asset_id)
    if request.method == 'POST':
        form = SolicitudAssetForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.asset = asset
            solicitud.solicitante = request.user
            solicitud.save()
            # Redirigir a la vista de detalle del asset, o donde consideres apropiado
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        form = SolicitudAssetForm()
    return render(request, 'asset/solicitud_form.html', {'form': form, 'asset': asset})

class CreateSolicitudView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):

        print(request.POST)  # Esto mostrará todos los datos del POST
        ot_id = request.POST.get('ot_id')
        asset_id = request.POST.get('asset_id')
        suministros = request.POST.get('suministros')
        items_ids = request.POST.getlist('item_id')
        cantidades = request.POST.getlist('cantidad')

        print("Items IDs:", items_ids)
        print("Cantidades:", cantidades)

        ot_id = request.POST.get('ot_id')
        asset_id = request.POST.get('asset_id')
        suministros = request.POST.get('suministros')
        
        nueva_solicitud = Solicitud.objects.create(
            solicitante=request.user,
            ot_id=ot_id,
            asset_id=asset_id,
            suministros=suministros,
            approved=False
        )

        items_ids = request.POST.getlist('item_id')
        cantidades = request.POST.getlist('cantidad')

        print("Items IDs:", items_ids)
        print("Cantidades:", cantidades)

        for item_id, cantidad in zip(items_ids, cantidades):
            print("Procesando item:", item_id, "con cantidad:", cantidad)  # Debugging statement
            if item_id and cantidad:
                try:
                    item = Item.objects.get(id=item_id)
                    cantidad = int(cantidad)
                    if cantidad > 0:
                        Suministro.objects.create(
                            Solicitud=nueva_solicitud,
                            item=item,
                            cantidad=cantidad
                        )
                        print("Suministro creado con éxito.")  # Debugging statement
                except Item.DoesNotExist:
                    print("Item no encontrado:", item_id)  # Debugging statement
                except ValueError:
                    print("Valor no válido para cantidad:", cantidad)  # Debugging statement
                except Exception as e:
                    print("Error no esperado:", str(e))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    

# from django.shortcuts import render, redirect
# from .forms import SolicitudForm, SuministroFormset
# from .models import Solicitud, Suministro, Item

# def create_solicitud(request):
#     if request.method == 'POST':
#         solicitud_form = SolicitudForm(request.POST)
#         suministro_formset = SuministroFormset(request.POST)
#         if solicitud_form.is_valid() and suministro_formset.is_valid():
#             solicitud = solicitud_form.save(commit=False)
#             solicitud.solicitante = request.user
            
#             solicitud.save()
            
#             # Crear un suministro por cada formulario en el formset
#             for form in suministro_formset:
#                 if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
#                     Suministro.objects.create(
#                         solicitud=solicitud,
#                         item=form.cleaned_data['item'],
#                         cantidad=form.cleaned_data['cantidad']
#                     )
#             return redirect(request.path)  # Redirige a la misma página
#         else:
#             print(solicitud_form.errors, suministro_formset.errors)
#     else:
#         solicitud_form = SolicitudForm()
#         suministro_formset = SuministroFormset(queryset=Suministro.objects.none())  # Inicia el formset vacío

#     context = {
#         'solicitud_form': solicitud_form,
#         'suministro_formset': suministro_formset
#     }
#     return render(request, 'got/assignedtasks_list_pendient.html', context)




class EditSolicitudView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        solicitud = get_object_or_404(Solicitud, pk=kwargs['pk'])
        suministros = request.POST.get('suministros')
        if suministros:
            solicitud.suministros = suministros
            solicitud.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    

class ApproveSolicitudView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        solicitud = Solicitud.objects.get(id=kwargs['pk'])
        solicitud.approved = not solicitud.approved
        solicitud.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
@receiver(post_save, sender=Solicitud)
def send_email_on_new_solicitud(sender, instance, created, **kwargs):
    if created:  # Comprueba si se ha creado una nueva solicitud
        suministros = Suministro.objects.filter(Solicitud=instance)
        suministros_list = "\n".join([f"{suministro.item}: {suministro.cantidad}" for suministro in suministros])
        subject = f'Nueva Solicitud de Suministros: {instance}'
        message = f'''
        Ha sido creada una nueva solicitud de suministros:
        Fecha de solicitud: {instance.creation_date.strftime("%d/%m/%Y")}
        Solicitante: {instance.solicitante.get_full_name()}
        Orden de trabajo: {instance.ot if instance.ot else "N/A"}
        Centro de costos: {instance.asset.name if instance.asset else "N/A"}
        Suministros: 
        
        {instance.suministros}

        Detalles de los Suministros Solicitados:
        {suministros_list}

        '''
        recipient_list = ['auxiliarmto@serport.co']  # Cambia a la dirección de correo deseada
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
    

@login_required
def update_sc(request, pk):
    if request.method == 'POST':
        solicitud = get_object_or_404(Solicitud, pk=pk)
        num_sc = request.POST.get('num_sc')
        solicitud.num_sc = num_sc
        solicitud.save()
        return redirect('got:rq-list')  # Asegúrate de redirigir a la vista adecuada
    return redirect('got:rq-list') 

class Reschedule_task(UpdateView):

    model = Task
    form_class = RescheduleTaskForm
    template_name = 'got/task_reschedule.html'
    success_url = reverse_lazy('got:my-tasks')

    def form_valid(self, form):
        return super().form_valid(form)


# ---------------------------- Activos (Assets) ---------------------------- #
class AssetsListView(LoginRequiredMixin, generic.ListView):

    model = Asset
    paginate_by = 20

    def get_queryset(self):
        queryset = Asset.objects.all()
        area = self.request.GET.get('area')
        user_groups = self.request.user.groups.values_list('name', flat=True)
        if 'buzos_members' in user_groups:
            queryset = queryset.filter(area='b')
        if area:
            queryset = queryset.filter(area=area)

        return queryset


class SolicitudesListView(LoginRequiredMixin, generic.ListView):
    
    model = Solicitud
    paginate_by = 15


class AssetDetailView(LoginRequiredMixin, generic.DetailView):

    model = Asset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.get_object()

        rotativos = Equipo.objects.filter(system__asset=asset, tipo='r').exists()

        if self.request.user.groups.filter(name='santamarta_station').exists():
            sys = asset.system_set.filter(location='Santa Marta').exclude(state='x')
        elif self.request.user.groups.filter(name='ctg_station').exists():
            sys = asset.system_set.filter(location='Cartagena').exclude(state='x')
        elif self.request.user.groups.filter(name='guyana_station').exists():
            sys = asset.system_set.filter(location='Guyana').exclude(state='x')
        else:
            sys = asset.system_set.all()

        other_asset_systems = System.objects.filter(location=asset.name).exclude(asset=asset)
        combined_systems = (sys.union(other_asset_systems)).order_by('group')
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        month_names_es = {
            "January": "Enero",
            "February": "Febrero",
            "March": "Marzo",
            "April": "Abril",
            "May": "Mayo",
            "June": "Junio",
            "July": "Julio",
            "August": "Agosto",
            "September": "Septiembre",
            "October": "Octubre",
            "November": "Noviembre",
            "December": "Diciembre"
        }

        current_month_name_en = datetime.now().strftime("%B")
        current_month_name_es = month_names_es[current_month_name_en]

        # Filtrar las rutas que cumplen con la condición del mes y año actuales
        filtered_rutas = []
        for ruta in Ruta.objects.filter(system__in=sys):
            if (ruta.next_date.month <= current_month and ruta.next_date.year <= current_year) or (ruta.intervention_date.month == current_month and ruta.intervention_date.year == current_year) or (ruta.ot and ruta.ot.state == 'x'):
                filtered_rutas.append(ruta)

        # Ordenar las rutas filtradas por next_date
        filtered_rutas.sort(key=lambda t: t.next_date)

        # rutas = sorted(Ruta.objects.filter(system__in=sys), key=lambda t: t.next_date)
        
        # Limitar a mostrar 10 sistemas
        paginator = Paginator(combined_systems, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # paginator_rutas = Paginator(rutas, 10)
        page_number_rutas = self.request.GET.get('page_rutas')
        # page_obj_rutas = paginator_rutas.get_page(page_number_rutas)

        context['sys_form'] = SysForm()
        context['page_obj'] = page_obj
        # context['page_obj_rutas'] = page_obj_rutas
        context['page_obj_rutas'] = filtered_rutas
        context['mes'] = current_month_name_es
        context['rotativos'] = rotativos
        context['other_asset_systems'] = other_asset_systems
        context['add_sys'] = combined_systems

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

    model = System
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system = self.get_object()
        context['is_structures'] = system.name.lower() == "estructuras"
        
        orders_list = Ot.objects.filter(system=system)

        view_type = self.kwargs.get('view_type', 'sys')  # Default a 'history'
        context['view_type'] = view_type

        if view_type == 'sys':
            paginator = Paginator(orders_list, 10)
        else:
            paginator = Paginator(orders_list, 4)

        page = self.request.GET.get('page')  # obtiene el número de página de GET request
        try:
            orders = paginator.page(page)
        except PageNotAnInteger:
            # Si la página no es un entero, entregar la primera página.
            orders = paginator.page(1)
        except EmptyPage:
            # Si la página está fuera de rango, entregar la última página de resultados.
            orders = paginator.page(paginator.num_pages)

        context['orders'] = orders

        try:
            equipment = Equipo.objects.get(code=view_type)
            context['equipo'] = equipment
        except Equipo.DoesNotExist:
            equipments = Equipo.objects.filter(system=system, subsystem=view_type)
            context['equipos'] = equipments

        subsystems = Equipo.objects.filter(system=system).exclude(subsystem__isnull=True).exclude(subsystem__exact='').values_list('subsystem', flat=True)

        # Usar set para eliminar duplicados, si el distinct no está funcionando como se espera
        context['unique_subsystems'] = list(set(subsystems))
        
        return context

class SysDelete(DeleteView):

    model = System

    def get_success_url(self):
        asset_code = self.object.asset.id
        success_url = reverse_lazy(
            'got:asset-detail', kwargs={'pk': asset_code})
        return str(success_url)


class SysUpdate(UpdateView):

    model = System
    form_class = SysForm
    template_name = 'got/system_form.html'


def add_location(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            return redirect('view-location', pk=location.pk)  # Redirige a una URL de éxito
    else:
        form = LocationForm()
    return render(request, 'got/add_location.html', {'form': form})

def view_location(request, pk):
    location = get_object_or_404(Location, pk=pk)
    return render(request, 'got/view_location.html', {'location': location})

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

    model = Equipo
    form_class = EquipoFormUpdate
    template_name = 'got/equipo_form.html'
    http_method_names = ['get', 'post']


class EquipoDelete(DeleteView):

    model = Equipo

    def get_success_url(self):
        sys_code = self.object.system.id
        success_url = reverse_lazy('got:sys-detail', kwargs={'pk': sys_code})
        return success_url

# ---------------------------- Failure Report ---------------------------- #

class FailureListView(LoginRequiredMixin, generic.ListView):

    model = FailureReport
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assets'] = Asset.objects.filter(area='a')
        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.groups.filter(name='maq_members').exists():
            supervised_assets = Asset.objects.filter(
                supervisor=self.request.user)

            queryset = queryset.filter(
                equipo__system__asset__in=supervised_assets)
        elif self.request.user.groups.filter(name='buzos_members').exists():
            supervised_assets = Asset.objects.filter(area='b')

            queryset = queryset.filter(equipo__system__asset__in=supervised_assets)

        return queryset


class FailureReportForm(LoginRequiredMixin, CreateView):
    model = FailureReport
    form_class = failureForm
    http_method_names = ['get', 'post']

    def send_email(self, context):
        """Sends an email compiled from the given context."""
        subject = 'Nuevo Reporte de Falla'
        email_template_name = 'got/failure_report_email.txt'
        
        email_body_html = render_to_string(email_template_name, context)
        # email_body_plain = strip_tags(email_body_html)
        
        email = EmailMessage(
            subject,
            # email_body_plain,
            email_body_html,
            settings.EMAIL_HOST_USER,
            [user.email for user in Group.objects.get(name='super_members').user_set.all()],
            reply_to=[settings.EMAIL_HOST_USER]
        )
        # email.content_subtype = 'html'
        
        if self.object.evidence:
            mimetype = f'image/{self.object.evidence.name.split(".")[-1]}'
            email.attach(
                'Evidencia.' + self.object.evidence.name.split(".")[-1],
                self.object.evidence.read(),  # Leer el archivo directamente
                mimetype
            )
        
        email.send()

    def get_email_context(self):
        """Builds the context dictionary for the email."""
        impacts_display = [self.object.get_impact_display(code) for code in self.object.impact]
        return {
            'reporter': self.object.reporter,
            'moment': self.object.moment.strftime('%Y-%m-%d %H:%M'),
            'equipo': f'{self.object.equipo.system.asset}-{self.object.equipo.name}',
            'description': self.object.description,
            'causas': self.object.causas,
            'suggest_repair': self.object.suggest_repair,
            'impact': impacts_display, 
            'critico': 'Sí' if self.object.critico else 'No',
            'report_url': self.request.build_absolute_uri(self.object.get_absolute_url()),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset_id = self.kwargs.get('asset_id')
        asset = get_object_or_404(Asset, pk=asset_id)
        context['asset_main'] = asset
        if 'image_form' not in context:
            context['image_form'] = UploadImages()  # Añadir el formulario de imágenes
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        asset_id = self.kwargs.get('asset_id')
        asset = get_object_or_404(Asset, pk=asset_id)
        form.fields['equipo'].queryset = Equipo.objects.filter(system__asset=asset)
        return form
    
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        image_form = UploadImages(request.POST, request.FILES)
        
        if form.is_valid() and image_form.is_valid():
            form.instance.reporter = request.user
            response = super().form_valid(form)
            context = self.get_email_context()  
            self.send_email(context)
            for file in request.FILES.getlist('file_field'):
                Image.objects.create(failure=self.object, image=file)  # Asociar las imágenes al reporte de falla
            return response
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form, **kwargs):
        context = self.get_context_data(form=form, **kwargs)
        return self.render_to_response(context)


class FailureDetailView(LoginRequiredMixin, generic.DetailView):

    model = FailureReport


class FailureReportUpdate(LoginRequiredMixin, UpdateView):

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
        description=f"Reporte de falla - {fail.equipo}",
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

    model = Ot
    paginate_by = 15

    # Formulario para filtrar Ots según descripción
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.groups.filter(name='buzos_members').exists():
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


class OtDetailView(LoginRequiredMixin, generic.DetailView):

    model = Ot

    # Formulario para crear, modificar o eliminar actividades
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.groups.filter(name='super_members').exists():
            context['task_form'] = ActForm()
        else:
            context['task_form'] = ActFormNoSup()
        context['state_form'] = FinishOtForm()
        context['image_form'] = UploadImages()

        # Agregar lógica para determinar el estado global de las tareas
        ot = self.get_object()
        all_tasks_finished = ot.task_set.filter(finished=False).exists()
        context['all_tasks_finished'] = not all_tasks_finished

        has_activities = ot.task_set.exists()
        context['has_activities'] = has_activities

        try:
            failure_report = ot.failure_report
        except FailureReport.DoesNotExist:
            failure_report = None

        context['failure_report'] = failure_report

        rutas = ot.ruta_set.all()
        context['rutas'] = rutas

        equipos = []
        for ruta in rutas:
            equipos.append(ruta.equipo)
        context['equipos'] = set(equipos)
        # context['equipos_por_ruta'] = {ruta.code: [ruta.equipo] if ruta.equipo else [] for ruta in rutas}

        return context

    def actualizar_rutas_dependientes(self, ruta):
        ruta.intervention_date = timezone.now()
        ruta.save()
        if ruta.dependencia is not None:
            self.actualizar_rutas_dependientes(ruta.dependencia)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        ot = self.get_object()

        if 'delete_task' in request.POST:
            task_id = request.POST.get('delete_task_id')
            task = Task.objects.get(id=task_id, ot=ot)
            task.delete()
            return redirect(ot.get_absolute_url()) 
    
        task_form_class = ActForm if request.user.groups.filter(name='super_members').exists() else ActFormNoSup
        task_form = task_form_class(request.POST, request.FILES)
        image_form = UploadImages(request.POST, request.FILES)

        if task_form.is_valid() and image_form.is_valid():
            # Guardar la tarea
            task = task_form.save(commit=False)
            task.ot = ot
            task.save()

            # Guardar cada imagen asociada a la tarea
            for file in request.FILES.getlist('file_field'):
                Image.objects.create(task=task, image=file)


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
                message = render_to_string('got/ot_finished_email.txt', {'ot': ot})
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
            return redirect(ot.get_absolute_url())

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

    model = Ot
    success_url = reverse_lazy('got:ot-list')


# --------------------------- Actividades --------------------------- #
class Finish_task(UpdateView):

    model = Task
    form_class = FinishTask
    template_name = 'got/task_finish_form.html'
    second_form_class = UploadImages
    success_url = reverse_lazy('got:my-tasks')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'image_form' not in context:
            context['image_form'] = self.second_form_class()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        image_form = self.second_form_class(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            response = super().form_valid(form)
            for img in request.FILES.getlist('file_field'):
                Image.objects.create(task=self.object, image=img)
            return response
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)

    def form_invalid(self, form, **kwargs):
        return self.render_to_response(self.get_context_data(form=form, **kwargs))
    

class Finish_task_ot(UpdateView):

    model = Task
    form_class = FinishTask
    template_name = 'got/task_finish_form.html'
    second_form_class = UploadImages
    # success_url = reverse_lazy('got:my-tasks')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'image_form' not in context:
            context['image_form'] = self.second_form_class()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        image_form = self.second_form_class(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            return self.form_valid(form, image_form)

            # response = super().form_valid(form)
            # for img in request.FILES.getlist('file_field'):
            #     Image.objects.create(task=self.object, image=img)
            # return response
        else:
            return self.form_invalid(form)

    def form_valid(self, form, image_form):
        self.object = form.save()

        # Guardar las imágenes
        for img in self.request.FILES.getlist('file_field'):
            Image.objects.create(task=self.object, image=img)

        # Aquí se establece el success_url dinámicamente
        ot = self.object.ot
        success_url = reverse('got:ot-detail', kwargs={'pk': ot.pk})
        return HttpResponseRedirect(success_url)
        # response = super().form_valid(form)
        # ot = self.object.ot 
        # self.success_url = reverse('got:ot-detail', kwargs={'pk': ot.pk})
        # return response

    def form_invalid(self, form, **kwargs):
        return self.render_to_response(self.get_context_data(form=form, **kwargs))


class TaskDetailView(LoginRequiredMixin, generic.DetailView):

    model = Task


class TaskUpdate(UpdateView):

    model = Task
    template_name = 'got/task_form.html'
    form_class = ActForm
    second_form_class = UploadImages

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'image_form' not in context:
            context['image_form'] = self.second_form_class()
        context['images'] = Image.objects.filter(task=self.get_object())
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        image_form = self.second_form_class(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            response = super().form_valid(form)
            if form.cleaned_data.get('delete_images'):
                self.object.images.all().delete()
            for img in request.FILES.getlist('file_field'):
                Image.objects.create(task=self.object, image=img)
            return response
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)

    def form_invalid(self, form, **kwargs):
        return self.render_to_response(self.get_context_data(form=form, **kwargs))


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
@login_required
def RutaListView(request):

    location_filter = request.GET.get('location', None)

    buceo = Asset.objects.filter(area='b')
    diques = Ruta.objects.filter(name__icontains='DIQUE')
    barcos = Asset.objects.filter(area='a')

    buceo_rowspan = len(buceo) + 1
    total_oks = 0
    total_non_dashes = 0

    buceo_data = []
    for asset in buceo:
        mensual = asset.check_ruta_status(30, location_filter)
        trimestral = asset.check_ruta_status(90, location_filter)
        semestral = asset.check_ruta_status(180, location_filter)
        anual = asset.check_ruta_status(365, location_filter)
        bianual = asset.check_ruta_status(730, location_filter)

        for status in [mensual, trimestral, semestral, anual, bianual]:
            if status == "Ok":
                total_oks += 1
            if status != "---":
                total_non_dashes += 1

        buceo_data.append({
            'asset': asset,
            'mensual': mensual,
            'trimestral': trimestral,
            'semestral': semestral,
            'anual': anual,
            'bianual': bianual,
        })

    ind_mtto = round((total_oks*100)/total_non_dashes, 2)


    motores_data = []
    for barco in barcos:
        sistema = barco.system_set.filter(group=200).first()
        sistema2 = barco.system_set.filter(group=300).first()
        motores_info = {
            'name': barco.name,
            'estribor': {
                'marca': '---',
                'modelo': '---',
                'lubricante': '---',
                'capacidad': 0,
                'fecha': '---',
                },
            'babor': {
                'marca': '---',
                'modelo': '---'},
            'generador': {'marca': '---', 'modelo': '---', 'lubricante': '---', 'capacidad': 0}
        }

        if sistema:
            motor_estribor = sistema.equipos.filter(name__icontains='Motor propulsor estribor').first()
            motor_babor = sistema.equipos.filter(name__icontains='Motor propulsor babor').first()
            motor_generador1 = sistema2.equipos.filter(Q(name__icontains='Motor generador estribor') | Q(name__icontains='Motor generador 1')).first()
            motor_generador2 = sistema2.equipos.filter(Q(name__icontains='Motor generador babor') | Q(name__icontains='Motor generador 2')).first()
            
            if motor_estribor:
                motores_info['estribor'] = {
                    'marca': motor_estribor.marca,
                    'modelo': motor_estribor.model,
                    'lubricante': motor_estribor.lubricante,
                    'capacidad': motor_estribor.volumen,
                    'horometro': motor_estribor.horometro,
                    'fecha': motor_estribor.last_hour_report_date(),
                    }
            if motor_babor:
                motores_info['babor'] = {
                    'marca': motor_babor.marca,
                    'modelo': motor_babor.model,
                    'lubricante': motor_babor.lubricante,
                    'capacidad': motor_babor.volumen,
                    'horometro': motor_babor.horometro,
                    'fecha': motor_babor.last_hour_report_date()
                    }
            if motor_generador1:
                motores_info['generador1'] = {
                    'marca': motor_generador1.marca,
                    'modelo': motor_generador1.model,
                    'lubricante': motor_generador1.lubricante,
                    'capacidad': motor_generador1.volumen,
                    'horometro': motor_generador1.horometro,
                    'fecha': motor_generador1.last_hour_report_date()
                    }
            if motor_generador2:
                motores_info['generador2'] = {
                    'marca': motor_generador2.marca,
                    'modelo': motor_generador2.model,
                    'lubricante': motor_generador2.lubricante,
                    'capacidad': motor_generador2.volumen,
                    'horometro': motor_generador2.horometro,
                    'fecha': motor_generador2.last_hour_report_date()
                    }

        motores_data.append(motores_info)

    context = {
        'dique_rutinas': diques,
        'buceo': buceo_data,
        'barcos': barcos,
        'motores_data': motores_data,
        'ind_mtto': ind_mtto,
        'buceo_rowspan': buceo_rowspan,
    }
    return render(request, 'got/ruta_list.html', context)


class RutaCreate(CreateView):

    model = Ruta
    form_class = RutaForm

    def form_valid(self, form):
        # Obtener el valor del parámetro pk desde la URL
        pk = self.kwargs['pk']
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

    m = 5

    area_filter = request.GET.get('area', None)

    assets = Asset.objects.annotate(num_ots=Count('system__ot'))
    if area_filter:
        assets = assets.filter(area=area_filter)
    top_assets = assets.order_by('-num_ots')[:5]
    ots_per_asset = [a.num_ots for a in top_assets]
    asset_labels = [a.name for a in top_assets]

    labels = ['Preventivo', 'Correctivo', 'Modificativo']

    earliest_start_date = Task.objects.filter(ot=OuterRef('pk')).order_by('start_date').values('start_date')[:1]
    # Subconsulta para calcular la fecha de finalización más tardía
    latest_final_date = Task.objects.filter(ot=OuterRef('pk')).annotate(
        final_date=ExpressionWrapper(
            F('start_date') + F('men_time'),
            output_field=DateField()
        )
    ).order_by('-final_date').values('final_date')[:1]

    # Anotar fechas de inicio y fin en `Ot` a través de subconsultas de `Task`
    bar = Ot.objects.annotate(
        start=Subquery(earliest_start_date),
        end=Subquery(latest_final_date)
    ).filter(state='x')

    if area_filter:
        bar = bar.filter(system__asset__area=area_filter)

    barcos = bar.filter(system__asset__area='a')

    if area_filter:
        ots = len(Ot.objects.filter(creation_date__month=m, creation_date__year=2024, system__asset__area=area_filter))

        ot_finish = len(Ot.objects.filter(
            creation_date__month=m,
            creation_date__year=2024, state='f',
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
        'barcos': barcos
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
    today = date.today()
    dates = [today - timedelta(days=x) for x in range(30)]
    equipos_rotativos = Equipo.objects.filter(system__asset=asset, tipo='r')

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

    equipos_data = []
    for equipo in equipos_rotativos:
        horas_reportadas = {date: 0 for date in dates}  # Prepara un diccionario con las fechas y horas iniciales a 0
        for hour in equipo.hours.filter(report_date__range=(dates[-1], today)):
            if hour.report_date in horas_reportadas:
                horas_reportadas[hour.report_date] += hour.hour

        equipos_data.append({
            'equipo': equipo,
            'horas': [horas_reportadas[date] for date in dates]  # Listar horas por cada fecha para el equipo
        })

    context = { 
        'form': form,
        'horas': hours,
        'asset': asset,
        'equipos_data': equipos_data,
        'equipos_rotativos': equipos_rotativos,
        'dates': dates
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

        combined_items = list(ots) + list(history_items)
        combined_items.sort(key=lambda x: x.history_date if hasattr(x, 'history_date') else x.creation_date, reverse=True)

        context['combined_items'] = combined_items
        context['asset'] = asset
        return context


def truncate_text(text, length=45):
    """Trunca el texto a una longitud especificada y añade '...' si es necesario."""
    if len(text) > length:
        return text[:length] + '...'
    return text


def calculate_status_code(t):
    ot_tasks = Task.objects.filter(ot=t)

    earliest_start_date = min(t.start_date for t in ot_tasks)
    latest_final_date = max(t.final_date for t in ot_tasks)

    today = date.today()

    if latest_final_date < today:
        return 0
    elif earliest_start_date < today < latest_final_date:
        return 1
    elif earliest_start_date > today:
        return 2

    return None


@login_required
def schedule(request, pk):

    tasks = Task.objects.filter(ot__system__asset=pk, ot__isnull=False, start_date__isnull=False, ot__state='x')
    ots = Ot.objects.filter(system__asset=pk, state='x')
    asset = get_object_or_404(Asset, pk=pk)
    systems = System.objects.filter(asset=asset)
    min_date = tasks.aggregate(Min('start_date'))['start_date__min']

    color_palette = itertools.cycle([
        'rgba(255, 99, 132, 0.2)',   # rojo
        'rgba(54, 162, 235, 0.2)',   # azul
        'rgba(255, 206, 86, 0.2)',   # amarillo
        'rgba(75, 192, 192, 0.2)',   # verde agua
        'rgba(153, 102, 255, 0.2)',  # púrpura
        'rgba(255, 159, 64, 0.2)',   # naranja
    ])

    # sta = [0 for i in tasks]
    n = 0
    # for ot in ots:
    #     sta[n] = calculate_status_code(ot)
    #     n += 1

    # Mapear cada responsable a un color
    responsibles = set(task.responsible.username for task in tasks if task.responsible)
    responsible_colors = {res: next(color_palette) for res in responsibles}

    chart_data = []
    n = 0
    for task in tasks:
        if task.finished:
            color = "rgba(192, 192, 192, 0.5)"
            border_color = "rgba(192, 192, 192, 1)"
        else:
            color = responsible_colors.get(task.responsible.username, "rgba(54, 162, 235, 0.2)")
            border_color = color.replace('0.2', '1') 
        
        chart_data.append({
            'start_date': task.start_date,
            'final_date': task.final_date,
            'description': truncate_text(task.ot.description),
            'name': f"{task.responsible.first_name} {task.responsible.last_name}",
            # 'status': task.finished,
            'activity_description': task.description,
            'background_color': color,
            'border_color': border_color,
            # 'status_code': sta[n],
        })
        n += 1
    
    # Agregar actividades desde las rutas
    # green_soft = 'rgba(75, 192, 192, 0.2)'    # verde suave
    # green_hard = 'rgba(75, 192, 192, 1)'     # verde fuerte
    # for system in systems:
    #     rutas = Ruta.objects.filter(system=system)
    #     for ruta in rutas:
    #         tasks_ruta = ruta.task_set.all()
    #         for task_ruta in tasks_ruta:
    #             chart_data.append({
    #                 'description': system.name,
    #                 'activity_description': ruta.name,
    #                 'start_date': ruta.next_date,
    #                 'final_date': ruta.next_date + timedelta(days=1),
    #                 'name': {task_ruta.responsible},
    #                 'status': 'preventivo',
    #                 'background_color': green_soft,
    #                 'border_color': green_hard
    #             })

    context = {
        'tasks': chart_data,
        'asset': asset,
        'min_date': min_date,
        'responsibles': responsible_colors,
    }
    return render(request, 'got/schedule.html', context)


def OperationListView(request):

    assets = Asset.objects.filter(area='a')
    operations = Operation.objects.order_by('start')

    operations_data = []
    for asset in assets:
        asset_operations = asset.operation_set.all().values(
            'start', 'end', 'proyecto', 'requirements'
        )
        operations_data.append({
            'asset': asset,
            'operations': list(asset_operations)
        })

    form = OperationForm(request.POST or None)
    modal_open = False 

    if request.method == 'POST':
        form = OperationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.path)
        else:
            modal_open = True 
    else:
        form = OperationForm()

    context= {
        'operations_data': operations_data,
        'operation_form': form,
        'modal_open': modal_open,
        'operaciones': operations,
        }

    return render(request, 'got/operation_list.html', context)


class OperationDelete(DeleteView):

    model = Operation
    success_url = reverse_lazy('got:operation-list')


class OperationUpdate(UpdateView):

    model = Operation
    form_class = OperationForm

    def get_success_url(self):

        return reverse('operation-list')


def generate_asset_pdf(request, asset_id):
    asset = get_object_or_404(Asset, pk=asset_id)
    systems = asset.system_set.all()

    systems_with_rutas = []
    for system in systems:
        rutas_data = []
        rutas = Ruta.objects.filter(system=system).prefetch_related('task_set')
        for ruta in rutas:
            # Recoger las tareas para cada ruta
            tasks = ruta.task_set.all()
            rutas_data.append({
                'ruta': ruta,
                'tasks': tasks,
                'ot_num': ruta.ot.num_ot if ruta.ot else 'N/A'  # Asegúrate que ruta.ot es accesible y no nulo
            })
        systems_with_rutas.append({
            'system': system,
            'rutas_data': rutas_data
        })

    context = {
        'asset': asset,
        'systems_with_rutas': systems_with_rutas
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Asset_{}.pdf"'.format(asset.pk)
    template = get_template('got/asset_pdf_template.html')
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


class DocumentCreateView(generic.View):
    form_class = DocumentForm
    template_name = 'got/add-document.html'

    def get(self, request, asset_id):
        asset = get_object_or_404(Asset, pk=asset_id)
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'asset': asset})

    def post(self, request, asset_id):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.asset = get_object_or_404(Asset, pk=asset_id)
            document.save()
            return redirect('got:asset-detail', pk=asset_id)
        return render(request, self.template_name, {'form': form})
    

class SolicitudCreate(CreateView):

    model = Solicitud
    form_class = SolicitudForm

    def form_valid(self, form):
        # Obtener el valor del parámetro pk desde la URL
        pk = self.kwargs['pk']
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

# class Meggeado(LoginRequiredMixin, generic.ListView):

#     model = Megger
#     template_name = 'got/assignedtasks_list_pendient.html'
#     paginate_by = 15