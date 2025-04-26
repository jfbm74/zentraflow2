# apps/ingesta_correo/views_reglas.py
"""
Vistas para la gestión de reglas de filtrado.
"""

import logging
import json
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.forms import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.db.models import Count, Max
from django.template.loader import render_to_string

from apps.ingesta_correo.models import ReglaFiltrado, ServicioIngesta, CondicionRegla, CategoriaRegla, CorreoIngesta, HistorialAplicacionRegla
from apps.ingesta_correo.services.regla_filtrado_service import ReglaFiltradoService
from apps.ingesta_correo.services.regla_test_service import ReglaTestService
from apps.tenants.utils import get_tenant_for_user
from .forms import ReglaFiltradoForm, CondicionReglaInlineFormSet, CategoriaReglaForm

logger = logging.getLogger(__name__)

class ReglasFiltradoView(LoginRequiredMixin, TemplateView):
    """Vista para la página de gestión de reglas de filtrado."""
    template_name = 'ingesta_correo/reglas_list.html'
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        """Añadir datos de contexto para la plantilla."""
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Marcar menú como activo
        context['active_menu'] = 'ingesta_correo'
        context['active_submenu'] = 'reglas'
        
        # Obtener las reglas de filtrado para este tenant
        context['reglas'] = ReglaFiltradoService.get_reglas_for_tenant(tenant)
        
        # Obtener los campos, condiciones y acciones disponibles para reglas
        context['campos'] = ReglaFiltrado.TipoCampo.choices
        context['condiciones'] = ReglaFiltrado.TipoCondicion.choices
        context['acciones'] = ReglaFiltrado.TipoAccion.choices
        
        # Verificar si existe el servicio de ingesta
        servicio_existe = ServicioIngesta.objects.filter(tenant=tenant).exists()
        context['servicio_existe'] = servicio_existe
        
        return context

class ReglaCrearView(LoginRequiredMixin, CreateView):
    """Vista basada en clase para crear una nueva regla de filtrado."""
    model = ReglaFiltrado
    form_class = ReglaFiltradoForm
    template_name = 'ingesta_correo/reglas/regla_form.html'
    
    def get_success_url(self):
        return reverse('ingesta_correo:regla_detail', kwargs={'regla_id': self.object.id})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        tenant = self.request.user.tenant
        servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
        kwargs['servicio'] = servicio
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
        
        # Si no hay un servicio activo, redireccionar
        if not servicio:
            messages.warning(self.request, "No hay un servicio de ingesta activo configurado.")
            return context
        
        # Obtener próxima prioridad disponible para inicializar el formulario
        proxima_prioridad = ReglaFiltrado.objects.filter(servicio=servicio).aggregate(Max('prioridad'))['prioridad__max']
        proxima_prioridad = proxima_prioridad + 10 if proxima_prioridad is not None else 10
        
        if self.request.POST:
            # Si es POST, añadir el formset con los datos POST
            context['formset'] = CondicionReglaInlineFormSet(self.request.POST)
        else:
            # Si es GET, inicializar el formulario y formset vacíos
            self.get_form().initial['prioridad'] = proxima_prioridad
            context['formset'] = CondicionReglaInlineFormSet()
        
        context['es_creacion'] = True
        context['active_menu'] = 'ingesta_correo'
        context['active_submenu'] = 'reglas'
        return context
    
    def form_valid(self, form):
        tenant = self.request.user.tenant
        servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
        
        if not servicio:
            messages.warning(self.request, "No hay un servicio de ingesta activo configurado.")
            return self.form_invalid(form)
        
        # Guardar la regla con los datos básicos
        regla = form.save(commit=False)
        regla.servicio = servicio
        regla.creado_por = self.request.user
        regla.modificado_por = self.request.user
        regla.save()
        
        # Si es regla compuesta, validar y guardar el formset de condiciones
        if regla.es_compuesta:
            formset = CondicionReglaInlineFormSet(self.request.POST, instance=regla)
            if formset.is_valid():
                formset.save()
            else:
                # Si el formset no es válido, eliminar la regla y mostrar errores
                regla.delete()
                return self.form_invalid(form)
        
        messages.success(self.request, f'Regla "{regla.nombre}" creada correctamente.')
        self.object = regla
        return super().form_valid(form)

