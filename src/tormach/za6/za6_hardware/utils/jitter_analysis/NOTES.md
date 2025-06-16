# Jitter analysis

NOTE:  These scripts should be considered notes to reproduce timing
charts on the Confluence [EtherCAT+and+RT+Jitter page][1].  They may
well not run on their own as they are.

NOTE:  These scripts required an update EtherCAT master with the
`ethercat pcap` command fixed.

[1]:  https://tormach.atlassian.net/wiki/spaces/ENG/pages/3196715105/EtherCAT+and+RT+Jitter

## Quick start

Start the robot, either normally or headless.

Capture 20 seconds of data from `halsampler` and `ethercat pcap`.

    bash -xe jitter.sh capture my_tag_name

Merge the `halsampler` and `pcap` data into `.csv` file by correlating
sampler output and EtherCAT incoming + outgoing datagrams.

    bash -xe jitter.sh merge my_tag_name

Load data into Octave

    ## Field definitions; changes depending on joint under analysis
    fields_drive_err = { ...
       "sample_number", "counter", ...
       "cycle_start_time_s", "cycle_start_time_ns", ...
       "cycle_exec_time", "read_exec_time", "write_exec_time", ...
       "joint6_drive_pos_cmd_s32", "joint6_drive_pos_fb_s32", ...
       "joint6_drive_pos_err_s32", ...
       "m_timestamp", "m_0_5_60FF_00h_counter", ...
       "m_0_5_607A_00h_position_reference", "m_0_5_6064_00h_position_actual_value", ...
       "m_0_5_60F4_00h_following_error_actual_value", ...
       "s_timestamp", "s_0_5_60FF_00h_counter" ...
       "s_0_5_607A_00h_position_reference", "s_0_5_6064_00h_position_actual_value", ...
       "s_0_5_60F4_00h_following_error_actual_value", ...

    ## Load samples
    samples_fname = "/tmp/jitter_capture/collated_drive_err.csv"
    samples = load_samples(samples_fname, fields_drive_err)

Plot samples

    ## HAL-centric plot
    ruw_timings(samples)
    ## ECAT-centric plot
    wru_timings(samples)


## Running

```
# Load `collated.generic.csv`
load_samples; samples = load_csv("generic");
# Plot samples, cutting off initial junk
plot_functs; plot_ferror_pos (samples(5000:end));
```

Plot manipulation with gnuplot backend without messing up areas:
- Select a rectangle & zoom with right-click, left-click
- `=` (`+`) and `-` to zoom in and out
- Arrow keys to pan around

## Install Octave

Install Octave (v6.4.0)

    sudo apt-get install octave liboctave-dev

Install octave io pkg from within Octave

    pkg install -forge io

## Octave cheat sheet

https://en.wikibooks.org/wiki/Octave_Programming_Tutorial
https://docs.octave.org/v6.4.0/

    ## help
    help

    ## Set printed value digits to max
    output_precision(16)

    ## Comments start with #
    %% or %

    ## Matrices:  Definition
    % Row vectors
    A = [1, 2, 3]  % print format:  "1 2 3"
    R1 = 2:4  % -> [2, 3, 4]  (Range from 2-4)
    R2 = 1:3:10  % -> [1, 4, 7, 10]  (Range from 1-10, incr. 3)
    % Column vectors
    B = [1; 2; 3]  % print format:  "1\n 2\n 3"
    % Matrix
    C = [1.1, 1.2, 1.3; 2.1, 2.2, 2.3; 3.1, 3.2, 3.3]
    % Misc. vector/matrix generation functions
    ones(2,3)  % -> [1,1,1; 1,1,1]  (2x3 matrix filled with 1)
    zeros(2)  % -> [0,0; 0,0]  (2x2 matrix filled with 0)
    rand(1,3)  % -> 2 len row vec, uniform random #s btw. 0..1; randn() (normal)
    randperm(4)  % -> 4 len row vec, 1:4 ordered randomly (1 dim only)
    diag(A)  % -> 3x3 matrix of zeros, diag elements from A
    diag(C)  % -> row vec with diag elements from C
    linspace(0,1,3) % -> [0.0, 0.5, 1.0]  (3 elements, 0..1);  also logspace()


    ## Matrices:  Indexing
    % Row/column vector:  index element
    A(1)  % -> 1  % first index is 1 ;(
    B(1)  % -> 1
    % Matrix: index element, row, column
    C(1,2)  % -> 1.2
    C(1,:)  % -> [1.1, 1.2, 1.3]  (row 1, as row vector)
    C(:,2)  % -> [1.2; 2.2; 3.2]  (column 2, as column vector)
    C(:,3)'  % -> [1.2, 2.2, 3.2]  (column 2, as row vector)
    C(:,end)  % -> [1.2; 2.3; 3.3]  (last column, as column vector)
    % Index multiple elements
    A([1,3])  % -> [1, 3]
    C([2,3], [1,2])  % -> [2.1, 2.2; 3.1, 3.2]  (select rows 2,3 & cols 1,2)
    % Index range of elements
    R2(2:4)  % -> [4, 7, 10]
    R2(2:end)  % -> [4, 7, 10]  (same as above)

    ## Matrices:  Operations
    length(C)  % -> 3; returns length of largest dimension
    size(C)  % -> [3,3]; returns len. 2 vector of dims (even scalars)
    % Dot operations:  apply operator element by element (not linear algebra)
    A .* B'  % -> [1, 4, 9]
    % Flipping, transposing
    fliplr(C)  % -> [1.3, 1.2, 1.1; 2.3, 2.2, 2.1; 3.3, 3.2, 3.1]
    flipud(C)  % -> [3.1, 3.2, 3.3; 2.1, 2.2, 2.3; 1.1, 1.2, 1.3]
    rot90(C)  % Rotate matrix counterclockwise; 2nd opt arg: # rotations
    reshape(R2,2,2)  % -> [1,7; 4,10]
    sort(A)  % Sort elements; vec col or matrix, sort elements within columns

    ## Cell arrays
    names = { "foo", "bar" };
    name_foo = names{1};

    ## Comma-separated lists
    % Type for function argument and return values
