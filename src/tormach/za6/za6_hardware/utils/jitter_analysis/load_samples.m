function samples = load_samples(
                       samples_fname, fields, samples_from=5000, samples_to=1e99
                     )
  pkg load io;

  samples_c = csv2cell(samples_fname);
  samples_rows = strrep(strrep(samples_c(1,:), ".", "_"), "-", "_");
  samples_all = cell2struct( samples_c(2:end,:), samples_rows, 2);

  ## `fields` must name fields in samples_all that correspond to
  ## these generic names, in this order
  fields_xlate = {
                  ## halsampler
                  "sample",
                  "counter",
                  "cycle_start_time_s",
                  "cycle_start_time_ns",
                  "cycle_exec_time",
                  "read_exec_time",
                  "write_exec_time",
                  "hal_pos_cmd",
                  "hal_pos_fb",
                  "hal_ferror",

                  ## ECAT master
                  "m_timestamp",
                  "m_counter",
                  "m_pos_cmd",
                  "m_pos_fb",
                  "m_ferror",

                  ## ECAT slaves
                  "s_timestamp",
                  "s_counter",
                  "s_pos_cmd",
                  "s_pos_fb",
                  "s_ferror",
  }.';

  ## Create new struct array with subset of samples and subset of fields

  ## Subset of samples:
  ## Initial sample timestamps & other things are unstable because the
  ## `ethercat pcap` command thrashes RT timings.  Just skip them.
  samples_from = max(samples_from, 20);
  samples_to = min(length(samples_all), samples_to);
  num_samps = samples_to-samples_from+1;
  samples_sub = samples_all(samples_from:samples_to);

  ## Subset of fields:
  ## Cherry-pick columns matching `fields` into cell array
  for i = 1:length(fields)
    field = fields{i};
    fieldx = fields_xlate{i};
    if (strcmp(fieldx, "m_ferror") || strcmp(fieldx, "s_ferror"))
      ## Special handling for ferror; sometimes parsed as uint?
      field_values{i} = num2cell(
                         ifelse(
                             [samples_sub.(field)] > 2^31,
                             [samples_sub.(field)] - 2^32,
                             [samples_sub.(field)]
                           )
      );
    else
      field_values{i} = {samples_sub.(field)};
    end
  end;
  ## Fix up HAL timestamps
  field_names = {fields_xlate{1:2}, "h_timestamp", fields_xlate{5:20}};
  secs = [field_values{3}{1:end}];
  nsecs = [field_values{4}{1:end}];
  h_timestamps = num2cell(secs + nsecs/1e9);
  field_values = {field_values{1:2}, h_timestamps, field_values{5:20}};

  ## A 2 x (length(fields)) cell that flattens out into args to
  ## struct() with translated field names
  struct_data = [
                 "sample", field_names;
                 {num2cell(1:num_samps), field_values{:}}
  ];
  ## The resulting struct array
  samples = struct(struct_data{:}).';

end