class ReglaEditarView(LoginRequiredMixin, UpdateView):
    """Vista basada en clase para editar una regla existente."""
    model = ReglaFiltrado
    form_class = ReglaFiltradoForm
    template_name = 'ingesta_correo/reglas/regla_form.html'
    pk_url_kwarg = 'regla_id'
    
    def get_success_url(self):
        return reverse('ingesta_correo:regla_detail', kwargs={'regla_id': self.object.id})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        tenant = self.request.user.tenant
        servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
        kwargs['servicio'] = servicio
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['formset'] = CondicionReglaInlineFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = CondicionReglaInlineFormSet(instance=self.object)
        
        context['es_creacion'] = False
        context['regla'] = self.object
        context['active_menu'] = 'ingesta_correo'
        context['active_submenu'] = 'reglas'
        return context
    
    def form_valid(self, form):
        # Guardar la regla con los datos básicos
        regla = form.save(commit=False)
        regla.modificado_por = self.request.user
        regla.save()
        
        # Si es regla compuesta, validar y guardar el formset de condiciones
        if regla.es_compuesta:
            formset = CondicionReglaInlineFormSet(self.request.POST, instance=regla)
            if formset.is_valid():
                formset.save()
            else:
                return self.form_invalid(form)
        
        messages.success(self.request, f'Regla "{regla.nombre}" actualizada correctamente.')
        return super().form_valid(form)

class ReglaEliminarView(LoginRequiredMixin, View):
    """Vista para eliminar una regla."""
    
    def post(self, request, regla_id):
        try:
            # Verificar que la regla pertenezca al tenant del usuario
            regla = get_object_or_404(ReglaFiltrado, 
                id=regla_id, 
                servicio__tenant=request.user.tenant
            )
            
            # Eliminar la regla usando el servicio
            ReglaFiltradoService.eliminar_regla(
                regla_id=regla.id,
                usuario=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Regla "{regla.nombre}" eliminada correctamente'
            })
            
        except Exception as e:
            logger.error(f"Error al eliminar regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Error al eliminar la regla: {str(e)}"
            }, status=400)

