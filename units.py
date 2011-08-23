#!/usr/bin/env python
#-*- coding:utf-8 -*-


BASE_TYPE_ID = 4
MINER_TYPE_ID = 5
TANK_TYPE_ID = 6

BASE_TYPE = 1111#GameObjectType(ID=BASE_TYPE_ID, name='base', vision_range=16, movable=False, can_build=True, when_attacked_get_minerals=True, can_store_minerals=True,
						 	#constructor=lambda player_ID: GameObject(type_ID=BASE_TYPE_ID, player_ID=player_ID))
MINER_TYPE = 1112#GameObjectType(ID=MINER_TYPE_ID, name='miner', vision_range=7, gather_size=1, cost_of_build=3,
						 	#constructor=lambda player_ID: GameObject(type_ID=MINER_TYPE_ID, player_ID=player_ID, minerals=0))
TANK_TYPE = 1113#GameObjectType(ID=BASE_TYPE_ID, name='tank', vision_range=7, attack_range=3, cost_of_build=10,
						 	#constructor=lambda player_ID: GameObject(type_ID=TANK_TYPE_ID, player_ID=player_ID))

GAME_OBJECT_TYPES_BY_ID = {
	TANK_TYPE_ID : TANK_TYPE,
	MINER_TYPE_ID : MINER_TYPE,
	BASE_TYPE_ID : BASE_TYPE,
}
