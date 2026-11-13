"""Diagnósticos públicos del proveedor, sin exponer cuerpos, cabeceras o claves."""
import socket
import ssl


def connection_diagnostic(error):
    status = getattr(error, "status_code", None)
    chain = []
    current = error
    for _ in range(8):
        if current is None or any(current is previous for previous in chain):
            break
        chain.append(current)
        current = current.__cause__ or current.__context__
    names = {type(item).__name__ for item in chain}
    if status == 401:
        code, message = "authentication", "NVIDIA rechazó la clave. Vuelve a copiarla completa desde tu cuenta de NVIDIA."
    elif status == 403:
        code, message = "access", "NVIDIA rechazó el acceso. Comprueba los permisos de tu cuenta para el modelo configurado."
    elif status == 429:
        code, message = "rate_limit", "NVIDIA indicó un límite de uso o de cuota. Espera y revisa los límites de tu cuenta."
    elif status == 404:
        code, message = "model", "NVIDIA no encontró el recurso solicitado. Revisa el modelo y el endpoint configurados en el servidor."
    elif any(isinstance(item, PermissionError) or getattr(item, "winerror", None) == 10013 for item in chain):
        code, message = "network_permission", "El proceso no tiene permiso para conectarse a NVIDIA. Revisa los permisos de red del entorno que ejecuta Streamlit."
    elif any(isinstance(item, ssl.SSLError) for item in chain) or any("CERTIFICATE_VERIFY_FAILED" in str(item) for item in chain):
        code, message = "certificate", "No se pudo verificar el certificado HTTPS de NVIDIA. Revisa los certificados de Python y del proxy de tu red; mantén activa la verificación HTTPS."
    elif any(isinstance(item, socket.gaierror) for item in chain):
        code, message = "dns", "No se pudo resolver el dominio de NVIDIA. Comprueba la conexión y el DNS del servidor."
    elif "ProxyError" in names:
        code, message = "proxy", "No se pudo conectar mediante el proxy. Revisa la configuración de proxy del servidor."
    elif names & {"APITimeoutError", "ConnectTimeout", "ReadTimeout", "TimeoutError"}:
        code, message = "timeout", "NVIDIA no respondió dentro del tiempo de espera. Intenta de nuevo en unos momentos."
    elif status is not None and status >= 500:
        code, message = "provider", "NVIDIA devolvió un error del servicio. Intenta de nuevo en unos momentos."
    elif "APIConnectionError" in names:
        code, message = "connection", "No se pudo establecer la conexión HTTPS con NVIDIA. Comprueba Internet, el proxy y los permisos de red del servidor. Este error no confirma que la clave sea incorrecta."
    else:
        code, message = "request", "No se pudo completar la solicitud al modelo. Revisa la configuración del servicio."
    return {"code": code, "message": message, "status": status}
