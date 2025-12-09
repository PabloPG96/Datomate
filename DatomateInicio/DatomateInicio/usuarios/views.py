from datetime import datetime, timedelta
from django.utils import timezone
import requests
from django.contrib import messages

from django.shortcuts import render, redirect
from django.views import View
import json


#API_ENDPOINT_HISTORICO = 'http://127.0.0.1:6000/'
#API_ENDPOINT_USUARIOS = 'http://127.0.0.1:5000/'
#API_ENDPOINT_MODELO = 'http://127.0.0.1:7000/'

API_ENDPOINT_HISTORICO = 'https://img-historial-90018350665.northamerica-south1.run.app'
API_ENDPOINT_USUARIOS = 'https://img-users-90018350665.northamerica-south1.run.app'
API_ENDPOINT_MODELO = 'https://img-modelo-90018350665.northamerica-south1.run.app'
# https://img-modelo-90018350665.northamerica-south1.run.app
# http://127.0.0.1:7000/

# Vista para la página de Inicio
class InicioAfterLoginView(View):
    template_name = 'usuarios/inicio.html'

    def get(self, request):
        # 1. Obtener el Token JWT de la Sesión
        token = request.session.get('access_token')

        if token is None:
            messages.error(request, "Debes iniciar sesión para acceder a los datos.")
            return redirect('usuarios:login')

        # Inicializar datos por defecto
        ultimos_registros = []
        humedad = 'N/A'
        temperatura = 'N/A'
        produccion = 'N/A'
        fechas_etiquetas = []
        temp_data = []
        hum_data = []

        # --- Configuración del Request ---
        headers = {"Authorization": f"Bearer {token}"}
        params = {'limit': 6, 'ordering': '-created_at'}

        try:
            response = requests.get((API_ENDPOINT_HISTORICO + "/api/v1/historico/"), headers=headers, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                registros_obtenidos = []

                if isinstance(data, dict) and 'results' in data:
                    registros_obtenidos = data.get('results', [])
                elif isinstance(data, list):
                    registros_obtenidos = data

                if registros_obtenidos:
                    registros_obtenidos.sort(key=lambda x: x.get('created_at', ''), reverse=True)

                    # Tomar SOLAMENTE los 6 más recientes
                    registros_mas_recientes = registros_obtenidos[:6]

                    registro_mas_reciente = registros_mas_recientes[0]

                    # Función auxiliar para convertir de forma segura
                    def safe_int(value, default=0):
                        try:
                            return int(float(value))
                        except (TypeError, ValueError):
                            return default

                    temp_raw = registro_mas_reciente.get('Temp_Media')
                    hum_raw = registro_mas_reciente.get('Humedad_Media')
                    prod_raw = registro_mas_reciente.get('Produccion_Media')

                    temperatura = f"{safe_int(temp_raw)} °C"
                    humedad = f"{safe_int(hum_raw)} %"
                    produccion = f"{safe_int(prod_raw)} Kg"


                    # Invertimos para la gráfica: [Antiguo, ..., Reciente]
                    registros_para_grafica = registros_mas_recientes.copy()
                    registros_para_grafica.reverse()

                    ultimos_registros_temp = []  # Para la tabla (se llenará en orden ascendente)

                    for reg in registros_para_grafica:
                        # --- Procesamiento de Fechas y Datos Numéricos ---
                        fecha_raw = reg.get('created_at')

                        if fecha_raw:
                            dt_object = datetime.fromisoformat(fecha_raw.replace('Z', '+00:00'))
                            fecha_tabla = dt_object.strftime('%Y/%m/%d')
                            fecha_etiqueta = dt_object.strftime('%d %b')
                        else:
                            fecha_tabla = 'N/D'
                            fecha_etiqueta = 'N/D'

                        temp_valor = round(reg.get('Temp_Media', 0))
                        hum_valor = round(reg.get('Humedad_Media', 0))

                        # 1. Datos para la TABLA
                        ultimos_registros_temp.append({
                            'fecha': fecha_tabla,
                            'temp': f"{temp_valor} °C",
                            'hum': f"{hum_valor} %",
                        })

                        # 2. Datos para la GRÁFICA (numéricos, en orden ASCENDENTE)
                        fechas_etiquetas.append(fecha_etiqueta)
                        temp_data.append(temp_valor)
                        hum_data.append(hum_valor)

                    # Invertir para la TABLA: [Reciente, ..., Antiguo]
                    ultimos_registros = ultimos_registros_temp.copy()
                    ultimos_registros.reverse()

            elif response.status_code == 401 or response.status_code == 403:
                messages.error(request,"Tu sesión ha expirado o no tienes permisos. Inicia sesión nuevamente.")
                return redirect('usuarios:login')

            else:
                messages.error(request, f"Error al obtener datos: {response.status_code}. Mensaje: {response.text}")

        except requests.exceptions.RequestException as e:
            messages.error(request, f"Error de conexión con el Microservicio de Datos: {e}")

        # 6. Enviar el contexto a la plantilla
        context = {
            "ultimos_registros": ultimos_registros,
            "fechas_etiquetas_json": json.dumps(fechas_etiquetas),
            "temp_data_json": json.dumps(temp_data),
            "hum_data_json": json.dumps(hum_data),
            "humedad": humedad,
            "temperatura": temperatura,
            "produccion": produccion,
        }
        return render(request, self.template_name, context)

def captura_view(request):
    # La lógica para procesar el formulario POST (envío de datos a la API)
    if request.method == 'POST':
        # Aquí iría el código para recoger los datos y enviarlos a la API
        # Por ahora, solo vamos a simular un éxito y redirigir:

        # 1. Recoger los datos del formulario (ejemplo)
        humedad = request.POST.get('humedad')
        temperatura = request.POST.get('temperatura')
        longitud_tallo = request.POST.get('longitud_tallo')
        diametro_tallo = request.POST.get('diametro_tallo')
        notas = request.POST.get('notas')

        # 2. Lógica de comunicación con la API externa (PENDIENTE)
        # requests.post(API_URL, data={'...'})

        # 3. Mostrar un mensaje de éxito (usaremos el sistema de messages de Django)
        from django.contrib import messages
        messages.success(request, f'Datos capturados exitosamente: Humedad={humedad}, Temp={temperatura}')

        # 4. Redirigir a la misma página o a una de éxito
        return redirect('usuarios:captura')

    # La lógica para mostrar el formulario (método GET)
    context = {
        'current_page': 'captura',
    }
    return render(request, 'usuarios/captura.html', context)

def reportes_view(request):
    context = {
        'current_page': 'reportes',
    }
    return render(request, 'usuarios/reportes.html', context)

def predicciones_view(request):
    context = {
        'current_page': 'predicciones',
    }
    return render(request, 'usuarios/predicciones.html', context)


def alertas_view(request):
    # Datos de ejemplo para las alertas
    alertas_activas = [
        {'tipo': 'Temperatura alta en el lote', 'tiempo': 'Hace 2 horas', 'color': 'warning'},
        {'tipo': 'Posible plaga: Araña roja', 'confianza': '92% de confianza', 'tiempo': 'Hace 5 minutos',
         'color': 'danger', 'leido': False},
        {'tipo': 'Posible plaga: Plaga del riego', 'confianza': '54% de confianza', 'tiempo': 'Hace 5 minutos',
         'color': 'warning', 'leido': True},
    ]

    context = {
        'current_page': 'alertas',
        'alertas_activas': alertas_activas,
    }
    return render(request, 'usuarios/alertas.html', context)


def perfil_view(request):
    if request.method == 'POST':
        # Lógica para procesar la actualización de datos
        pais = request.POST.get('pais')
        username = request.POST.get('username')
        descripcion = request.POST.get('descripcion')

        # 1. Lógica de comunicación con la API externa para actualizar (PENDIENTE)
        # requests.post(API_URL_UPDATE, data={'...'})

        messages.success(request, f'Perfil actualizado exitosamente para el usuario: {username}')
        return redirect('usuarios:perfil')

    # La lógica para mostrar el formulario (método GET)
    context = {
        'current_page': 'perfil',
        # Datos de ejemplo o datos obtenidos de la API (simulación)
        'datos_perfil': {
            'nombre_actual': 'Jhonny Castillo',
            'pais_actual': 'México',
            'email': 'jhonny.c@datomate.com',
            'descripcion_actual': 'Experto en monitoreo y predicción de cultivos de tomate.',
        }
    }
    return render(request, 'usuarios/perfil.html', context)

def cerrar_sesion_view(request):
    # Por ahora, simplemente redirige a inicio o a la página de login (si la tuvieras)
    return render(request, 'usuarios/placeholder.html', {'current_page': '', 'titulo': 'Cerrar Sesión'})


#ViewS de Usuario enfocado a su cuenta -------------------------------

class activarCuenta(View):
    template_name = "inicioUsuarios/active_account.html"
    # URL de tu microservicio MS-Usuarios
    api_url = API_ENDPOINT_USUARIOS + "/accounts/activar/"

    def get(self, request):
        return render(request, self.template_name, {})

    def post(self, request):
        # 1. Recibir la información del formulario
        email = request.POST.get("email")
        otp = request.POST.get("otp")

        # 2. Preparar el JSON
        payload = {
            "email": email,
            "otp": otp,
        }
        print("Enviando payload de activación:", payload)

        try:
            # 3. Enviar al microservicio
            response = requests.post(self.api_url, json=payload)

            try:
                data = response.json()
            except ValueError:
                data = {"detail": "Respuesta inesperada del servidor."}

            # 4. Verificar respuesta (200 OK suele ser para activación exitosa)
            if response.status_code == 200:
                # Éxito
                messages.success(request, "¡Cuenta activada correctamente! Ya puedes iniciar sesión.")
                print("Cuenta activada.")

                # Redireccionar al Login
                return redirect("usuarios:login")

            else:
                # Fallo (OTP incorrecto, expirado, usuario no encontrado, etc.)
                mensaje_error = data.get("detail") or data.get("error") or "No se pudo activar la cuenta."
                messages.error(request, mensaje_error)
                print(f"Error activando cuenta: {mensaje_error}")

                # Renderizamos la misma página para que intente de nuevo.
                # Pasamos el 'email' en el contexto para que no tenga que escribirlo otra vez
                return render(request, self.template_name, {"email": email})

        except requests.exceptions.RequestException as e:
            # 5. Error de conexión
            err_msg = "Error al conectar con el servicio de Activación"
            messages.error(request, err_msg)
            print("Error de Conexión:", e)
            return render(request, self.template_name, {"email": email})


class forgotCuenta(View):
    template_name = "inicioUsuarios/forgot_password.html"
    api_url = API_ENDPOINT_USUARIOS + "/accounts/forgot/"

    def get(self, request):
        return render(request, self.template_name, {})

    def post(self, request):
        telefono_celular = request.POST.get("telefono_celular")
        email = request.POST.get("email")  # Opcional, por si usas ambos

        if not telefono_celular and not email:
            messages.error(request, "Por favor ingresa un teléfono o correo.")
            return render(request, self.template_name, {})


        payload = {}
        if telefono_celular:
            payload["telefono_celular"] = telefono_celular
        if email:
            payload["email"] = email

        print("Solicitando recuperación para:", payload)

        try:
            response = requests.post(self.api_url, json=payload)

            try:
                data = response.json()
            except ValueError:
                data = {"detail": "Error inesperado del servidor."}

            if response.status_code == 200:
                messages.success(request, "Se ha enviado un código OTP a tu correo/teléfono.")

                # Guardamos el identificador en la sesión para el siguiente paso
                # Así la vista de 'reset' sabe a quién cambiarle la contraseña
                if telefono_celular:
                    request.session['reset_telefono'] = telefono_celular
                if email:
                    request.session['reset_email'] = email

                # Redirigir a la vista de "Reset Password" (donde ponen el OTP y la nueva clave)
                # Asegúrate de tener esta URL definida en tus urls.py, por ejemplo 'usuarios:reset'
                return redirect("usuarios:reset")

            else:
                # Error (Usuario no encontrado, etc.)
                mensaje_error = data.get("detail") or data.get("error") or "No se pudo procesar la solicitud."
                messages.error(request, mensaje_error)
                return render(request, self.template_name, {})

        except requests.exceptions.RequestException as e:
            err_msg = "Error al conectar con el servicio de Recuperación"
            messages.error(request, err_msg)
            print("Error de Conexión:", e)
            return render(request, self.template_name, {})

class loginCuenta(View):
    template_name = "inicioUsuarios/login.html"
    api_url = API_ENDPOINT_USUARIOS + "/accounts/login/"

    def get(self, request):
        return render(request, self.template_name, {})

    def post(self, request):
        # Recibir la informacion del front
        identificador = request.POST.get("identificador")
        password = request.POST.get("password")

        payload = {
            "identificador": identificador,
            "password": password,
        }
        print(payload)
        try:
            response = requests.post(self.api_url, json=payload)
            data = response.json()
            # verificar la respuesta
            if response.status_code != 200:
                messages.error(request, "Credenciales incorrectas...")
                return render(request, self.template_name, {"Error": data.get(
                    "detail", "Credenciales incorrectas")
                })

            # Guardar los tokens
            request.session["access_token"] = data.get("access_token")  # **********
            request.session["refresh_token"] = data.get("refresh_token")
            request.session["user"] = data.get("user")
            print("...")
            # Esta es la corrección
            messages.success(request, data.get("mensaje", "Bienvenido a Datomate"))
            print("Usuario Encontrado y redireccionando...")
            return redirect("/inicioAfterLogin/")

        except requests.exceptions.RequestException as e:
            messages.error(request, "Error al conectar con el servicion de Autentificacion")
            print("Error de Conexion", e)
            return render(request, self.template_name,
                          {"Error": "Error al conectar con el servicion de Autentificacion"})


class registroCuenta(View):
    template_name = "inicioUsuarios/registro.html"
    api_url = API_ENDPOINT_USUARIOS + "/accounts/registro/"

    def get(self, request):
        return render(request, self.template_name, {})

    def post(self, request):
        email = request.POST.get("email")
        telefono_celular = request.POST.get("telefono_celular")
        nombre_usuario = request.POST.get("nombre_usuario")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        payload = {
            "email": email,
            "telefono_celular": telefono_celular,
            "nombre_usuario": nombre_usuario,
            "password": password,
            "password2": password2
        }
        print("Enviando payload:", payload)

        try:
            response = requests.post(self.api_url, json=payload)

            # Intentar decodificar la respuesta JSON, incluso si hay error
            try:
                data = response.json()
            except ValueError:
                data = {"detail": "Error inesperado en la respuesta del servidor."}

            if response.status_code not in [200, 201]:
                mensaje_error = data.get("detail") or data.get("error") or str(data)

                messages.error(request, f"Error al registrar: {mensaje_error}")
                print(f"Error API ({response.status_code}): {mensaje_error}")

                # Renderizamos de nuevo el registro con el error
                return render(request, self.template_name, {"Error": mensaje_error})

            # Éxito
            print("Usuario registrado exitosamente.")
            messages.success(request, "Cuenta creada con éxito. Por favor activala.")

            # Redireccionar al Login
            return redirect("usuarios:activar")

        except requests.exceptions.RequestException as e:
            # Error de conexión (Microservicio apagado, etc.)
            err_msg = "Error al conectar con el servicio de Registro"
            messages.error(request, err_msg)
            print("Error de Conexión:", e)
            return render(request, self.template_name, {"Error": err_msg})


class resetCuenta(View):
    template_name = "inicioUsuarios/reset_password.html"
    # Asegúrate que esta URL coincida con tu MS-Usuarios
    api_url = API_ENDPOINT_USUARIOS + "/accounts/reset/"

    def get(self, request):
        return render(request, self.template_name, {})

    def post(self, request):
        # 1. Recuperar el identificador del usuario
        # Intentamos obtenerlo del formulario (si lo pusiste en un input hidden)
        telefono_celular = request.POST.get("telefono_celular")
        email = request.POST.get("email")

        # Si no viene en el formulario, lo sacamos de la sesión (del paso anterior 'forgot')
        if not telefono_celular:
            telefono_celular = request.session.get('reset_telefono')
        if not email:
            email = request.session.get('reset_email')

        # Si no tenemos ni uno ni otro, hay un error de flujo
        if not telefono_celular and not email:
            messages.error(request,
                           "Error de sesión: No se identificó al usuario. Intenta el proceso de recuperación nuevamente.")
            return redirect("usuarios:forgot")  # Redirige al inicio del proceso

        # 2. Obtener el resto de datos
        otp = request.POST.get("otp")
        new_password = request.POST.get("new_password")
        new_password2 = request.POST.get("new_password2")

        # 3. Armar el payload
        payload = {
            "otp": otp,
            "new_password": new_password,
            "new_password2": new_password2
        }
        # Añadir el identificador que tengamos disponible
        if telefono_celular:
            payload["telefono_celular"] = telefono_celular
        if email:
            payload["email"] = email

        print("Enviando reset payload:", payload)

        try:
            # 4. Enviar a la API
            response = requests.post(self.api_url, json=payload)

            try:
                data = response.json()
            except ValueError:
                data = {"detail": "Error inesperado del servidor."}

            # 5. Verificar éxito (200 OK)
            if response.status_code == 200:
                messages.success(request, "¡Contraseña restablecida con éxito! Por favor inicia sesión.")

                # Limpiar la sesión (ya no necesitamos guardar el teléfono/mail)
                if 'reset_telefono' in request.session:
                    del request.session['reset_telefono']
                if 'reset_email' in request.session:
                    del request.session['reset_email']

                # Redirigir al Login
                return redirect("usuarios:login")

            else:
                # Error (OTP incorrecto, contraseñas no coinciden, expirado)
                mensaje_error = data.get("detail") or data.get("error") or "No se pudo cambiar la contraseña."

                # Manejo especial para errores de validación de campos (diccionarios)
                if isinstance(data, dict):
                    # Si el API devuelve {"new_password": ["Las contraseñas no coinciden"]}
                    for key, value in data.items():
                        if isinstance(value, list):
                            mensaje_error = f"{key}: {value[0]}"
                            break

                messages.error(request, mensaje_error)
                print(f"Error reset password: {mensaje_error}")

                # Regresamos el OTP para que no tenga que volver a escribirlo si solo falló el password
                return render(request, self.template_name, {"otp": otp})

        except requests.exceptions.RequestException as e:
            err_msg = "Error al conectar con el servicio de Restablecimiento"
            messages.error(request, err_msg)
            print("Error de Conexión:", e)
            return render(request, self.template_name, {"otp": otp})

class inicioCuenta(View):
    template_name = "inicioUsuarios/inicioCuenta.html"

    def get(self, request):
        return render(request, self.template_name, {})

    def post(self, request):
        return render(request, self.template_name, {})

#-----------------------------------------------------------------------
# View para editar perfil
#----------------------------------------------------------------

class editarPerfilView(View):
    template_name = "usuarios/perfil.html"
    api_url = API_ENDPOINT_USUARIOS + "/accounts/editarPerfil/"

    def get(self, request):
        token = request.session.get("access_token")

        if not token:
            messages.error(request, "Debes iniciar sesión para editar tu perfil.")
            return redirect("usuarios:login")

        return render(request, self.template_name)

    def post(self, request):
        token = request.session.get("access_token")

        if not token:
            messages.error(request, "No hay token activo, inicia sesión.")
            return redirect("usuarios:login")

        # Campos permitidos
        data = {
            "bio": request.POST.get("bio"),
            "nombre_usuario": request.POST.get("nombre_usuario"),
            "pais": request.POST.get("pais"),
        }

        try:
            response = requests.patch(
                self.api_url,
                json=data,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )

        except requests.exceptions.RequestException:
            messages.error(request, "Error al conectar con el microservicio.")
            return redirect("usuarios:perfil")

        if response.status_code == 200:
            # Actualizar datos en la sesión
            perfil = response.json().get("perfil")

            if perfil:
                request.session["user"] = {
                    "email": perfil["email"],
                    "nombre_usuario": perfil["nombre_usuario"],
                    "pais": perfil["pais"],
                    "bio": perfil["bio"],
                }

            messages.success(request, "Perfil actualizado correctamente.")

        else:
            try:
                errores = response.json().get("errores")
                if errores:
                    # Mostrar los errores del microservicio
                    error_msg = ", ".join([f"{k}: {v}" for k, v in errores.items()])
                else:
                    error_msg = response.json().get("error", "Error desconocido.")
            except:
                error_msg = "Error desconocido."

            messages.error(request, f"No se pudo actualizar: {error_msg}")

        return render(request, self.template_name)

#---------------------------------------------- ------------------------------------
# View para ver los datos del usuario ya en el Perfil desde el inicio
#----------------------------------------------------------------------------------
class cargarPerfilView(View):
    template_name = "usuarios/perfil.html"
    api_url = API_ENDPOINT_USUARIOS + "/accounts/editarPerfil/"
    api_datos_url = API_ENDPOINT_USUARIOS + "/accounts/datosUsuario/"

    def get(self, request):
        token = request.session.get("access_token")

        if not token:
            messages.error(request, "Debes iniciar sesión para editar tu perfil.")
            return redirect("usuarios:login")

        # Llamar a la API para obtener los datos actualizados del usuario
        try:
            response = requests.get(
                self.api_datos_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo contactar al microservicio.")
            return render(request, self.template_name)

        if response.status_code == 200:
            data = response.json()

            # Guardamos los datos en la sesión
            request.session["user"] = {
                "email": data.get("email", ""),
                "nombre_usuario": data.get("nombre_usuario", ""),
                "pais": data.get("pais", ""),
                "bio": data.get("bio", "")
            }
        else:
            messages.error(request, "No se pudieron obtener los datos del usuario.")

        return render(request, self.template_name)


#---------------------------------------------- ------------------------------------
# View para la captura de datos en el inicio
#----------------------------------------------------------------------------------
class CapturaDatosView(View):
    template_name = 'usuarios/captura.html'
    api_url = API_ENDPOINT_HISTORICO + '/api/v1/historico/'

    def get(self, request):
        token = request.session.get('access_token')

        if token is None:
            messages.error(request, "Debe iniciar sesión para capturar datos")
            return redirect('usuarios:login')

        return render(request, self.template_name)

    def post(self, request):
        token = request.session.get('access_token')

        if token is None:
            messages.error(request, "Sesión expirada. Inicie sesión nuevamente.")
            return redirect('usuarios:login')

        # Campos
        humedad = request.POST.get("humedad")
        temperatura = request.POST.get("temperatura")
        longitud_tallo = request.POST.get("longitud_tallo")
        diametro_tallo = request.POST.get("diametro_tallo")

        # Lista para validar
        campos = {
            "Humedad": humedad,
            "Temperatura": temperatura,
            "Longitud del tallo": longitud_tallo,
            "Diámetro del tallo": diametro_tallo
        }

        # 1. Validación: campos vacíos
        for nombre, valor in campos.items():
            if valor is None or valor.strip() == "":
                messages.error(request, f"El campo '{nombre}' no puede estar vacío.")
                return render(request, self.template_name)

        # 2. Validación: solo números
        for nombre, valor in campos.items():
            try:
                float(valor)
            except ValueError:
                messages.error(request, f"El campo '{nombre}' debe ser numérico.")
                return render(request, self.template_name)

        # 3. Validación: números positivos
        for nombre, valor in campos.items():
            if float(valor) < 0:
                messages.error(request, f"El campo '{nombre}' debe ser un número positivo.")
                return render(request, self.template_name)

        # Construcción del payload
        payload = {
            "Humedad_Media": float(humedad),
            "Temp_Media": float(temperatura),
            "Longitud_Tallo": float(longitud_tallo),
            "Diametro_Tallo": float(diametro_tallo)
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            data = response.json()

            if response.status_code not in [200, 201]:
                mensaje_error = data.get("detail") or data.get("error") or str(data)
                messages.error(request, f"Error al guardar: {mensaje_error}")
                return render(request, self.template_name)

            messages.success(request, "Registro guardado correctamente.")
            return redirect("usuarios:captura")

        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar al microservicio.")
            return render(request, self.template_name)


#----------------------- View para ver la predicción
class VerPrediccionView(View):
    template_name = 'usuarios/predicciones.html'
    api_url = API_ENDPOINT_MODELO + '/api/v1/prediccion/predecir/'

    def get(self, request):
        token = request.session.get('access_token')
        if token is None:
            messages.error(request, "Debe iniciar sesión para ver predicciones.")
            return redirect('usuarios:login')

        return render(request, self.template_name)

    def post(self, request):
        token = request.session.get('access_token')

        if token is None:
            messages.error(request, "Sesión expirada. Inicie sesión nuevamente.")
            return redirect('usuarios:login')

        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.post(self.api_url, headers=headers, timeout=15)
        except Exception:
            messages.error(request, "No se pudo conectar al servicio de predicción.")
            return render(request, self.template_name)

        if response.status_code == 400:
            data = response.json()
            msg = data.get("error", "Se requieren al menos 5 registros para predecir.")
            messages.warning(request, msg)
            return render(request, self.template_name)

        if response.status_code != 200:
            messages.error(request, "Ocurrió un error al generar la predicción.")
            return render(request, self.template_name)

        data = response.json()

        context = {
            "dia_predicho": data.get("dia_predicho"),
            "produccion_predicha": data.get("produccion_predicha_kg"),
        }

        return render(request, self.template_name, context)

#-------------------------------------------------------------------------------------------
# View para gráficar
#-------------------------------------------------------------------------------------------

class PrediccionesListaView(View):
    template_name = "usuarios/predicciones.html"
    api_url = API_ENDPOINT_MODELO + "/api/v1/predicciones/"

    def get(self, request):
        token = request.session.get("access_token")

        if not token:
            messages.error(request, "Debes iniciar sesión para ver las predicciones.")
            return redirect("usuarios:login")

        # Consumir API
        try:
            response = requests.get(
                self.api_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo contactar al microservicio de predicciones.")
            return render(request, self.template_name)

        if response.status_code != 200:
            messages.error(request, "No se pudieron obtener las predicciones.")
            return render(request, self.template_name)

        predicciones = response.json()

        fechas = [p["dia_predicho"] for p in predicciones]
        valores = [p["produccion_predicha_kg"] for p in predicciones]

        # Convertir a JSON válido para evitar errores
        fechas_json = json.dumps(fechas)
        valores_json = json.dumps(valores)

        return render(request, self.template_name, {
            "fechas": fechas_json,
            "valores": valores_json,
        })

#-------------------------------------------------------------------------------------------
# View para Reportes
#-------------------------------------------------------------------------------------------

class ReportesGenerales(View):
    template_name = 'usuarios/reportes.html'

    def get(self, request):

        # --- Parámetros desde la URL ---
        rango = request.GET.get("rango", "30d")
        tipo = request.GET.get("tipo", "temperatura")

        token = request.session.get('access_token')
        if not token:
            messages.error(request, "Debes iniciar sesión.")
            return redirect('usuarios:login')

        headers = {"Authorization": f"Bearer {token}"}

        # --- Definir fecha inicial ---
        ahora = timezone.now()
        if rango == "7d":
            fecha_inicio = ahora - timedelta(days=7)
        elif rango == "1y":
            fecha_inicio = ahora - timedelta(days=365)
        else:
            fecha_inicio = ahora - timedelta(days=30)

        params = { "ordering": "-created_at", "limit": 1000 }

        try:
            response = requests.get((API_ENDPOINT_HISTORICO + "/api/v1/historico/"), headers=headers, params=params)
            data = response.json()

        except Exception as e:
            messages.error(request, f"Error obteniendo datos: {e}")
            data = {}

        registros_raw = data.get("results", []) if isinstance(data, dict) else data

        # --- Filtrar por rango ---
        registros = []

        for r in registros_raw:
            fecha_raw = r.get("created_at")
            if not fecha_raw:
                continue

            fecha = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00"))

            if fecha >= fecha_inicio:
                registros.append({
                    "fecha": fecha,
                    "temperatura": float(r.get("Temp_Media", 0)),
                    "humedad": float(r.get("Humedad_Media", 0)),
                    "longitud": float(r.get("Longitud_Tallo", 0)),
                    "diametro": float(r.get("Diametro_Tallo", 0)),
                })

        registros.sort(key=lambda x: x["fecha"])

        # --- Mapeo de tipos ---
        tipo_map = {
            "temperatura": ("temperatura", "#FFD966"),
            "humedad": ("humedad", "#6AA84F"),
            "longitud": ("longitud", "#6FA8DC"),
            "diametro": ("diametro", "#FF6F6F"),
        }

        clave, color = tipo_map.get(tipo, ("temperatura", "#FFD966"))

        labels = [r["fecha"].strftime("%d %b") for r in registros]
        valores = [r[clave] for r in registros]

        # --- Agrupador automático para evitar 365 puntos ---
        def agrupar(lbls, vals, max_pts=60):
            n = len(lbls)
            if n <= max_pts:
                return lbls, vals

            paso = n // max_pts
            new_lbls = []
            new_vals = []

            for i in range(0, n, paso):
                grupo = vals[i:i+paso]
                new_lbls.append(lbls[i])
                new_vals.append(sum(grupo) / len(grupo))

            return new_lbls, new_vals

        labels, valores = agrupar(labels, valores)

        context = {
            "labels_json": json.dumps(labels),
            "valores_json": json.dumps(valores),
            "tipo_seleccionado": tipo.capitalize(),
            "color": color,
            "rango_actual": rango,
        }

        return render(request, self.template_name, context)
