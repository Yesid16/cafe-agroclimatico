def run(module, *args):
    import subprocess, sys
    from pathlib import Path
    log = Path('results/logs') / (module.replace('.', '_') + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-u', '-m', module, *args]
    with log.open('w', encoding='utf-8') as saved:
        with subprocess.Popen(command, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True,
                              encoding='utf-8', errors='replace', bufsize=1) as proc:
            for line in proc.stdout:
                print(line, end='', flush=True)
                saved.write(line)
                saved.flush()
            code = proc.wait()
    if code:
        raise RuntimeError(f'{module} terminó con código {code}. Error completo arriba y en {log}.')
    print(f'Completado: {module}', flush=True)
