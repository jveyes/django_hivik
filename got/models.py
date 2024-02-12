from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from datetime import date, timedelta


class Asset(models.Model):
    '''
    Activos de la empresa
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
    state = models.CharField(choices=STATUS, default='m')

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('got:assets-detail', args=[str(self.id)])
    
    class Meta:
        permissions = (('can_see_completely', 'Access to completely info'),)


class System(models.Model):
    '''
    Sistema agrupados de cada activo, relacion directa con activos y vinulo con ordenes 
    de trabajo
    '''
    name = models.CharField(max_length=50)
    gruop = models.IntegerField()
    asset = models.ForeignKey(
        Asset,
        on_delete = models.CASCADE,
    )

    def __str__(self):
        return '%s - %s - %s' % (self.asset, self.gruop, self.name)

class Ot(models.Model):
    '''
    Ordenes de trabajo
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
    state = models.CharField(choices=STATUS, default='a')

    def __str__(self):
        return '%s - %s' % (self.num_ot, self.description)
    
    def get_absolute_url(self):
        return reverse('got:ot-detail', args=[str(self.num_ot)])


class Task(models.Model):
    '''
    Actividades que se deben realizar de cada orden de trabajo
    '''
    ot = models.ForeignKey(Ot, on_delete=models.CASCADE)
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    description = models.TextField()
    news = models.TextField(blank=True, null=True)
    evidence = models.ImageField(upload_to='evidencias', null=True, blank=True)
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
