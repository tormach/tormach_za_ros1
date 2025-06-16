include <params.scad>;

rotate([90, 0, 180])
    scale([joint_scale_factor, joint_scale_factor, scale_factor])
        wheel();
