import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction, GroupAction
from launch_ros.actions import Node, PushRosNamespace

ROBOTS = ["bot1", "bot3"]


def generate_launch_description():
    pkg_share = get_package_share_directory('warehouse_bot')
    map_yaml = os.path.join(pkg_share, 'maps', 'warehouse_map.yaml')

    groups = []
    for ns in ROBOTS:
        params_file = os.path.join(pkg_share, 'config', f'nav2_params_{ns}.yaml')

        map_server = Node(
            package='nav2_map_server', executable='map_server', name='map_server',
            output='screen', parameters=[params_file, {'yaml_filename': map_yaml}])

        amcl = Node(
            package='nav2_amcl', executable='amcl', name='amcl',
            output='screen', parameters=[params_file])

        controller_server = Node(
            package='nav2_controller', executable='controller_server', name='controller_server',
            output='screen', parameters=[params_file])

        planner_server = Node(
            package='nav2_planner', executable='planner_server', name='planner_server',
            output='screen', parameters=[params_file])

        behavior_server = Node(
            package='nav2_behaviors', executable='behavior_server', name='behavior_server',
            output='screen', parameters=[params_file])

        bt_navigator = Node(
            package='nav2_bt_navigator', executable='bt_navigator', name='bt_navigator',
            output='screen', parameters=[params_file])

        lifecycle_manager_localization = Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='lifecycle_manager_localization', output='screen', parameters=[params_file])

        lifecycle_manager_navigation = Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='lifecycle_manager_navigation', output='screen', parameters=[params_file])

        delayed_lifecycle = TimerAction(
            period=6.0,
            actions=[lifecycle_manager_localization, lifecycle_manager_navigation]
        )

        groups.append(GroupAction([
            PushRosNamespace(ns),
            map_server, amcl, controller_server, planner_server,
            behavior_server, bt_navigator, delayed_lifecycle,
        ]))

    return LaunchDescription(groups)