class ReglaFiltradoApiView(LoginRequiredMixin, View):
    """API para operaciones CRUD de reglas de filtrado."""
    
    @method_decorator(csrf_protect)
    def get(self, request, regla_id=None):
        """
        Obtiene detalles de una regla específica o lista todas las reglas.
        
        Args:
            request: Solicitud HTTP
            regla_id: ID opcional de la regla para obtener detalles
            
        Returns:
            JsonResponse con los datos solicitados
        """
        tenant = request.user.tenant
        
        try:
            if regla_id:
                # Obtener una regla específica
                try:
                    regla = ReglaFiltrado.objects.get(id=regla_id)
                    
                    # Verificar permisos
                    if regla.servicio.tenant != tenant and not request.user.is_superuser:
                        return JsonResponse({
                            'success': False,
                            'message': 'No tiene permisos para ver esta regla.'
                        }, status=403)
                    
                    # Devolver datos de la regla
                    return JsonResponse({
                        'success': True,
                        'regla': {
                            'id': regla.id,
                            'nombre': regla.nombre,
                            'campo': regla.campo,
                            'condicion': regla.condicion,
                            'valor': regla.valor,
                            'accion': regla.accion,
                            'activa': regla.activa,
                            'prioridad': regla.prioridad,
                            'creado_en': regla.creado_en.isoformat() if regla.creado_en else None,
                            'modificado_en': regla.modificado_en.isoformat() if regla.modificado_en else None,
                            'creado_por': regla.creado_por.email if regla.creado_por else None
                        }
                    })
                    
                except ReglaFiltrado.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Regla no encontrada.'
                    }, status=404)
            else:
                # Obtener todas las reglas
                reglas = ReglaFiltradoService.get_reglas_for_tenant(tenant)
                
                # Formatear los datos para la respuesta
                reglas_data = [{
                    'id': regla.id,
                    'nombre': regla.nombre,
                    'campo': regla.campo,
                    'campo_display': regla.get_campo_display(),
                    'condicion': regla.condicion,
                    'condicion_display': regla.get_condicion_display(),
                    'valor': regla.valor,
                    'accion': regla.accion,
                    'accion_display': regla.get_accion_display(),
                    'activa': regla.activa,
                    'prioridad': regla.prioridad,
                } for regla in reglas]
                
                return JsonResponse({
                    'success': True,
                    'reglas': reglas_data
                })
                
        except Exception as e:
            logger.error(f"Error al obtener reglas: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al obtener reglas: {str(e)}'
            }, status=500)
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """
        Crea una nueva regla de filtrado.
        
        Args:
            request: Solicitud HTTP con datos de la regla
            
        Returns:
            JsonResponse con el resultado de la operación
        """
        try:
            tenant = request.user.tenant
            usuario = request.user
            
            # Obtener datos del cuerpo de la solicitud
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                # Si no es JSON, intentar obtener de POST
                data = request.POST.dict()
            
            # Crear regla usando el servicio
            regla = ReglaFiltradoService.crear_regla(tenant, usuario, data)
            
            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': 'Regla creada correctamente.',
                'regla': {
                    'id': regla.id,
                    'nombre': regla.nombre,
                    'campo': regla.campo,
                    'campo_display': regla.get_campo_display(),
                    'condicion': regla.condicion,
                    'condicion_display': regla.get_condicion_display(),
                    'valor': regla.valor,
                    'accion': regla.accion,
                    'accion_display': regla.get_accion_display(),
                    'activa': regla.activa,
                    'prioridad': regla.prioridad,
                }
            })
            
        except ValidationError as e:
            logger.warning(f"Error de validación al crear regla: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al crear regla: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al crear la regla: {str(e)}'
            }, status=500)
    
    @method_decorator(csrf_protect)
    def put(self, request, regla_id):
        """
        Actualiza una regla de filtrado existente.
        
        Args:
            request: Solicitud HTTP con datos actualizados
            regla_id: ID de la regla a actualizar
            
        Returns:
            JsonResponse con el resultado de la operación
        """
        try:
            usuario = request.user
            
            # Obtener datos del cuerpo de la solicitud
            data = json.loads(request.body)
            
            # Actualizar regla usando el servicio
            regla = ReglaFiltradoService.actualizar_regla(regla_id, usuario, data)
            
            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': 'Regla actualizada correctamente.',
                'regla': {
                    'id': regla.id,
                    'nombre': regla.nombre,
                    'campo': regla.campo,
                    'campo_display': regla.get_campo_display(),
                    'condicion': regla.condicion,
                    'condicion_display': regla.get_condicion_display(),
                    'valor': regla.valor,
                    'accion': regla.accion,
                    'accion_display': regla.get_accion_display(),
                    'activa': regla.activa,
                    'prioridad': regla.prioridad,
                }
            })
            
        except ValidationError as e:
            logger.warning(f"Error de validación al actualizar regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except json.JSONDecodeError:
            logger.warning(f"Error al parsear JSON de la solicitud para actualizar regla {regla_id}")
            return JsonResponse({
                'success': False,
                'message': 'Formato de datos inválido. Se esperaba JSON.'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al actualizar regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar la regla: {str(e)}'
            }, status=500)
    
    @method_decorator(csrf_protect)
    def delete(self, request, regla_id):
        """
        Elimina una regla de filtrado.
        """
        try:
            # Verificar que la regla pertenezca al tenant del usuario
            regla = get_object_or_404(ReglaFiltrado, 
                id=regla_id, 
                servicio__tenant=request.user.tenant
            )
            
            # Guardar nombre para mensaje
            nombre_regla = regla.nombre
            
            # Eliminar la regla
            ReglaFiltradoService.eliminar_regla(
                regla_id=regla.id,
                usuario=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Regla "{nombre_regla}" eliminada correctamente'
            })
            
        except Exception as e:
            logger.error(f"Error al eliminar regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Error al eliminar la regla: {str(e)}"
            })

