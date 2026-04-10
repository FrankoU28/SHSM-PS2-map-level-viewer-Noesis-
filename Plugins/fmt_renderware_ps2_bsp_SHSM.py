"""Noesis Python Plugin

      File: fmt_renderware_ps2_bsp_SHSM.py
   Authors: Laurynas Zubavičius (Sparagas)
            IWILLCRAFT
            Rodolfo Nuñez (roocker666) [por el script fmt_sho_ps2_map_bsp.py]
            FrankoU_28 
   Adapted: For Silent Hill: Shattered Memories (PS2)
   Purpose: RenderWare (Sony - PlayStation 2) - Silent Hill Shattered Memories PS2
            Loads geometry WITH vertex colors AND textures (when PNGs are present).
  Category: 3D static map models
 File Mask: *.shsm_bsp
"""

from inc_noesis import *
import struct as _struct

# VIF packet markers that precede each data buffer inside a vertex group
_PAT_VERT  = b'\x05\x04\x01\x00\x01\x00'  # vertex positions
_PAT_UV    = b'\x05\x04\x01\x00\x01\x01'  # UV coordinates
_PAT_COLOR = b'\x05\x04\x01\x00\x01\x02'  # vertex colors (RGBA ubyte)
_PAT_NORM  = b'\x05\x04\x01\x00\x01\x03'  # normals (marks end, not used for rendering)

_STRIDE_W  = 16  # XYZW float (pad byte 0x6C)
_STRIDE_NO = 12  # XYZ  float (pad byte 0x68)


class RwId:
    RW_ID_STRING           = 0x02
    RW_ID_EXTENSION        = 0x03
    RW_ID_TEXTURE          = 0x06
    RW_ID_MATERIAL         = 0x07
    RW_ID_MAT_LIST         = 0x08
    RW_ID_ATOMIC_SECT      = 0x09
    RW_ID_PLANE_SECT       = 0x0A
    RW_ID_WORLD            = 0x0B
    RW_ID_BIN_MESH_PLUGIN  = 0x050E
    RW_ID_NATIVE_DATA_PLUGIN = 0x0510

# chunk parsers
class RwHeader:
    def __init__(self, bs):
        self.id  = bs.readUInt()
        self.len = bs.readUInt()
        self.ver = bs.readUInt()


class RwSkip:
    def __init__(self, bs):
        self.hdr = RwHeader(bs)
        bs.seek(self.hdr.len, NOESEEK_REL)


class RWString:
    def __init__(self, bs):
        self.hdr = RwHeader(bs)
        raw = bs.readBytes(self.hdr.len)
        try:
            self.str = noeStrFromBytes(raw)
        except Exception:
            try:
                decoded = raw.decode("latin-1").rstrip("\x00").strip()
                self.str = decoded if all(32 <= ord(c) <= 126 for c in decoded) else ""
            except Exception:
                self.str = ""


class RwExtension:
    def __init__(self, bs):
        self.hdr = RwHeader(bs)
        remaining = self.hdr.len
        while remaining > 0:
            chunk_id  = bs.readUInt()
            chunk_len = bs.readUInt()
            bs.seek(-8, NOESEEK_REL)
            RwSkip(bs)
            remaining -= 12 + chunk_len


class RwStructTexture:
    def __init__(self, bs):
        self.hdr          = RwHeader(bs)
        self.filter_mode  = bs.readByte()
        self.uv_addr_mode = bs.readByte()
        self.has_mipmaps  = bs.readShort()


class RwTexture:
    def __init__(self, bs):
        self.hdr        = RwHeader(bs)
        self.rw_struct  = RwStructTexture(bs)
        self.name       = RWString(bs)       # main tex name
        self.alpha_name = RWString(bs)       # alpha name — garbage in SHSM, handled above
        self.extension  = RwExtension(bs)


class RwStructMaterial:
    def __init__(self, bs):
        self.hdr         = RwHeader(bs)
        self.pad_flg     = bs.readInt()
        self.rgba        = bs.readUInt()
        self.unk         = bs.readInt()
        self.has_texture = bs.readInt()
        self.ambient     = bs.readFloat()
        self.specular    = bs.readFloat()
        self.diffuse     = bs.readFloat()


class RwMaterial:
    def __init__(self, bs):
        self.hdr       = RwHeader(bs)
        self.rw_struct = RwStructMaterial(bs)
        self.texture   = RwTexture(bs) if self.rw_struct.has_texture else None
        self.extension = RwExtension(bs)

    @property
    def tex_name(self):
        return self.texture.name.str if self.texture else ""


class RwStructMatList:
    def __init__(self, bs):
        self.hdr          = RwHeader(bs)
        self.num_material = bs.readUInt()
        self.mat_idx      = [bs.readInt() for _ in range(self.num_material)]


