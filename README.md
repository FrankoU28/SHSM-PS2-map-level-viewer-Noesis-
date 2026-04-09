# Visor de Mapas SHSM PS2 (Plugin Noesis)

Plugin de Noesis para visualizar y exportar archivos BSP de mapas de la versión PS2 de Silent Hill: Shattered Memories, con soporte completo de texturas.

## Modo de Uso

1. **Renombra los archivos BSP**: Cambia la extensión de tus archivos `.bsp` de SHSM a `.shsm_bsp` 
2. **Instala el plugin**: Coloca este plugin en la carpeta `plugins/python` de Noesis junto con los demás plugins
3. **Abre los mapas**: Carga cualquier archivo `.shsm_bsp` en Noesis para visualizarlo

## Preparación de Modelos

1. **Extraé los archivos de DATA.ARC**: Usá la herramienta de [IWILLCRAFT RenderEclipseExtractor](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools) (ahora conocida como **Climax ARC Manager**)
2. **Descomprimí los recursos**: Ejecutá el script [ClimaxSH_Unpack_Resource.bms](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools/blob/main/scripts/ClimaxSH_Unpack_Resource.bms) para extraer los archivos sin extensión que contienen los modelos de mapas.
3. **Identificá los modelos BSP**: Una vez extraídos, vas a encontrar archivos sin extensión. Los archivos BSP suelen ser dos, el que corresponde es el de mayor peso.
4. **Renombrá los BSP**: Cambia la extensión BSP con mayor peso, por ejemplo: `8.bsp` -> `8.shsm_bsp`
5. **Verificá la integridad**: Aseguráte de que los archivos renombrados sean reconocidos correctamente por Noesis
6. **Abrir en Noesis**: Cargá los archivos `.shsm_bsp` en Noesis para visualizar y exportar los modelos

## Preparación de Texturas

1. **Extraé los archivos de DATA.ARC**: Usá la herramienta de [IWILLCRAFT RenderEclipseExtractor](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools) (ahora conocida como **Climax ARC Manager**)
2. **Descomprimí los recursos**: Ejecutá el script [ClimaxSH_Unpack_Resource.bms](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools/blob/main/scripts/ClimaxSH_Unpack_Resource.bms) para extraer los archivos sin extensión que contienen los modelos de mapas junto a sus demas archivos.
3. **Identificá las texturas**: Una vez extraídos, encontrarás varios archivos sin extensión. Los primeros archivos (generalmente del 0 al 6) son las texturas
4. **Renombrá las texturas**: Cambia la extensión de estos archivos a `.txd`
5. **Convertí a PNG**: Usá [MagicTXD](https://gtaforums.com/topic/851436-relopensrc-magictxd/) o el plugin de Noesis [tex_SilentHillClimax.py](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools/blob/main/scripts/tex_SilentHillClimax.py) para abrir cada archivo `.txd` y exportarlos como PNG
6. **Colocá las texturas**: Coloca los PNG exportados en la misma carpeta que el archivo BSP renombrado (con extensión `.shsm_bsp`)

## Método Técnico

El plugin utiliza un enfoque robusto para la extracción de geometría:

- **Extracción de materiales**: Recorre el árbol de fragmentos (chunks) de RenderWare para extraer la lista de materiales (con nombres de texturas) y el mapeo de divisiones (split) → ID de material usando BinMeshPlg
- **Escaneo de patrones VIF**: Realiza un escaneo binario VIF dentro del rango de datos exacto de cada división para extraer de forma robusta vértices, coordenadas UV y colores
- **Evita crashes**: Este enfoque previene fallos de C causados por `rapi.unpackPS2VIF()` con los datos VIF de SHSM

## Cambios respecto a Origins (fmt_renderware_ps2_bsp.py)

- Extracción de geometría mediante escaneo de patrones binarios en lugar de `rapi.unpackPS2VIF()`
- Escaneo delimitado por división → garantiza asignación correcta de materiales
- Soporte mejorado para caracteres no ASCII en nombres de texturas (mediante RWString)
- Registrado como `.shsm_bsp` para evitar conflictos con el plugin `.bsp` de Origins
- Función `bsp_load_model` envuelta en try/except para mayor estabilidad
