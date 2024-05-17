from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.db.models import Sum, Count, Case, When, IntegerField, Value
from datetime import datetime
import uuid
from django.contrib.postgres.fields import ArrayField
from simple_history.models import HistoricalRecords


def get_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"media/{datetime.now():%Y%m%d%H%M%S}.{ext}"
    return filename


def get_upload_pdfs(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"pdfs/{uuid.uuid4()}.{ext}"
    return filename


class Asset(models.Model):

    AREA = (
        ('a', 'Motonave'),
        ('b', 'Buceo'),
        ('o', 'Oceanografía'),
        ('l', 'Locativo'),
        ('v', 'Vehiculos'),
        ('x', 'Apoyo'),
    )

    abbreviation = models.CharField(max_length=3, unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    area = models.CharField(max_length=1, choices=AREA, default='a')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    imagen = models.ImageField(upload_to=get_upload_path, null=True, blank=True)

    # Propiedades adicionales para barcos
    bandera = models.CharField(default='Colombia', max_length=50, null=True, blank=True)
    eslora = models.DecimalField(default=0, max_digits=8, decimal_places=2, null=True, blank=True)
    manga = models.DecimalField(default=0, max_digits=8, decimal_places=2, null=True, blank=True)
    puntal = models.DecimalField(default=0, max_digits=8, decimal_places=2, null=True, blank=True)
    calado_maximo = models.DecimalField(default=0, max_digits=8, decimal_places=2, null=True, blank=True)
    deadweight = models.IntegerField(default=0, null=True, blank=True)
    arqueo_bruto = models.IntegerField(default=0, null=True, blank=True)
    arqueo_neto = models.IntegerField(default=0, null=True, blank=True)
    espacio_libre_cubierta = models.IntegerField(default=0, null=True, blank=True)

    
    def check_ruta_status(self, frecuency, location=None):
        if location:
            rutas = self.system_set.filter(rutas__frecuency=frecuency, rutas__system__location=location)
        else:
            rutas = self.system_set.filter(rutas__frecuency=frecuency)
        
        if not rutas.exists():
            return "---"
        all_on_time = True
        for system in rutas:
            for ruta in system.rutas.filter(frecuency=frecuency):
                if ruta.next_date < date.today():
                    all_on_time = False
                    break
            if not all_on_time:
                break
        return "Ok" if all_on_time else "Requiere"  

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('got:asset-detail', args=[str(self.abbreviation)])

    class Meta:
        permissions = (('can_see_completely', 'Access to completely info'),)
        ordering = ['area', 'name']


class System(models.Model):

    STATUS = (
        ('m', 'Mantenimiento'),
        ('o', 'Operativo'),
        ('x', 'Fuera de servicio')
    )

    name = models.CharField(max_length=50)
    group = models.IntegerField()
    location = models.CharField(max_length=50, default="Cartagena", null=True, blank=True)
    state = models.CharField(choices=STATUS, default='m', max_length=1)

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, to_field='abbreviation')

    def __str__(self):
        return '%s/%s' % (self.asset, self.name)

    def get_absolute_url(self):
        return reverse('got:sys-detail', args=[self.id])

    class Meta:
        ordering = ['asset__name', 'group']
    
    @property
    def maintenance_percentage(self):
        rutas = self.rutas.all()
        if not rutas:
            return 0

        total_value = 0

        for ruta in rutas:
            if ruta.maintenance_status == 'c':
                total_value += 1
            elif ruta.maintenance_status == 'p':
                total_value += 0.5
            elif ruta.maintenance_status == 'e' and ruta.next_date > date.today():
                total_value += 1
            

        max_possible_value = len(rutas)
        if max_possible_value == 0:
            return None

        return round((total_value / max_possible_value) * 100, 2)


class Equipo(models.Model):

    TIPO = (
        ('r', 'Rotativo'),
        ('nr', 'No rotativo'),
    )

    name = models.CharField(max_length=50)
    date_inv = models.DateField()
    code = models.CharField(primary_key=True, max_length=50)
    model = models.CharField(max_length=50, null=True, blank=True)
    serial = models.CharField(max_length=50, null=True, blank=True)
    marca = models.CharField(max_length=50, null=True, blank=True)
    fabricante = models.CharField(max_length=50, null=True, blank=True)
    feature = models.TextField()
    imagen = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    manual_pdf = models.FileField(upload_to=get_upload_pdfs, null=True, blank=True)

    # Componentes de tipo rotativo
    tipo = models.CharField(choices=TIPO, default='nr', max_length=2)
    initial_hours = models.IntegerField(default=0)
    horometro = models.IntegerField(default=0, null=True, blank=True)
    prom_hours = models.IntegerField(default=0, null=True, blank=True)
    lubricante = models.CharField(max_length=100, null=True, blank=True)
    volumen = models.IntegerField(default=0, null=True, blank=True)


    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='equipos')

    def calculate_horometro(self):
        total_hours = self.hours.aggregate(total=Sum('hour'))['total'] or 0
        return total_hours + self.initial_hours
    
    def last_hour_report_date(self):
        last_report = self.hours.order_by('-report_date').first()
        return last_report.report_date if last_report else None

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ['name', 'code']

    def get_absolute_url(self):
        return reverse('got:sys-detail', args=[self.system.id])


