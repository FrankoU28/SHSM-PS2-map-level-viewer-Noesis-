###############################################################################
# AYUDA PARA RENOMBRADO MASIVO (ejecutar por separado, NO dentro de Noesis)
# renombra todos los archivos .bsp de una carpeta a .shsm_bsp.
# uso: python rename_shsm_bsp.py <ruta_de_la_carpeta>
#
import os
import sys

folder = sys.argv[1] if len(sys.argv) > 1 else "."

for fname in os.listdir(folder):
    if fname.lower().endswith(".bsp"):
        src = os.path.join(folder, fname)
        dst = os.path.join(folder, fname[:-4] + ".shsm_bsp")
        os.rename(src, dst)
        print(f"Renamed: {fname} -> {os.path.basename(dst)}")

print("\nFinished Process")