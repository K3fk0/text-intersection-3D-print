"""
Script for creating 3D printed text intersection objects.

This script is designed for Blender on Windows devices.

It creates new panel for user, that allows them to select which type of 3D print text export they want.
User can choose between normal 3D text intersection and multiple models
created from all letters in both words.
To be able to correctly create 3D model separated by letters, both words have to have the same length.
Words use AGENCYB font.

The script uses bpy module for all blender related modelling.
"""

import bpy
from math import radians


def clear_workspace():
    """ Deletes all previous model from workspace."""
    # select all objects
    bpy.ops.object.select_all(action='SELECT')

    # delete them
    bpy.ops.object.delete()


def create_text_object(txt, extrude_size, name, rotation_z,
                       centre_position, platform_height, font):
    """
    Creates one text object in the center of the workspace.
    Object is extruded, in order to compute intersection of two text objects.

    :param txt:             text to be converted into 3D object
    :param extrude_size:    how much should the text object be extruded, to create correct intersection
    :param name:            name of text object after it is created
                            (only used when creating intersection of objects)
    :param rotation_z:      rotation of 3D text object
    :param centre_position: where should be the origin of object on x-axis
    :param platform_height: Height of platform
    :param font:            Used font

    :return:    created text object
    """
    # create text object
    bpy.ops.object.text_add(enter_editmode=False, align='WORLD',
                            location=(0, centre_position, platform_height - 0.02), scale=(2, 2, 2),
                            rotation=(radians(90), 0, rotation_z))

    # set text data to wanted text
    text_obj = bpy.context.object
    text_obj.data.body = txt

    # rename object in collection of objects
    text_obj.name = name
    text_obj.data.name = name + " data"

    # align text to center
    text_obj.data.align_x = 'CENTER'

    # change font
    if font is not None:
        text_obj.data.font = font

    # change text size
    text_obj.data.size = 3

    # extrude object to find intersection
    text_obj.data.extrude = extrude_size

    # convert text object to mesh object
    bpy.ops.object.convert(target='MESH')

    return text_obj


def create_intersection_object(fst_text):
    """
    Creates intersection object from both created text objects.
    Objects are searched by their name.

    :param fst_text:    Text object to use the intersection modifier in Blender on.

    :return:    Intersection object
    """
    # make first text object active
    bpy.context.view_layer.objects.active = bpy.data.objects["first text"]

    # create intersect modifier for first text mesh
    fst_intersect_mod = fst_text.modifiers.new("Intersection on first object",
                                               'BOOLEAN')
    fst_intersect_mod.operation = 'INTERSECT'
    fst_intersect_mod.use_self = True
    fst_intersect_mod.object = bpy.data.objects["second text"]

    # apply modifier
    bpy.ops.object.modifier_apply(modifier="Intersection on first object")

    # make second text object active
    bpy.context.view_layer.objects.active = bpy.data.objects["second text"]

    # delete second text object
    bpy.ops.object.delete()

    # make first text object active
    bpy.context.view_layer.objects.active = bpy.data.objects["first text"]

    # rename final mesh
    intersect_mesh = bpy.context.object
    intersect_mesh.name = "final mesh"
    intersect_mesh.data.name = "final mesh data"

    intersect_mesh.data.use_auto_smooth = True

    return intersect_mesh