class ReglaEstadoView(LoginRequiredMixin, View):
    """Vista para cambiar el estado (activo/inactivo) de una regla."""
    
    @method_decorator(csrf_protect)
    def post(self, request, regla_id):
        """
        Cambia el estado de una regla.
        
        Args:
            request: Solicitud HTTP con el nuevo estado
            regla_id: ID de la regla
            
        Returns:
            JsonResponse con el resultado de la operación
        """
        try:
            usuario = request.user
            
            # Obtener el estado del cuerpo de la solicitud
            try:
                data = json.loads(request.body)
                activa = data.get('activa', False)
            except json.JSONDecodeError:
                # Si no es JSON, intentar obtener de POST
                activa = request.POST.get('activa') == 'true'
            
            # Cambiar estado usando el servicio
            regla = ReglaFiltradoService.cambiar_estado_regla(regla_id, usuario, activa)
            
            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': f'Estado de la regla {"activado" if activa else "desactivado"} correctamente.',
                'activa': regla.activa
            })
            
        except ValidationError as e:
            logger.warning(f"Error de validación al cambiar estado de regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al cambiar estado de regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al cambiar estado de la regla: {str(e)}'
            }, status=500)

class ReglasReordenarView(LoginRequiredMixin, View):
    """Vista para reordenar las prioridades de las reglas."""
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """
        Actualiza el orden de prioridad de las reglas.
        
        Args:
            request: Solicitud HTTP con el nuevo orden
            
        Returns:
            JsonResponse con el resultado de la operación
        """
        try:
            usuario = request.user
            
            # Obtener los datos de ordenamiento
            try:
                data = json.loads(request.body)
                orden_reglas = data.get('orden', [])
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de datos inválido. Se esperaba JSON.'
                }, status=400)
            
            # Reordenar reglas usando el servicio
            ReglaFiltradoService.reordenar_reglas(usuario, orden_reglas)
            
            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': 'Reglas reordenadas correctamente.'
            })
            
        except ValidationError as e:
            logger.warning(f"Error de validación al reordenar reglas: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al reordenar reglas: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al reordenar reglas: {str(e)}'
            }, status=500)

