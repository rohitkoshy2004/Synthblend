# =========================================================
# SYNTHBLEND4
# YOLO Synthetic Dataset Generator
# =========================================================

import bpy
import os
import time
import json
import subprocess
import sys
import numpy as np

from random import uniform, randint

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    PointerProperty,
    EnumProperty,
)

from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
)

from bpy.utils import previews


# =========================================================
# CONFIG
# =========================================================

DEBUG = True
MAIN_OBJECT_NAME = 'Target'

custom_icons = None
dataset_log = []


# =========================================================
# SESSION
# =========================================================

session = {
    'real_renders': 0,
    'gt_renders': 0,
    'pairs': 0,
    'start_time': None,
    'total': 0,
    'done': 0,
    'running': False,
}


def reset_session():

    session.update({
        'real_renders': 0,
        'gt_renders': 0,
        'pairs': 0,
        'start_time': None,
        'total': 0,
        'done': 0,
        'running': False,
    })


def session_elapsed():

    if session['start_time'] is None:
        return 0

    return int(time.time() - session['start_time'])


def session_eta():

    elapsed = session_elapsed()

    if session['done'] == 0 or elapsed == 0:
        return '—'

    rate = session['done'] / elapsed
    remaining = session['total'] - session['done']

    eta = int(remaining / rate)

    if eta >= 60:
        return f'{eta // 60}m {eta % 60}s'

    return f'{eta}s'


# =========================================================
# HELPERS
# =========================================================

def log(s):

    if DEBUG:
        print(s)


def create_view_layers(context):

    context.scene.view_layers[0].name = 'real'

    if 'ground_truth' not in context.scene.view_layers:
        context.scene.view_layers.new(name='ground_truth')

    log('- view layers ready')


def create_mode_switcher_node_group():

    if 'mode_switcher' in bpy.data.node_groups:

        bpy.data.node_groups.remove(
            bpy.data.node_groups['mode_switcher']
        )

    ng = bpy.data.node_groups.new(
        'mode_switcher',
        'ShaderNodeTree'
    )

    ng.interface.new_socket(
        name='Real',
        in_out='INPUT',
        socket_type='NodeSocketShader'
    )

    ng.interface.new_socket(
        name='Ground Truth',
        in_out='INPUT',
        socket_type='NodeSocketColor'
    )

    ng.interface.new_socket(
        name='Switch',
        in_out='OUTPUT',
        socket_type='NodeSocketShader'
    )

    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    gi.location = (-300, 0)
    go.location = (300, 0)

    mix = ng.nodes.new('ShaderNodeMixShader')

    mix.location = (0, 0)
    mix.inputs[0].default_value = 0.0

    ng.links.new(
        gi.outputs[0],
        mix.inputs[1]
    )

    ng.links.new(
        gi.outputs[1],
        mix.inputs[2]
    )

    ng.links.new(
        mix.outputs[0],
        go.inputs[0]
    )

    log('- mode_switcher ready')


def set_mix_shader_value(value):

    ng = bpy.data.node_groups.get('mode_switcher')

    if not ng:
        return

    for n in ng.nodes:

        if n.type == 'MIX_SHADER':
            n.inputs[0].default_value = value


def add_camera_focus(context):

    camera = context.scene.objects.get('Camera')
    target = context.scene.objects.get(MAIN_OBJECT_NAME)

    if not camera or not target:
        return

    if 'Track To' not in camera.constraints:

        t = camera.constraints.new(type='TRACK_TO')

        t.target = target
        t.track_axis = 'TRACK_NEGATIVE_Z'
        t.up_axis = 'UP_Y'


def insert_mode_switcher_node(material):

    for l in list(material.node_tree.links):

        if l.to_socket.name == 'Surface':

            if (
                l.from_node.type == 'GROUP'
                and l.from_node.node_tree
                and l.from_node.node_tree.name == 'mode_switcher'
            ):
                return

            pre = l.from_node
            post = l.to_node

            material.node_tree.links.remove(l)

            group = material.node_tree.nodes.new(
                type='ShaderNodeGroup'
            )

            group.node_tree = bpy.data.node_groups['mode_switcher']

            material.node_tree.links.new(
                pre.outputs[0],
                group.inputs[0]
            )

            material.node_tree.links.new(
                group.outputs[0],
                post.inputs[0]
            )

            return


