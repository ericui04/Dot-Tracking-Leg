from reacher import forward_kinematics
from reacher import inverse_kinematics
from reacher import reacher_robot_utils
from reacher import reacher_sim_utils
import pybullet as p
import time
import contextlib
import numpy as np
import cv2
from absl import app
from absl import flags
from pupper_hardware_interface import interface
from sys import platform

flags.DEFINE_bool("run_on_robot", False, "Whether to run on robot or in simulation.")
flags.DEFINE_bool("ik"          , False, "Whether to control arms through cartesian coordinates(IK) or joint angles")
flags.DEFINE_list("set_joint_angles", [], "List of joint angles to set at initialization.")
FLAGS = flags.FLAGS

KP = 5.0  # Amps/rad
KD = 2.0  # Amps/(rad/s)
MAX_CURRENT = 3  # Amps

UPDATE_DT = 0.01  # seconds

HIP_OFFSET = 0.0335  # meters
L1 = 0.08  # meters
L2 = 0.11  # meters

# CAMERA INTRINSIC MATRIX

# video resolution width
resolution_width = 1920  
# video resolution height
resolution_height = 1080
# frame rate
fps = 30
# assume fov 60 since it is common for smartphone cameras
horizontal_fov_degrees = 60

# calculate focal length
focal_length_w = resolution_width / (2 * np.tan(np.deg2rad(horizontal_fov_degrees / 2)))

focal_length_h = resolution_height / (2 * np.tan(np.deg2rad(horizontal_fov_degrees / 2)))

# assume principal point is at the center of the image
principal_point = (resolution_width / 2, resolution_height / 2)

# create matrix
intrinsic_matrix = np.array([[focal_length_w, 0, principal_point[0]],
                             [0, focal_length_h, principal_point[1]],
                             [0, 0, 1]])

# height of robot base of robot off of ground
robot_base_height = -0.07

# depth: height of camera above ground
depth = 0.67

# transform point into robot frame, since we aligned the orientation of the camera to the robot frame, only z-axis is different from world frame
def transform_to_robot_frame(point_2d):
  # apply camera intrinsic matrix to get coordinate in global frame
  red_dot_global = np.linalg.inv(intrinsic_matrix) @ np.array([point_2d[0][0], point_2d[0][1], 1])
  # account for rotation and height of camera
  red_dot_global = red_dot_global * depth
  red_dot_global[1] = red_dot_global[1] * -1
  # account for base of robot being above ground
  red_dot_global[2] = robot_base_height
  return red_dot_global

# detect circles and return the coordinate in the robot frame
def detect_and_transform_circles(frame):
  # reduce noise from frame
  blurred_frame = cv2.medianBlur(frame, 3)
  # separate into channels so can extract red
  channeled_frame = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2Lab)
  # threshold to get red pixels
  frame_red = cv2.inRange(channeled_frame, np.array([20, 150, 150]), np.array([190, 255, 255]))
  # blur again to reduce noise and account for other red detections
  frame_red = cv2.GaussianBlur(frame_red, (5, 5), 2, 2)
  # hough transform to detect circles, min and max radius set to prevent it from picking up on our leg as a circle
  circles = cv2.HoughCircles(frame_red, cv2.HOUGH_GRADIENT, 1, frame_red.shape[0] / 8, param1=100, param2=18, minRadius=50, maxRadius=100)

  if circles is not None:
    circles = np.round(circles[0, :]).astype("int")
    # get pixel coordinates of circles
    center_x, center_y = circles[0, 0], circles[0, 1]
    print("pixel coordinates:", center_x, center_y)

    # transform pixel coordinate to robot frame
    center_point_camera_frame = np.array([[center_x, center_y]], dtype=np.float32)
    center_point_robot_frame = transform_to_robot_frame(center_point_camera_frame)
    # get x, y, z coordinates in robot frame
    x = center_point_robot_frame[0]
    print(x)
    y = center_point_robot_frame[1]
    print(y)
    z = center_point_robot_frame[2]
    print(z)

    print("robot frame coordinates:", center_point_robot_frame)
    # draw black circle for visual testing that the circle has been detected
    cv2.circle(frame, center=(center_x, center_y), radius=circles[0, 2], color=(0, 0, 0), thickness=2)

    return np.array([x, y, z])

  # no circles, returns 0
  return np.zeros(3)

# start video
cap = cv2.VideoCapture(0)

# set resolution/frame rate of video capture
cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_height)
cap.set(cv2.CAP_PROP_FPS, fps)

