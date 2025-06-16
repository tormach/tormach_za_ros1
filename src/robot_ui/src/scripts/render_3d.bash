#!/usr/bin/env bash
if [ ! "$BASH_VERSION" ]; then
    echo "Warning: this script should be executed with bash"
    exec /bin/bash "$0"
fi
cd "$(dirname "${BASH_SOURCE[0]}")" || exit

cd ../robot_ui/res/3d || exit
openscad -o x_plus.stl x_plus.scad
openscad -o x_minus.stl x_minus.scad
openscad -o y_plus.stl y_plus.scad
openscad -o y_minus.stl y_minus.scad
openscad -o z_plus.stl z_plus.scad
openscad -o z_minus.stl z_minus.scad
openscad -o a_plus.stl a_plus.scad
openscad -o a_minus.stl a_minus.scad
openscad -o b_plus.stl b_plus.scad
openscad -o b_minus.stl b_minus.scad
openscad -o c_plus.stl c_plus.scad
openscad -o c_minus.stl c_minus.scad
openscad -o joint_x_plus.stl joint_x_plus.scad
openscad -o joint_x_minus.stl joint_x_minus.scad
openscad -o joint_y_plus.stl joint_y_plus.scad
openscad -o joint_y_minus.stl joint_y_minus.scad
openscad -o joint_z_plus.stl joint_z_plus.scad
openscad -o joint_z_minus.stl joint_z_minus.scad
