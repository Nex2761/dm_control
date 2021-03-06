# Copyright 2018 The dm_control Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

"""Tests for mjcf observables."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Internal dependencies.

from absl.testing import absltest
from dm_control import mjcf
from dm_control.composer.observation.observable import mjcf as mjcf_observable
import numpy as np

_MJCF = """
<mujoco>
  <worldbody>
    <light pos="0 0 1"/>
    <body name="body" pos="0 0 0">
      <joint name="my_hinge" type="hinge" pos="-.1 -.2 -.3" axis="1 -1 0"/>
      <geom name="my_box" type="box" size=".1 .2 .3" rgba="0 0 1 1"/>
      <geom name="small_sphere" type="sphere" size=".12" pos=".1 .2 .3"/>
    </body>
    <camera name="world" mode="targetbody" target="body" pos="1 1 1" />
  </worldbody>
</mujoco>
"""


class ObservableTest(absltest.TestCase):

  def testMJCFFeature(self):
    mjcf_root = mjcf.from_xml_string(_MJCF)
    physics = mjcf.Physics.from_mjcf_model(mjcf_root)

    my_hinge = mjcf_root.find('joint', 'my_hinge')
    hinge_observable = mjcf_observable.MJCFFeature(
        kind='qpos', mjcf_element=my_hinge)
    hinge_observation = hinge_observable.observation_callable(physics)()
    np.testing.assert_array_equal(
        hinge_observation, physics.named.data.qpos[my_hinge.full_identifier])

    small_sphere = mjcf_root.find('geom', 'small_sphere')
    box_observable = mjcf_observable.MJCFFeature(
        kind='xpos', mjcf_element=small_sphere, update_interval=5)
    box_observation = box_observable.observation_callable(physics)()
    self.assertEqual(box_observable.update_interval, 5)
    np.testing.assert_array_equal(
        box_observation, physics.named.data.geom_xpos[
            small_sphere.full_identifier])

    my_box = mjcf_root.find('geom', 'my_box')
    list_observable = mjcf_observable.MJCFFeature(
        kind='xpos', mjcf_element=[my_box, small_sphere])
    list_observation = (
        list_observable.observation_callable(physics)())
    np.testing.assert_array_equal(
        list_observation,
        physics.named.data.geom_xpos[[my_box.full_identifier,
                                      small_sphere.full_identifier]])

    with self.assertRaisesRegexp(ValueError, 'expected an `mjcf.Element`'):
      mjcf_observable.MJCFFeature('qpos', 'my_hinge')
    with self.assertRaisesRegexp(ValueError, 'expected an `mjcf.Element`'):
      mjcf_observable.MJCFFeature('geom_xpos', [my_box, 'small_sphere'])

  def testMJCFCamera(self):
    mjcf_root = mjcf.from_xml_string(_MJCF)
    physics = mjcf.Physics.from_mjcf_model(mjcf_root)

    camera = mjcf_root.find('camera', 'world')
    camera_observable = mjcf_observable.MJCFCamera(
        mjcf_element=camera, height=480, width=640, update_interval=7)
    self.assertEqual(camera_observable.update_interval, 7)
    camera_observation = camera_observable.observation_callable(physics)()
    np.testing.assert_array_equal(
        camera_observation, physics.render(480, 640, 'world'))
    self.assertEqual(camera_observation.shape,
                     camera_observable.array_spec.shape)
    self.assertEqual(camera_observation.dtype,
                     camera_observable.array_spec.dtype)

    camera_observable.height = 300
    camera_observable.width = 400
    camera_observation = camera_observable.observation_callable(physics)()
    self.assertEqual(camera_observable.height, 300)
    self.assertEqual(camera_observable.width, 400)
    np.testing.assert_array_equal(
        camera_observation, physics.render(300, 400, 'world'))
    self.assertEqual(camera_observation.shape,
                     camera_observable.array_spec.shape)
    self.assertEqual(camera_observation.dtype,
                     camera_observable.array_spec.dtype)

    with self.assertRaisesRegexp(ValueError, 'expected an `mjcf.Element`'):
      mjcf_observable.MJCFCamera('world')
    with self.assertRaisesRegexp(ValueError, 'expected an `mjcf.Element`'):
      mjcf_observable.MJCFCamera([camera])
    with self.assertRaisesRegexp(ValueError, 'expected a <camera>'):
      mjcf_observable.MJCFCamera(mjcf_root.find('body', 'body'))

if __name__ == '__main__':
  absltest.main()
