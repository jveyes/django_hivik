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
    STATUS = (
        ('m', 'Mantenimiento'),
        ('o', 'Operacion'),
        ('d', 'Dique'),
        ('x', 'Fuera de servicio')
    )

    name = models.CharField(max_length=50)
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    location = models.CharField(max_length=50)
    state = models.CharField(choices=STATUS, default='m', max_length=50)

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
    name = models.CharField(max_length=50)
    gruop = models.IntegerField()
    asset = models.ForeignKey(Asset, on_delete = models.CASCADE)

    def __str__(self):
        return '%s - %s - %s' % (self.asset, self.gruop, self.name)
    
    def get_absolute_url(self):
        return reverse('got:sys-detail', args=[str(self.id)])
    
    class Meta:
        ordering = ['asset__name', 'gruop']

class Equipo(models.Model):
    '''
    Momentaneamente seran componentes rotativos (inactivo)
    '''
    STATUS = (
        ('m', 'Mantenimiento'),
        ('o', 'Operativo'),
        ('x', 'Fuera de servicio')
    )

    name = models.CharField(max_length=50)
    date_inv = models.DateField(null=True, blank=True)
    code = models.CharField(primary_key=True, max_length=50)
    location_int = models.CharField(max_length=50, null=True, blank=True)
    area = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    serial = models.CharField(max_length=50, null=True, blank=True)
    marca = models.CharField(max_length=50, null=True, blank=True)
    fabricante = models.CharField(max_length=50, null=True, blank=True)
    feature = models.TextField()
    state = models.CharField(choices=STATUS, max_length=50)
    imagen = models.ImageField(upload_to='media/', null=True, blank=True)

    system = models.ForeignKey(System, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos')

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name', 'code']

class Ruta(models.Model):
    '''
    (inactivo)
    '''
    name = models.CharField(max_length=50)
    component = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    frecuency = models.IntegerField()
    code = models.CharField(primary_key=True, max_length=50)
    intervention_date = models.DateField()

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='rutas')

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
    state = models.CharField(choices=STATUS, default='a', max_length=50)

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
    ot = models.ForeignKey(Ot, on_delete=models.CASCADE)
    # ruta = models.ForeignKey(Ruta, on_delete=models.SET_NULL, null=True, blank=True)
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    description = models.TextField()
    news = models.TextField(blank=True, null=True)
    evidence = models.ImageField(upload_to='media/', null=True, blank=True)
    start_date = models.DateField()
    men_time = models.IntegerField(default=1)
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
