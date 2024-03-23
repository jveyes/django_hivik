from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.db.models import Sum


class Asset(models.Model):
    '''
    Modelo para representar activos.
    Incluye propiedades especificas para Barcos.
    '''
    AREA = (
        ('a', 'Remolcadores'),
        ('b', 'Buceo'),
        ('o', 'Oceanografia'),
        ('l', 'Locativo'),
        ('v', 'Vehiculos'),
        ('x', 'Apoyo'),
    )

    name = models.CharField(max_length=50)
    area = models.CharField(max_length=1, choices=AREA, default='a')
    supervisor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
        )

    # Propiedades adicionales para barcos
    bandera = models.CharField(
        default='Colombia', max_length=50, null=True, blank=True
        )
    eslora = models.DecimalField(
        default=0, max_digits=8, decimal_places=2, null=True, blank=True
        )
    manga = models.DecimalField(
        default=0, max_digits=8, decimal_places=2, null=True, blank=True
        )
    puntal = models.DecimalField(
        default=0, max_digits=8, decimal_places=2, null=True, blank=True
        )
    calado_maximo = models.DecimalField(
        default=0, max_digits=8, decimal_places=2, null=True, blank=True
        )
    deadweight = models.IntegerField(
        default=0, null=True, blank=True
        )
    arqueo_bruto = models.IntegerField(
        default=0, null=True, blank=True
        )
    arqueo_neto = models.IntegerField(
        default=0, null=True, blank=True
        )
    espacio_libre_cubierta = models.IntegerField(
        default=0, null=True, blank=True
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('got:asset-detail', args=[str(self.id)])

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
    gruop = models.IntegerField()
    location = models.CharField(max_length=50, default="Cartagena", null=True, blank=True)
    state = models.CharField(choices=STATUS, default='m', max_length=50)

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    def __str__(self):
        return '%s/%s' % (self.asset, self.name)
    
    def get_absolute_url(self):
        return reverse('got:sys-detail', args=[self.id])
    
    class Meta:
        ordering = ['asset__name', 'gruop']


class Equipo(models.Model):

    TIPO = (
        ('r', 'Rotativo'),
        ('nr', 'No rotativo'),
    )

    name = models.CharField(max_length=50)
    date_inv = models.DateField(null=True, blank=True)
    code = models.CharField(primary_key=True, max_length=50)
    model = models.CharField(max_length=50, null=True, blank=True)
    serial = models.CharField(max_length=50, null=True, blank=True)
    marca = models.CharField(max_length=50, null=True, blank=True)
    fabricante = models.CharField(max_length=50, null=True, blank=True)
    feature = models.TextField()
    imagen = models.ImageField(upload_to='media/', null=True, blank=True)
    manual_pdf = models.FileField(upload_to='pdfs/', null=True, blank=True)

    initial_hours = models.IntegerField(default=0)
    horometro = models.IntegerField(default=0, null=True, blank=True)
    prom_hours = models.IntegerField(default=0, null=True, blank=True)
    tipo = models.CharField(choices=TIPO, default='nr', max_length=50)

    system = models.ForeignKey(System, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos')

    def calculate_horometro(self):
        total_hours = self.hours.aggregate(total=Sum('hour'))['total'] or 0
        return total_hours + self.initial_hours

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name', 'code']

    def get_absolute_url(self):
        return reverse('got:sys-detail', args=[self.system.id])


class HistoryHour(models.Model):

    report_date = models.DateField()
    hour = models.IntegerField()
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    component = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='hours')

    def __str__(self):
        return '%s: %s - %s (%s)' % (self.report_date, self.component, self.hour, self.reporter)
    
    class Meta:
        ordering = ['-report_date']

class Ruta(models.Model):
    
    CONTROL = (
        ('d', 'Días'),
        ('h', 'Horas'),
    )
    
    code = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    control = models.CharField(choices=CONTROL, max_length=50)
    frecuency = models.IntegerField()
    intervention_date = models.DateField()

    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='rutas')
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True) 

    @property
    def next_date(self):
        if self.control=='d':
            ndate = self.intervention_date + timedelta(days=self.frecuency)
        else:
            try:
                ndays = int(self.frecuency/self.equipo.prom_hours)
                ndate = self.intervention_date + timedelta(days=ndays)
            except (ZeroDivisionError, AttributeError):
                ndate = self.intervention_date + timedelta(days=30)
        return ndate
    
    @property
    def percentage_remaining(self):
        days_remaining = (self.next_date - date.today()).days
        if self.control=='d':
            percent = int((days_remaining / self.frecuency) * 100)
        else:
            try:
                ndays = int(self.frecuency/self.equipo.prom_hours)
                percent = int((days_remaining / ndays) * 100)
            except (ZeroDivisionError, AttributeError):
                percent = 'n'
        return percent

    @property
    def maintenance_status(self):
        percentage = self.percentage_remaining
        if 25 <= percentage <= 100:
            return 'c'
        elif 5 <= percentage <= 26:
            return 'p'
        elif percentage == 'n':
            return percentage
        else:
            return 'v' 

    def __str__(self):
        return '%s - %s' % (self.code, self.system)
    
    def get_absolute_url(self):
        return reverse('got:sys-detail', args=[str(self.system.id)])


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
    super = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null = True,
        blank = True
    )
    state = models.CharField(choices=STATUS, default='x', max_length=50)
    tipo_mtto = models.CharField(choices=TIPO_MTTO, max_length=50)
    info_contratista_pdf = models.FileField(upload_to='pdfs/', null=True, blank=True)

    system = models.ForeignKey(System, on_delete=models.CASCADE)

    def __str__(self):
        return '%s - %s' % (self.num_ot, self.description)
    
    def get_absolute_url(self):
        return reverse('got:ot-detail', args=[str(self.num_ot)])
    
    class Meta:
        ordering = ['-num_ot']


class Task(models.Model):
    '''
    Actividades (v1.0)
    '''
    ot = models.ForeignKey(Ot, on_delete=models.CASCADE, null=True, blank=True)
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, null=True, blank=True)
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    description = models.TextField()
    procedimiento = models.TextField(default="---", blank=True, null=True)
    hse = models.TextField(default="---", blank=True, null=True)
    suministros = models.TextField(default="---", blank=True, null=True)
    news = models.TextField(blank=True, null=True)
    evidence = models.ImageField(upload_to='media/', null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    men_time = models.IntegerField(default=0)
    finished = models.BooleanField()

    def __str__(self):
        return self.description
    
    def get_absolute_url(self):
        return reverse('got:task-detail', args=[str(self.id)])

    @property
    def is_overdue(self):
        if self.start_date and date.today() > self.start_date + timedelta(days=self.men_time):
            return True
        return False
