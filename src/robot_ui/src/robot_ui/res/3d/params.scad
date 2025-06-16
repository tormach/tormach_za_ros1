th = 2;
scale_factor = 10 / 1000;
joint_scale_factor = 25 / 1000;

module arrow() {
    translate([0,-9,-(th/2)])
    linear_extrude(height=th) {
        import(file = "arrow_east.dxf", center=true, dpi = 96);
    }
}

module wheel() {
    translate([-9,-9,-(th/2)])
    linear_extrude(height=th) {
        import(file = "sync.dxf", center=true, dpi = 96);
    }
}
