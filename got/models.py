from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.utils import timezone

from django.core.validators import RegexValidator


class Asset(models.Model):
    '''
    Activos (v1.0)
    '''

    AREA = (
        ('b', 'Buceo'),
        ('a', 'Artefactos Navales'),
        ('o', 'Oceanografia'),
        ('l', 'Locativo'),
        ('v', 'Vehiculos')
    )

    name = models.CharField(max_length=50)
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    area = models.CharField(choices=AREA, default='a', max_length=50)
    
    # Propiedades adicionales para artefactos navales
    bandera = models.CharField(default='Colombia', max_length=50, null=True, blank=True)
    eslora = models.DecimalField(default=0,max_digits=8, decimal_places=2, null=True, blank=True)
    
    manga = models.DecimalField(default=0,max_digits=8, decimal_places=2, null=True, blank=True)
    puntal = models.DecimalField(default=0,max_digits=8, decimal_places=2, null=True, blank=True)
    calado_maximo = models.DecimalField(default=0,max_digits=8, decimal_places=2, null=True, blank=True)
    deadweight = models.IntegerField(default=0, null=True, blank=True)
    arqueo_bruto = models.IntegerField(default=0, null=True, blank=True)
    arqueo_neto = models.IntegerField(default=0, null=True, blank=True)
    espacio_libre_cubierta = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('got:asset-detail', args=[str(self.id)])
    
    class Meta:
        permissions = (('can_see_completely', 'Access to completely info'),)


class System(models.Model):
    '''
    Sistema agrupados de cada activo, relacion directa con activos y vinculo con ordenes 
    de trabajo (v1.0)
    '''

    STATUS = (
        ('m', 'Mantenimiento'),
        ('o', 'Operativo'),
        ('x', 'Fuera de servicio')
    )

    name = models.CharField(max_length=50)
    gruop = models.IntegerField()
    location = models.CharField(max_length=50, default="Cartagena", null=True, blank=True)
    state = models.CharField(choices=STATUS, default='m', max_length=50)

    asset = models.ForeignKey(Asset, on_delete = models.CASCADE)

    def __str__(self):
        return '%s - %s - %s' % (self.asset, self.gruop, self.name)
    
    def get_absolute_url(self):
        return reverse('got:sys-detail', args=[self.id])
    
    class Meta:
        ordering = ['asset__name', 'gruop']

class Equipo(models.Model):
    '''
    Momentaneamente seran componentes rotativos (inactivo)
    '''

    name = models.CharField(max_length=50)
    date_inv = models.DateField(null=True, blank=True)
    code = models.CharField(primary_key=True, max_length=50)
    model = models.CharField(max_length=50, null=True, blank=True)
    serial = models.CharField(max_length=50, null=True, blank=True)
    marca = models.CharField(max_length=50, null=True, blank=True)
    fabricante = models.CharField(max_length=50, null=True, blank=True)
    feature = models.TextField()
    imagen = models.ImageField(upload_to='media/', null=True, blank=True)

    system = models.ForeignKey(System, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos')

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name', 'code']

    def get_absolute_url(self):
        return reverse('got:sys-detail', args=[self.system.id])

class Ruta(models.Model):
    '''
    (inactivo)
    '''
    code = models.CharField(primary_key=True, max_length=50)
    frecuency = models.IntegerField()
    intervention_date = models.DateField()
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='rutas')

    @property
    def next_date(self):
        return self.intervention_date + timedelta(days=self.frecuency)
    
    @property
    def is_overdue(self):
        return date.today() >= self.next_date

    def __str__(self):
        return '%s - %s' % (self.code, self.equipo)


class Ot(models.Model):
    '''
    Ordenes de trabajo (v1.0)
    '''
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

    creation_date = models.DateField(auto_now=True)
    num_ot = models.AutoField(primary_key=True)
    description = models.TextField()
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    super = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null = True,
        blank = True
    )
    state = models.CharField(choices=STATUS, default='x', max_length=50)
    tipo_mtto = models.CharField(choices=TIPO_MTTO, default='c', max_length=50)

    def __str__(self):
        return '%s - %s' % (self.num_ot, self.description)
    
    def get_absolute_url(self):
        return reverse('got:ot-detail', args=[str(self.num_ot)])
    
    class Meta:
        ordering = ['num_ot']


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
