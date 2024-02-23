from django.shortcuts import render, get_object_or_404, redirect

# Autenticacion de usuario y permisos
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin

# Vistas genericas basadas en clases
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views import generic, View

# Librerias de django para manejo de las URLS
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy

# Modelos y formularios
from .models import Asset, Ot, Task
from .forms import OtsDescriptionFilterForm, RescheduleTaskForm, OtForm, ActForm

# Librerias auxiliares
from datetime import timedelta, date
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage


# ----------------------------------- Main views ------------------------------------------

# Mis actividades
class AssignedTaskByUserListView(LoginRequiredMixin, generic.ListView):
    '''
    Vista generica basada en clases que muestra las actividades en ejecucion de cada
    cada miembro de serport (v1.0)
    '''
    model = Task
    template_name = 'got/assignedtasks_list_pendient_user.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        for obj in context['task_list']:
            time = obj.men_time
            obj.final_date = obj.start_date + timedelta(days=time)

        return context

    def get_queryset(self):
        if self.request.user.is_staff:
            tasks = Task.objects.filter(finished=False).order_by('start_date')
        else: 
            tasks = Task.objects.filter(Q(responsible=self.request.user) & Q(finished=False)).order_by('start_date')

        paginator = Paginator(tasks, self.paginate_by)
        page_number = self.request.GET.get('page')

        try: 
            current_page = Paginator.page(page_number)

        except EmptyPage:
            current_page = paginator.page(paginator.num_pages)

        return current_page
    

# Equipos
class AssetsListView(LoginRequiredMixin, generic.ListView):
    '''
    Vista generica para mostrar el listado de los centros de costos (v1.0)
    '''
    model = Asset
    paginate_by = 10


# Detalle de equipos y listado de sistemas
class AssetsDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Vista generica para mostrar detalle de activos (v1.0)
    '''
    model = Asset


# Ordenes de trabajo
class OtListView(LoginRequiredMixin, generic.ListView):
    '''
    Vista generica para listado de ordenes de trabajo (v1.0)
    '''
    model = Ot
    paginate_by = 10

    # Formulario para filtrar Ots según descripción
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = OtsDescriptionFilterForm
        return context

    def get_queryset(self):
        form = OtsDescriptionFilterForm(self.request.GET)
        if form.is_valid():
            description = form.cleaned_data.get('description', '')
            queryset = Ot.objects.filter(description__icontains=description)
            return queryset
        return Ot.objects.all()


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
        return context
    
    def post(self, request, *args, **kwargs):
        ot = self.get_object()
        task_form = ActForm(request.POST, request.FILES)

        if task_form.is_valid():
            act = task_form.save(commit=False)
            act.ot = ot
            act.save()
            return redirect(act.get_absolute_url())
        else:
            return render(request, self.template_name, {'ot': ot, 'task_form': task_form})


# Detalle de actividades
class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Detalle de actividades (v1.0)
    '''
    model = Task


# ------------------------------------- Formularios -------------------------------------------
    
# Vista de formulario para reprogramar actividades
@permission_required('got.can_see_completely')
def reschedule_task(request, pk):
    '''
    Vista formulario para reprogramar actividades (v1.0)
    '''
    act = get_object_or_404(Task, pk=pk)

    time = act.men_time
    final_date = act.start_date + timedelta(days=time)

    if request.method == 'POST':
        form = RescheduleTaskForm(request.POST)

        if form.is_valid():
            act.start_date = form.cleaned_data['start_date']
            act.news = form.cleaned_data['news']
            act.men_time = form.cleaned_data['men_time']
            act.save()
            return HttpResponseRedirect(reverse('got:my-tasks'))

    else:
        proposed_reschedule_date = date.today() + timedelta(weeks=1)
        form =RescheduleTaskForm(initial={'proposed_date': proposed_reschedule_date,})
    
    return render(request, 'got/task_reschedule.html', {'form': form, 'task': act, 'final_date': final_date})


class OtCreate(CreateView):
    '''
    Vista formulario para crear ordenes de trabajo (v1.0)
    '''
    model = Ot
    form_class = OtForm


class OtUpdate(UpdateView):
    '''
    Vista formulario para actualizar ordenes de trabajo (v1.0)
    '''
    model = Ot
    form_class = OtForm


class OtDelete(DeleteView):
    '''
    Vista formulario para confirmar eliminacion de ordenes de trabajo (v1.0)
    '''
    model = Ot
    success_url = reverse_lazy('got:ot-list')


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


# Reportes
def report_pdf(request, num_ot):
    '''
    Funcion para crear reportes pdf
    '''
    ot_info = Ot.objects.get(num_ot=num_ot)
    template_path = 'got/pdf_template.html'
    context = {'ot': ot_info}
    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = 'filename="orden_de_trabajo.pdf'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
