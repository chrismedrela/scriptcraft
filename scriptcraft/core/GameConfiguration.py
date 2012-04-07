#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

from scriptcraft.core import Language
from scriptcraft.core import UnitType
from scriptcraft.utils import *



class GameConfiguration(namedtuple("GameConfiguration",
    ('units_types_by_names',
     'main_base_type',
     'main_miner_type',
     'minerals_for_main_unit_at_start',
     'probability_of_mineral_deposit_growing',
     'languages_by_names')
    )):
    __slots__ = ()

    @ copy_if_an_instance_given
    def __new__(cls,
                units_types,
                main_base_type,
                main_miner_type,
                minerals_for_main_unit_at_start,
                probability_of_mineral_deposit_growing,
                languages):

        units_types_by_names = {}
        for unit_type in units_types:
            for name in unit_type.names:
                if name in units_types_by_names:
                    raise ValueError("Units types with the same names are not allowed.")
                units_types_by_names[name] = unit_type

        if main_base_type not in units_types or main_miner_type not in units_types:
            raise ValueError("main_base_type or main_miner_type not in units_types")

        languages_by_names = {}
        for language in languages:
            if language.name in languages_by_names:
                raise ValueError("Languages with the same names are not allowed")
            languages_by_names[language.name] = language

        arg = (units_types_by_names,
               main_base_type,
               main_miner_type,
               minerals_for_main_unit_at_start,
               probability_of_mineral_deposit_growing,
               languages_by_names)

        return cls.__bases__[0].__new__(cls,
                                        units_types_by_names,
                                        main_base_type,
                                        main_miner_type,
                                        minerals_for_main_unit_at_start,
                                        probability_of_mineral_deposit_growing,
                                        languages_by_names)

    def __deepcopy__(self, memo):
        c = GameConfiguration(self)
        return c


DEFAULT_GAME_CONFIGURATION = GameConfiguration(
    units_types=[UnitType.DEFAULT_BASE_TYPE,
                 UnitType.DEFAULT_MINER_TYPE,
                 UnitType.DEFAULT_TANK_TYPE],
    main_base_type=UnitType.DEFAULT_BASE_TYPE,
    main_miner_type=UnitType.DEFAULT_MINER_TYPE,
    minerals_for_main_unit_at_start=10,
    probability_of_mineral_deposit_growing=0.1,
    languages = [Language.DEFAULT_CPP_LANGUAGE,
                 Language.DEFAULT_PYTHON_LANGUAGE],
)