def main(argv):
  run_on_robot = FLAGS.run_on_robot
  reacher = reacher_sim_utils.load_reacher()

  # Sphere markers for the students' FK solutions
  shoulder_sphere_id = reacher_sim_utils.create_debug_sphere([1, 0, 0, 1])
  elbow_sphere_id    = reacher_sim_utils.create_debug_sphere([0, 1, 0, 1])
  foot_sphere_id     = reacher_sim_utils.create_debug_sphere([0, 0, 1, 1])
  target_sphere_id   = reacher_sim_utils.create_debug_sphere([1, 1, 1, 1], radius=0.01)

  joint_ids = reacher_sim_utils.get_joint_ids(reacher)
  param_ids = reacher_sim_utils.get_param_ids(reacher, FLAGS.ik)
  reacher_sim_utils.zero_damping(reacher)

  p.setPhysicsEngineParameter(numSolverIterations=10)

  # Set up physical robot if we're using it, starting with motors disabled
  if run_on_robot:
    serial_port = reacher_robot_utils.get_serial_port()
    hardware_interface = interface.Interface(serial_port)
    time.sleep(0.25)
    hardware_interface.set_joint_space_parameters(kp=KP, kd=KD, max_current=MAX_CURRENT)
    hardware_interface.deactivate()

  # Whether or not the motors are enabled
  motor_enabled = False
  if run_on_robot:
    mode_text_id = p.addUserDebugText(f"Motor Enabled: {motor_enabled}", [0, 0, 0.2])
  def checkEnableMotors():
    nonlocal motor_enabled, mode_text_id

    # If spacebar (key 32) is pressed and released (0b100 mask), then toggle motors on or off
    if p.getKeyboardEvents().get(32, 0) & 0b100:
      motor_enabled = not motor_enabled
      if motor_enabled:
        hardware_interface.set_activations([0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0])
      else:
        hardware_interface.deactivate()
      p.removeUserDebugItem(mode_text_id)
      mode_text_id = p.addUserDebugText(f"Motor Enabled: {motor_enabled}", [0, 0, 0.2])

  # Control Loop Variables
  p.setRealTimeSimulation(1)
  counter = 0
  last_command = time.time()
  joint_angles = np.zeros(3)
  if flags.FLAGS.set_joint_angles:
    # first the joint angles to 0,0,0
    for idx, joint_id in enumerate(joint_ids):
      p.setJointMotorControl2(
        reacher,
        joint_id,
        p.POSITION_CONTROL,
        joint_angles[idx],
        force=2.
      )
    joint_angles = np.array(flags.FLAGS.set_joint_angles, dtype=np.float32)
    # Set the simulated robot to match the joint angles
    for idx, joint_id in enumerate(joint_ids):
      p.setJointMotorControl2(
        reacher,
        joint_id,
        p.POSITION_CONTROL,
        joint_angles[idx],
        force=2.
      )

  print("\nRobot Status:\n")

  # Main loop
  while (True):

    # Whether or not to send commands to the real robot
    enable = False

    # If interfacing with the real robot, handle those communications now
    if run_on_robot:
      hardware_interface.read_incoming_data()
      checkEnableMotors()

    # Determine the direction of data transfer
    real_to_sim = not motor_enabled and run_on_robot

    # Control loop
    if time.time() - last_command > UPDATE_DT:
      last_command = time.time()
      counter += 1

      # Read the slider values
      try:
        slider_values = np.array([p.readUserDebugParameter(id) for id in param_ids])
      except:
        pass
      if FLAGS.ik:
        # xyz = slider_values (original code)
        ret, captured_frame = cap.read()
        output_frame = captured_frame.copy()

        # detect circles and transform to robot frame to be used as x, y, z target end-effector position
        xyz = detect_and_transform_circles(output_frame)

        # display what camera is recording for visual testing
        cv2.imshow('frame', output_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
          break
        p.resetBasePositionAndOrientation(target_sphere_id, posObj=xyz, ornObj=[0, 0, 0, 1])
      else:
        joint_angles = slider_values
        enable = True

      # If IK is enabled, update joint angles based off of goal XYZ position
      if FLAGS.ik:
          ret = inverse_kinematics.calculate_inverse_kinematics(xyz, joint_angles[:3])
          if ret is not None:
            enable = True
            # Wraps angles between -pi, pi
            joint_angles = np.arctan2(np.sin(ret), np.cos(ret))

            # Double check that the angles are a correct solution before sending anything to the real robot
            pos = forward_kinematics.fk_foot(joint_angles[:3])[:3,3]
            if np.linalg.norm(np.asarray(pos) - xyz) > 0.05:
              joint_angles = np.zeros_like(joint_angles)
              if flags.FLAGS.set_joint_angles:
                joint_angles = np.array(flags.FLAGS.set_joint_angles, dtype=np.float32)
              print("Prevented operation on real robot as inverse kinematics solution was not correct")

      # If real-to-sim, update the joint angles based on the actual robot joint angles
      if real_to_sim:
        joint_angles = hardware_interface.robot_state.position[6:9]
        joint_angles[0] *= -1

      # Set the simulated robot to match the joint angles
      for idx, joint_id in enumerate(joint_ids):
        p.setJointMotorControl2(
          reacher,
          joint_id,
          p.POSITION_CONTROL,
          joint_angles[idx],
          force=2.
        )

      # Set the robot angles to match the joint angles
      if run_on_robot and enable:
        full_actions = np.zeros([3, 4])
        full_actions[:, 2] = joint_angles
        full_actions[0, 2] *= -1

        # Prevent set_actuator_positions from printing to the console
        with contextlib.redirect_stdout(None):
          hardware_interface.set_actuator_postions(full_actions)

      # Get the calculated positions of each joint and the end effector
      shoulder_pos = forward_kinematics.fk_shoulder(joint_angles[:3])[:3,3]
      elbow_pos    = forward_kinematics.fk_elbow(joint_angles[:3])[:3,3]
      foot_pos     = forward_kinematics.fk_foot(joint_angles[:3])[:3,3]

      # Show the bebug spheres for FK
      p.resetBasePositionAndOrientation(shoulder_sphere_id, posObj=shoulder_pos, ornObj=[0, 0, 0, 1])
      p.resetBasePositionAndOrientation(elbow_sphere_id   , posObj=elbow_pos   , ornObj=[0, 0, 0, 1])
      p.resetBasePositionAndOrientation(foot_sphere_id    , posObj=foot_pos    , ornObj=[0, 0, 0, 1])

      # Show the result in the terminal
      if counter % 20 == 0:
        print(f"\rJoint angles: [{', '.join(f'{q: .3f}' for q in joint_angles[:3])}] | Position: ({', '.join(f'{p: .3f}' for p in foot_pos)})", end='')

app.run(main)