@login_required
def reglas_list(request):
    """Vista para listar todas las reglas de filtrado."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        messages.warning(request, "No hay un servicio de ingesta activo configurado.")
        return redirect('ingesta_correo:ingesta_control_panel')
    
    # Obtener todas las reglas para este servicio
    reglas = ReglaFiltrado.objects.filter(servicio=servicio).order_by('prioridad', 'nombre')
    
    # Obtener categorías para el filtro
    categorias = CategoriaRegla.objects.filter(servicio=servicio)
    
    # Aplicar filtros
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')
    accion = request.GET.get('accion')
    busqueda = request.GET.get('busqueda')
    
    if categoria_id and categoria_id != 'todos':
        reglas = reglas.filter(categoria_id=categoria_id)
        
    if estado:
        if estado == 'activas':
            reglas = reglas.filter(activa=True)
        elif estado == 'inactivas':
            reglas = reglas.filter(activa=False)
            
    if tipo:
        if tipo == 'simples':
            reglas = reglas.filter(es_compuesta=False)
        elif tipo == 'compuestas':
            reglas = reglas.filter(es_compuesta=True)
            
    if accion:
        reglas = reglas.filter(accion=accion)
        
    if busqueda:
        reglas = reglas.filter(nombre__icontains=busqueda) | reglas.filter(descripcion__icontains=busqueda)
    
    # Estadísticas
    estadisticas = {
        'total_reglas': reglas.count(),
        'reglas_activas': reglas.filter(activa=True).count(),
        'reglas_simples': reglas.filter(es_compuesta=False).count(),
        'reglas_compuestas': reglas.filter(es_compuesta=True).count(),
    }
    
    # Si es una petición AJAX, devolver sólo la tabla
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            'ingesta_correo/reglas/reglas_table.html', 
            {'reglas': reglas, 'estadisticas': estadisticas}
        )
        return JsonResponse({'html': html})
    
    return render(request, 'ingesta_correo/reglas/reglas_list.html', {
        'reglas': reglas,
        'categorias': categorias,
        'estadisticas': estadisticas,
        'tipo_acciones': ReglaFiltrado.TipoAccion.choices,
        'filtros': {
            'categoria': categoria_id,
            'estado': estado,
            'tipo': tipo,
            'accion': accion,
            'busqueda': busqueda
        }
    })

@login_required
def regla_detail(request, regla_id):
    """Vista para ver los detalles de una regla específica."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        messages.warning(request, "No hay un servicio de ingesta activo configurado.")
        return redirect('ingesta_correo:ingesta_control_panel')
    
    regla = get_object_or_404(ReglaFiltrado, id=regla_id, servicio=servicio)
    
    # Obtener condiciones si es una regla compuesta
    condiciones = None
    if regla.es_compuesta:
        condiciones = regla.condiciones.all().order_by('orden')
    
    # Obtener historial de aplicación
    historial = HistorialAplicacionRegla.objects.filter(regla=regla).order_by('-fecha_aplicacion')[:20]
    
    return render(request, 'ingesta_correo/reglas/regla_detail.html', {
        'regla': regla,
        'condiciones': condiciones,
        'historial': historial
    })

@login_required
def regla_create(request):
    """Vista para crear una nueva regla de filtrado."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        messages.warning(request, "No hay un servicio de ingesta activo configurado.")
        return redirect('ingesta_correo:ingesta_control_panel')
    
    # Obtener próxima prioridad disponible
    proxima_prioridad = ReglaFiltrado.objects.filter(servicio=servicio).aggregate(Max('prioridad'))['prioridad__max']
    proxima_prioridad = proxima_prioridad + 10 if proxima_prioridad is not None else 10
    
    if request.method == 'POST':
        form = ReglaFiltradoForm(request.POST, servicio=servicio)
        formset = CondicionReglaInlineFormSet(request.POST, instance=ReglaFiltrado())
        
        if form.is_valid():
            regla = form.save(commit=False)
            regla.servicio = servicio
            regla.creado_por = request.user
            regla.modificado_por = request.user
            regla.save()
            
            # Si es una regla compuesta, guardar las condiciones
            if regla.es_compuesta:
                formset = CondicionReglaInlineFormSet(request.POST, instance=regla)
                if formset.is_valid():
                    formset.save()
                else:
                    # Si el formset no es válido, mostrar errores y eliminar la regla
                    regla.delete()
                    return render(request, 'ingesta_correo/reglas/regla_form.html', {
                        'form': form,
                        'formset': formset,
                        'es_creacion': True
                    })
            
            messages.success(request, f'Regla "{regla.nombre}" creada correctamente.')
            return redirect('ingesta_correo:regla_detail', regla_id=regla.id)
    else:
        form = ReglaFiltradoForm(servicio=servicio, initial={'prioridad': proxima_prioridad})
        formset = CondicionReglaInlineFormSet(instance=ReglaFiltrado())
    
    return render(request, 'ingesta_correo/reglas/regla_form.html', {
        'form': form,
        'formset': formset,
        'es_creacion': True
    })

@login_required
def regla_edit(request, regla_id):
    """Vista para editar una regla existente."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        messages.warning(request, "No hay un servicio de ingesta activo configurado.")
        return redirect('ingesta_correo:ingesta_control_panel')
    
    regla = get_object_or_404(ReglaFiltrado, id=regla_id, servicio=servicio)
    
    if request.method == 'POST':
        form = ReglaFiltradoForm(request.POST, instance=regla, servicio=servicio)
        formset = CondicionReglaInlineFormSet(request.POST, instance=regla)
        
        if form.is_valid():
            regla = form.save(commit=False)
            regla.modificado_por = request.user
            regla.save()
            
            # Si es una regla compuesta, guardar las condiciones
            if regla.es_compuesta:
                if formset.is_valid():
                    formset.save()
                else:
                    return render(request, 'ingesta_correo/reglas/regla_form.html', {
                        'form': form,
                        'formset': formset,
                        'es_creacion': False,
                        'regla': regla
                    })
            
            messages.success(request, f'Regla "{regla.nombre}" actualizada correctamente.')
            return redirect('ingesta_correo:regla_detail', regla_id=regla.id)
    else:
        form = ReglaFiltradoForm(instance=regla, servicio=servicio)
        formset = CondicionReglaInlineFormSet(instance=regla)
    
    return render(request, 'ingesta_correo/reglas/regla_form.html', {
        'form': form,
        'formset': formset,
        'es_creacion': False,
        'regla': regla
    })

