
"""Tests for CAECase delayed (asynchronous) saving."""
import asyncio
import json
from pathlib import Path

import pytest

from caecase import CAECase
#
# @pytest.fixture
# def temp_caecase_obj_path():
#     path = Path("test_caecase_obj.json")
#     yield path
#     if path.exists():
#         path.unlink()
#
#
# @pytest.fixture
# def caecase_obj():
#     return CAECase()
#
#
# @pytest.fixture
# def caecase_obj_path(tmp_path):
#     return tmp_path / "caecase_obj.json"
#
# #
# # @pytest.mark.asyncio
# # async def test_caecase_delayed_save(caecase_obj_path):
# #     cm = CAECase(caecase_obj_path)
# #     cm._save_delay = 0.1  # Ускоряем тест
# #
# #     # Меняем параметры (должно запустить отложенное сохранение)
# #     cm.parameters.test1 = 1
# #     cm.parameters.test2 = 2
# #
# #     # Ждём больше, чем задержка
# #     await asyncio.sleep(0.2)
# #
# #     # Проверяем, что файл создан и содержит данные
# #     assert caecase_obj_path.exists()
# #     with caecase_obj_path.open("r", encoding="utf-8") as f:
# #         data = json.load(f)
# #
# #     assert data["parameters"]["test1"]["value"] == 1
# #     assert data["parameters"]["test2"]["value"] == 2
# #
# #
# # @pytest.mark.asyncio
# # async def test_caecase_save_cancellation(caecase_obj_path):
# #     cm = CAECase(caecase_obj_path)
# #     cm._save_delay = 1.0
# #
# #     cm.parameters.temp = 100
# #     # Сразу меняем ещё раз — предыдущая задача должна отмениться
# #     cm.parameters.temp = 200
# #
# #     await asyncio.sleep(1.2)  # Ждём завершения последней задачи
# #
# #     with caecase_obj_path.open("r", encoding="utf-8") as f:
# #         data = json.load(f)
# #
# #     assert data["parameters"]["temp"]["value"] == 200  # Сохранилось последнее значение
#
# from time import sleep
# # @pytest.mark.asyncio
# def test_caecase_force_save(caecase_obj_path):
#     caecase = CAECase(caecase_obj_path)
#     caecase._save_delay = 5.0  # Большая задержка
#
#     caecase.parameters.urgent = 999
#     caecase.save()  # Принудительное сохранение
#     sleep(4)
#     assert caecase_obj_path.exists()
#     with caecase_obj_path.open("r", encoding="utf-8") as f:
#         data = json.load(f)
#
#     assert data["parameters"]["urgent"]["value"] == 999
