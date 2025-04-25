import os
import subprocess
import sys
import time
import signal
import threading

processes = []
stop_threads = False

def signal_handler(sig, frame):
    global stop_threads
    print('¡Deteniendo todos los servicios!')
    stop_threads = True
    for process in processes:
        if process.poll() is None:  # Si el proceso sigue en ejecución
            process.terminate()
            process.wait()  # Esperar a que el proceso termine
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

def log_output(process, prefix):
    global stop_threads
    while not stop_threads:
        line = process.stdout.readline()
        if line:
            print(f"[{prefix}] {line.strip()}")
        elif process.poll() is not None:
            break
        time.sleep(0.1)

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

# Crear hilos para leer la salida de cada proceso
threads = [
    threading.Thread(target=log_output, args=(worker, "WORKER")),
    threading.Thread(target=log_output, args=(beat, "BEAT")),
    threading.Thread(target=log_output, args=(django, "DJANGO"))
]

# Iniciar los hilos
for thread in threads:
    thread.daemon = True
    thread.start()

# Esperar hasta que el usuario presione Ctrl+C o algún proceso termine
try:
    while all(process.poll() is None for process in processes):
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    signal_handler(None, None)
    # Esperar a que los hilos terminen
    stop_threads = True
    for thread in threads:
        thread.join(timeout=1)