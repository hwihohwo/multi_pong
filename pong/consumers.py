from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
import json
import numpy as np
import asyncio
import cProfile

class PongConsumer(AsyncWebsocketConsumer):
	channel_layer = get_channel_layer()
	groups = {}
	groups_info = {}
	max_group_size = 2
	radius = 0.04
	bar_position = 2.5
	bar_width = 0.08
	bar_height = 0.7
	bar_depth = 0.1
	ground_height = 3.0
	ground_width = 6.0


	async def get_group_member_count(self, channel_name):
		for group_name, members in PongConsumer.groups.items():
			if channel_name in members:
				return len(members)
		return 0

	async def add_to_group(self, channel_name):
		for group_name, members in PongConsumer.groups.items():
			if len(members) < PongConsumer.max_group_size:
				await PongConsumer.channel_layer.group_add(group_name, channel_name)
				members.append(channel_name)
				return group_name
		new_group_name = f"group_{len(PongConsumer.groups) + 1}"
		await PongConsumer.channel_layer.group_add(new_group_name, channel_name)
		PongConsumer.groups[new_group_name] = [channel_name]
		return new_group_name

	async def send_disconnect_message(self, event):
		message = event['message']
		await self.send(text_data=json.dumps({
			'type': 'disconnect_message',
			'message': message
		}))

	async def initialize_group(self):
		tmp_vector = np.array([1.0, 1.0, 0.0])
		sphere_direction = tmp_vector / np.linalg.norm(tmp_vector)
		PongConsumer.groups_info[self.my_group] = {
			'sphere_direction': [sphere_direction[0], sphere_direction[1], sphere_direction[2]],

			'sphere_position': [0.0, 0.0, 0.0],

			'sphere_speed': 0.03,

			'player_1_score': 0,
			'player_2_score': 0,

			'p1_bar_position': [-PongConsumer.bar_position, 0.0, 0.0],

			'p2_bar_position': [PongConsumer.bar_position, 0.0, 0.0],

			'p1_moving_up': False,

			'p1_moving_down': False,

			'p2_moving_up': False,

			'p2_moving_down': False,

			'sphere_bounding_box': {
				'x_min': -PongConsumer.radius,
				'x_max': PongConsumer.radius,
				'y_min': -PongConsumer.radius,
				'y_max': PongConsumer.radius,
				'z_min': -PongConsumer.radius,
				'z_max': PongConsumer.radius
			},

			'p2_bar_box' : {
				'x_min': PongConsumer.bar_position - PongConsumer.bar_width / 2,
				'x_max': PongConsumer.bar_position + PongConsumer.bar_width / 2,
				'y_min': -PongConsumer.bar_height / 2,
				'y_max': PongConsumer.bar_height / 2,
				'z_min': -PongConsumer.bar_depth / 2,
				'z_max': PongConsumer.bar_depth / 2
			},

			'p1_bar_box' : {
				'x_min': -PongConsumer.bar_position - PongConsumer.bar_width / 2,
				'x_max': -PongConsumer.bar_position + PongConsumer.bar_width / 2,
				'y_min': -PongConsumer.bar_height / 2,
				'y_max': PongConsumer.bar_height / 2,
				'z_min': -PongConsumer.bar_depth / 2,
				'z_max': PongConsumer.bar_depth / 2
			},

			'upper_plane_normal': [0.0, -1.0, 0.0],

			'upper_plane_constant': PongConsumer.ground_height / 2.0,

			'lower_plane_normal': [0.0, 1.0, 0.0],

			'lower_plane_constant': PongConsumer.ground_height / 2.0,

			'left_plane_normal': [1.0, 0.0, 0.0],

			'left_plane_constant': PongConsumer.ground_width / 2.0,

			'right_plane_normal': [-1.0, 0.0, 0.0],

			'right_plane_constant': PongConsumer.ground_width / 2.0,
		}

	async def check_box_plane_collision(self, box_coordinates, plane_normal, plane_constant):
		min, max = 0, 0

		if plane_normal[0] > 0:
			min = plane_normal[0] * box_coordinates['x_min']
			max = plane_normal[0] * box_coordinates['x_max']
		
		else:
			min = plane_normal[0] * box_coordinates['x_max']
			max = plane_normal[0] * box_coordinates['x_min']
		
		if plane_normal[1] > 0:
			min += plane_normal[1] * box_coordinates['y_min']
			max += plane_normal[1] * box_coordinates['y_max']
		
		else:
			min += plane_normal[1] * box_coordinates['y_max']
			max += plane_normal[1] * box_coordinates['y_min']

		if plane_normal[2] > 0:
			min += plane_normal[2] * box_coordinates['z_min']
			max += plane_normal[2] * box_coordinates['z_max']

		else:
			min += plane_normal[2] * box_coordinates['z_max']
			max += plane_normal[2] * box_coordinates['z_min']

		return min <= -plane_constant and max >= -plane_constant

	async def check_box_bar_collision(self, box1_coordinates, box2_coordinates):
		return not (box1_coordinates['x_max'] < box2_coordinates['x_min'] or
				box1_coordinates['x_min'] > box2_coordinates['x_max'] or
				box1_coordinates['y_max'] < box2_coordinates['y_min'] or
				box1_coordinates['y_min'] > box2_coordinates['y_max'] or
				box1_coordinates['z_max'] < box2_coordinates['z_min'] or
				box1_coordinates['z_min'] > box2_coordinates['z_max'])

	async def reflect_vector(self, vector, normal):
		vector = np.array(vector)
		normal = np.array(normal)
		return vector - 2 * np.dot(vector, normal) * normal

	async def reflect_vector_from_bar(self, sphere_position, normal, bar_position):
		tmp_vector = np.array([0, 0, 0])
		position = np.array([sphere_position[0], sphere_position[1], sphere_position[2]])
		b_position = np.array([bar_position[0], bar_position[1], bar_position[2]])
		tmp_vector = (position - b_position) + normal
		return tmp_vector / np.linalg.norm(tmp_vector)

	async def check_sphere_collision(self):
		if await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['upper_plane_normal'], PongConsumer.groups_info[self.my_group]['upper_plane_constant']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector(PongConsumer.groups_info[self.my_group]['sphere_direction'], PongConsumer.groups_info[self.my_group]['upper_plane_normal'])

		elif await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['lower_plane_normal'], PongConsumer.groups_info[self.my_group]['lower_plane_constant']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector(PongConsumer.groups_info[self.my_group]['sphere_direction'], PongConsumer.groups_info[self.my_group]['lower_plane_normal'])

		elif await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['left_plane_normal'], PongConsumer.groups_info[self.my_group]['left_plane_constant']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector(PongConsumer.groups_info[self.my_group]['sphere_direction'], PongConsumer.groups_info[self.my_group]['left_plane_normal'])

		elif await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['right_plane_normal'], PongConsumer.groups_info[self.my_group]['right_plane_constant']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector(PongConsumer.groups_info[self.my_group]['sphere_direction'], PongConsumer.groups_info[self.my_group]['right_plane_normal'])

		elif await self.check_box_bar_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['p1_bar_box']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector_from_bar(PongConsumer.groups_info[self.my_group]['sphere_position'], np.array([1, 0, 0]), PongConsumer.groups_info[self.my_group]['p1_bar_position'])

		elif await self.check_box_bar_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['p2_bar_box']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector_from_bar(PongConsumer.groups_info[self.my_group]['sphere_position'], np.array([-1, 0, 0]), PongConsumer.groups_info[self.my_group]['p2_bar_position'])

	async def moving_bar_bounding_box(self, box_coordinates, speed):
		box_coordinates['y_min'] += speed
		box_coordinates['y_max'] += speed

	async def moving_sphere_bounding_box(self, box_coordinates):
		box_coordinates['x_min'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][0] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		box_coordinates['x_max'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][0] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		box_coordinates['y_min'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][1] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		box_coordinates['y_max'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][1] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		box_coordinates['z_min'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][2] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		box_coordinates['z_max'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][2] * PongConsumer.groups_info[self.my_group]['sphere_speed']

	async def main_loop(self):
		while True:
			await self.check_sphere_collision()

			# if PongConsumer.groups_info[self.my_group]['p1_moving_up'] and not await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['p1_bar_box'], PongConsumer.groups_info[self.my_group]['upper_plane_normal'], PongConsumer.groups_info[self.my_group]['upper_plane_constant']):
			# 	PongConsumer.groups_info[self.my_group]['p1_bar_position'][1] += 0.03
			# 	await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group]['p1_bar_box'], 0.03)
			# if PongConsumer.groups_info[self.my_group]['p1_moving_down'] and not await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['p1_bar_box'], PongConsumer.groups_info[self.my_group]['lower_plane_normal'], PongConsumer.groups_info[self.my_group]['lower_plane_constant']):
			# 	PongConsumer.groups_info[self.my_group]['p1_bar_position'][1] -= 0.03
			# 	await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group]['p1_bar_box'], -0.03)
			
			# if PongConsumer.groups_info[self.my_group]['p2_moving_up'] and not await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['p2_bar_box'], PongConsumer.groups_info[self.my_group]['upper_plane_normal'], PongConsumer.groups_info[self.my_group]['upper_plane_constant']):
			# 	PongConsumer.groups_info[self.my_group]['p2_bar_position'][1] += 0.03
			# 	await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group]['p2_bar_box'], 0.03)
			# if PongConsumer.groups_info[self.my_group]['p2_moving_down'] and not await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['p2_bar_box'], PongConsumer.groups_info[self.my_group]['lower_plane_normal'], PongConsumer.groups_info[self.my_group]['lower_plane_constant']):
			# 	PongConsumer.groups_info[self.my_group]['p2_bar_position'][1] -= 0.03
			# 	await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group]['p2_bar_box'], -0.03)

			PongConsumer.groups_info[self.my_group]['sphere_position'][0] += PongConsumer.groups_info[self.my_group]['sphere_direction'][0] * PongConsumer.groups_info[self.my_group]['sphere_speed']
			PongConsumer.groups_info[self.my_group]['sphere_position'][1] += PongConsumer.groups_info[self.my_group]['sphere_direction'][1] * PongConsumer.groups_info[self.my_group]['sphere_speed']
			PongConsumer.groups_info[self.my_group]['sphere_position'][2] += PongConsumer.groups_info[self.my_group]['sphere_direction'][2] * PongConsumer.groups_info[self.my_group]['sphere_speed']

			await self.moving_sphere_bounding_box(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'])

			await PongConsumer.channel_layer.group_send(
			    self.my_group,
			    {
			        'type': 'send_positions',
			        'sphere_position': PongConsumer.groups_info[self.my_group]['sphere_position'],
			        'p1_bar_position': PongConsumer.groups_info[self.my_group]['p1_bar_position'],
			        'p2_bar_position': PongConsumer.groups_info[self.my_group]['p2_bar_position']
			    }
			)
			asyncio.sleep(1000 / 60)


	async def send_positions(self, event):
		sphere_position = event['sphere_position']
		p1_bar_position = event['p1_bar_position']
		p2_bar_position = event['p2_bar_position']
		await self.send(text_data=json.dumps({
			'type': 'positions',
			'sphere_position': sphere_position,
			'p1_bar_position': p1_bar_position,
			'p2_bar_position': p2_bar_position
		}))

	# async def send_sphere_position(self, event):
	# 	sphere_position = event['sphere_position']
	# 	await self.send(text_data=json.dumps({
	# 		'type': 'sphere_position',
	# 		'sphere_position': sphere_position
	# 	}))

	# async def send_p1_bar_position(self, event):
	# 	p1_bar_position = event['p1_bar_position']
	# 	await self.send(text_data=json.dumps({
	# 		'type': 'p1_bar_position',
	# 		'p1_bar_position': p1_bar_position
	# 	}))

	# async def send_p2_bar_position(self, event):
	# 	p2_bar_position = event['p2_bar_position']
	# 	await self.send(text_data=json.dumps({
	# 		'type': 'p2_bar_position',
	# 		'p2_bar_position': p2_bar_position
	# 	}))

	async def connect(self):
		self.my_group = await self.add_to_group(self.channel_name)
		await self.accept()
		my_group_member_count = await self.get_group_member_count(self.channel_name)
		if my_group_member_count == 1:
			await self.send(text_data=json.dumps({
				'type': 'player_num',
				'player_num': 1
			}))
		if my_group_member_count == 2:
			await self.send(text_data=json.dumps({
				'type': 'player_num',
				'player_num': 2
			}))
			await self.initialize_group()
			asyncio.create_task(self.main_loop())

	async def disconnect(self, close_code):
		await self.channel_layer.group_send(
			self.my_group,
			{
				'type': 'send_disconnect_message',
				'message': 'disconnect_all'
			}
		)

		# await self.channel_layer.group_discard(
        #     self.my_group,
        #     self.channel_name
        # )

	async def handle_keydown(self, data):
		player_key = f"p{data['player_num']}_bar"
		position_key = f"{player_key}_position"
		box_key = f"{player_key}_box"
		direction = 0.05 if data['keycode'] == 'ArrowUp' else -0.05 if data['keycode'] == 'ArrowDown' else 0

		if direction != 0 and not await self.check_box_plane_collision(
			PongConsumer.groups_info[self.my_group][box_key],
			PongConsumer.groups_info[self.my_group][f"{'upper' if direction > 0 else 'lower'}_plane_normal"],
			PongConsumer.groups_info[self.my_group][f"{'upper' if direction > 0 else 'lower'}_plane_constant"]
		):
			PongConsumer.groups_info[self.my_group][position_key][1] += direction
			await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group][box_key], direction)

	async def receive(self, text_data):
		data = json.loads(text_data)

		if data['type'] == 'disconnect':
			self.close()

		elif data['type'] == 'keydown':
			await self.handle_keydown(data)
		# elif data['type'] == 'keydown':
		# 	if data['keycode'] == 'ArrowUp':
		# 		if data['player_num'] == 1:
		# 			PongConsumer.groups_info[self.my_group]['p1_moving_up'] = True
		# 		else:
		# 			PongConsumer.groups_info[self.my_group]['p2_moving_up'] = True
		# 	elif data['keycode'] == 'ArrowDown':
		# 		if data['player_num'] == 1:
		# 			PongConsumer.groups_info[self.my_group]['p1_moving_down'] = True
		# 		else:
		# 			PongConsumer.groups_info[self.my_group]['p2_moving_down'] = True

		# 	elif data['type'] == 'keyup':
		# 		if data['keycode'] == 'ArrowUp':
		# 			if data['player_num'] == 1:
		# 				PongConsumer.groups_info[self.my_group]['p1_moving_up'] = False
		# 			else:
		# 				PongConsumer.groups_info[self.my_group]['p2_moving_up'] = False
		# 		elif data['keycode'] == 'ArrowDown':
		# 			if data['player_num'] == 1:
		# 				PongConsumer.groups_info[self.my_group]['p1_moving_down'] = False
		# 			else:
		# 				PongConsumer.groups_info[self.my_group]['p2_moving_down'] = False
		# if data['type'] == 'keydown':
		# 	if data['keycode'] == 'ArrowUp':
		# 		if data['player_num'] == 1 and not await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['p1_bar_box'], PongConsumer.groups_info[self.my_group]['upper_plane_normal'], PongConsumer.groups_info[self.my_group]['upper_plane_constant']):
		# 			PongConsumer.groups_info[self.my_group]['p1_bar_position'][1] += 0.03
		# 			await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group]['p1_bar_box'], 0.03)
		# 		elif data['player_num'] == 2 and not await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['p2_bar_box'], PongConsumer.groups_info[self.my_group]['upper_plane_normal'], PongConsumer.groups_info[self.my_group]['upper_plane_constant']):
		# 			PongConsumer.groups_info[self.my_group]['p2_bar_position'][1] += 0.03
		# 			await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group]['p2_bar_box'], 0.03)
		# 	elif data['keycode'] == 'ArrowDown':
		# 		if data['player_num'] == 1 and not await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['p1_bar_box'], PongConsumer.groups_info[self.my_group]['lower_plane_normal'], PongConsumer.groups_info[self.my_group]['lower_plane_constant']):
		# 			PongConsumer.groups_info[self.my_group]['p1_bar_position'][1] -= 0.03
		# 			await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group]['p1_bar_box'], -0.03)
		# 		elif data['player_num'] == 2 and not await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['p2_bar_box'], PongConsumer.groups_info[self.my_group]['lower_plane_normal'], PongConsumer.groups_info[self.my_group]['lower_plane_constant']):
		# 			PongConsumer.groups_info[self.my_group]['p2_bar_position'][1] -= 0.03
		# 			await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group]['p2_bar_box'], -0.03)