@login_required
@csrf_protect
def regla_delete(request, regla_id):
    """Vista para eliminar una regla."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        return JsonResponse({'success': False, 'message': "No hay un servicio de ingesta activo configurado."})
    
    regla = get_object_or_404(ReglaFiltrado, id=regla_id, servicio=servicio)
    
    if request.method == 'POST':
        nombre = regla.nombre
        regla.delete()
        return JsonResponse({'success': True, 'message': f'Regla "{nombre}" eliminada correctamente.'})
    
    return JsonResponse({'success': False, 'message': 'Método no soportado.'})

class ReglaToggleView(LoginRequiredMixin, View):
    """Vista para activar/desactivar una regla de filtrado."""
    
    def post(self, request, regla_id):
        try:
            # Obtener la regla verificando que pertenezca al tenant del usuario
            regla = get_object_or_404(ReglaFiltrado, 
                id=regla_id, 
                servicio__tenant=request.user.tenant
            )
            
            # Cambiar el estado usando el servicio
            resultado = ReglaFiltradoService.cambiar_estado_regla(
                regla_id=regla.id,
                usuario=request.user,
                activa=not regla.activa
            )
            
            # Construir mensaje descriptivo
            mensaje = f'Regla {"activada" if resultado.activa else "desactivada"} correctamente'
            
            return JsonResponse({
                'success': True,
                'message': mensaje,
                'activo': resultado.activa
            })
            
        except Exception as e:
            logger.error(f"Error al cambiar estado de regla {regla_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Error al cambiar el estado de la regla: {str(e)}"
            }, status=400)

@login_required
@csrf_protect
def regla_reorder(request):
    """Vista para reordenar reglas."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        return JsonResponse({'success': False, 'message': "No hay un servicio de ingesta activo configurado."})
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        regla_ids = request.POST.getlist('regla_ids[]')
        
        # Actualizar prioridades
        for i, regla_id in enumerate(regla_ids):
            try:
                regla = ReglaFiltrado.objects.get(id=regla_id, servicio=servicio)
                regla.prioridad = (i + 1) * 10
                regla.save(update_fields=['prioridad'])
            except ReglaFiltrado.DoesNotExist:
                pass
                
        return JsonResponse({'success': True, 'message': 'Orden de reglas actualizado correctamente.'})
    
    return JsonResponse({'success': False, 'message': 'Método no soportado.'})

