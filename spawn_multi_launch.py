#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

# name -> spawn (x, y)
ROBOTS = {
    "bot1": (-7.0, 0.0),
    "bot3": (-7.0, 2.0),
}


def _urdf_for(ns, raw_urdf):
    # Prefix the gz-plugin frame names so each robot gets its own TF tree
    # (robot_state_publisher's frame_prefix handles base_link/lidar_link/etc,
    # these three plugin tags are the ones NOT covered by frame_prefix).
    txt = raw_urdf
    txt = txt.replace("<odom_frame>odom</odom_frame>",
                       f"<odom_frame>{ns}/odom</odom_frame>")
    txt = txt.replace("<robot_base_frame>base_link</robot_base_frame>",
                       f"<robot_base_frame>{ns}/base_link</robot_base_frame>")
    txt = txt.replace("<gz_frame_id>lidar_link</gz_frame_id>",
                       f"<gz_frame_id>{ns}/lidar_link</gz_frame_id>")
    # Pin these to explicit absolute gz topics so there's no dependence on
    # how Gazebo happens to auto-scope a relative plugin/sensor topic.
    txt = txt.replace("<topic>cmd_vel</topic>", f"<topic>/{ns}/cmd_vel</topic>")
    txt = txt.replace("<odom_topic>odom</odom_topic>", f"<odom_topic>/{ns}/odom</odom_topic>")
    txt = txt.replace("<topic>scan</topic>", f"<topic>/{ns}/scan</topic>")
    txt = txt.replace("<topic>joint_states</topic>", f"<topic>/{ns}/joint_states</topic>")
    return txt


def generate_launch_description():
    pkg_share = get_package_share_directory("warehouse_bot")
    world_file = os.path.join(pkg_share, "worlds", "warehouse.sdf")
    urdf_file = os.path.join(pkg_share, "urdf", "my_robot.urdf")

    with open(urdf_file, "r") as f:
        raw_urdf = f.read()

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": f"-r {world_file}"}.items(),
    )

    nodes = [gazebo]
    bridge_args = [
        "/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V",
        "/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock",
        "/model/dynamic_obstacle_1/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
        "/model/dynamic_obstacle_2/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
        "/model/dynamic_obstacle_3/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
    ]
    bridge_remaps = [
        ("/model/dynamic_obstacle_1/cmd_vel", "/dynamic_obstacle_1/cmd_vel"),
        ("/model/dynamic_obstacle_2/cmd_vel", "/dynamic_obstacle_2/cmd_vel"),
        ("/model/dynamic_obstacle_3/cmd_vel", "/dynamic_obstacle_3/cmd_vel"),
    ]

    for ns, (x, y) in ROBOTS.items():
        robot_description = _urdf_for(ns, raw_urdf)

        nodes.append(Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            namespace=ns,
            output="screen",
            parameters=[{
                "robot_description": robot_description,
                "use_sim_time": True,
                "frame_prefix": f"{ns}/",
            }],
        ))

        nodes.append(Node(
            package="ros_gz_sim",
            executable="create",
            name="spawn_" + ns,
            namespace=ns,
            output="screen",
            arguments=["-name", ns, "-topic", "robot_description",
                       "-x", str(x), "-y", str(y), "-z", "0.15"],
        ))

        # these topics are absolute in the per-robot URDF now, so gz topic
        # name == ros topic name, no remap needed
        bridge_args += [
            f"/{ns}/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            f"/{ns}/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry",
            f"/{ns}/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan",
            f"/{ns}/joint_states@sensor_msgs/msg/JointState@gz.msgs.Model",
        ]

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="parameter_bridge",
        output="screen",
        arguments=bridge_args,
        remappings=bridge_remaps,
    )
    nodes.append(bridge)

    nodes.append(Node(
        package="warehouse_bot",
        executable="dynamic_obstacles_mover",
        output="screen",
    ))

    return LaunchDescription(nodes)
