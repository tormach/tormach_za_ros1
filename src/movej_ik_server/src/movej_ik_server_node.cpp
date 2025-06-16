#include "movej_ik_server/movej_ik_server.h"

int main(int argc, char** argv)
{
  ros::init(argc, argv, "movej_ik_server");
  ros::AsyncSpinner spinner(1);
  spinner.start();

  MoveJIKServer tl;
  ros::Rate rate(10);  // 10 Hz rate

  bool opw_params_set = false;
  while (ros::ok())
  {
    rate.sleep();

    if (!opw_params_set)
    {
      double a1_val;
      ros::param::get("~opw_params/a1", a1_val);
      if (a1_val > 0.01)
      {
        tl.ik_solver->update_opw_params();
        opw_params_set = true;
      }
    }
  }

  ros::shutdown();

  return 0;
}