@login_required
def categorias_list(request):
    """Vista para listar categorías de reglas."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        messages.warning(request, "No hay un servicio de ingesta activo configurado.")
        return redirect('ingesta_correo:ingesta_control_panel')
    
    categorias = CategoriaRegla.objects.filter(servicio=servicio).annotate(num_reglas=Count('reglas')).order_by('nombre')
    
    return render(request, 'ingesta_correo/reglas/categorias_list.html', {
        'categorias': categorias
    })

@login_required
def categoria_create(request):
    """Vista para crear una nueva categoría."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        messages.warning(request, "No hay un servicio de ingesta activo configurado.")
        return redirect('ingesta_correo:ingesta_control_panel')
    
    if request.method == 'POST':
        form = CategoriaReglaForm(request.POST, servicio=servicio)
        
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada correctamente.')
            return redirect('ingesta_correo:categorias_list')
    else:
        form = CategoriaReglaForm(servicio=servicio)
    
    return render(request, 'ingesta_correo/reglas/categoria_form.html', {
        'form': form,
        'es_creacion': True
    })

@login_required
def categoria_edit(request, categoria_id):
    """Vista para editar una categoría existente."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        messages.warning(request, "No hay un servicio de ingesta activo configurado.")
        return redirect('ingesta_correo:ingesta_control_panel')
    
    categoria = get_object_or_404(CategoriaRegla, id=categoria_id, servicio=servicio)
    
    if request.method == 'POST':
        form = CategoriaReglaForm(request.POST, instance=categoria, servicio=servicio)
        
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada correctamente.')
            return redirect('ingesta_correo:categorias_list')
    else:
        form = CategoriaReglaForm(instance=categoria, servicio=servicio)
    
    return render(request, 'ingesta_correo/reglas/categoria_form.html', {
        'form': form,
        'es_creacion': False,
        'categoria': categoria
    })

@login_required
@csrf_protect
def categoria_delete(request, categoria_id):
    """Vista para eliminar una categoría."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        return JsonResponse({'success': False, 'message': "No hay un servicio de ingesta activo configurado."})
    
    categoria = get_object_or_404(CategoriaRegla, id=categoria_id, servicio=servicio)
    
    # Verificar si hay reglas usando esta categoría
    if categoria.reglas.exists():
        return JsonResponse({
            'success': False, 
            'message': f'No se puede eliminar la categoría porque tiene {categoria.reglas.count()} reglas asociadas.'
        })
    
    if request.method == 'POST':
        nombre = categoria.nombre
        categoria.delete()
        return JsonResponse({'success': True, 'message': f'Categoría "{nombre}" eliminada correctamente.'})
    
    return JsonResponse({'success': False, 'message': 'Método no soportado.'})