class RwMatList:
    def __init__(self, bs):
        self.hdr       = RwHeader(bs)
        self.rw_struct = RwStructMatList(bs)
        num_unique     = sum(1 for idx in self.rw_struct.mat_idx if idx == -1)
        self._mats     = [RwMaterial(bs) for _ in range(num_unique)]
        self.names     = [m.tex_name for m in self._mats]


class RwStructAtomicSect:
    def __init__(self, bs):
        self.hdr = RwHeader(bs)
        bs.seek(self.hdr.len, NOESEEK_REL)


class BinMeshPlg:
    def __init__(self, bs):
        self.hdr         = RwHeader(bs)
        self.is_tristrip = bs.readInt()
        self.num_splits  = bs.readUInt()
        self.num_indices = bs.readUInt()
        self.mat_ids     = []
        self.face_counts = []
        for _ in range(self.num_splits):
            fc = bs.readUInt()
            mi = bs.readUInt()
            self.face_counts.append(fc)
            self.mat_ids.append(mi)


class SplitData:
    def __init__(self, mat_id, vif_bytes):
        self.mat_id   = mat_id
        self.vif_data = vif_bytes


class RwAtomicSect:
    def __init__(self, bs, mat_list):
        tmp        = bs.tell()
        self.hdr   = RwHeader(bs)
        self.rw_struct = RwStructAtomicSect(bs)

        ext_hdr    = RwHeader(bs)          # Extension container header
        bin_mesh   = BinMeshPlg(bs)        # BinMeshPlg (first chunk in extension)

        # NativeDataPlugin (second chunk in extension)
        nat_hdr    = RwHeader(bs)
        nat_struct = RwHeader(bs)
        platform   = bs.readUInt()         # 4 = PS2

        self.splits = []
        for i in range(bin_mesh.num_splits):
            size      = bs.readUInt()
            mesh_type = bs.readUInt()
            raw       = bs.readBytes(size)
            self.splits.append(SplitData(bin_mesh.mat_ids[i], raw))

        bs.seek(tmp + 12 + self.hdr.len)


class RwStructPlaneSect:
    def __init__(self, bs):
        self.hdr             = RwHeader(bs)
        self.unk_type        = bs.readUInt()
        self.unk_value       = bs.readFloat()
        self.is_left_atomic  = bs.readInt()
        self.is_right_atomic = bs.readInt()
        self.left_value      = bs.readFloat()
        self.right_value     = bs.readFloat()


class RwPlaneSect:
    def __init__(self, bs, mat_list):
        self.hdr       = RwHeader(bs)
        self.rw_struct = RwStructPlaneSect(bs)

        self.left  = (RwAtomicSect if self.rw_struct.is_left_atomic  else RwPlaneSect)(bs, mat_list)
        self.right = (RwAtomicSect if self.rw_struct.is_right_atomic else RwPlaneSect)(bs, mat_list)


class RwStructWorld:
    def __init__(self, bs):
        self.hdr            = RwHeader(bs)
        self.is_root_atomic = bs.readUInt()
        bs.seek(self.hdr.len - 4, NOESEEK_REL)


# geometry extraction: binary pattern scan inside each split's VIF bytes
def _find_in(blob, pattern, start, end):
    positions = []
    pos = start
    while pos < end:
        pos = blob.find(pattern, pos, end)
        if pos == -1:
            break
        positions.append(pos)
        pos += 1
    return positions


def _commit_split(vif_bytes, mat_name):
    vlen = len(vif_bytes)
    if vlen < 16:
        return

    vert_hits = _find_in(vif_bytes, _PAT_VERT, 0, vlen)
    if not vert_hits:
        return

    for vp in vert_hits:
        if vp + 9 > vlen:
            continue

        vnum     = vif_bytes[vp + 7]
        pad_byte = vif_bytes[vp + 8]
        if vnum == 0:
            continue

        if   pad_byte == 0x6C: stride = _STRIDE_W
        elif pad_byte == 0x68: stride = _STRIDE_NO
        else: continue

        # vertex buffer
        vbuf_start = vp + 9
        vbuf_end   = vbuf_start + vnum * stride
        if vbuf_end > vlen:
            continue
        vbuf = vif_bytes[vbuf_start:vbuf_end]

        # UV buffer
        uv_pat_pos = vif_bytes.find(_PAT_UV, vbuf_end, vlen)
        if uv_pat_pos == -1:
            continue
        uv_start = uv_pat_pos + 9
        uv_end   = uv_start + vnum * 8
        if uv_end > vlen:
            continue
        uvbuf = vif_bytes[uv_start:uv_end]

        if _struct.unpack_from("<I", uvbuf, 0)[0] == 0xE5E5E5E5:
            continue

        # color buffer
        col_pat_pos = vif_bytes.find(_PAT_COLOR, uv_end, vlen)
        if col_pat_pos == -1:
            continue
        col_start = col_pat_pos + 9
        col_end   = col_start + vnum * 4
        if col_end > vlen:
            continue
        colbuf = vif_bytes[col_start:col_end]

        #commit to Noesis rpg context
        rapi.rpgBindPositionBuffer(vbuf,   noesis.RPGEODATA_FLOAT, stride)
        rapi.rpgBindUV1Buffer(uvbuf,       noesis.RPGEODATA_FLOAT, 8)
        rapi.rpgBindColorBuffer(colbuf,    noesis.RPGEODATA_UBYTE, 4, 4)
        rapi.rpgSetMaterial(mat_name)
        rapi.rpgCommitTriangles(None, -1, vnum, noesis.RPGEO_TRIANGLE_STRIP)
        rapi.rpgClearBufferBinds()