class Component(models.Model):
    name = models.CharField(max_length=50)
    serial = models.CharField(max_length=50, null=True, blank=True)
    marca = models.CharField(max_length=50, null=True, blank=True)
    presentacion = models.CharField(max_length=50)
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=50)
    direccion = models.CharField(max_length=100)
    contact = models.CharField(max_length=50)
    num_contact = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Salida(models.Model):

    lugar_destino = models.ForeignKey(Location, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    motivo = models.TextField()
    persona_transporte = models.CharField(max_length=100)
    matricula_vehiculo = models.CharField(max_length=10)

    def __str__(self):
        return f"Salida a {self.lugar_destino} ({self.fecha})"

    def get_absolute_url(self):
        return reverse('got:salida-detail', args=[str(self.id)])


class SalidaItem(models.Model):
    salida = models.ForeignKey(Salida, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Component, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    imagen = models.ImageField(upload_to=get_upload_path, null=True, blank=True)

    def __str__(self):
        return f"{self.cantidad}x {self.item.name} ({self.salida})"


class HistoryHour(models.Model):

    report_date = models.DateField()
    hour = models.DecimalField(max_digits=5, decimal_places=2)
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    component = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='hours')

    def __str__(self):
        return '%s: %s - %s (%s)' % (self.report_date, self.component, self.hour, self.reporter)

    class Meta:
        ordering = ['-report_date']
        unique_together = ('component', 'report_date')


class Ot(models.Model):

    STATUS = (
        ('a', 'Abierto'),
        ('x', 'En ejecucion'),
        ('f', 'Finalizado'),
        ('c', 'Cancelado'),
    )

    TIPO_MTTO = (
        ('p', 'Preventivo'),
        ('c', 'Correctivo'),
        ('m', 'Modificativo'),
    )

    creation_date = models.DateField(auto_now_add=True)
    num_ot = models.AutoField(primary_key=True)
    description = models.TextField()
    super = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.CharField(choices=STATUS, default='x', max_length=50)
    tipo_mtto = models.CharField(choices=TIPO_MTTO, max_length=1)
    info_contratista_pdf = models.FileField(upload_to=get_upload_path,null=True, blank=True)
    ot_aprobada = models.FileField(upload_to=get_upload_path,null=True, blank=True)
    suministros = models.TextField(default="", blank=True, null=True)

    system = models.ForeignKey(System, on_delete=models.CASCADE)

    def all_tasks_finished(self):
        related_tasks = self.task_set.all()
        if related_tasks.exists() and all(task.finished for task in related_tasks):
            return True
        return False

    def __str__(self):
        return '%s - %s' % (self.num_ot, self.description)

    def get_absolute_url(self):
        return reverse('got:ot-detail', args=[str(self.num_ot)])

    class Meta:
        ordering = ['-num_ot']


class Ruta(models.Model):

    CONTROL = (
        ('d', 'Días'),
        ('h', 'Horas'),
    )

    code = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    control = models.CharField(choices=CONTROL, max_length=1)
    frecuency = models.IntegerField()
    intervention_date = models.DateField()
    suministros = models.TextField(default="", blank=True, null=True)

    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='rutas')
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True)
    ot = models.ForeignKey(Ot, on_delete=models.SET_NULL, null=True, blank=True)
    dependencia = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependiente')
    astillero = models.CharField(max_length=50, default="", null=True, blank=True)


    @property
    def next_date(self):
        if self.control == 'd':
            ndays = self.frecuency
            return self.intervention_date + timedelta(days=ndays)
        elif self.control == 'h':
            period = self.equipo.hours.filter(report_date__gte=self.intervention_date, report_date__lte=date.today()).aggregate(total_hours=Sum('hour'))['total_hours'] or 0
            inv = self.frecuency - period
            try:
                ndays = int(inv/self.equipo.prom_hours)
            except (ZeroDivisionError, AttributeError):
                ndays = int(self.frecuency/1)
        elif self.control == 'h' and not self.ot:
            inv = self.frecuency - self.equipo.horometro
            try:
                ndays = int(inv/self.equipo.prom_hours)
            except (ZeroDivisionError, AttributeError):
                ndays = int(self.frecuency/1)
        
        return date.today() + timedelta(days=ndays)

    @property
    def daysleft(self):
        return (self.next_date - date.today()).days

    @property
    def percentage_remaining(self):
        days_remaining = (self.next_date - date.today()).days
        if self.control == 'd':
            percent = int((days_remaining / self.frecuency) * 100)
        else:
            hours_period = self.equipo.hours.filter(
                    report_date__gte=self.intervention_date,
                    report_date__lte=date.today()
                ).aggregate(total_hours=Sum('hour'))['total_hours'] or 0
            inv = self.frecuency - hours_period
            percent = int((inv / self.frecuency) * 100)
        return percent

    @property
    def maintenance_status(self):
        percentage = self.percentage_remaining
        if not self.ot:
            return 'e'
        elif percentage <= 10 and not self.ot:
            return 'p'
        elif self.ot.state=='x':
            return 'p'
        else:
            if 25 <= percentage <= 100:
                return 'c'
            elif 5 <= percentage <= 24:
                return 'p'
            else:
                return 'v'

    def __str__(self):
        return '%s - %s - %s' % (self.code, self.system, self.name)

    def get_absolute_url(self):
        return reverse('got:sys-detail', args=[str(self.system.id)])

    class Meta:
        ordering = ['frecuency']