@login_required
def regla_test(request, regla_id=None):
    """Vista para probar una regla contra ejemplos de correos."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        messages.warning(request, "No hay un servicio de ingesta activo configurado.")
        return redirect('ingesta_correo:ingesta_control_panel')
    
    regla = None
    if regla_id:
        regla = get_object_or_404(ReglaFiltrado, id=regla_id, servicio=servicio)
    
    # Obtener correos para probar
    correos = CorreoIngesta.objects.filter(servicio=servicio).order_by('-fecha_recepcion')[:20]
    
    # Obtener todas las reglas para el selector
    reglas = ReglaFiltrado.objects.filter(servicio=servicio, activa=True).order_by('prioridad', 'nombre')
    
    # Resultados de la prueba
    resultados = []
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        regla_id = request.POST.get('regla_id')
        correo_id = request.POST.get('correo_id')
        
        try:
            regla = ReglaFiltrado.objects.get(id=regla_id, servicio=servicio)
            correo = CorreoIngesta.objects.get(id=correo_id, servicio=servicio)
            
            # Evaluar la regla
            resultado = regla.evaluar(correo)
            
            # Detalles de evaluación
            detalles = {
                'evaluacion': resultado,
                'fecha': timezone.now().isoformat(),
                'accion': regla.get_accion_display(),
                'detalles': {}
            }
            
            # Si es regla compuesta, detallar cada condición
            if regla.es_compuesta:
                condiciones_detalle = []
                for condicion in regla.condiciones.all():
                    resultado_condicion = condicion.evaluar(correo)
                    condiciones_detalle.append({
                        'campo': condicion.get_campo_display(),
                        'condicion': condicion.get_condicion_display(),
                        'valor': condicion.valor,
                        'resultado': resultado_condicion
                    })
                detalles['detalles']['condiciones'] = condiciones_detalle
                detalles['detalles']['operador'] = regla.get_operador_logico_display()
            else:
                # Detalles para regla simple
                valor_campo = regla._obtener_valor_campo(correo, regla.campo)
                detalles['detalles'] = {
                    'campo': regla.get_campo_display(),
                    'condicion': regla.get_condicion_display(),
                    'valor_esperado': regla.valor,
                    'valor_encontrado': valor_campo
                }
            
            # Guardar el historial de prueba
            HistorialAplicacionRegla.objects.create(
                regla=regla,
                correo=correo,
                resultado=resultado,
                accion_ejecutada=regla.get_accion_display(),
                detalles=detalles
            )
            
            return JsonResponse({
                'success': True,
                'resultado': resultado,
                'detalles': detalles
            })
        except (ReglaFiltrado.DoesNotExist, CorreoIngesta.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Regla o correo no encontrado.'})
    
    return render(request, 'ingesta_correo/reglas/regla_test.html', {
        'regla_seleccionada': regla,
        'reglas': reglas,
        'correos': correos
    })

@login_required
def batch_test(request):
    """Vista para probar todas las reglas contra un conjunto de correos."""
    tenant = get_tenant_for_user(request.user)
    servicio = tenant.servicioingestaconfig.active_service if hasattr(tenant, 'servicioingestaconfig') else None
    
    if not servicio:
        messages.warning(request, "No hay un servicio de ingesta activo configurado.")
        return redirect('ingesta_correo:ingesta_control_panel')
    
    # Obtener correos para probar
    correos = CorreoIngesta.objects.filter(servicio=servicio).order_by('-fecha_recepcion')[:10]
    
    # Obtener reglas activas
    reglas = ReglaFiltrado.objects.filter(servicio=servicio, activa=True).order_by('prioridad', 'nombre')
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        correo_ids = request.POST.getlist('correo_ids[]')
        
        resultados = []
        
        for correo_id in correo_ids:
            try:
                correo = CorreoIngesta.objects.get(id=correo_id, servicio=servicio)
                correo_resultado = {
                    'correo_id': correo.id,
                    'asunto': correo.asunto,
                    'remitente': correo.remitente,
                    'resultados': []
                }
                
                for regla in reglas:
                    # Evaluar la regla
                    resultado = regla.evaluar(correo)
                    correo_resultado['resultados'].append({
                        'regla_id': regla.id,
                        'nombre': regla.nombre,
                        'resultado': resultado,
                        'accion': regla.get_accion_display()
                    })
                
                resultados.append(correo_resultado)
            except CorreoIngesta.DoesNotExist:
                pass
                
        return JsonResponse({
            'success': True,
            'resultados': resultados
        })
    
    return render(request, 'ingesta_correo/reglas/batch_test.html', {
        'correos': correos,
        'reglas': reglas
    })

class ReglaTestView(View):
    def post(self, request, regla_id):
        regla = get_object_or_404(ReglaFiltrado, id=regla_id, tenant=request.tenant)
        datos_prueba = request.POST.dict()
        
        servicio = ReglaTestService()
        resultado = servicio.evaluar_regla_completa(regla, datos_prueba)
        
        return JsonResponse(resultado)