def _collect_splits(node, out):
    if isinstance(node, RwAtomicSect):
        out.extend(node.splits)
    elif isinstance(node, RwPlaneSect):
        _collect_splits(node.left,  out)
        _collect_splits(node.right, out)


def _load_world(data, mdl_list):
    bs = NoeBitStream(data)

    world_hdr  = RwHeader(bs)       # RW_WORLD header
    rw_struct  = RwStructWorld(bs)
    mat_list   = RwMatList(bs)

    if rw_struct.is_root_atomic:
        root = RwAtomicSect(bs, mat_list)
    else:
        root = RwPlaneSect(bs, mat_list)

    all_splits = []
    _collect_splits(root, all_splits)

    for split in all_splits:
        mat_id   = split.mat_id
        mat_name = mat_list.names[mat_id] if mat_id < len(mat_list.names) else ""
        try:
            _commit_split(split.vif_data, mat_name)
        except Exception:
            rapi.rpgClearBufferBinds()

    mdl = rapi.rpgConstructModel()

    # load textures from disk
    path     = rapi.getDirForFilePath(rapi.getInputName())
    tex_list = []
    seen     = set()
    for name in mat_list.names:
        if not name or name in seen:
            continue
        seen.add(name)
        png = path + "/Textures/" + name + ".png"
        if rapi.checkFileExists(png):
            tex_list.append(noesis.loadImageRGBA(png))

    noe_mats = [NoeMaterial(t.name, t.name) for t in tex_list]
    mdl.setModelMaterials(NoeModelMaterials(tex_list, noe_mats))
    mdl_list.append(mdl)

# Noesis entry points
def registerNoesisTypes():
    # ".shsm_bsp" avoids collision with the Origins ".bsp" plugin
    # rename your SHSM .bsp files to .shsm_bsp before opening in Noesis
    handle = noesis.register("Silent Hill: Shattered Memories PS2 BSP", ".shsm_bsp")
    noesis.setHandlerTypeCheck(handle, bsp_check_type)
    noesis.setHandlerLoadModel(handle, bsp_load_model)
    return 1


def _is_shsm_bsp(data):
    try:
        if len(data) < 200:
            return False
        def ru(o): return _struct.unpack_from("<I", data, o)[0]
        if ru(0) != RwId.RW_ID_WORLD:
            return False
        wsl = ru(16)
        if not (4 <= wsl <= 256):
            return False
        ml_off = 12 + 12 + wsl
        if ml_off + 24 >= len(data) or ru(ml_off) != RwId.RW_ID_MAT_LIST:
            return False
        mls_len = ru(ml_off + 16)
        num_mat = ru(ml_off + 24)
        if num_mat == 0 or num_mat > 512:
            return False
        m0 = ml_off + 12 + 12 + mls_len
        if m0 + 24 >= len(data) or ru(m0) != RwId.RW_ID_MATERIAL:
            return False
        ms_len  = ru(m0 + 16)
        has_tex = ru(m0 + 24 + 12)
        if not has_tex:
            return False
        tx_off  = m0 + 12 + 12 + ms_len
        if tx_off + 24 >= len(data) or ru(tx_off) != RwId.RW_ID_TEXTURE:
            return False
        ts_len  = ru(tx_off + 16)
        nm_off  = tx_off + 12 + 12 + ts_len
        if nm_off + 12 >= len(data) or ru(nm_off) != RwId.RW_ID_STRING:
            return False
        nm_len  = ru(nm_off + 4)
        if nm_len == 0 or nm_off + 12 + nm_len > len(data):
            return False
        raw  = data[nm_off + 12 : nm_off + 12 + nm_len]
        name = raw.split(b'\x00')[0].decode('ascii', errors='replace')
        return len(name) > 0
    except Exception:
        return False


def bsp_check_type(data):
    return 1 if _is_shsm_bsp(data) else 0


def bsp_load_model(data, mdlList):
    rapi.rpgCreateContext()
    try:
        _load_world(data, mdlList)
    except Exception as e:
        rapi.rpgClearBufferBinds()
        noesis.logPopup()
        print("SHSM BSP load error: " + str(e))
        import traceback
        traceback.print_exc()
    return 1