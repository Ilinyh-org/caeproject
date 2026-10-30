
import pytest
from pathlib import Path
from caecase import CAECase
import json
import asyncio
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
# #     cm._save_delay = 0.1  # Speed up the test
# #
# #     # Change parameters (should trigger the delayed save)
# #     cm.parameters.test1 = 1
# #     cm.parameters.test2 = 2
# #
# #     # Wait longer than the delay
# #     await asyncio.sleep(0.2)
# #
# #     # Check that the file was created and contains data
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
# #     # Change again immediately — the previous task should be cancelled
# #     cm.parameters.temp = 200
# #
# #     await asyncio.sleep(1.2)  # Wait for the last task to finish
# #
# #     with caecase_obj_path.open("r", encoding="utf-8") as f:
# #         data = json.load(f)
# #
# #     assert data["parameters"]["temp"]["value"] == 200  # The last value was saved
#
# from time import sleep
# # @pytest.mark.asyncio
# def test_caecase_force_save(caecase_obj_path):
#     caecase = CAECase(caecase_obj_path)
#     caecase._save_delay = 5.0  # Large delay
#
#     caecase.parameters.urgent = 999
#     caecase.save()  # Forced save
#     sleep(4)
#     assert caecase_obj_path.exists()
#     with caecase_obj_path.open("r", encoding="utf-8") as f:
#         data = json.load(f)
#
#     assert data["parameters"]["urgent"]["value"] == 999