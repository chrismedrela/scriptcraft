#!/usr/bin/env python
#-*- coding:utf-8 -*-

class GameConfiguration(namedtuple("GameConfiguration"),
    ('units_types_by_names',
     'main_base_type',
     'main_miner_type',
     'minerals_for_main_unit_at_start',
     'probability_of_mineral_deposit_growing',
     'languages_by_names')
    ):
    __slots__ = ()

    def __new__(cls,
                units_types,
                main_base_type,
                main_miner_type,
                minerals_for_main_unit_at_start,
                probability_of_mineral_deposit_growing,
                languages_by_names):

        units_types_by_names = {}
        for unit in units_types:
            if len(unit.type.names) == 0:
                raise ValueError("Unit without name(s) is not allowed.")
            for name in unit.type.names:
                if name in units_types_by_names:
                    raise ValueError("Units types with the same names are not allowed.")
                units_types_by_names[name] = unit

        if main_base_type not in units_types:
            raise ValueError("Main_base_type not in units_types")
        if main_miner_type not in units_types:
            raise ValueError("Main_miner_type not in units_types")

        arg = (units_types_by_names,
               main_base_type,
               main_miner_type,
               minerals_for_main_unit_at_start,
               probability_of_mineral_deposit_growing,
               languages_by_names)

        return cls.__bases__[0].__new__(cls, type, arg)

