##
## Plotting functions
##

global ns_to_s;
ns_to_s = 1e-9;

function plot_exec_times (samples)
    global ns_to_s;
    figure;
    hold on;
    plot([samples.sample], [samples.cycle_exec_time] * ns_to_s);
    ## plot([samples.sample], [samples.read_exec_time] * ns_to_s);
    ## plot([samples.sample], [samples.write_exec_time] * ns_to_s);
    hold off;
end

function plot_packet_jitter (samples)
  ## Measure jitter of outgoing & incoming packets
  ## - Assume nominal period is 1ms
  per = 0.001;                  # sec.
  ## - Set t0, timestamp of zeroth sample, to 1 period before first
  ##   sample's timestamp
  t0m = samples(1).m_timestamp - per;
  t0s = samples(1).s_timestamp - per;
  ## - Init plot
  figure;
  hold on;
  ## Jitter calculation:
  ## - If jitter were zero, time since zeroth timestamp would be
  ##   sample number * period
  ## - Jitter is calculated as the difference between the actual
  ##   time since zeroth timestamp and that ideal duration
  ideal_duration = [samples.sample] * 0.001;
  m_jitter = [samples.m_timestamp] - (t0m + ideal_duration);
  plot([samples.sample], m_jitter - min(m_jitter));
  s_jitter = [samples.s_timestamp] - (t0s + ideal_duration);
  plot([samples.sample], s_jitter - min(s_jitter));
  hold off;
end

function plot_position_cmd_fb (samples)
    figure;
    hold on;
    ## pos cmd
    plot([samples.sample], [samples.m_0_2_607A_00h_position_reference]);
    plot([samples.sample], [samples.joint3_drive_pos_cmd_s32]);
    ## pos fb
    plot([samples.sample], [samples.s_0_2_6064_00h_position_actual_value]);
    hold off;
end

function plot_ferror (samples)
  figure;
  hold on;
  xlabel("sample number");
  ylabel("reference units");
  ## Drive-reported following error
  plot([samples.sample],
       [samples.s_0_2_60F4_00h_following_error_actual_value],
       "k;s ferror;");
  ## HAL following error
  plot([samples.sample],
       [samples.joint3_drive_pos_cmd_s32]
       - [samples.joint3_drive_pos_fb_s32],
       "--k;h ferror;");
  ## ECAT following error
  plot([samples.sample],
       [samples.m_0_2_607A_00h_position_reference]
       - [samples.s_0_2_6064_00h_position_actual_value],
       "..k;m cmd - s fb;");
  ## ## Following error adjusted by 2x velocity reference
  ## plot([samples.sample],
  ##      [samples.m_0_2_607A_00h_position_reference]
  ##      - [samples.s_0_2_6064_00h_position_actual_value]
  ##      - [samples.m_0_2_60B1_00h_velocity_reference] * 0.002,
  ##      ";scaled cmd-fb hack;");
  ## Delta position command
  plot([samples(2:end).sample],
       [samples(2:end).m_0_2_607A_00h_position_reference]
       - [samples(1:end-1).m_0_2_607A_00h_position_reference],
       "b;delta cmd;");
  ## Delta position feedback
  plot([samples(2:end).sample],
       [samples(2:end).s_0_2_6064_00h_position_actual_value]
       - [samples(1:end-1).s_0_2_6064_00h_position_actual_value],
       "--b;delta fb;");
  hold off;
end

function h = plot_ferror_pos (samples)
  ## Fortunately the update exec times in ns are of a similar scale to
  ## raw reference counts, or this chart would be much harder to read.
  ## (I wasn't able to get multi-axis plots with multiple curves each to
  ## work at all.)
  h = figure;
  hold on;
  ylabel("reference units");
  xlabel("sample #");

  ## Update function times
  area([samples.sample], [samples.cycle_exec_time],
       "facecolor", "g",
       "edgecolor", "g",
       "basevalue", 0,
       "displayname", "cycle exec t");
  area([samples.sample], [samples.read_exec_time],
       "facecolor", "y", "facealpha", 0.25,
       "edgecolor", "w",
       "basevalue", 0,
       "displayname", "read exec t");
  area([samples.sample], [samples.write_exec_time],
       "facecolor", "g", "facealpha", 0.25,
       "edgecolor", "w",
       "basevalue", 0,
       "displayname", "write exec t");

  ## Drive-reported following error
  plot([samples.sample],
       [samples.s_0_2_60F4_00h_following_error_actual_value],
       "k;s ferror;");
  ## HAL following error is always the same as the next, ECAT following error
  ## ## HAL following error
  ## plot([samples.sample],
  ##      [samples.joint3_drive_pos_cmd_s32]
  ##      - [samples.joint3_drive_pos_fb_s32],
  ##      "--k;h ferror;");
  ## ECAT following error
  plot([samples.sample],
       [samples.m_0_2_607A_00h_position_reference]
       - [samples.s_0_2_6064_00h_position_actual_value],
       "-.k;m cmd - s fb;");
  ## Delta position command
  plot([samples(2:end).sample],
       diff([samples.m_0_2_607A_00h_position_reference]),
       "b;delta cmd;");
  ## Delta position feedback
  plot([samples(2:end).sample],
       diff([samples.s_0_2_6064_00h_position_actual_value]),
       "--b;delta fb;");

  zeros = ifelse(diff([samples.s_0_2_6064_00h_position_actual_value]), 0, 1);

  dpf = ([samples(2:end).s_0_2_6064_00h_position_actual_value]
         - [samples(1:end-1).s_0_2_6064_00h_position_actual_value]);

  delta_fb = diff([samples.s_0_2_6064_00h_position_actual_value]);
  delta_cmd = diff([samples.m_0_2_607A_00h_position_reference]);
  filler = ifelse(delta_fb, delta_fb, delta_cmd);
  fixed_delta_fb = delta_fb + filler;

  hold off;

end


function sanity_checks (samples)
  ## position cmd should be the same in HAL, ECAT out & ECAT in
  num_not_equal = length(
                      [samples(
                           [samples.joint3_drive_pos_cmd_s32] ~=
                           [samples.m_0_2_607A_00h_position_reference]
                         )]
                    );
  if (num_not_equal > 0)
    disp("Position cmd:  Number of ECAT out packets not matching HAL:");
    disp(num_not_equal)
  end
  num_not_equal = length(
                      [samples(
                           [samples.joint3_drive_pos_cmd_s32] ~=
                           [samples.s_0_2_607A_00h_position_reference]
                         )]
                    );
  if (num_not_equal > 0)
    disp("Position cmd:  Number of ECAT in packets not matching HAL:");
    disp(num_not_equal)
  end
    ## position fb should be the same in HAL & ECAT in
    ## - skip initial samples, which get messed up by ethercat pcap cmd
  not_equal = [samples(
                   [samples.joint3_drive_pos_fb_s32] ~=
                   [samples.s_0_2_6064_00h_position_actual_value]
                 ).sample];
  if (length(not_equal) > 0)
    disp("Position fb:  ECAT in packets not matching HAL:  (count, sample #)");
    disp(length(not_equal));
    disp(num2cell(not_equal));
  end
end
