from setuptools import setup, find_packages
from glob import glob
import os

package_name = 'warehouse_bot'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'maps'), glob('maps/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rahul',
    maintainer_email='rahul@example.com',
    description='Warehouse robot navigation using pure Nav2 (ROS 2 Jazzy, Gazebo Harmonic)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'lot_navigator = warehouse_bot.lot_navigator_node:main',
            'lot_input = warehouse_bot.lot_input:main',
            'lot_input_bot1 = warehouse_bot.lot_input_bot1:main',
            'lot_input_bot2 = warehouse_bot.lot_input_bot2:main',
            'lot_input_bot3 = warehouse_bot.lot_input_bot3:main',
            'generate_map = warehouse_bot.generate_map:main',
            'dynamic_obstacles_mover = warehouse_bot.dynamic_obstacles_mover:main',
            'metrics_logger = metrics_logger:main',
        ],
    },
)
