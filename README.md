<h1 align="center">
  <a>Visor de Mapas SHSM PS2 (Plugin Noesis)</a>
</h1>

<h4 align="center">Plugin de Noesis para visualizar y exportar archivos BSP de mapas de la versión PS2 de Silent Hill: Shattered Memories, con soporte completo de texturas.</h4>

<p align="center">
  <img src="./Images/sm_logo.png" alt="SHSM_Logo">
  <br>

## Modo de Uso

1. **Renombra los archivos BSP**: Cambia la extensión de tus archivos `.bsp` de SHSM a `.shsm_bsp` 
2. **Instala el plugin**: Coloca este plugin en la carpeta `plugins/python` de Noesis junto con los demás plugins
3. **Abre los mapas**: Carga cualquier archivo `.shsm_bsp` en Noesis para visualizarlo

### Preparación de Modelos

1. **Extraé los archivos de DATA.ARC**: Usá la herramienta de [IWILLCRAFT RenderEclipseExtractor](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools) (ahora conocida como **Climax ARC Manager**)
2. **Descomprimí los recursos**: Ejecutá el script [ClimaxSH_Unpack_Resource.bms](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools/blob/main/scripts/ClimaxSH_Unpack_Resource.bms) para extraer los archivos sin extensión que contienen los modelos de mapas.
3. **Identificá los modelos BSP**: Una vez extraídos, vas a encontrar archivos sin extensión. Los archivos BSP suelen ser dos, el que corresponde es el de mayor peso.
4. **Renombrá los BSP**: Cambia la extensión BSP con mayor peso, por ejemplo: `8.bsp` -> `8.shsm_bsp`
5. **Verificá la integridad**: Aseguráte de que los archivos renombrados sean reconocidos correctamente por Noesis
6. **Abrir en Noesis**: Cargá los archivos `.shsm_bsp` en Noesis para visualizar y exportar los modelos

### Preparación de Texturas

1. **Extraé los archivos de DATA.ARC**: Usá la herramienta de [IWILLCRAFT RenderEclipseExtractor](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools) (ahora conocida como **Climax ARC Manager**)
2. **Descomprimí los recursos**: Ejecutá el script [ClimaxSH_Unpack_Resource.bms](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools/blob/main/scripts/ClimaxSH_Unpack_Resource.bms) para extraer los archivos sin extensión que contienen los modelos de mapas junto a sus demas archivos.
3. **Identificá las texturas**: Una vez extraídos, encontrarás varios archivos sin extensión. Los primeros archivos (generalmente del 0 al 6) son las texturas
4. **Renombrá las texturas**: Cambia la extensión de estos archivos a `.txd`
5. **Convertí a PNG**: Usá [MagicTXD](https://gtaforums.com/topic/851436-relopensrc-magictxd/) o el plugin de Noesis [tex_SilentHillClimax.py](https://github.com/IWILLCRAFT-M0d/RenderEclipse-Tools/blob/main/scripts/tex_SilentHillClimax.py) para abrir cada archivo `.txd` y exportarlos como PNG
6. **Colocá las texturas**: Coloca los PNG exportados en la misma carpeta que el archivo BSP renombrado (con extensión `.shsm_bsp`)

## Método Técnico

El plugin implementa un enfoque híbrido que combina lo mejor de dos estrategias diferentes:

### Extracción de Materiales y Texturas

1. **Recorrido de estructura RenderWare** (inspiración: `fmt_renderware_ps2_bsp.py` de Origins de [IWILLCRAFT](https://github.com/IWILLCRAFT-M0d) y [Laurynas Zubavičius (Sparagas)](https://github.com/Sparagas))
   - Recorre el árbol de fragmentos (chunks) de RenderWare secuencialmente
   - Extrae la lista de materiales con sus nombres de texturas asociadas
   - Lee el mapeo de divisiones (splits) → IDs de material desde el BinMeshPlg
   - Mantiene el **contexto de materiales** para después asociar geometría a texturas

### Extracción de Geometría

2. **Escaneo de patrones binarios VIF** (inspiración: `fmt_sho_ps2_map_bsp.py` de [RODOLFO NUÑEZ (roocker666)](https://www.youtube.com/@rodolfonunez666) y [Laurynas Zubavičius (Sparagas)](https://github.com/Sparagas))
   - En lugar de usar `rapi.unpackPS2VIF()` (que causa crashes con datos VIF de SHSM), busca patrones binarios VIF directamente
   - Los patrones buscados son:
     - `\x05\x04\x01\x00\x01\x00` → posiciones de vértices (XYZW)
     - `\x05\x04\x01\x00\x01\x01` → coordenadas UV
     - `\x05\x04\x01\x00\x01\x02` → colores RGBA (ubyte)
   - **Delimit el escaneo al rango exacto de cada split** → garantiza asociación correcta de geometría a materiales
   - Extrae vértices, coordenadas UV y colores de forma robusta sin crashes

### Cambios Técnicos Específicos

- Extracción de geometría mediante escaneo de patrones binarios delimitados por split en lugar de `rapi.unpackPS2VIF()`
- Preservación del mapeo split → materialID → nombre de textura del árbol RenderWare
- Manejo robusta de caracteres no ASCII en nombres de texturas mediante RWString
- Registrado como `.shsm_bsp` para evitar conflictos con el plugin `.bsp` de Origins (`fmt_renderware_ps2_bsp.py`)
- Función `bsp_load_model` envuelta en try/except para mayor tolerancia a errores
- Búsqueda y carga de texturas en carpeta `/Textures/` junto al archivo BSP
