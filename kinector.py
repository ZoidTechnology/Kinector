import bpy
import math
from kinector import kinect

bl_info = {
	'name': 'Kinector',
	'author': 'Zoid Technology',
	'version': (1, 0),
	'blender': (3, 3, 0)
}

JOINTS = (
	'SpineBase',
	'SpineMid',
	'Neck',
	'Head',
	'ShoulderLeft',
	'ElbowLeft',
	'WristLeft',
	'HandLeft',
	'ShoulderRight',
	'ElbowRight',
	'WristRight',
	'HandRight',
	'HipLeft',
	'KneeLeft',
	'AnkleLeft',
	'FootLeft',
	'HipRight',
	'KneeRight',
	'AnkleRight',
	'FootRight',
	'SpineShoulder',
	'HandTipLeft',
	'ThumbLeft',
	'HandTipRight',
	'ThumbRight'
)

BONES = (
	('LowerSpine', None, 'SpineMid', 0, 0, ({'target': 'HipLeft', 'track_axis': 'TRACK_NEGATIVE_X'}, {'target': 'HipRight', 'track_axis': 'TRACK_X', 'influence': 0.5})),
	('UpperSpine', 'LowerSpine', 'SpineShoulder', 0, 0, ({'target': 'ShoulderLeft', 'track_axis': 'TRACK_NEGATIVE_X'}, {'target': 'ShoulderRight', 'track_axis': 'TRACK_X', 'influence': 0.5})),
	('Neck', 'UpperSpine', 'Neck', 0, 0),
	('Head', 'Neck', 'Head', 0, 0),
	('ClavicleLeft', 'UpperSpine', 'ShoulderLeft', 90, 0),
	('UpperArmLeft', 'ClavicleLeft', 'ElbowLeft', 135, -45, ({'target': 'WristLeft', 'track_axis': 'TRACK_NEGATIVE_Z'},)),
	('LowerArmLeft', 'UpperArmLeft', 'WristLeft', 135, -45),
	('HandLeft', 'LowerArmLeft', 'HandLeft', 135, -45),
	('FingerLeft', 'HandLeft', 'HandTipLeft', 135, -45),
	('ThumbLeft', 'LowerArmLeft', 'ThumbLeft', 180, 0),
	('ClavicleRight', 'UpperSpine', 'ShoulderRight', -90, 0),
	('UpperArmRight', 'ClavicleRight', 'ElbowRight', -135, 45, ({'target': 'WristRight', 'track_axis': 'TRACK_NEGATIVE_Z'},)),
	('LowerArmRight', 'UpperArmRight', 'WristRight', -135, 45),
	('HandRight', 'LowerArmRight', 'HandRight', -135, 45),
	('FingerRight', 'HandRight', 'HandTipRight', -135, 45),
	('ThumbRight', 'LowerArmRight', 'ThumbRight', 180, 0),
	('HipLeft', None, 'HipLeft', 90, 0),
	('UpperLegLeft', 'HipLeft', 'KneeLeft', 180, 0, ({'target': 'AnkleLeft', 'track_axis': 'TRACK_Z'},)),
	('LowerLegLeft', 'UpperLegLeft', 'AnkleLeft', 180, 0),
	('FootLeft', 'LowerLegLeft', 'FootLeft', 180, 0),
	('HipRight', None, 'HipRight', -90, 0),
	('UpperLegRight', 'HipRight', 'KneeRight', 180, 0, ({'target': 'AnkleRight', 'track_axis': 'TRACK_Z'},)),
	('LowerLegRight', 'UpperLegRight', 'AnkleRight', 180, 0),
	('FootRight', 'LowerLegRight', 'FootRight', 180, 0)
)

connected = False
active_bodies = []

class KINECTOR_PG_properties(bpy.types.PropertyGroup):
	update_rate: bpy.props.IntProperty(name='Update Rate', min=1, default=60)
	process_noise: bpy.props.FloatProperty(name='Process Noise', default=1)
	observation_noise: bpy.props.FloatProperty(name='Observation Noise', default=0.02)
	body_offset: bpy.props.IntProperty(name='Body Offset', min=0)
	insert_keyframes: bpy.props.BoolProperty(name='Insert Keyframes')