def add_platform(intersect_mesh, centre_position,
                 platform_height, width, depth, is_top_platform=False):
    """
    Adds bottom and optionally top platform on given intersection object.

    :param intersect_mesh:  Give intersection object.
    :param centre_position: Centre position of intersection object.
    :param platform_height: Height of created platform.
    :param width:           Width of platform
    :param depth:           Depth of platform
    :param is_top_platform: Determines if top or bottom platform is being created.
    """
    # set height location of platform
    z_location = 0
    if is_top_platform:
        z_location = 1.98 + platform_height

    # create platform as cube object
    bpy.ops.mesh.primitive_cube_add(enter_editmode=True, align='WORLD',
                                    location=(0, centre_position, z_location),
                                    scale=(depth / 2 + 0.2, width / 2 + 0.2, platform_height))

    # rename object in collection of objects
    platform_obj = bpy.context.object
    platform_obj.name = "platform"
    platform_obj.data.name = "platform data"

    # deselect all objects
    bpy.ops.mesh.select_all(action='DESELECT')

    # go to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # select bottom face to create platform look of the platform
    if is_top_platform:
        platform_obj.data.polygons[5].select = True
    else:
        platform_obj.data.polygons[4].select = True

    # resize the bottom face adequately
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.resize(value=(1 + platform_height * 4 / depth,
                                    1 + platform_height * 4 / width, 1))

    # go back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # make intersect mesh active
    bpy.context.view_layer.objects.active = intersect_mesh

    # create union modifier for intersect object and platform
    union_mod = intersect_mesh.modifiers.new("Union of intersect mesh and platform",
                                             'BOOLEAN')
    union_mod.operation = 'UNION'
    union_mod.use_self = True
    union_mod.object = bpy.data.objects["platform"]

    # apply modifier
    bpy.ops.object.modifier_apply(modifier="Union of intersect mesh and platform")

    # make second text object active
    bpy.context.view_layer.objects.active = bpy.data.objects["platform"]

    # delete second text object
    bpy.ops.object.delete()

    # set intersect object as active
    bpy.context.view_layer.objects.active = intersect_mesh


def finalize_mesh(max_size):
    """
    Finalizes object before it exporting into stl to be able to correctly 3D print it.

    :param max_size: Max size of object on x/y-axis
    """
    # select final mesh
    bpy.ops.object.select_all(action='SELECT')
    final_mesh = bpy.context.object

    # create new decimate modifier and apply it
    decimate_mod = final_mesh.modifiers.new("Decimate modifier", 'DECIMATE')
    decimate_mod.decimate_type = 'DISSOLVE'
    bpy.ops.object.modifier_apply(modifier="Decimate modifier")

    # scale to final size
    final_obj = bpy.data.objects["final mesh"]
    print(final_obj.dimensions.x)
    print(final_obj.dimensions.y)
    print(final_obj.dimensions.z)

    scale = min(max_size / final_obj.dimensions.x,
                max_size / final_obj.dimensions.y,
                max_size / final_obj.dimensions.z)
    final_obj.scale = (scale, scale, scale)


def export_to_stl(file):
    """
    Exports object into stl file with given path.

    :param file: Path to export file.
    """
    # select final object
    bpy.ops.object.select_all(action='SELECT')

    # export to file
    bpy.ops.export_mesh.stl(check_existing=True, filepath=file,
                            filter_glob="*.stl", ascii=False, use_mesh_modifiers=True,
                            axis_forward='Y', axis_up='Z', global_scale=1.0)


def single_mesh(fst, snd, with_platform, platform_height, font, centre_position=0):
    """
    Creates one piece text intersection 3D object.

    :param fst:             First word of 3D text intersection object
    :param snd:             Second word of 3D text intersection object
    :param with_platform:   Determines, if user wants to model also top platform
    :param platform_height: Height of platform/s
    :param font:       Used font
    :param centre_position: Centre position of created 3D text intersection object
    """
    fst_text = create_text_object(fst, len(snd) * 2, "first text", 0,
                                  centre_position, platform_height, font)
    _ = create_text_object(snd, len(fst) * 2, "second text", radians(90),
                           centre_position, platform_height, font)

    intersect_mesh = create_intersection_object(fst_text)

    # get width and depth of object
    width = intersect_mesh.dimensions.z
    depth = intersect_mesh.dimensions.x

    add_platform(intersect_mesh, centre_position, platform_height, width, depth)
    if with_platform:
        add_platform(intersect_mesh, centre_position, platform_height, width, depth, True)


