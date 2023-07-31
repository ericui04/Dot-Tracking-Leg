import math
import numpy as np
import copy

HIP_OFFSET = 0.0335
L1 = 0.08 # length of link 1
L2 = 0.11 # length of link 2
TOLERANCE = 0.01 # tolerance for inverse kinematics
PERTURBATION = 0.0001 # perturbation for finite difference method

def rotation_matrix(axis, angle):
  """
  Create a 3x3 rotation matrix which rotates about a specific axis

  Args:
    axis:  String. One of either "x", "y" or "z". Represents the axis of rotation
    angle: Number. The amount to rotate about the axis in radians

  Returns:
    3x3 rotation matrix as a numpy array
  """

  # Convert the axis to lowercase to allow uppercase inputs as well
  axis = axis.lower()

  if axis == "x":
    rot_mat = np.array([[]])
  elif axis == "y":
    rot_mat = np.array([[]])
  elif axis == "z":
    rot_mat = np.array([[]])
  else:
    raise ValueError(f"Incorrect axis \"{axis}\" provided, cannot calculate rotation matrix")

  return rot_mat

def homogenous_transformation_matrix(axis, angle, v_A):
  """
  Create a 4x4 transformation matrix which transforms from frame A to frame B

  Args:
    axis:  String. One of either "x", "y" or "z". Represents the axis of rotation
    angle: Number. The amount to rotate about the axis in radians
    v_A:   Vector. The vector translation from A to B defined in frame A

  Returns:
    4x4 transformation matrix as a numpy array
  """

  T = np.eye(4)
  return T

def fk_hip(joint_angles):
  """
  Use forward kinematics equations to calculate the xyz coordinates of the hip
  frame given the joint angles of the robot

  Args:
    joint_angles: numpy array of 3 elements stored in the order [hip_angle, shoulder_angle, 
                  elbow_angle]. Angles are in radians
  Returns:
    4x4 matrix representing the pose of the hip frame in the base frame
  """

  shoulder_joint_xyz = np.array([0.15, 0.0, -0.1])  # remove this line when you write your solution
  return shoulder_joint_xyz

def fk_shoulder(joint_angles):
  """
  Use forward kinematics equations to calculate the xyz coordinates of the shoulder
  joint given the joint angles of the robot

  Args:
    joint_angles: numpy array of 3 elements stored in the order [hip_angle, shoulder_angle, 
                  elbow_angle]. Angles are in radians
  Returns:
    4x4 matrix representing the pose of the shoulder frame in the base frame
  """

  shoulder_joint_xyz = np.array([0.15, 0.0, -0.1])  # remove this line when you write your solution
  return shoulder_joint_xyz

def fk_elbow(joint_angles):
  """
  Use forward kinematics equations to calculate the xyz coordinates of the elbow
  joint given the joint angles of the robot

  Args:
    joint_angles: numpy array of 3 elements stored in the order [hip_angle, shoulder_angle, 
                  elbow_angle]. Angles are in radians
  Returns:
    4x4 matrix representing the pose of the elbow frame in the base frame
  """

  elbow_joint_xyz = np.array([0.15, 0.1, -0.1]) # remove this line when you write your solution
  return elbow_joint_xyz

def fk_foot(joint_angles):
  """
  Use forward kinematics equations to calculate the xyz coordinates of the foot given 
  the joint angles of the robot

  Args:
    joint_angles: numpy array of 3 elements stored in the order [hip_angle, shoulder_angle, 
                  elbow_angle]. Angles are in radians
  Returns:
    4x4 matrix representing the pose of the end effector frame in the base frame
  """

  foot_joint_xyz = np.array([0.15, 0.2, -0.1])  # remove this line when you write your solution
  return foot_joint_xyz
