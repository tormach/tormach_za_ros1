## EtherCAT read -> update -> write timing
##
## HAL thread update execution-centric plot of read/update/write
## function execution, ECAT packets in/out, and start of next HAL
## update

function ruw_timings (samples, period = 1/1000, use_array_ix=true)
  ## Samples with values relevant to current sampler run
  s_cur = samples(1:end-1);
  ## Samples with values relevant to next sampler run
  s_next = samples(2:end);

  ## Sample index vector
  if (use_array_ix)
    sample = [1:length(s_cur)];
  else
    sample = [s_cur.sample];
  end
  ## HAL timestamp at beginning of thread update, right before read
  hal_start_ts = [s_cur.h_timestamp];
  ## HAL timestamp at end of thread update, right after write
  hal_end_ts = hal_start_ts + [s_next.cycle_exec_time] / 1000000000;
  ## lcec.0.read start+end timestamps
  ## - lcec.0.read called when counter=n
  lcec_read_start_ts = hal_start_ts;
  lcec_read_end_ts = hal_start_ts + [s_cur.read_exec_time] / 1000000000;
  ## lcec.0.write start+end timestamps
  ## - lcec.0.write called when counter=n+1
  lcec_write_start_ts = hal_end_ts - [s_next.write_exec_time] / 1000000000;
  lcec_write_end_ts = hal_end_ts;
  ## Incoming ECAT packet timestamp
  ecat_recv_ts = [s_cur.s_timestamp];
  ## ecat_recv_ts = [s_next.s_timestamp];  # WTF
  ## Outgoing ECAT packet timestamp
  ecat_xmit_ts = [s_next.m_timestamp];
  ## Next HAL start timestamp
  hal_next_start_ts = [s_next.h_timestamp];

  ## Delta pos cmd & fb
  delta_cmd = diff([samples.m_pos_cmd]);
  delta_fb = diff([samples.s_pos_fb]);
  ## Following error, HAL & drive
  ferror_hal = [s_cur.m_pos_cmd] - [s_next.s_pos_fb];
  ferror_drive = [s_cur.s_ferror];
  ## Delta pos & ferror, scaled so positive values fit in left Y axis
  pos_scaled = period / max(delta_cmd);
  delta_cmd_scaled = delta_cmd * pos_scaled;
  delta_fb_scaled = delta_fb * pos_scaled;
  ferror_hal_scaled = ferror_hal * pos_scaled;
  ferror_drive_scaled = ferror_drive * pos_scaled;

  ## Plots:  timings on left Y axis;  errors on right Y axis
  gcf;
  clf;
  ## h = figure;
  hold on;
  ylabel("time since HAL thread start, s");
  xlabel("sample #");

  ## - HAL update next start
  plot(sample, hal_next_start_ts - hal_start_ts, "g;HAL next cycle start;");
  ## - lcec.0.write executing (start to ECAT pkt transmit)
  area(sample, hal_end_ts - hal_start_ts,
       "displayname", "lcec.0.write executing",
       "facecolor", "y", "edgecolor", "y", "basevalue", 0
      );
  ## - ECAT packet out
  plot(sample, ecat_xmit_ts - hal_start_ts, "--r;ECAT pkt out;");
  ## - controller updates executing (ROS controller + cmd/fb chains)
  area(sample, lcec_write_start_ts - hal_start_ts,
       "displayname", "Controller update executing",
       "facecolor", "r", "edgecolor", "r", "basevalue", 0
      );
  ## - lcec.0.read executing
  area(sample, lcec_read_end_ts - hal_start_ts,
       "displayname", "lcec.0.read executing",
       "facecolor", "g", "edgecolor", "g", "basevalue", 0
      );
  ## - ECAT packet in
  plot(sample, ecat_recv_ts - hal_start_ts, "r;ECAT pkt in;");

  ## - Delta cmd & fb
  plot(sample, delta_cmd_scaled, "--b;delta cmd;");
  plot(sample, delta_fb_scaled, "b;delta fb;");
  ## - Ferror, HAL & drive
  plot(sample, ferror_hal_scaled, "k;ferror HAL;");
  plot(sample, ferror_drive_scaled, "--k;ferror drive;");

  hold off;
end