def mesh_by_letters(fst_word, snd_word, with_platform, platform_height, font):
    """
    Creates separate models for each letter of two words as multiple 3D text intersection objects.

    :param fst_word:        First word
    :param snd_word:        Second word
    :param with_platform:   Determines, if user wants to model also top platform
    :param platform_height  Height of platforms
    :param font:            Used font
    """
    fst_length = len(fst_word)

    for i in range(fst_length):
        single_mesh(fst_word[i], snd_word[i], with_platform,
                    platform_height, font, i * 2 - fst_length // 2 - 2)


def main(fst, snd, by_letters, with_top_platform, platform_height, font):
    clear_workspace()

    if by_letters:
        mesh_by_letters(fst, snd, with_top_platform, platform_height, font)
    else:
        single_mesh(fst, snd, with_top_platform, platform_height, font)

    # join all objects to one mesh
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.join()

    bpy.context.object.location = (0, 0, 0)


class Model_mesh(bpy.types.Operator):
    """
    Blender operator used for creating 3D text intersection model.
    """
    bl_idname = "mesh.model"
    bl_label = "Model"
    bl_options = {'REGISTER', 'UNDO'}

    fst: bpy.props.StringProperty(name="Enter first word: ", description="First word")
    snd: bpy.props.StringProperty(name="Enter second word: ", description="Second word")
    font_path: bpy.props.StringProperty(name="Font path: ", description="Absolute filepath of the font to be used")
    by_letters: bpy.props.BoolProperty(name="Separate words by letters?", default=False,
                                       description="Separate by letters")
    platform_height: bpy.props.FloatProperty(name="Platform height (cm)?", min=0.5,
                                             max=2, step=1, default=1, description="Height of the platform/s")
    with_top_platform: bpy.props.BoolProperty(name="Top platform?", default=False, description="Model also top platform")

    @classmethod
    def poll(cls, _):
        return True

    def invoke(self, context, _):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, _):
        if self.by_letters and not len(self.fst) == len(self.snd):
            self.report({"WARNING"}, "Words have to have the same "
                                     "length in order to model them separately by letters.")
            return {"CANCELLED"}

        try:
            font = bpy.data.fonts.load(filepath=self.font_path)
        except RuntimeError:
            self.report({"WARNING"}, "Could not load wanted font. Chose default instead.")
            font = None

        main(self.fst.upper(), self.snd.upper(), self.by_letters,
             self.with_top_platform, self.platform_height / 10, font)
        return {'FINISHED'}


class Export_model(bpy.types.Operator):
    """
    Blender operator used for finalizing and exporting created model.
    """
    bl_idname = "mesh.export"
    bl_label = "Export"
    bl_options = {'REGISTER', 'UNDO'}

    filename: bpy.props.StringProperty(name="Export directory: ", description="Absolute filepath to the directory, "
                                                                              "where the model will be exported")
    max_size: bpy.props.IntProperty(name="Max model size (cm)", min=1, max=100, default=10,
                                    description="Maximal length of model")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, _):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, _):
        if len(self.filename) == 0:
            self.report({"WARNING"}, "Invalid directory path.")
            return {'CANCELLED'}

        finalize_mesh(self.max_size / 100)
        export_to_stl(self.filename + "\\export.stl")
        return {'FINISHED'}


class CUSTOM_PT_Text_3D_panel(bpy.types.Panel):
    """
    Blender panel that uses Blender operators, for creating 3D text intersection object and exporting it.
    """
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "3D-Text"
    bl_label = "3D-Text model"

    def draw(self, _):
        self.layout.operator("mesh.model")
        self.layout.operator("mesh.export")


def register():
    bpy.utils.register_class(Model_mesh)
    bpy.utils.register_class(Export_model)
    bpy.utils.register_class(CUSTOM_PT_Text_3D_panel)


def unregister():
    bpy.utils.unregister_class(Model_mesh)
    bpy.utils.unregister_class(Export_model)
    bpy.utils.unregister_class(CUSTOM_PT_Text_3D_panel)


if __name__ == "__main__":
    register()