def toggle_mode(context):

    scene = context.scene
    sb = scene.synthblend

    if sb.mode == 0:

        context.window.view_layer = scene.view_layers['ground_truth']

        sb.mode = 1

        scene.render.filter_size = 0
        scene.view_settings.view_transform = 'Standard'

        set_mix_shader_value(1.0)

    else:

        context.window.view_layer = scene.view_layers['real']

        sb.mode = 0

        scene.render.filter_size = 1.5
        scene.view_settings.view_transform = 'Filmic'

        set_mix_shader_value(0.0)


def set_defect_value(mat_name, node_name, value):

    mat = bpy.data.materials.get(mat_name)

    if not mat:
        return

    node = mat.node_tree.nodes.get(node_name)

    if not node:
        return

    node.outputs[0].default_value = value


def random_camera(context):

    camera = context.scene.objects['Camera']

    r = 4.0 + uniform(-0.2, 8.0)
    theta = np.pi / 2 + uniform(-np.pi / 8, np.pi / 8)
    phi = uniform(0, 2 * np.pi)

    camera.location = (
        r * np.sin(theta) * np.cos(phi),
        r * np.sin(theta) * np.sin(phi),
        r * np.cos(theta),
    )


def run_variation_all(context):

    random_camera(context)

    set_defect_value(
        'helmet',
        'Value',
        uniform(0, 1)
    )

    set_defect_value(
        'helmet',
        'Value.001',
        uniform(0, 1)
    )

    set_defect_value(
        'visor',
        'Value',
        uniform(0, 2 * np.pi)
    )


def render_layer(context, layer, filepath):

    scene = context.scene
    sb = scene.synthblend

    res = int(sb.resolution)

    scene.render.resolution_x = res
    scene.render.resolution_y = res

    os.makedirs(
        os.path.dirname(filepath),
        exist_ok=True
    )

    context.window.view_layer = scene.view_layers[layer]

    scene.render.filepath = filepath
    scene.render.image_settings.file_format = 'PNG'

    bpy.ops.render.render(write_still=True)

    log(f'- rendered {filepath}')


# =========================================================
# PROPERTIES
# =========================================================

class MyProperties(PropertyGroup):

    n_samples: IntProperty(
        name="Samples",
        default=1000,
        min=1,
        max=100000
    )

    output_dir: StringProperty(
        name="Output Folder",
        default="../output/",
        subtype='DIR_PATH'
    )

    target_collection: PointerProperty(
        type=bpy.types.Collection
    )

    resolution: EnumProperty(
        name="Resolution",
        items=[
            ('256', '256x256', ''),
            ('512', '512x512', ''),
            ('640', '640x640 (YOLO)', ''),
            ('1024', '1024x1024', ''),
        ],
        default='640'
    )

    mode: IntProperty(
        default=0,
        min=0,
        max=1
    )

    setup_expanded: BoolProperty(default=True)
    preview_expanded: BoolProperty(default=True)
    dataset_expanded: BoolProperty(default=True)
    stats_expanded: BoolProperty(default=True)


# =========================================================
# OPERATORS
# =========================================================

class WM_OT_GenerateComponents(Operator):

    bl_label = "Generate Components"
    bl_idname = "wm.gen_components"

    def execute(self, context):

        create_view_layers(context)
        create_mode_switcher_node_group()
        add_camera_focus(context)

        self.report(
            {'INFO'},
            "Components Generated"
        )

        return {'FINISHED'}


