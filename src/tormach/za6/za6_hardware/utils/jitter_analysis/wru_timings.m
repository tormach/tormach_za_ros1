## EtherCAT outgoing packet -> incoming -> next outgoing packet timing
##
## Sample includes measurements from the whole cycle;
##
## however, write & cycle exec times are calculated from previous
## sample cycle start time
##
## For a sample, HAL data is sampled in middle of update
## - "Current" ECAT outgoing is really last update
## - Current ECAT incoming is this update

function wru_timings (samples, period = 1/1000)
  ## "Current update" means HAL update in which HAL sampler was run;
  ## sampler was run in the middle of the update, **before** counter
  ## is incremented
  ##
  ## Cycle we want is from one ECAT outgoing packet to next, ending at
  ## the current update
  ##
  ## Current update and ECAT packets will have same counter value

  ## Samples with values relevant to prev/cur/next HAL update
  s_prev = samples(1:end-2);
  s_cur = samples(2:end-1);
  s_next = samples(3:end);

  ## HAL start timestamps
  hal_start_ts = [samples.h_timestamp];
  hal_start_ts_prev = hal_start_ts(1:end-2);
  hal_start_ts_cur = hal_start_ts(2:end-1);
  hal_start_ts_next = hal_start_ts(3:end);

  ## Sample index vector (current)
  sample = [s_cur.sample];

  ## HAL end timestamps:  start_ts + exec_time, but sampled start_ts leads
  hal_end_ts_prev = hal_start_ts_prev + [s_cur.cycle_exec_time] / 1000000000;
  hal_end_ts_cur = hal_start_ts_cur + [s_next.cycle_exec_time] / 1000000000;

  ## These are what we're actually plotting, in order

  ## Outgoing ECAT packet timestamp
  ecat_xmit_ts = [s_cur.m_timestamp];
  ## lcec.0.write end timestamp:  prev update end
  lcec_write_end_ts = hal_end_ts_prev;

  ## lcec.0.read start timestamp:  cur update start
  lcec_read_start_ts = hal_start_ts_cur;
  ## Incoming ECAT packet timestamp
  ecat_recv_ts = [s_cur.s_timestamp];
  ## lcec.0.read end timestamp:  cur update start + read exec
  lcec_read_end_ts = hal_start_ts_cur + [s_cur.read_exec_time] / 1000000000;

  ## lcec.0.write next start timestamp:  cur update end less next write exec time
  lcec_write_start_next_ts = hal_end_ts_cur - [s_next.write_exec_time] / 1000000000;
  ## Outgoing ECAT next packet timestamp
  ecat_xmit_next_ts = [s_next.m_timestamp];

  ## Delta pos cmd & fb
  delta_cmd = diff([s_cur.m_pos_cmd]);
  delta_fb = diff([s_cur.s_pos_fb]);
  ## Following error, HAL & drive
  ferror_hal = [s_cur.m_pos_cmd] ...
               - [s_next.s_pos_fb];
  ferror_drive = [s_next.s_ferror];
  ## Delta pos & ferror, scaled so positive values fit in left Y axis
  pos_scaled = period / max(delta_cmd);
  delta_cmd_scaled = delta_cmd * pos_scaled;
  delta_fb_scaled = delta_fb * pos_scaled;
  ferror_hal_scaled = ferror_hal * pos_scaled;
  ferror_drive_scaled = ferror_drive * pos_scaled;

  ## Plots
  gcf;
  clf;
  ## h = figure;
  hold on;
  ylabel("Time since last outgoing ECAT datagram, s");
  xlabel("Sample #");

  # - lcec.0.write executing (start to ECAT pkt transmit)
  area(sample, ecat_xmit_next_ts-ecat_xmit_ts,
       ## "displayname", "lcec.0.write executing",
       "facecolor", "y", "edgecolor", "y", "basevalue", 0
      );
  # - controller updates executing (ROS controller + cmd/fb chains)
  area(sample, lcec_write_start_next_ts-ecat_xmit_ts,
       "displayname", "Controller update executing",
       "facecolor", "r", "edgecolor", "r", "basevalue", 0
      );
  # - lcec.0.read executing
  area(sample, lcec_read_end_ts-ecat_xmit_ts,
       "displayname", "lcec.0.read executing",
       "facecolor", "g", "edgecolor", "g", "basevalue", 0
      );
  # - between HAL updates
  area(sample, lcec_read_start_ts-ecat_xmit_ts,
       ## "displayname", "(between HAL updates)",
       "facecolor", "w", "edgecolor", "w", "basevalue", 0
      );
  # - lcec.0.write executing (ECAT pkt transmit to end)
  area(sample, lcec_write_end_ts-ecat_xmit_ts,
       "displayname", "lcec.0.write executing",
       "facecolor", "y", "edgecolor", "y", "basevalue", 0
      );

  ## - ECAT incoming packet
  plot(sample, ecat_recv_ts-ecat_xmit_ts, "r;ECAT pkt in;");
  ## - ECAT next outgoing packet
  plot(sample, ecat_xmit_next_ts-ecat_xmit_ts, "--r;ECAT pkt out;");

  ## - Delta cmd & fb
  plot(sample(2:end), delta_cmd_scaled, "--b;delta cmd;");
  plot(sample(2:end), delta_fb_scaled, "b;delta fb;");
  ## - Ferror, HAL & drive
  plot(sample, ferror_hal_scaled, "k;ferror HAL;");
  plot(sample, ferror_drive_scaled, "--k;ferror drive;");


  hold off;
end
