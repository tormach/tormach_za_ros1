include <params.scad>;

rotate([0, 0, 0])
    scale([joint_scale_factor, joint_scale_factor, scale_factor])
        wheel();