class WM_OT_UpdateMaterials(Operator):

    bl_label = "Update Materials"
    bl_idname = "wm.update_materials"

    def execute(self, context):

        col = context.scene.synthblend.target_collection

        if not col:

            self.report(
                {'ERROR'},
                "No collection selected"
            )

            return {'CANCELLED'}

        for o in col.objects:

            for m in o.data.materials:

                if m:
                    insert_mode_switcher_node(m)

        self.report(
            {'INFO'},
            "Materials Updated"
        )

        return {'FINISHED'}


class WM_OT_ToggleMaterials(Operator):

    bl_label = "Toggle Real / GT"
    bl_idname = "wm.toggle_real_gt"

    def execute(self, context):

        toggle_mode(context)

        return {'FINISHED'}


class WM_OT_SampleVariation(Operator):

    bl_label = "Sample Variation"
    bl_idname = "wm.sample_variation"

    def execute(self, context):

        run_variation_all(context)

        return {'FINISHED'}


class WM_OT_CameraPreset(Operator):

    bl_label = "Camera Preset"
    bl_idname = "wm.camera_preset"

    preset: StringProperty()

    def execute(self, context):

        cam = context.scene.objects.get("Camera")

        if not cam:
            return {'CANCELLED'}

        if self.preset == 'TOP':
            cam.location = (0, 0, 6)

        elif self.preset == 'FRONT':
            cam.location = (0, -6, 0)

        elif self.preset == 'SIDE':
            cam.location = (6, 0, 0)

        elif self.preset == 'RANDOM':
            random_camera(context)

        return {'FINISHED'}


class WM_OT_OpenOutput(Operator):

    bl_label = "Open Output Folder"
    bl_idname = "wm.open_output"

    def execute(self, context):

        path = bpy.path.abspath(
            context.scene.synthblend.output_dir
        )

        if sys.platform == "win32":
            subprocess.Popen(f'explorer "{path}"')

        return {'FINISHED'}


class WM_OT_StartDataset(Operator):

    bl_label = "Generate Dataset"
    bl_idname = "wm.start_dataset"

    def execute(self, context):

        global dataset_log

        dataset_log.clear()

        scene = context.scene
        sb = scene.synthblend

        base = bpy.path.abspath(sb.output_dir)

        real_dir = os.path.join(base, 'real')
        gt_dir = os.path.join(base, 'ground_truth')

        os.makedirs(real_dir, exist_ok=True)
        os.makedirs(gt_dir, exist_ok=True)

        if sb.mode != 0:
            toggle_mode(context)

        session['start_time'] = time.time()
        session['total'] = sb.n_samples
        session['done'] = 0
        session['running'] = True

        for i in range(sb.n_samples):

            pair_id = randint(0, 999999)

            run_variation_all(context)

            real_path = os.path.join(
                real_dir,
                f'{pair_id:06d}.png'
            )

            gt_path = os.path.join(
                gt_dir,
                f'{pair_id:06d}.png'
            )

            render_layer(
                context,
                'real',
                real_path
            )

            toggle_mode(context)

            render_layer(
                context,
                'ground_truth',
                gt_path
            )

            toggle_mode(context)

            cam = context.scene.objects['Camera']

            dataset_log.append({
                "id": pair_id,
                "camera_location": list(cam.location),
                "real_path": real_path,
                "gt_path": gt_path
            })

            session['real_renders'] += 1
            session['gt_renders'] += 1
            session['pairs'] += 1
            session['done'] += 1

        report_path = os.path.join(
            base,
            'dataset_report.json'
        )

        with open(report_path, 'w') as f:
            json.dump(dataset_log, f, indent=4)

        session['running'] = False

        self.report(
            {'INFO'},
            "Dataset Generation Complete"
        )

        return {'FINISHED'}


class WM_OT_ResetSession(Operator):

    bl_label = "Reset Session"
    bl_idname = "wm.reset_session"

    def execute(self, context):

        reset_session()

        return {'FINISHED'}


# =========================================================
# PANEL
# =========================================================

def draw_section_header(layout, label, prop_owner, prop_name):

    row = layout.row(align=True)

    icon = (
        'DISCLOSURE_TRI_DOWN'
        if getattr(prop_owner, prop_name)
        else 'DISCLOSURE_TRI_RIGHT'
    )

    row.prop(
        prop_owner,
        prop_name,
        icon=icon,
        icon_only=True,
        emboss=False
    )

    row.label(text=label)