class KINECTOR_OT_add_body(bpy.types.Operator):
	"""Add Kinector body to the scene"""
	bl_idname = 'kinector.add_body'
	bl_label = 'Kinector Body'
	bl_options = {'REGISTER', 'UNDO'}

	body: bpy.props.IntProperty(name='Body', min=0)
	size: bpy.props.FloatProperty(name='Joint Size', default=0.05)
	
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)

	def execute(self, context):
		context.view_layer.objects.active = None

		for object in bpy.context.selected_objects:
			object.select_set(False)

		for joint in JOINTS:
			name = joint + str(self.body)
			object = bpy.data.objects.get(name)

			if not object:
				object = bpy.data.objects.new(name, None)
				object.empty_display_size = self.size
				context.view_layer.active_layer_collection.collection.objects.link(object)
			
			object.select_set(True)

		name = 'Body' + str(self.body)
		armature = bpy.data.armatures.new(name)
		object = bpy.data.objects.new(name, armature)

		context.view_layer.active_layer_collection.collection.objects.link(object)
		object.select_set(True)
		context.view_layer.objects.active = object

		for bone in BONES:
			bpy.ops.object.mode_set(mode='EDIT')

			edit_bone = armature.edit_bones.new(bone[0])

			if bone[1]:
				edit_bone.parent = armature.edit_bones[bone[1]]
				edit_bone.use_connect = True
			
			angle = math.radians(bone[3] + 90)
			edit_bone.tail = (edit_bone.head[0] + math.cos(angle), 0, edit_bone.head[2] + math.sin(angle))
			edit_bone.roll = math.radians(bone[4])
			edit_bone.inherit_scale = 'NONE'

			bpy.ops.object.mode_set(mode='POSE')

			pose_bone = object.pose.bones[bone[0]]

			if not bone[1]:
				constraint = pose_bone.constraints.new('COPY_LOCATION')
				constraint.target = bpy.data.objects[JOINTS[0] + str(self.body)]

			constraint = pose_bone.constraints.new('STRETCH_TO')
			constraint.target = bpy.data.objects[bone[2] + str(self.body)]
			constraint.rest_length = 1
			constraint.volume = 'NO_VOLUME'

			for constraint_properties in bone[5] if len(bone) > 5 else ():
				constraint = pose_bone.constraints.new('LOCKED_TRACK')
				constraint.lock_axis = 'LOCK_Y'

				for property, value in constraint_properties.items():
					if property == 'target':
						value = bpy.data.objects[value + str(self.body)]

					setattr(constraint, property, value)

		bpy.ops.object.mode_set(mode='OBJECT')

		return {'FINISHED'}

class KINECTOR_OT_connect(bpy.types.Operator):
	"""Connect to Kinect"""
	bl_idname = 'kinector.connect'
	bl_label = 'Connect'

	def invoke(self, context, event):
		result = kinect.open()

		if result:
			self.report({'ERROR'}, 'Failed to connect: ' + str(result))
			return {'CANCELLED'}
		
		bpy.app.timers.register(update)

		global connected
		connected = True

		return {'FINISHED'}

class KINECTOR_OT_disconnect(bpy.types.Operator):
	"""Disconnect from Kinect"""
	bl_idname = 'kinector.disconnect'
	bl_label = 'Disconnect'

	def invoke(self, context, event):
		if bpy.app.timers.is_registered(update):
			bpy.app.timers.unregister(update)
		
		result = kinect.close()

		if result:
			self.report({'ERROR'}, 'Failed to disconnect: ' + str(result))
			return {'CANCELLED'}
		
		global connected
		connected = False

		return {'FINISHED'}

class KINECTOR_PT_panel(bpy.types.Panel):
	bl_label = 'Kinector'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'

	def draw(self, context):
		layout = self.layout
		properties = context.scene.kinector

		layout.prop(properties, 'update_rate')
		layout.separator()

		layout.prop(properties, 'process_noise')
		layout.prop(properties, 'observation_noise')
		layout.separator()

		layout.prop(properties, 'body_offset')
		layout.prop(properties, 'insert_keyframes')
		layout.separator()

		operator = KINECTOR_OT_disconnect.bl_idname if connected else KINECTOR_OT_connect.bl_idname
		layout.operator(operator)

def add_body(self, context):
	layout = self.layout

	layout.separator()
	layout.operator(KINECTOR_OT_add_body.bl_idname, icon='OUTLINER_OB_ARMATURE')

def update():
	global active_bodies
	properties = bpy.context.scene.kinector

	if not kinect.update(properties.process_noise, properties.observation_noise):
		bodies = kinect.getBodies()

		for id, body in enumerate(bodies):
			if body.tracked:
				if not id in active_bodies:
					active_bodies.append(id)
			elif id in active_bodies:
				active_bodies.remove(id)
		
		for body_index, id in enumerate(active_bodies):
			for joint_index, joint_name in enumerate(JOINTS):
				object = bpy.data.objects.get(joint_name + str(body_index + properties.body_offset))

				if object:
					joint = bodies[id].joints[joint_index]

					object.location.x = joint.x
					object.location.y = joint.z
					object.location.z = joint.y

					if properties.insert_keyframes:
						object.keyframe_insert(data_path='location')

	return 1 / properties.update_rate

classes = (
	KINECTOR_PG_properties,
	KINECTOR_OT_add_body,
	KINECTOR_OT_connect,
	KINECTOR_OT_disconnect,
	KINECTOR_PT_panel
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Scene.kinector = bpy.props.PointerProperty(type=KINECTOR_PG_properties)
	bpy.types.VIEW3D_MT_add.append(add_body)

def unregister():
	bpy.types.VIEW3D_MT_add.remove(add_body)

	if connected:
		bpy.ops.kinector.disconnect('INVOKE_DEFAULT')

	del bpy.types.Scene.kinector
	
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)