class Task(models.Model):

    ot = models.ForeignKey(Ot, on_delete=models.CASCADE, null=True, blank=True)
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, null=True, blank=True)
    responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    description = models.TextField()
    procedimiento = models.TextField(default="", blank=True, null=True)
    hse = models.TextField(default="", blank=True, null=True)
    news = models.TextField(blank=True, null=True)
    evidence = models.ImageField(upload_to=get_upload_path, null=True, blank=True)

    start_date = models.DateField(null=True, blank=True)
    men_time = models.IntegerField(default=0)
    finished = models.BooleanField()

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse('got:task-detail', args=[str(self.id)])

    @property
    def is_overdue(self):
        overdue_date = self.start_date + timedelta(days=self.men_time)
        return self.start_date and date.today() > overdue_date

    @property
    def final_date(self):
        return self.start_date + timedelta(days=self.men_time)
 
    class Meta:
        permissions = (('can_reschedule_task', 'Reprogramar actividades'),)


class FailureReport(models.Model):

    IMPACT = (
        ('s', 'La seguridad personal'),
        ('m', 'El medio ambiente'),
        ('i', 'Integridad del equipo/sistema'),
        ('o', 'El desarrollo normal de las operaciones'),
    )

    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)

    moment = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    causas = models.TextField()
    suggest_repair = models.TextField(null=True, blank=True)
    critico = models.BooleanField()
    evidence = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    closed = models.BooleanField(default=False)
    impact = ArrayField(models.CharField(max_length=1, choices=IMPACT), default=list, blank=True)
    related_ot = models.OneToOneField('Ot', on_delete=models.SET_NULL, null=True, blank=True, related_name='failure_report')

    class Meta:
        ordering = ['-moment']

    def __str__(self):
        status = "Cerrado" if self.closed else "Abierto"
        return f'Reporte de falla en {self.equipo.name} - {status}'

    def get_absolute_url(self):
        # Suponiendo que 'got:failure-report-detail' es el nombre de tu URL
        # para la vista de detalle y que usas el ID del reporte como parámetro
        return reverse('got:failure-report-detail', kwargs={'pk': self.pk})

    def get_impact_display(self, impact_code):
        """Devuelve la representación en texto de un código de impacto."""
        return dict(self.IMPACT).get(impact_code, "Desconocido")



class Image(models.Model):

    failure = models.ForeignKey(FailureReport, related_name='images', on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey(Task, related_name='images', on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to=get_upload_path)