class OBJECT_PT_SynthBlendPanel(Panel):

    bl_label = "SynthBlend4"

    bl_idname = "OBJECT_PT_synthblend_panel"

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bl_category = "Annotation"

    def draw(self, context):

        layout = self.layout

        scene = context.scene
        sb = scene.synthblend

        # =====================================================
        # SETUP
        # =====================================================

        draw_section_header(
            layout,
            "Setup",
            sb,
            "setup_expanded"
        )

        if sb.setup_expanded:

            box = layout.box()

            box.operator(
                "wm.gen_components",
                icon='SETTINGS'
            )

            box.prop(sb, "target_collection")

            box.operator(
                "wm.update_materials",
                icon='MATERIAL'
            )

        # =====================================================
        # PREVIEW
        # =====================================================

        draw_section_header(
            layout,
            "Preview",
            sb,
            "preview_expanded"
        )

        if sb.preview_expanded:

            box = layout.box()

            row = box.row(align=True)

            row.operator(
                "wm.toggle_real_gt",
                text="Real",
                icon='RENDER_STILL'
            )

            row.operator(
                "wm.toggle_real_gt",
                text="GT",
                icon='IMAGE_DATA'
            )

            box.operator(
                "wm.sample_variation",
                icon='FILE_REFRESH'
            )

            box.separator()

            row = box.row(align=True)

            row.operator(
                "wm.camera_preset",
                text="Top"
            ).preset = 'TOP'

            row.operator(
                "wm.camera_preset",
                text="Front"
            ).preset = 'FRONT'

            row.operator(
                "wm.camera_preset",
                text="Side"
            ).preset = 'SIDE'

            row.operator(
                "wm.camera_preset",
                text="Random"
            ).preset = 'RANDOM'

        # =====================================================
        # DATASET
        # =====================================================

        draw_section_header(
            layout,
            "Dataset",
            sb,
            "dataset_expanded"
        )

        if sb.dataset_expanded:

            box = layout.box()

            box.prop(sb, "n_samples")
            box.prop(sb, "resolution")
            box.prop(sb, "output_dir")

            box.operator(
                "wm.open_output",
                icon='FILE_FOLDER'
            )

            box.operator(
                "wm.start_dataset",
                icon='RENDER_ANIMATION'
            )

        # =====================================================
        # STATS
        # =====================================================

        draw_section_header(
            layout,
            "Session Stats",
            sb,
            "stats_expanded"
        )

        if sb.stats_expanded:

            box = layout.box()

            box.label(
                text=f"Real Renders: {session['real_renders']}"
            )

            box.label(
                text=f"GT Masks: {session['gt_renders']}"
            )

            box.label(
                text=f"Pairs: {session['pairs']}"
            )

            elapsed = session_elapsed()

            box.label(
                text=f"Elapsed: {elapsed}s"
            )

            if session['running']:

                box.label(
                    text=f"ETA: {session_eta()}"
                )

            box.operator(
                "wm.reset_session",
                icon='TRASH'
            )


# =========================================================
# REGISTER
# =========================================================

classes = (

    MyProperties,

    WM_OT_GenerateComponents,
    WM_OT_UpdateMaterials,

    WM_OT_ToggleMaterials,
    WM_OT_SampleVariation,

    WM_OT_CameraPreset,
    WM_OT_OpenOutput,

    WM_OT_StartDataset,

    WM_OT_ResetSession,

    OBJECT_PT_SynthBlendPanel,
)


def register():

    global custom_icons

    for cls in classes:
        bpy.utils.register_class(cls)

    custom_icons = previews.new()

    bpy.types.Scene.synthblend = PointerProperty(
        type=MyProperties
    )


def unregister():

    global custom_icons

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.synthblend

    previews.remove(custom_icons)


if __name__ == "__main__":
    register()
