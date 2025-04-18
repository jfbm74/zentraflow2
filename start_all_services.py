import os
import subprocess
import sys
import time
import signal

processes = []

def signal_handler(sig, frame):
    print('¡Deteniendo todos los servicios!')
    for process in processes:
        if process.poll() is None:  # Si el proceso sigue en ejecución
            process.terminate()
    sys.exit(0)

# Configurar el manejador de señal para CTRL+C
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_process(command, name):
    print(f"Iniciando {name}...")
    # Usar shell=True en Windows, False en Unix
    process = subprocess.Popen(
        command,
        shell=sys.platform == 'win32',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(process)
    return process

# Iniciar Redis si no está funcionando
try:
    subprocess.run(["redis-cli", "ping"], check=True, capture_output=True)
    print("Redis ya está en ejecución.")
except (subprocess.CalledProcessError, FileNotFoundError):
    print("Iniciando Redis...")
    subprocess.run(["brew", "services", "start", "redis"], check=True)

# Iniciar Celery Worker
worker = start_process(
    ["celery", "-A", "zentraflow", "worker", "--loglevel=info"],
    "Celery Worker"
)

# Iniciar Celery Beat
beat = start_process(
    ["celery", "-A", "zentraflow", "beat", "--loglevel=info"],
    "Celery Beat"
)

# Dar tiempo para que los procesos de Celery inicien
time.sleep(2)

# Iniciar Django runserver
django = start_process(
    ["python", "manage.py", "runserver"],
    "Django Server"
)

def log_output(process, prefix):
    for line in iter(process.stdout.readline, ''):
        print(f"[{prefix}] {line.strip()}")

# Leer y mostrar la salida de cada proceso
import threading
threading.Thread(target=log_output, args=(worker, "WORKER"), daemon=True).start()
threading.Thread(target=log_output, args=(beat, "BEAT"), daemon=True).start()
threading.Thread(target=log_output, args=(django, "DJANGO"), daemon=True).start()

# Esperar hasta que el usuario presione Ctrl+C
try:
    while all(process.poll() is None for process in processes):
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    signal_handler(None, None)